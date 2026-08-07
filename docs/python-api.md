# Python API

`behave-runner` can also be used as a Python library. The public API is
kept small and lives mainly under `behave_runner.core`. This page is
auto-generated from the source docstrings with `mkdocstrings`.

## Entry point

The `behave_runner.__main__:main` function is the same entry point used by
the `behave-runner` console script.

```python
from behave_runner.__main__ import main

main()
```

For programmatic use, create a `RunConfig` and call `run`:

```python
from behave_runner.core.orchestrator import RunConfig, run

config = RunConfig(features=["features"], tags=["@smoke"])
exit_code = run(config)
```

## Core modules

### Orchestrator

::: behave_runner.core.orchestrator

### Configuration

::: behave_runner.core.config

### Dependency checking

::: behave_runner.core.deps

### Output management

::: behave_runner.core.output

### File watcher

::: behave_runner.core.watcher

### Exceptions

::: behave_runner.exceptions

### Utilities

::: behave_runner.utils
