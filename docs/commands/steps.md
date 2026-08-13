# steps

Manage step libraries.

## Description

`steps` delegates to `behave-steplib`. It lists, shows, searches, validates,
and installs step libraries that provide reusable step definitions.

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

### steps show

```bash
behave-runner steps show PATTERN [ARGS]...
```

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `PATTERN` | TEXT | required | Step pattern to show. |
| `[ARGS]...` | TEXT | None | Additional arguments. |

Show details for a specific step pattern.

### steps search

```bash
behave-runner steps search QUERY [ARGS]...
```

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `QUERY` | TEXT | required | Search query. |
| `[ARGS]...` | TEXT | None | Additional arguments. |

Search for step libraries by partial pattern.

### steps validate

```bash
behave-runner steps validate [ARGS]...
```

Validate step contracts.

### steps init

```bash
behave-runner steps init [ARGS]...
```

Generate `features/environment.py` with autoload wiring.

### steps install

```bash
behave-runner steps install NAME [ARGS]...
```

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `NAME` | TEXT | required | Step library name to install. |
| `[ARGS]...` | TEXT | None | Additional arguments. |

## Examples

```bash
# List installed step libraries
behave-runner steps list

# Install a step library
behave-runner steps install http

# Search for a step library
behave-runner steps search auth

# Show details for a specific step pattern
behave-runner steps show "I send a POST request"

# Validate step contracts
behave-runner steps validate

# Generate autoload environment.py
behave-runner steps init
```

## Dependencies

Requires `behave-steplib`. Install with:

```bash
pip install "behave-runner[steplib]"
```
