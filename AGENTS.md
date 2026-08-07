# Agent Notes for behave-runner

This file captures project-specific conventions and verification steps discovered
while working on the codebase.

## Repository

- `behave-runner` is a unified CLI for the Behave BDD ecosystem.
- Entry point: `behave_runner.__main__:main`.
- Main Typer app: `behave_runner.cli.app:app`.

## Build

```powershell
python -m build
```

Builds `behave_runner-1.0.1.tar.gz` and `behave_runner-1.0.1-py3-none-any.whl`
in `dist/`.

## Lint / Type Checking

```powershell
ruff check .
ruff format --check .
mypy --strict behave_runner
```

## Test

Run the full suite (excluding e2e tests):

```powershell
pytest -m "not e2e_web and not e2e_api"
```

Run with coverage (required `fail_under = 90`):

```powershell
pytest --cov=behave_runner --cov-report=term-missing --cov-fail-under=90 -m "not e2e_web and not e2e_api"
```

## Security

```powershell
python -m bandit -r behave_runner -c pyproject.toml
```

Bandit is configured via `[tool.bandit]` in `pyproject.toml` and excludes the
`tests/` directory.

## Coverage

The project targets 90% coverage. As of the latest audit, the non-e2e test suite
reaches ~95% coverage with 287 passed tests.

## Notable Architecture

- `behave_runner/core/orchestrator.py` builds behave commands from `RunConfig`
  and delegates to optional packages (`behave-pool`, `behave-retry`,
  `behave-priority`, `behave-trace`) with graceful fallbacks.
- `behave_runner/core/config.py` loads `[tool.behave-runner]` from
  `pyproject.toml` or `[behave-runner]` from `behave.ini`, normalizing profile
  values to correct Python types.
- `behave_runner/commands/*.py` are thin Typer command wrappers that delegate to
  external `behave-*` CLIs.

## Common Pitfalls

- `behave.ini` uses flat dot-notation keys (e.g.
  `profiles.default.parallel = 4`) which are converted to nested dictionaries.
- Profile values may be strings from `behave.ini`; they must be coerced to
  `int`/`bool`/`list` before constructing `RunConfig`.
- `subprocess.run` calls use list arguments and `shell=False`; `# nosec` is used
  to suppress bandit B404/B603/B607 findings after manual review.
