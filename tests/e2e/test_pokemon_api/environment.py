"""Environment for Pokémon API E2E tests."""

from __future__ import annotations

from typing import Any

import requests

BASE_URL = "https://pokeapi.co/api/v2"


def before_all(context: Any) -> None:
    """Set up requests session with base URL."""
    context.session = requests.Session()
    context.base_url = BASE_URL


def after_all(context: Any) -> None:
    """Close requests session."""
    if hasattr(context, "session"):
        context.session.close()
