# impact

Detect scenarios affected by code changes.

## Description

`impact` runs `behave-doctor scan` to find which scenarios depend on the
files that changed. You can optionally run those scenarios automatically
with `--run`.

## Usage

```bash
behave-runner impact [OPTIONS] [PATH]
```

## Options

| Flag | Type | Default | Description |
| ------ | ------ | --------- | ------------- |
| `[PATH]` | TEXT | `.` | Project root directory to analyze. |
| `--format` | TEXT | `text` | Output format: `text`, `json`, `sarif`. |
| `--run` | BOOLEAN | `False` | Run affected scenarios after detecting them. |

## Examples

```bash
# Detect affected scenarios from the current directory
behave-runner impact

# Analyze a specific directory
behave-runner impact src/

# Detect and run affected scenarios
behave-runner impact --run

# Export results as JSON
behave-runner impact --format json
```

## Dependencies

Requires `behave-doctor`. Install with:

```bash
pip install "behave-runner[doctor]"
```
