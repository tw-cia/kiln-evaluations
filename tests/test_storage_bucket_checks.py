"""The storage-bucket checks, tested against hand-made Outputs: they must pass a good one and fail broken ones."""


def test_a_good_output_passes_the_kcl_tests_check(storage_bucket_checks):
    storage_bucket_checks.add_sample(1)

    outcomes = storage_bucket_checks.run()

    assert outcomes[("test_kcl_tests_pass", "storage-bucket-1")] == "passed"


def test_a_project_with_no_tests_fails_the_kcl_tests_check(storage_bucket_checks):
    storage_bucket_checks.add_sample(1, mutate=lambda project: (project / "kcl-scripts" / "storagebucket_test.k").unlink())

    outcomes = storage_bucket_checks.run()

    assert outcomes[("test_kcl_tests_pass", "storage-bucket-1")] == "failed"


def test_a_good_output_passes_the_xrd_check(storage_bucket_checks):
    storage_bucket_checks.add_sample(1)

    outcomes = storage_bucket_checks.run()

    assert outcomes[("test_xrd_declares_the_api", "storage-bucket-1")] == "passed"


def test_an_xrd_that_defaults_versioning_to_false_fails_the_xrd_check(storage_bucket_checks):
    def flip_the_default(project):
        xrd = next((project / "manifests" / "crossplane-compositions").glob("*/xrd.yaml"))
        text = xrd.read_text()
        assert "default: true" in text  # the fixture really has the default we are about to break
        xrd.write_text(text.replace("default: true", "default: false"))

    storage_bucket_checks.add_sample(1, mutate=flip_the_default)

    outcomes = storage_bucket_checks.run()

    assert outcomes[("test_xrd_declares_the_api", "storage-bucket-1")] == "failed"


def test_a_good_output_passes_the_generated_files_check(storage_bucket_checks):
    storage_bucket_checks.add_sample(1)

    outcomes = storage_bucket_checks.run()

    assert outcomes[("test_generated_files_are_current", "storage-bucket-1")] == "passed"


def test_a_hand_edited_generated_file_fails_the_generated_files_check(storage_bucket_checks):
    def hand_edit(project):
        composition = next((project / "manifests" / "crossplane-compositions").glob("*/composition.yaml"))
        composition.write_text(composition.read_text() + "# edited by hand\n")

    storage_bucket_checks.add_sample(1, mutate=hand_edit)

    outcomes = storage_bucket_checks.run()

    assert outcomes[("test_generated_files_are_current", "storage-bucket-1")] == "failed"


def test_every_sample_is_checked_on_its_own_with_ids_naming_case_and_sample(storage_bucket_checks):
    def no_tests(project):
        (project / "kcl-scripts" / "storagebucket_test.k").unlink()

    storage_bucket_checks.add_sample(1)
    storage_bucket_checks.add_sample(2, mutate=no_tests)
    storage_bucket_checks.add_sample(10)

    outcomes = storage_bucket_checks.run()

    assert outcomes[("test_kcl_tests_pass", "storage-bucket-1")] == "passed"
    assert outcomes[("test_kcl_tests_pass", "storage-bucket-2")] == "failed"
    assert outcomes[("test_kcl_tests_pass", "storage-bucket-10")] == "passed"
    assert {sample for _, sample in outcomes} == {"storage-bucket-1", "storage-bucket-2", "storage-bucket-10"}
