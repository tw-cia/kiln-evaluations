# Kiln Evaluations

Measures how well an LLM agent can use kiln, and therefore how good kiln's documentation and tooling are. The agent is evaluated blind: it never sees how it will be judged.

## Language

**Case**:
A task given to the agent, together with the checks that judge the result.
_Avoid_: Test case, scenario, eval

**Prompt**:
The part of a case the agent sees: the task, worded as a user would ask it.
_Avoid_: Task, instruction

**Sample**:
One attempt at a case. A case is attempted several times because the agent's results vary.
_Avoid_: Trial, iteration, attempt

**Output**:
Everything one sample produces: the project the agent worked in, the transcript of the session, and the manifest describing it.
_Avoid_: Result, artifact

**Check**:
One assertion about an output, and the unit of grading. Hidden from the agent.
_Avoid_: Test, assertion

**Static check**:
A check that inspects an output without deploying it: its tests pass, it generates, and it renders.
_Avoid_: Offline check, unit check

**Live check**:
A check that applies an output to a real cluster and cloud account and probes what got created. Only samples whose static checks all pass are applied.
_Avoid_: Integration check, e2e check

**Run**:
One execution of the whole pipeline: every case sampled, then every output checked.
_Avoid_: Job, build, workflow

**Blind**:
The agent sees only its own prompt while generating; no check, other case, or grading detail is visible to it.
_Avoid_: Sandboxed, hidden (those name mechanisms, not the property)

**Research**:
Looking outside kiln's own documentation and skills during a sample, such as web searches or fetches and network commands in a shell. Recorded and penalized, never blocked, since needing it signals a gap in kiln's documentation.
_Avoid_: Lookup, browsing, external access
