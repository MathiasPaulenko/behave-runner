"""Browser setup/teardown for saucedemo E2E tests."""

from __future__ import annotations

from typing import Any


def before_all(context: Any) -> None:
    """Set up Selenium WebDriver before all tests."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    context.browser = webdriver.Chrome(options=options)


def after_all(context: Any) -> None:
    """Tear down browser after all tests."""
    if hasattr(context, "browser"):
        context.browser.quit()


def before_scenario(context: Any, scenario: Any) -> None:
    """Reset browser state before each scenario."""
    if hasattr(context, "browser"):
        context.browser.delete_all_cookies()
        context.browser.get("about:blank")
