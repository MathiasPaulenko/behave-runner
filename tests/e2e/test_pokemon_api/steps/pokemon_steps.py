"""Step definitions for Pokémon API feature."""

from __future__ import annotations

from typing import Any

from behave import given, then


@given('I request pokemon "{name}"')
def step_request_pokemon(context: Any, name: str) -> None:
    """Request a Pokémon by name from the API."""
    url = f"{context.base_url}/pokemon/{name}"
    context.response = context.session.get(url, timeout=30)


@then("the response status should be {status:d}")
def step_response_status(context: Any, status: int) -> None:
    """Verify the response status code."""
    assert context.response.status_code == status, (
        f"Expected {status}, got {context.response.status_code}"
    )


@then('the pokemon name should be "{name}"')
def step_pokemon_name(context: Any, name: str) -> None:
    """Verify the Pokémon name in the response."""
    data = context.response.json()
    assert data["name"] == name, f"Expected {name}, got {data['name']}"


@then("the pokemon should have stats")
def step_pokemon_has_stats(context: Any) -> None:
    """Verify the Pokémon has stats in the response."""
    data = context.response.json()
    stats = data.get("stats", [])
    assert len(stats) > 0, "Pokemon should have stats"
