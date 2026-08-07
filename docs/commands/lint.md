# lint

Lint feature files for best practices.

## Description

`lint` delegates to `behave-lint` and runs static analysis on `.feature`
files. Any positional arguments are forwarded directly to `behave-lint`.

## Usage

```bash
behave-runner lint [ARGS]...
```

## Options

`lint` accepts pass-through arguments for `behave-lint`.

## Examples

```bash
# Lint the default features directory
behave-runner lint

# Lint a specific directory
behave-runner lint features/

# Pass extra flags to behave-lint
behave-runner lint --strict
```

## Dependencies

Requires `behave-lint`. Install with:

```bash
pip install "behave-runner[lint]"
```
