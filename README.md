# behave-runner

> A unified CLI entry point for the Behave BDD ecosystem.

<!-- markdownlint-disable MD013 -->
[![CI](https://github.com/MathiasPaulenko/behave-runner/actions/workflows/ci.yml/badge.svg)](https://github.com/MathiasPaulenko/behave-runner/actions/workflows/ci.yml)
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
- Reports in console, HTML, Markdown, JSON, XLSX and PDF formats.
- Trace viewer and web dashboard support.
- Step library management and feature/step generation.
- Impact analysis to detect scenarios affected by code changes.
- Graceful degradation when optional extras are missing.

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
pip install -e ".[dev]"
pre-commit install
```

## Quick Start

```bash
behave-runner init
behave-runner run
behave-runner list
behave-runner watch
```

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

## License

MIT
