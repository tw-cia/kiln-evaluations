"""Turn a finished pipeline run into OpenTelemetry spans: one per job, plus a `run.summary` for the whole run.

Reads the jobs' results and outputs from $NEEDS (the `toJSON(needs)` of the report job), so nothing here runs agent
code or reads agent files: the values are treated as data and only ever become span attributes.
Sends OTLP/JSON to $OTEL_EXPORTER_OTLP_ENDPOINT/v1/traces. It never fails the pipeline: telemetry is best-effort.
"""

import hashlib
import json
import os
import sys
import urllib.request

# outputs that describe the run rather than one job: they go on the summary only
SUMMARY_KEYS = ("turns", "tool_calls", "tokens_input", "tokens_output", "tokens_reasoning", "tokens_cache_read",
                "tokens_cache_write", "cost", "tests_passed", "tests_failed", "prompt_sha256", "config_sha256")


def _value(text):
    """OTLP attribute value from a string output: ints and floats stay numbers so they can be aggregated."""
    for cast, key in ((int, "intValue"), (float, "doubleValue")):
        try:
            number = cast(text)
        except (TypeError, ValueError):
            continue
        return {key: str(number) if key == "intValue" else number}
    return {"stringValue": str(text)}


def _attributes(values):
    return [{"key": key, "value": _value(value)} for key, value in values.items() if value not in (None, "")]


def _parse_pairs(text):
    pairs = {}
    for item in (text or "").split(","):
        key, _, value = item.partition("=")
        if key.strip():
            pairs[key.strip()] = value
    return pairs


def _span(trace_id, name, start, end, ok, attributes):
    digest = hashlib.sha256(f"{trace_id}/{name}".encode()).hexdigest()
    return {
        "traceId": trace_id,
        "spanId": digest[:16],
        "name": name,
        "kind": 1,
        "startTimeUnixNano": str(int(start * 1e9)),
        "endTimeUnixNano": str(int(end * 1e9)),
        "attributes": _attributes(attributes),
        "status": {"code": 1 if ok else 2},
    }


def build(needs, resource):
    key = f"{resource.get('github.run_id')}-{resource.get('github.run_attempt')}-{resource.get('case')}-{resource.get('model')}"
    trace_id = hashlib.sha256(key.encode()).hexdigest()[:32]
    spans, summary, starts, ends, failed = [], {}, [], [], None
    for job, info in needs.items():
        if info.get("result") == "skipped":
            continue
        outputs = info.get("outputs") or {}
        try:
            start, end = float(outputs["started"]), float(outputs["ended"])
        except (KeyError, ValueError):
            continue  # the job never got far enough to record its times
        starts.append(start)
        ends.append(end)
        ok = info.get("result") == "success"
        if not ok and failed is None:
            failed = job
        own = {k: v for k, v in outputs.items() if k not in ("started", "ended") and k not in SUMMARY_KEYS}
        spans.append(_span(trace_id, f"pipeline.{job}", start, end, ok, {"job": job, "result": info.get("result"), **own}))
        summary.update({k: v for k, v in outputs.items() if k in SUMMARY_KEYS})
    if spans:
        start, end = min(starts), max(ends)
        spans.append(_span(trace_id, "run.summary", start, end, failed is None, {
            "verdict": "passed" if failed is None else f"failed at {failed}",
            "duration_seconds": round(end - start),
            **summary,
        }))
    return {"resourceSpans": [{
        "resource": {"attributes": _attributes({"service.name": "pipeline", **resource})},
        "scopeSpans": [{"scope": {"name": "kiln-evaluations"}, "spans": spans}],
    }]}


def main():
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").rstrip("/")
    if not endpoint:
        print("OTEL_EXPORTER_OTLP_ENDPOINT is not set: nothing to send")
        return 0
    payload = build(json.loads(os.environ["NEEDS"]), _parse_pairs(os.environ.get("OTEL_RESOURCE_ATTRIBUTES")))
    count = len(payload["resourceSpans"][0]["scopeSpans"][0]["spans"])
    headers = {"Content-Type": "application/json", **_parse_pairs(os.environ.get("OTEL_EXPORTER_OTLP_HEADERS"))}
    request = urllib.request.Request(f"{endpoint}/v1/traces", json.dumps(payload).encode(), headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            print(f"sent {count} spans: HTTP {response.status}")
    except Exception as error:  # best-effort: report it, never fail the run
        print(f"could not send {count} spans: {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
