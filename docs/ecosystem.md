# Ecosystem

`behave-runner` is the unified entry point for the BehaveLib ecosystem.
It orchestrates 21 libraries across nine categories: core, execution,
debug, quality, scaffolding, steps, utility, recording, and reporting.
Each library is an independent package that can be used on its own, but
`behave-runner` ties them together with a single CLI.

## Quick reference

| Library | Category | Purpose | Extra |
| --- | --- | --- | --- |
| [behave](https://github.com/behave/behave) | Core | BDD framework. | included |
| [behave-kit](https://github.com/MathiasPaulenko/behave-kit) | Core | Timeouts and config profiles. | included |
| [behave-model](https://github.com/MathiasPaulenko/behave-model) | Core | Feature and scenario parsing. | included |
| [behave-pool](https://github.com/MathiasPaulenko/behave-pool) | Execution | Parallel and sharded runs. | parallel |
| [behave-priority](https://github.com/MathiasPaulenko/behave-priority) | Execution | Priority ordering and smoke flags. | priority |
| [behave-retry](https://github.com/MathiasPaulenko/behave-retry) | Execution | Retry and flaky report support. | retry |
| [behave-trace](https://github.com/MathiasPaulenko/behave-trace) | Debug | Trace viewer and UI. | trace |
| [behave-doctor](https://github.com/MathiasPaulenko/behave-doctor) | Quality | Project health and impact analysis. | doctor |
| [behave-lint](https://github.com/MathiasPaulenko/behave-lint) | Quality | Feature file linting. | lint |
| [behave-format](https://github.com/MathiasPaulenko/behave-format) | Quality | Feature file formatting. | format |
| [behave-gen](https://github.com/MathiasPaulenko/behave-gen) | Scaffolding | Project and feature generation. | gen |
| [behave-steplib](https://github.com/MathiasPaulenko/behave-steplib) | Steps | Step library management. | steplib |
| [behave-comments](https://github.com/MathiasPaulenko/behave-comments) | Utility | Comment metadata extraction. | comments |
| [behave-tables](https://github.com/MathiasPaulenko/behave-tables) | Utility | Table helpers. | — |
| [wavexis](https://github.com/MathiasPaulenko/wavexis) | Recording | Browser session recording. | record |
| [behave-modern-console-report](https://github.com/MathiasPaulenko/behave-modern-console-report) | Reporting | Console report. | report-console |
| [behave-modern-html-report](https://github.com/MathiasPaulenko/behave-modern-html-report) | Reporting | HTML report. | report-html |
| [behave-modern-md-report](https://github.com/MathiasPaulenko/behave-modern-md-report) | Reporting | Markdown report. | report-md |
| [behave-modern-json-report](https://github.com/MathiasPaulenko/behave-modern-json-report) | Reporting | JSON report. | report-json |
| [behave-modern-sheets-report](https://github.com/MathiasPaulenko/behave-modern-sheets-report) | Reporting | XLSX/CSV report. | report-sheets |
| [behave-modern-file-report](https://github.com/MathiasPaulenko/behave-modern-file-report) | Reporting | File report. | report-file |

---

## Core libraries

Installed by default with `pip install behave-runner`. These are the
minimum dependencies needed to parse and run Behave scenarios.

### [behave](https://github.com/behave/behave)

The foundational BDD framework for Python. It parses `.feature` files,
matches Gherkin steps to Python step definitions, and executes
scenarios. `behave-runner` builds the final `behave` command line from
your flags and delegates execution to it.

**Used by:** `run`, `list`, `select`, `watch`, `report generate`

### [behave-kit](https://github.com/MathiasPaulenko/behave-kit)

Provides per-scenario timeouts and configuration profile helpers.
`behave-runner` uses it to enforce `--scenario-timeout` and to load
named profiles from `pyproject.toml` or `behave.ini`.

**Used by:** `run` (`--scenario-timeout`, `--profile`), `watch` (`--profile`, `--scenario-timeout`)

### [behave-model](https://github.com/MathiasPaulenko/behave-model)

A standalone parser for `.feature` files. It produces a structured
representation of features, scenarios, steps, tags, and locations
without executing anything. `behave-runner` uses it to list and select
scenarios without running them.

**Used by:** `list`, `select`

---

## Execution libraries

Optional libraries that control how scenarios are distributed, ordered,
and retried during a run.

### [behave-pool](https://github.com/MathiasPaulenko/behave-pool)

Enables parallel test execution with worker processes. Supports
distribution schemes (`scenario`, `feature`), load-balancing strategies
(`lpt`, `round`), and CI sharding (`--shard i/n`). When `--parallel` is
set, `behave-runner` delegates to `behave-pool` instead of running
`behave` directly.

**Used by:** `run` (`--parallel`, `--shard`, `--parallel-scheme`, `--parallel-balance`, `--parallel-timing-file`), `watch` (`--parallel`)

**Install:**

```bash
pip install "behave-runner[parallel]"
```

### [behave-priority](https://github.com/MathiasPaulenko/behave-priority)

Allows scenarios to be executed in priority order based on annotations
or metadata. Also provides fail-fast semantics that stop the run at the
first failure while respecting priority.

**Used by:** `run` (`--priority-order`, `--fail-fast`), `watch` (`--priority-order`, `--fail-fast`)

**Install:**

```bash
pip install "behave-runner[priority]"
```

### [behave-retry](https://github.com/MathiasPaulenko/behave-retry)

Retries failed scenarios a configurable number of times and can
generate a flakiness report showing which scenarios are unstable across
retries.

**Used by:** `run` (`--retries`, `--flaky-report`), `watch` (`--retries`)

**Install:**

```bash
pip install "behave-runner[retry]"
```

---

## Debug libraries

### [behave-trace](https://github.com/MathiasPaulenko/behave-trace)

Provides a trace viewer and web dashboard for post-run analysis. It can
launch an interactive debugger, serve a UI dashboard, or generate trace
files that can be inspected after the run.

**Used by:** `run` (`--ui`, `--debug`, `--trace`), `watch` (`--ui`, `--debug`, `--trace`), `trace show`, `trace serve`, `open trace`

**Install:**

```bash
pip install "behave-runner[trace]"
```

---

## Quality libraries

Static analysis and formatting tools for `.feature` files.

### [behave-doctor](https://github.com/MathiasPaulenko/behave-doctor)

Diagnoses project health by scanning for common issues: missing step
definitions, unused steps, feature inconsistencies, and orphaned
scenarios. Also powers the impact-analysis feature that detects which
scenarios are affected by code changes.

**Used by:** `doctor`, `impact`

**Install:**

```bash
pip install "behave-runner[doctor]"
```

### [behave-lint](https://github.com/MathiasPaulenko/behave-lint)

Runs static analysis rules on `.feature` files to enforce best
practices: consistent naming, tag usage, scenario structure, and more.
All positional arguments are forwarded directly to `behave-lint`.

**Used by:** `lint`

**Install:**

```bash
pip install "behave-runner[lint]"
```

### [behave-format](https://github.com/MathiasPaulenko/behave-format)

Automatically formats `.feature` files to a consistent style. Supports
check-only mode (`--check`) and diff preview (`--diff`). Additional
arguments like `--in-place` are passed through to `behave-format`.

**Used by:** `format`

**Install:**

```bash
pip install "behave-runner[format]"
```

---

## Scaffolding libraries

### [behave-gen](https://github.com/MathiasPaulenko/behave-gen)

Generates project structures, feature file skeletons, and step
definitions from step libraries or browser recordings. It powers project
initialization, feature scaffolding, and step generation from
`wavexis` recordings.

**Used by:** `init`, `generate step`, `generate feature`, `record` (step generation phase)

**Install:**

```bash
pip install "behave-runner[gen]"
```

---

## Step libraries

### [behave-steplib](https://github.com/MathiasPaulenko/behave-steplib)

Manages reusable step libraries that provide common step definitions
for HTTP, databases, authentication, and more. You can list, search,
show, validate, install, and initialize autoload wiring for step
libraries.

**Used by:** `steps list`, `steps show`, `steps search`, `steps validate`, `steps init`, `steps install`

**Install:**

```bash
pip install "behave-runner[steplib]"
```

---

## Utility libraries

### [behave-comments](https://github.com/MathiasPaulenko/behave-comments)

Extracts and processes comments from `.feature` files. Useful for
documentation generation and annotation extraction.

**Install:**

```bash
pip install "behave-runner[comments]"
```

### [behave-tables](https://github.com/MathiasPaulenko/behave-tables)

Provides helpers for working with Gherkin data tables in step
definitions. Not directly required by `behave-runner`; install separately
if needed.

---

## Recording libraries

### [wavexis](https://github.com/MathiasPaulenko/wavexis)

Records browser interactions and exports them as YAML workflows.
`behave-runner record` launches `wavexis` to capture a session, then
optionally feeds the recording to `behave-gen` to generate step
definitions automatically.

**Used by:** `record`

**Install:**

```bash
pip install "behave-runner[record]"
```

---

## Reporting libraries

Six independent formatters that produce reports in different formats.
All are invoked through the `report generate` command by selecting the
appropriate `--format`.

### [behave-modern-console-report](https://github.com/MathiasPaulenko/behave-modern-console-report)

Pretty-prints test results to the terminal with colors and summary
tables.

**Used by:** `report generate --format console`

**Install:**

```bash
pip install "behave-runner[report-console]"
```

### [behave-modern-html-report](https://github.com/MathiasPaulenko/behave-modern-html-report)

Generates a self-contained HTML report with charts, scenario details,
and step-level timing.

**Used by:** `report generate --format html`

**Install:**

```bash
pip install "behave-runner[report-html]"
```

### [behave-modern-md-report](https://github.com/MathiasPaulenko/behave-modern-md-report)

Generates a Markdown report suitable for embedding in wikis, PRs, or
documentation sites.

**Used by:** `report generate --format md`

**Install:**

```bash
pip install "behave-runner[report-md]"
```

### [behave-modern-json-report](https://github.com/MathiasPaulenko/behave-modern-json-report)

Generates a machine-readable JSON report for CI integrations and
custom dashboards.

**Used by:** `report generate --format json`

**Install:**

```bash
pip install "behave-runner[report-json]"
```

### [behave-modern-sheets-report](https://github.com/MathiasPaulenko/behave-modern-sheets-report)

Generates XLSX/CSV spreadsheets with test results for tracking and
reporting.

**Used by:** `report generate --format sheets`

**Install:**

```bash
pip install "behave-runner[report-sheets]"
```

### [behave-modern-file-report](https://github.com/MathiasPaulenko/behave-modern-file-report)

Generates a plain-text file report for archival or log ingestion.

**Used by:** `report generate --format file`

**Install:**

```bash
pip install "behave-runner[report-file]"
```

---

## Installing groups

You can install libraries individually or use extras that bundle them:

```bash
# Core only
pip install behave-runner

# Execution extras
pip install "behave-runner[parallel,priority,retry]"

# Reporting extras
pip install "behave-runner[report-html,report-json]"

# Everything
pip install "behave-runner[all]"
```

## Graceful degradation

If a flag needs a library that is not installed, `behave-runner` prints a
warning and falls back to the nearest safe behavior instead of crashing.
For example, `--parallel 4` without `behave-pool` installed will run
scenarios sequentially with a warning.
