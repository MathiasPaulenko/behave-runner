# steps

Manage step libraries.

## Description

`steps` delegates to `behave-steplib`. It lists, searches, and installs
step libraries that provide reusable step definitions.

## Usage

```bash
behave-runner steps [COMMAND] [ARGS]...
```

## Subcommands

### steps list

```bash
behave-runner steps list [ARGS]...
```

List available step libraries.

### steps install

```bash
behave-runner steps install NAME [ARGS]...
```

| Argument | Tipo | Default | Descripción |
| --- | --- | --- | --- |
| `NAME` | TEXT | required | Step library name to install. |
| `[ARGS]...` | TEXT | None | Additional arguments. |

### steps search

```bash
behave-runner steps search QUERY [ARGS]...
```

| Argument | Tipo | Default | Descripción |
| --- | --- | --- | --- |
| `QUERY` | TEXT | required | Search query. |
| `[ARGS]...` | TEXT | None | Additional arguments. |

## Examples

```bash
# List installed step libraries
behave-runner steps list

# Install a step library
behave-runner steps install http

# Search for a step library
behave-runner steps search auth
```

## Dependencies

Requires `behave-steplib`. Install with:

```bash
pip install "behave-runner[steplib]"
```
