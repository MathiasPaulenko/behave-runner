"""Step definitions for priority test fixture."""

from behave import given, then


@given("a step")
def step_given(context):
    pass


@then("I verify priority")
def step_verify_priority(context):
    pass


@then("I verify smoke")
def step_verify_smoke(context):
    pass
