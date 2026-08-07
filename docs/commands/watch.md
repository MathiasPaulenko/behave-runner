# watch

Re-run tests automatically when feature or step files change.

## Description

`watch` monitors the feature directory, step files, `environment.py`,
`behave.ini`, and `pyproject.toml`. When a change is detected, it re-runs
the test suite with the same filters you provided.

## Usage

```bash
behave-runner watch [OPTIONS] [FEATURES]...
```

## Options

| Flag | Type | Default | Descripción |
| ------ | ------ | --------- | ------------- |
| `[FEATURES]...` | PATH | `features` | Feature paths to watch and run. |
| `--tags` `-t` | TEXT | None | Filter by tags. |
| `--debounce` | INTEGER | `500` | Debounce time in milliseconds. |
| `--pattern` | TEXT | None | Glob pattern to filter watched files. |
| `--ui` | BOOLEAN | `False` | Use `behave-trace` UI mode when available. |

## Examples

```bash
# Watch the default features directory
behave-runner watch

# Watch a specific directory with tag filter
behave-runner watch --tags @smoke features/

# Watch only .feature files matching a pattern
behave-runner watch --pattern "*.feature"

# Watch with UI mode
behave-runner watch --ui
```

## Dependencies

The base `watch` command is included with `behave-runner`.
The `--ui` flag requires `behave-runner[trace]`.
