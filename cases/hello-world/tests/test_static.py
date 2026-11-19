"""Hidden check for the hello-world case: only prompt.md is ever shown to the agent."""


def test_hello_file_has_the_expected_content(sample):
    assert (sample / "project" / "hello.txt").read_text() == "Hello, world!\n"
