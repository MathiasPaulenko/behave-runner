"""Step definitions for saucedemo cart feature."""

from __future__ import annotations

from typing import Any

from behave import given, then, when
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.support.ui import WebDriverWait


def _wait(context: Any, timeout: int = 15) -> WebDriverWait:
    """Create a WebDriverWait for the current browser."""
    return WebDriverWait(context.browser, timeout)


@when("I add the first product to the cart")
def step_add_first_product(context: Any) -> None:
    """Add the first product to the cart."""
    btn = _wait(context).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test^='add-to-cart']"))
    )
    btn.click()


@when("I remove the first product from the cart")
def step_remove_first_product(context: Any) -> None:
    """Remove the first product from the cart."""
    btn = _wait(context).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test^='remove-']"))
    )
    btn.click()
    _wait(context).until(EC.invisibility_of_element_located((By.CLASS_NAME, "shopping_cart_badge")))


@given("I have added the first product to the cart")
def step_have_added_first_product(context: Any) -> None:
    """Ensure the first product is in the cart."""
    btn = _wait(context).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test^='add-to-cart']"))
    )
    btn.click()


@then('the cart badge should show "{count}"')
def step_cart_badge_count(context: Any, count: str) -> None:
    """Verify cart badge shows expected count."""
    badge = _wait(context).until(
        EC.presence_of_element_located((By.CLASS_NAME, "shopping_cart_badge"))
    )
    assert badge.text == count, f"Expected {count}, got {badge.text}"


@then("the cart badge should be empty")
def step_cart_badge_empty(context: Any) -> None:
    """Verify cart badge is not present or has no count."""
    badges = context.browser.find_elements(By.CLASS_NAME, "shopping_cart_badge")
    for badge in badges:
        if badge.is_displayed() and badge.text:
            raise AssertionError(f"Cart badge should be empty, got '{badge.text}'")


@when("I go to the cart")
def step_go_to_cart(context: Any) -> None:
    """Navigate to the cart page."""
    _wait(context).until(EC.element_to_be_clickable((By.CLASS_NAME, "shopping_cart_link"))).click()
    _wait(context).until(EC.presence_of_element_located((By.ID, "cart_contents_container")))
