# open

Open the latest report or trace viewer in the browser.

## Description

`open` finds the latest report or trace file in the output directory and
opens it with the default browser.

## Usage

```bash
behave-runner open [OPTIONS] [TARGET]
```

## Options

| Flag | Tipo | Default | Descripción |
| --- | --- | --- | --- |
| `[TARGET]` | TEXT | `report` | What to open: `report` or `trace`. |
| `--output` | PATH | `reports` | Directory containing reports. |

## Examples

```bash
# Open the latest report
behave-runner open

# Open the latest trace
behave-runner open trace

# Use a custom reports directory
behave-runner open --output my-reports/
```

## Dependencies

The base `open` command is included with `behave-runner`.
Opening `trace` requires `behave-trace`:

```bash
pip install "behave-runner[trace]"
```
