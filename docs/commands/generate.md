# generate

Generate step definitions and feature files using behave-gen.

## Description

`generate` provides subcommands for scaffolding new behave artifacts.
You can generate step definitions from a step library or create a feature
file skeleton.

## Usage

```bash
behave-runner generate [COMMAND] [ARGS]...
```

## Subcommands

### generate step

```bash
behave-runner generate step --lib <library>
```

| Flag | Tipo | Default | Descripción |
| --- | --- | --- | --- |
| `--lib` | TEXT | required | Step library name (e.g. `http`, `auth`). |

### generate feature

```bash
behave-runner generate feature [OPTIONS] NAME
```

| Flag | Tipo | Default | Descripción |
| --- | --- | --- | --- |
| `NAME` | TEXT | required | Feature name without the `.feature` extension. |
| `--tags` | TEXT | None | Comma or space separated tags. |

## Examples

```bash
# Generate steps from the http library
behave-runner generate step --lib http

# Generate a new feature file
behave-runner generate feature login

# Generate a feature with tags
behave-runner generate feature login --tags "@smoke,@fast"
```

## Dependencies

Requires `behave-gen`. Install with:

```bash
pip install "behave-runner[gen]"
```
