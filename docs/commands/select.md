# select

Filter scenarios with advanced rules.

## Description

`select` lets you find scenarios by tag expression, regex pattern, or
feature name. It is useful for CI pipelines, dry runs, or preparing a
subset of tests before execution.

## Usage

```bash
behave-runner select [OPTIONS] [FEATURES]...
```

## Options

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `[FEATURES]...` | PATH | `features` | Paths to feature files or directories. |
| `--pattern` | TEXT | None | Regex pattern to match scenario names. |
| `--tags` `-t` | TEXT | None | Filter by tags. Use `~@tag` to exclude. |
| `--feature` | TEXT | None | Filter by feature name. |
| `--format` | TEXT | `text` | Output format: `text`, `names`, `json`. |

## Examples

```bash
# Select scenarios matching a regex
behave-runner select --pattern "login.*success"

# Include @smoke, exclude @slow
behave-runner select --tags @smoke --tags ~@slow

# Filter by feature name
behave-runner select --feature "user" --format json
```

## Dependencies

The `select` command is included with `behave-runner`.
