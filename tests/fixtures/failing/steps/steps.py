"""Step definitions for failing test fixture."""

from behave import given, then, when


@given("a step")
def step_given(context):
    pass


@when("I do something that fails")
def step_fail(context):
    assert False, "Intentional failure"  # noqa: B011, S101


@then("I should see a failure")
def step_see_failure(context):
    pass
