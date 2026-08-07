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

| Flag | Type | Default | Descripción |
| ------ | ------ | --------- | ------------- |
| `[PATH]` | TEXT | `.` | Project root directory to analyze. |
| `--format` | TEXT | `text` | Output format: `text`, `json`, `sarif`. |
| `--run` | BOOLEAN | `False` | Run affected scenarios after detecting them. |

## Examples

```bash
# Detect affected scenarios from the last commit
behave-runner impact $(git diff --name-only HEAD~1)

# Analyze specific files
behave-runner impact src/auth.py src/models/user.py

# Detect and run affected scenarios
behave-runner impact $(git diff --name-only HEAD~1) --run

# Export results as JSON
behave-runner impact --format json
```

## Dependencies

Requires `behave-doctor`. Install with:

```bash
pip install "behave-runner[doctor]"
```
