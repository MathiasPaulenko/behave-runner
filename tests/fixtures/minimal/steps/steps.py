"""Step definitions for minimal login feature."""

from behave import given, then, when


@given("I am on the login page")
def step_on_login_page(context):
    pass


@when("I enter valid credentials")
def step_enter_credentials(context):
    pass


@then("I should be logged in")
def step_should_be_logged_in(context):
    pass
