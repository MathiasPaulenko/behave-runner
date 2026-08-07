# list

List all scenarios from feature files without executing them.

## Description

`list` parses the feature files, collects every scenario that matches the
given tags, and prints a table with the feature name, scenario name,
location, and tags.

## Usage

```bash
behave-runner list [OPTIONS] [FEATURES]...
```

## Options

| Flag | Type | Default | Description |
| ------ | ------ | --------- | ------------- |
| `[FEATURES]...` | PATH | `features` | Paths to feature files or directories. |
| `--tags` `-t` | TEXT | None | Filter scenarios by tags. |
| `--format` | TEXT | `text` | Output format: `text`, `json`. |

## Examples

```bash
# List all scenarios
behave-runner list

# List scenarios in a specific directory
behave-runner list features/

# List only @smoke scenarios as JSON
behave-runner list --tags @smoke --format json
```

## Dependencies

The `list` command is included with `behave-runner`.
