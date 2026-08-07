# behave-runner

A unified CLI entry point for the Behave BDD ecosystem with subcommands for
running, listing, selecting, linting, formatting, watching, reporting and more.

## Features

- **run** — Execute behave tests with parallel, retries, sharding, and
  priority support
- **list** — List all scenarios from feature files
- **select** — Filter scenarios by tags, patterns, or feature names
- **lint** — Lint feature files for best practices
- **format** — Format feature files automatically
- **doctor** — Diagnose project health
- **impact** — Detect scenarios affected by code changes
- **watch** — Re-run tests on file changes
- **report** — Generate test reports (console, HTML, Markdown, JSON, sheets, file)
- **trace** — Visual trace of test execution
- **steps** — Manage step libraries
- **generate** — Scaffold new projects
- **config** — Manage configuration

## Installation

```bash
pip install behave-runner
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

```bash
# Initialize a new behave project
behave-runner init --name my-project

# Run all tests
behave-runner run features/

# List scenarios
behave-runner list features/

# Run only smoke tests
behave-runner run --tags @smoke features/

# Generate HTML report
behave-runner report generate --format html features/
```

## Configuration

Configure `behave-runner` via `pyproject.toml`:

```toml
[tool.behave-runner]
parallel = 4

[tool.behave-runner.profiles.smoke]
tags = ["@smoke"]

[tool.behave-runner.profiles.ci]
parallel = 8
format = "json"
output = "reports/ci.json"
```

Or use a classic `behave.ini` file. Run `behave-runner config show` to inspect
configuration.

## License

MIT
