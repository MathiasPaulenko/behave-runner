# format

Format feature files automatically.

## Description

`format` delegates to `behave-format`. You can preview changes with
`--diff`, check formatting without modifying files with `--check`, or
modify files in place with `--in-place`.

## Usage

```bash
behave-runner format [OPTIONS] [ARGS]...
```

## Options

| Flag | Tipo | Default | Descripción |
| ------ | ------ | --------- | ------------- |
| `--check` | BOOLEAN | `False` | Check only, do not modify files. |
| `--diff` | BOOLEAN | `False` | Show diff of changes. |
| `--in-place` | BOOLEAN | `False` | Modify files in place. |
| `[ARGS]...` | TEXT | None | Arguments to pass to `behave-format`. |

## Examples

```bash
# Format all feature files in place
behave-runner format --in-place

# Check formatting without modifying
behave-runner format --check

# Show diff of proposed changes
behave-runner format --diff
```

## Dependencies

Requires `behave-format`. Install with:

```bash
pip install "behave-runner[format]"
```
