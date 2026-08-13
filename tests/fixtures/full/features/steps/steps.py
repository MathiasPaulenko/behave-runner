"""Steps for the full test fixture."""

from behave import given, then, when


# --- Auth steps ---

@given("I am on the login page")
def step_on_login_page(context):
    context.on_login_page = True


@when("I enter valid credentials")
def step_valid_creds(context):
    context.logged_in = True


@when("I enter invalid credentials")
def step_invalid_creds(context):
    context.logged_in = False
    context.error_message = "Invalid username or password"


@when("I enter invalid credentials 3 times")
def step_invalid_3_times(context):
    context.logged_in = False
    context.account_locked = True
    context.lockout_message = "Account locked after 3 failed attempts"


@then("I should be logged in")
def step_should_be_logged_in(context):
    assert getattr(context, "logged_in", False), "Expected to be logged in"


@then("I should not be logged in")
def step_should_not_be_logged_in(context):
    assert not getattr(context, "logged_in", True), "Expected NOT to be logged in"


@then("I should see the dashboard")
def step_see_dashboard(context):
    assert getattr(context, "logged_in", False)


@then("I should see an error message")
def step_see_error(context):
    assert getattr(context, "error_message", None) is not None


@then("my account should be locked")
def step_account_locked(context):
    assert getattr(context, "account_locked", False)


@then("I should see a lockout message")
def step_see_lockout(context):
    assert getattr(context, "lockout_message", None) is not None


@given("I am logged in")
def step_logged_in(context):
    context.logged_in = True


@when("I click logout")
def step_click_logout(context):
    context.logged_in = False
    context.session_cleared = True


@then("my session should be cleared")
def step_session_cleared(context):
    assert getattr(context, "session_cleared", False)


@then("I should be redirected to login")
def step_redirected_to_login(context):
    assert not getattr(context, "logged_in", True)


# --- Cart steps ---

@given("I have an empty cart")
def step_empty_cart(context):
    context.cart = []
    context.cart_total = 0


@given("I have a cart with 2 items")
def step_cart_with_2(context):
    context.cart = [{"price": 10}, {"price": 20}]
    context.cart_total = 30


@given("I have a cart with items totaling 100")
def step_cart_totaling_100(context):
    context.cart = [{"price": 100}]
    context.cart_total = 100


@when("I add a product priced at {price:d}")
def step_add_product(context, price):
    context.cart.append({"price": price})
    context.cart_total = sum(item["price"] for item in context.cart)


@when("I remove the first item")
def step_remove_first(context):
    if context.cart:
        context.cart.pop(0)
        context.cart_total = sum(item["price"] for item in context.cart)


@when("I apply a discount of {percent:d} percent")
def step_apply_discount(context, percent):
    context.cart_total = int(context.cart_total * (100 - percent) / 100)


@then("my cart should have {count:d} item")
def step_cart_count(context, count):
    assert len(context.cart) == count, f"Expected {count} items, got {len(context.cart)}"


@then("my cart should have {count:d} items")
def step_cart_count_plural(context, count):
    assert len(context.cart) == count, f"Expected {count} items, got {len(context.cart)}"


@then("the cart total should be {total:d}")
def step_cart_total(context, total):
    assert context.cart_total == total, f"Expected {total}, got {context.cart_total}"


# --- Failure steps ---

@given("I have a failing step")
def step_failing(context):
    assert False, "Intentional failure for testing"


@then("the scenario should fail")
def step_should_fail(context):
    assert False, "This step should not be reached"
