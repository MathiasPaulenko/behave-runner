"""Step definitions for saucedemo checkout feature."""

from __future__ import annotations

from typing import Any

from behave import then, when
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.support.ui import WebDriverWait


def _wait(context: Any, timeout: int = 15) -> WebDriverWait:
    """Create a WebDriverWait for the current browser."""
    return WebDriverWait(context.browser, timeout)


@when('I checkout with first name "{first}" last name "{last}" and zip "{zip_code}"')
def step_checkout_info(context: Any, first: str, last: str, zip_code: str) -> None:
    """Fill in checkout information."""
    _wait(context).until(EC.element_to_be_clickable((By.ID, "checkout"))).click()
    _wait(context).until(EC.presence_of_element_located((By.ID, "first-name"))).send_keys(first)
    context.browser.find_element(By.ID, "last-name").send_keys(last)
    context.browser.find_element(By.ID, "postal-code").send_keys(zip_code)
    context.browser.find_element(By.ID, "continue").click()
    _wait(context).until(EC.presence_of_element_located((By.ID, "checkout_summary_container")))


@when("I finish the checkout")
def step_finish_checkout(context: Any) -> None:
    """Complete the checkout."""
    _wait(context).until(EC.element_to_be_clickable((By.ID, "finish"))).click()


@then("I should see the checkout complete message")
def step_should_see_checkout_complete(context: Any) -> None:
    """Verify checkout complete message is displayed."""
    _wait(context).until(EC.presence_of_element_located((By.ID, "checkout_complete_container")))
