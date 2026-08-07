# behave-runner

CLI completa para Behave con subcomandos — punto de entrada unificado del
ecosistema BehaveLib.

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
- **report** — Generate test reports (HTML, JSON, Markdown, XLSX, PDF)
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
behave-runner init my-project

# Run all tests
behave-runner run features/

# List scenarios
behave-runner list features/

# Run only smoke tests
behave-runner run --tags @smoke features/

# Generate JSON report
behave-runner run --format json --output reports/results.json features/
```

## Configuration

Configure `behave-runner` via `pyproject.toml`:

```toml
[tool.behave-runner]
default_parallel = 4
output_dir = "reports"

[tool.behave-runner.profiles.ci]
parallel = 8
format = "json"
```

## License

MIT
