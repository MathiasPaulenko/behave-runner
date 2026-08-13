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

| Flag | Type | Default | Description |
| ------ | ------ | --------- | ------------- |
| `[FEATURES]...` | PATH | `features` | Feature paths to watch and run. |
| `--tags` `-t` | TEXT | None | Filter by tags. |
| `--debounce` | INTEGER | `500` | Debounce time in milliseconds. Must be >= 0. |
| `--pattern` | TEXT | None | Glob pattern to filter watched files. |
| `--profile` | TEXT | None | Load a configuration profile from `pyproject.toml`. |
| `--retries` | INTEGER | None | Number of retries for failed scenarios. |
| `--parallel` `-n` | INTEGER | None | Number of parallel processes. |
| `--format` | TEXT | None | Output format. |
| `--ui` | BOOLEAN | `False` | Use `behave-trace` UI mode when available. |
| `--debug` | BOOLEAN | `False` | Enable debug tracing. |
| `--trace` | BOOLEAN | `False` | Enable trace viewer. |
| `--priority-order` | BOOLEAN | `False` | Run scenarios in priority order. |
| `--fail-fast` | BOOLEAN | `False` | Stop on first failure with priority. |
| `--scenario-timeout` | INTEGER | None | Per-scenario timeout in seconds. |

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
Optional flags need the corresponding extras:

- `behave-runner[parallel]` for `--parallel`
- `behave-runner[priority]` for `--priority-order` and `--fail-fast`
- `behave-runner[retry]` for `--retries`
- `behave-runner[trace]` for `--ui`, `--debug`, `--trace`
