---
title: Installation
description: Install behave-runner with pip, optional extras, or from source.
---

## Requirements

- Python 3.11 or newer
- A working `pip` installation

## Install from PyPI

The fastest way to get started is to install the base package:

```bash
pip install behave-runner
```

This installs the CLI, the core orchestrator, and the integration with
[behave](https://github.com/behave/behave),
[behave-kit](https://github.com/MathiasPaulenko/behave-kit), and
[behave-model](https://github.com/MathiasPaulenko/behave-model).

## Optional extras

`behave-runner` follows a modular design. Optional features are shipped as
extras so you only install what you need.

| Extra | Enables |
| ----- | ------- |
| `parallel` | Parallel execution via [behave-pool](https://github.com/MathiasPaulenko/behave-pool) |
| `priority` | Priority ordering via [behave-priority](https://github.com/MathiasPaulenko/behave-priority) |
| `retry` | Retry failed scenarios via [behave-retry](https://github.com/MathiasPaulenko/behave-retry) |
| `trace` | Trace viewer and UI mode via [behave-trace](https://github.com/MathiasPaulenko/behave-trace) |
| `lint` | Feature file linting via [behave-lint](https://github.com/MathiasPaulenko/behave-lint) |
| `format` | Feature file formatting via [behave-format](https://github.com/MathiasPaulenko/behave-format) |
| `doctor` | Project health checks via [behave-doctor](https://github.com/MathiasPaulenko/behave-doctor) |
| `gen` | Project scaffolding via [behave-gen](https://github.com/MathiasPaulenko/behave-gen) |
| `steplib` | Step library management via [behave-steplib](https://github.com/MathiasPaulenko/behave-steplib) |
| `comments` | Comment extraction via [behave-comments](https://github.com/MathiasPaulenko/behave-comments) |
| `report-html` | HTML reports via [behave-modern-html-report](https://github.com/MathiasPaulenko/behave-modern-html-report) |
| `report-md` | Markdown reports via [behave-modern-md-report](https://github.com/MathiasPaulenko/behave-modern-md-report) |
| `report-json` | JSON reports via [behave-modern-json-report](https://github.com/MathiasPaulenko/behave-modern-json-report) |
| `report-console` | Console reports via [behave-modern-console-report](https://github.com/MathiasPaulenko/behave-modern-console-report) |
| `report-sheets` | Spreadsheet reports via [behave-modern-sheets-report](https://github.com/MathiasPaulenko/behave-modern-sheets-report) |
| `report-file` | File reports via [behave-modern-file-report](https://github.com/MathiasPaulenko/behave-modern-file-report) |
| `record` | Browser recording via [wavexis](https://github.com/MathiasPaulenko/wavexis) |

Install one or more extras with brackets:

```bash
pip install "behave-runner[parallel,retry,report-html]"
```

!!! tip "Install everything"
    Use the `all` extra to install the full ecosystem in one command.

```bash
pip install "behave-runner[all]"
```

## Install from source

Clone the repository and install the package in editable mode with the
dependencies needed for development:

```bash
git clone https://github.com/MathiasPaulenko/behave-runner.git
cd behave-runner
pip install -e ".[dev]"
pre-commit install
```

This also installs `ruff`, `mypy`, `pytest`, and the pre-commit hooks so you can
run the same checks the CI runs.

!!! note "Documentation dependencies"
    Install the `docs` extra to build the documentation site locally.

```bash
pip install -e ".[docs]"
```

## Verify the installation

Check the installed version and list the available commands:

```bash
behave-runner --version
behave-runner --help
```

A working installation prints the version and a table with all top-level
commands.
