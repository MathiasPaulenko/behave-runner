"""Step definitions for saucedemo login feature."""

from __future__ import annotations

from typing import Any

from behave import given, then, when
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://www.saucedemo.com"


def _wait(context: Any, timeout: int = 20) -> WebDriverWait:
    """Create a WebDriverWait for the current browser."""
    return WebDriverWait(context.browser, timeout)


@given("I am on the saucedemo login page")
def step_on_login_page(context: Any) -> None:
    """Navigate to the saucedemo login page."""
    context.browser.get(BASE_URL)
    _wait(context).until(EC.presence_of_element_located((By.ID, "login-button")))


@when('I login with username "{username}" and password "{password}"')
def step_login(context: Any, username: str, password: str) -> None:
    """Fill in login form and submit."""
    _wait(context).until(EC.presence_of_element_located((By.ID, "user-name"))).send_keys(username)
    context.browser.find_element(By.ID, "password").send_keys(password)
    context.browser.find_element(By.ID, "login-button").click()


@then("I should see the products page")
def step_should_see_products(context: Any) -> None:
    """Verify the products page is displayed."""
    _wait(context).until(EC.presence_of_element_located((By.CLASS_NAME, "inventory_list")))


@then("I should see an error message")
def step_should_see_error(context: Any) -> None:
    """Verify an error message is displayed."""
    _wait(context).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='error']")))


@given("I am logged in as a standard user")
def step_logged_in_standard(context: Any) -> None:
    """Log in as standard_user."""
    context.browser.get(BASE_URL)
    _wait(context).until(EC.presence_of_element_located((By.ID, "user-name"))).send_keys(
        "standard_user"
    )
    context.browser.find_element(By.ID, "password").send_keys("secret_sauce")
    context.browser.find_element(By.ID, "login-button").click()
    _wait(context).until(EC.presence_of_element_located((By.CLASS_NAME, "inventory_list")))
