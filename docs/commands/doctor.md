# doctor

Diagnose project health.

## Description

`doctor` delegates to `behave-doctor` and runs static analysis rules on
the project. It helps detect common setup problems, missing step
definitions, and feature inconsistencies.

## Usage

```bash
behave-runner doctor [ARGS]...
```

## Options

`doctor` accepts pass-through arguments for `behave-doctor`.

## Examples

```bash
# Diagnose the current project
behave-runner doctor

# Diagnose a specific path
behave-runner doctor my-project/

# Pass extra flags to behave-doctor
behave-runner doctor --format json
```

## Dependencies

Requires `behave-doctor`. Install with:

```bash
pip install "behave-runner[doctor]"
```
