# trace

Trace viewer and dashboard.

## Description

`trace` delegates to `behave-trace`. It can show the trace viewer for a
completed run or serve it as a web dashboard.

## Usage

```bash
behave-runner trace [COMMAND] [ARGS]...
```

## Subcommands

### trace show

```bash
behave-runner trace show [ARGS]...
```

### trace serve

```bash
behave-runner trace serve [ARGS]...
```

## Options

`trace show` and `trace serve` accept pass-through arguments for
`behave-trace`.

## Examples

```bash
# Show the trace viewer for the latest run
behave-runner trace show

# Serve the trace dashboard
behave-runner trace serve

# Pass extra arguments to behave-trace
behave-runner trace show --run-id 123
```

## Dependencies

Requires `behave-trace`. Install with:

```bash
pip install "behave-runner[trace]"
```
