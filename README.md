# behave-runner

> A unified CLI entry point for the Behave BDD ecosystem.

<!-- markdownlint-disable MD013 -->
[![CI](https://github.com/MathiasPaulenko/behave-runner/actions/workflows/ci.yml/badge.svg)](https://github.com/MathiasPaulenko/behave-runner/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/MathiasPaulenko/behave-runner/branch/main/graph/badge.svg)](https://codecov.io/gh/MathiasPaulenko/behave-runner)
[![PyPI](https://img.shields.io/pypi/v/behave-runner)](https://pypi.org/project/behave-runner/)
[![Python](https://img.shields.io/pypi/pyversions/behave-runner)](https://pypi.org/project/behave-runner/)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://mathiaspaulenko.github.io/behave-runner/)
[![License](https://img.shields.io/pypi/l/behave-runner)](https://github.com/MathiasPaulenko/behave-runner/blob/main/LICENSE)
<!-- markdownlint-enable MD013 -->

`behave-runner` is a single, extensible command-line interface for the
[Behave](https://behave.readthedocs.io/) BDD ecosystem. It wraps common Behave
workflows into focused subcommands and degrades gracefully when optional plugins
are not installed.

## Why behave-runner?

- **One CLI for everything** — run, list, filter, lint, format, watch, report,
  trace, generate and analyze scenarios from one tool.
- **Plugin-friendly** — optional extras add parallel execution, retries,
  priority ordering, trace viewers, report formatters, step libraries and more
  without breaking core behavior.
- **Fast feedback** — watch mode, impact analysis and rich terminal output keep
  the test loop tight.
- **Project scaffolding** — initialize a new Behave project, generate steps or
  features, and validate project health with `doctor`.

## Features

- Run, list, select, lint, format, watch, report, trace, steps, impact,
  generate, init, config, open and record commands.
- Optional parallel execution, sharding, retries and priority ordering.
- Configuration profiles via `pyproject.toml` or `behave.ini`.
- Watch mode that re-runs tests when files change.
- Reports in console, HTML, Markdown, JSON, sheets and file formats.
- Trace viewer and web dashboard support.
- Step library management and feature/step generation.
- Impact analysis to detect scenarios affected by code changes.
- Graceful degradation when optional extras are missing.

## Requirements

- Python 3.11 or higher
- Behave ecosystem packages (installed automatically as optional extras)

## Installation

```bash
pip install behave-runner
```

To install all optional extensions:

```bash
pip install "behave-runner[all]"
```

For development:

```bash
git clone https://github.com/MathiasPaulenko/behave-runner.git
cd behave-runner
pip install -e ".[dev]"
pre-commit install
```

## Getting Started

### 1. Initialize a project

```bash
behave-runner init
```

This creates a standard Behave layout: `features/`, `features/steps/` and
`environment.py`.

### 2. List scenarios

```bash
behave-runner list
```

Shows every scenario in the project without running anything.

### 3. Run the suite

```bash
behave-runner run
```

Runs every feature. You can also target a specific feature or tag:

```bash
behave-runner run --tags @smoke
behave-runner run features/login.feature
```

### 4. Filter with `select`

```bash
behave-runner select --tags @smoke
behave-runner select --pattern "login"
```

### 5. Watch files

```bash
behave-runner watch
```

Re-runs `behave-runner run` whenever a `.feature`, `.py` or config file
changes. Press `Ctrl+C` to stop.

### 6. Lint and format

```bash
behave-runner lint
behave-runner format
```

### 7. Reports and traces

```bash
behave-runner report generate --format html
behave-runner report show
```

With `behave-trace` installed:

```bash
behave-runner trace show
```

### Configuration

You can store profiles in `pyproject.toml`:

```toml
[tool.behave-runner]
parallel = 4

[tool.behave-runner.profiles.smoke]
tags = ["@smoke"]

[tool.behave-runner.profiles.ci]
parallel = 8
format = "json"
```

Or use a classic `behave.ini` file. Run `behave-runner config show` to inspect
configuration.

## Commands

| Command     | Description                                              |
| ----------- | -------------------------------------------------------- |
| `run`       | Execute Behave tests.                                    |
| `watch`     | Re-run tests when files change.                          |
| `list`      | List scenarios without executing them.                   |
| `select`    | Filter scenarios by tags, regex or name.                 |
| `lint`      | Lint `.feature` files.                                   |
| `format`    | Format `.feature` files.                                 |
| `doctor`    | Check project health.                                    |
| `init`      | Initialize a new Behave project.                         |
| `generate`  | Generate steps or features.                              |
| `record`    | Record a browser session and generate steps.             |
| `report`    | Generate and open reports.                               |
| `trace`     | View traces or serve a trace dashboard.                  |
| `steps`     | Manage step libraries.                                   |
| `impact`    | Detect scenarios affected by code changes.               |
| `open`      | Open the latest report or trace in the default browser.  |
| `config`    | Manage configuration profiles.                           |

## Ecosystem

`behave-runner` is the entry point for the BehaveLib ecosystem. The libraries
below can be installed individually or through `behave-runner` extras.

<!-- markdownlint-disable MD013 -->

| Library                         | Category   | Purpose                                  | Extra            |
| ------------------------------- | ---------- | ---------------------------------------- | ---------------- |
| `behave`                        | Core       | BDD framework.                           | core             |
| `behave-kit`                    | Core       | Timeouts and config profiles.            | core             |
| `behave-model`                  | Core       | Feature and scenario parsing.            | core             |
| `behave-pool`                   | Execution  | Parallel and sharded runs.               | `parallel`       |
| `behave-priority`               | Execution  | Priority ordering and smoke flags.       | `priority`       |
| `behave-retry`                  | Execution  | Retry and flaky report support.          | `retry`          |
| `behave-trace`                  | Debug      | Trace viewer and UI.                     | `trace`          |
| `behave-doctor`                 | Quality    | Project health and impact analysis.      | `doctor`         |
| `behave-lint`                   | Quality    | Feature file linting.                    | `lint`           |
| `behave-format`                 | Quality    | Feature file formatting.                 | `format`         |
| `behave-gen`                    | Scaffold   | Project and feature generation.          | `gen`            |
| `behave-steplib`                | Steps      | Step library management.                 | `steplib`        |
| `behave-comments`               | Utility    | Comment metadata extraction.             | `comments`       |
| `behave-tables`                 | Utility    | Table helpers.                           | —                |
| `wavexis`                       | Recording  | Browser session recording.               | `record`         |
| `behave-modern-console-report`  | Reporting  | Console report.                          | `report-console` |
| `behave-modern-html-report`     | Reporting  | HTML report.                             | `report-html`    |
| `behave-modern-md-report`       | Reporting  | Markdown report.                         | `report-md`      |
| `behave-modern-json-report`     | Reporting  | JSON report.                             | `report-json`    |
| `behave-modern-sheets-report`   | Reporting  | XLSX/CSV report.                         | `report-sheets`  |
| `behave-modern-file-report`     | Reporting  | File report.                             | `report-file`    |

<!-- markdownlint-enable MD013 -->

Install groups:

```bash
# Execution extras
pip install "behave-runner[parallel,priority,retry]"

# Reporting extras
pip install "behave-runner[report-html,report-json]"

# Everything
pip install "behave-runner[all]"
```

## Documentation

Full documentation is available at:

<https://mathiaspaulenko.github.io/behave-runner/>

## Contributing

Contributions are welcome. Please read
[CONTRIBUTING.md](https://github.com/MathiasPaulenko/behave-runner/blob/main/CONTRIBUTING.md)
for guidelines.

## Links

- **Repository**: <https://github.com/MathiasPaulenko/behave-runner>
- **Issues**: <https://github.com/MathiasPaulenko/behave-runner/issues>
- **Discussions**: <https://github.com/MathiasPaulenko/behave-runner/discussions>
- **PyPI**: <https://pypi.org/project/behave-runner/>

## Acknowledgements

`behave-runner` is built on top of the
[Behave](https://behave.readthedocs.io/) BDD framework and the
[BehaveLib](https://github.com/MathiasPaulenko) ecosystem of plugins. It uses
[Typer](https://typer.tiangolo.com/) for the CLI and
[Rich](https://rich.readthedocs.io/) for terminal output.

## License

MIT
