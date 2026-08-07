# run

Execute behave tests with native and optional ecosystem flags.

## Description

The `run` command is the main entry point for executing behave scenarios.
It builds the final behave command from the provided flags and optional
configuration profiles, then dispatches to the right runner:
sequential, parallel, priority-ordered, retry, sharded, or trace/UI.

## Usage

```bash
behave-runner run [OPTIONS] [FEATURES]...
```

## Options

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `[FEATURES]...` | PATH | `features` | Feature paths. |
| `--tags` `-t` | TEXT | None | Filter by tags. |
| `--dry-run` | BOOLEAN | `False` | Parse scenarios without executing. |
| `--stop-on-failure` | BOOLEAN | `False` | Stop at first failure. |
| `--max-fail` | INTEGER | None | Maximum failures before stopping. |
| `--timeout` | INTEGER | None | Global timeout in seconds. |
| `--format` | TEXT | None | Output format for behave. |
| `--output` | TEXT | None | Output file for the generated report. |
| `--parallel` `-n` | INTEGER | None | Number of parallel workers. |
| `--shard` | TEXT | None | CI shard in `i/n` form. |
| `--retries` | INTEGER | None | Number of retries for failed scenarios. |
| `--flaky-report` | BOOLEAN | `False` | Generate a flakiness report. |
| `--priority-order` | BOOLEAN | `False` | Run scenarios in priority order. |
| `--smoke` | BOOLEAN | `False` | Run only `@smoke` scenarios. |
| `--fail-fast` | BOOLEAN | `False` | Stop at the first failure. |
| `--profile` | TEXT | None | Load a configuration profile. |
| `--scenario-timeout` | INTEGER | None | Per-scenario timeout. |
| `--ui` | BOOLEAN | `False` | Launch the trace UI. |
| `--debug` | BOOLEAN | `False` | Enable interactive debugging. |
| `--trace` | BOOLEAN | `False` | Enable the trace viewer. |

## Examples

```bash
# Run all scenarios in the default features/ directory
behave-runner run

# Run only smoke tests
behave-runner run --tags @smoke

# Parallel execution with retries
behave-runner run --parallel 4 --retries 2

# Run with a CI profile
behave-runner run --profile ci

# Dry run with tag filter
behave-runner run --dry-run --tags @smoke features/

# Run a specific shard in CI
behave-runner run --shard 1/3 --parallel 4
```

## Dependencies

The base `run` command only requires `behave`.
Optional flags need the corresponding extras:

- `behave-runner[parallel]` for `--parallel` and `--shard`
- `behave-runner[priority]` for `--priority-order` and `--fail-fast`
- `behave-runner[retry]` for `--retries` and `--flaky-report`
- `behave-runner[trace]` for `--ui`, `--debug`, `--trace`

The `--format` and `--output` flags are passed directly to `behave` and do
not require any extra dependencies. Use the `report generate` command for
advanced report formats (HTML, Markdown, JSON, sheets, file).
