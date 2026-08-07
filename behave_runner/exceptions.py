"""Custom exceptions for behave-runner."""

from __future__ import annotations


class BehaveRunnerError(Exception):
    """Base exception for behave-runner."""


class DependencyMissingError(BehaveRunnerError):
    """Raised when an optional dependency is required but not installed."""

    def __init__(self, feature: str, package: str) -> None:
        self.feature = feature
        self.package = package
        super().__init__(
            f"Feature '{feature}' requires '{package}'. "
            f"Install with: pip install behave-runner[{feature}]"
        )


class ConfigError(BehaveRunnerError):
    """Raised when there is a configuration error."""
