# report

Generate and show test reports.

## Description

`report` generates reports from feature files or test results. It
unifies the `behave-modern-*-report` formatters under one command and can
open the latest report in the browser.

## Usage

```bash
behave-runner report [COMMAND] [ARGS]...
```

## Subcommands

### report generate

```bash
behave-runner report generate [OPTIONS] [FEATURES]...
```

| Flag | Tipo | Default | Description |
| --- | --- | --- | --- |
| `[FEATURES]...` | PATH | `features` | Paths to feature files or directories. |
| `--format` | TEXT | `console` | Report format. |
| `--output` | PATH | None | Output directory for reports. |

### report show

```bash
behave-runner report show [OPTIONS]
```

| Flag | Tipo | Default | Description |
| --- | --- | --- | --- |
| `--output` | PATH | `reports` | Directory containing reports. |

## Examples

```bash
# Generate a console report
behave-runner report generate

# Generate an HTML report
behave-runner report generate --format html

# Generate a JSON report to a specific directory
behave-runner report generate --format json --output reports/

# Open the latest report in the browser
behave-runner report show
```

## Dependencies

`report generate` needs the formatter for the chosen format:

- `behave-runner[report-console]` for `console`
- `behave-runner[report-html]` for `html`
- `behave-runner[report-md]` for `md`
- `behave-runner[report-json]` for `json`
- `behave-runner[report-sheets]` for `xlsx`
- `behave-runner[report-file]` for `pdf`
