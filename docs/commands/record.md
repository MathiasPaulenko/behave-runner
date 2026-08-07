# record

Record a browser session and generate behave steps.

## Description

`record` opens `wavexis` to record browser interactions. After the
recording finishes, it generates a step definition file and a feature
skeleton using `behave-gen`.

## Usage

```bash
behave-runner record [OPTIONS] [URL]
```

## Options

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `[URL]` | TEXT | `about:blank` | URL to record. |
| `--output` | PATH | `recordings` | Output directory. |
| `--name` | TEXT | `recorded_step` | Name for the step. |

## Examples

```bash
# Record the current browser session
behave-runner record

# Record a specific URL
behave-runner record https://example.com

# Save with a custom name and output directory
behave-runner record https://example.com --name login --output recordings/
```

## Dependencies

Requires `wavexis`. Install with:

```bash
pip install "behave-runner[record]"
```

Optional step generation requires `behave-gen`:

```bash
pip install "behave-runner[record,gen]"
```
