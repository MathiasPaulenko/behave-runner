# config

Manage behave-runner configuration.

## Description

`config` reads, initializes, and edits the `[tool.behave-runner]` section
in `pyproject.toml`.

## Usage

```bash
behave-runner config [COMMAND]
```

## Subcommands

### config show

```bash
behave-runner config show
```

Display the current `[tool.behave-runner]` configuration.

### config init

```bash
behave-runner config init
```

Create the `[tool.behave-runner]` section in `pyproject.toml` if it does
not exist.

### config set

```bash
behave-runner config set KEY VALUE
```

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `KEY` | TEXT | required | Configuration key to set. Supports dotted notation (e.g. `profiles.ci.parallel`). |
| `VALUE` | TEXT | required | Value to assign. Parsed as integer, boolean, or string. |

## Examples

```bash
# Show the current configuration
behave-runner config show

# Initialize the config section
behave-runner config init

# Set a value
behave-runner config set parallel 4
behave-runner config set format json
behave-runner config set tags "[@smoke, @fast]"

# Set a profile value using dotted notation
behave-runner config set profiles.ci.parallel 8
```

## Dependencies

The `config` command is included with `behave-runner`.
