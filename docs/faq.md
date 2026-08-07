# FAQ

## How do I run tests in parallel?

Install the `parallel` extra and use the `--parallel` flag:

```bash
pip install "behave-runner[parallel]"
behave-runner run --parallel 4 features/
```

## How do I retry flaky tests?

Install the `retry` extra and set `--retries`:

```bash
pip install "behave-runner[retry]"
behave-runner run --retries 2 features/
```

## How do I generate a JSON report?

Install the `report-json` extra and use `--format json`:

```bash
pip install "behave-runner[report-json]"
behave-runner run --format json --output reports/results.json features/
```

## How do I use profiles?

Define profiles in `pyproject.toml`:

```toml
[tool.behave-runner.profiles.ci]
parallel = 8
format = "json"
```

Then run:

```bash
behave-runner run --profile ci
```

## What happens if an optional dependency is missing?

`behave-runner` prints a warning and falls back to a safe behavior. For
example, if `behave-pool` is missing, `--parallel` is ignored and the run
proceeds sequentially.

## How do I watch files for changes?

Use the `watch` command:

```bash
behave-runner watch features/
```

It polls `features/`, `steps/`, `environment.py`, `behave.ini`, and
`pyproject.toml` and re-runs the suite on every change.

## How do I list all scenarios without running them?

```bash
behave-runner list features/
```

You can also export the list to JSON:

```bash
behave-runner list features/ --format json
```

## How do I find scenarios affected by code changes?

```bash
behave-runner impact $(git diff --name-only HEAD~1) --run
```

This uses `behave-doctor` to detect affected scenarios and runs them.

## How do I record a browser session?

Install the `record` extra and run:

```bash
pip install "behave-runner[record,gen]"
behave-runner record https://example.com
```

## Where are the reports saved?

By default, reports are written to `reports/`. Use `--output` to change the
directory.

## How do I embed `behave-runner` in my own Python script?

Use the public Python API:

```python
from behave_runner.core.orchestrator import RunConfig, run

config = RunConfig(features=["features"], tags=["@smoke"])
exit_code = run(config)
```

See the [Python API](python-api.md) page for the full reference.
