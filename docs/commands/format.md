# format

Format feature files automatically.

## Description

`format` delegates to `behave-format`. You can preview changes with
`--diff` or check formatting without modifying files with `--check`.
Any additional arguments are forwarded to `behave-format`.

## Usage

```bash
behave-runner format [OPTIONS] [ARGS]...
```

## Options

| Flag | Type | Default | Description |
| ------ | ------ | --------- | ------------- |
| `--check` | BOOLEAN | `False` | Check only, do not modify files. |
| `--diff` | BOOLEAN | `False` | Show diff of changes. |
| `[ARGS]...` | TEXT | None | Arguments to pass to `behave-format`. |

## Examples

```bash
# Check formatting without modifying
behave-runner format --check

# Show diff of proposed changes
behave-runner format --diff

# Pass extra arguments to behave-format
behave-runner format --in-place features/
```

## Dependencies

Requires `behave-format`. Install with:

```bash
pip install "behave-runner[format]"
```
