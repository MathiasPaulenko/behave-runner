"""Step definitions for Pokémon Types API feature."""

from __future__ import annotations

from typing import Any

from behave import given, then


@given('I request type "{name}"')
def step_request_type(context: Any, name: str) -> None:
    """Request a Pokémon type by name from the API."""
    url = f"{context.base_url}/type/{name}"
    context.response = context.session.get(url, timeout=30)


@then('the type name should be "{name}"')
def step_type_name(context: Any, name: str) -> None:
    """Verify the type name in the response."""
    data = context.response.json()
    assert data["name"] == name, f"Expected {name}, got {data['name']}"


@then("the type should have damage relations")
def step_type_has_damage_relations(context: Any) -> None:
    """Verify the type has damage relations in the response."""
    data = context.response.json()
    relations = data.get("damage_relations", {})
    assert "double_damage_from" in relations, "Type should have damage relations"
