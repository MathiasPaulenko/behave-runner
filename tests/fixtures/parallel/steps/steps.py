"""Step definitions for parallel test feature."""

from behave import given, then, when


@given("a step")
def step_given(context):
    pass


@when("I do something {n}")
def step_when(context, n):
    pass


@then("I verify {n}")
def step_then(context, n):
    pass
