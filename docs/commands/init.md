# init

Initialize a new behave project.

## Description

`init` delegates to `behave-gen` to scaffold a new behave project with a
standard directory layout, including `features/`, `steps/`, and
`environment.py`.

## Usage

```bash
behave-runner init [OPTIONS] [ARGS]...
```

## Options

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--name` | TEXT | None | Project name for the generated structure. |
| `[ARGS]...` | TEXT | None | Additional arguments for `behave-gen`. |

## Examples

```bash
# Initialize in the current directory
behave-runner init

# Initialize a named project
behave-runner init --name my-project

# Initialize with extra behave-gen arguments
behave-runner init --name my-project -- --template minimal
```

## Dependencies

Requires `behave-gen`. Install with:

```bash
pip install "behave-runner[gen]"
```
