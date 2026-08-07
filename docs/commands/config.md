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

| Argument | Tipo | Default | Descripción |
| --- | --- | --- | --- |
| `KEY` | TEXT | required | Configuration key to set. |
| `VALUE` | TEXT | required | Value to assign. |

## Examples

```bash
# Show the current configuration
behave-runner config show

# Initialize the config section
behave-runner config init

# Set a value
behave-runner config set parallel 4
behave-runner config set format json
```

## Dependencies

The `config` command is included with `behave-runner`.
