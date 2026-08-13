---
title: CLI Reference
description: Complete reference for the behave-runner command-line interface.
---

<!-- markdownlint-disable MD013 -->

## Usage

```bash
behave-runner [OPTIONS] COMMAND [ARGS]...
```

## Global options

| Option | Description |
| ------ | ----------- |
| `--version` | Show the version and exit. |
| `--install-completion` | Install shell completion for the current shell. |
| `--show-completion` | Show shell completion source for customization. |
| `--help` | Show the help message and exit. |

## Commands overview

| Command | Description |
| ------- | ----------- |
| `run` | Execute behave tests. |
| `list` | List scenarios without executing them. |
| `select` | Filter scenarios with advanced rules. |
| `watch` | Watch files and re-run tests automatically. |
| `init` | Initialize a new behave project. |
| `lint` | Run `behave-lint` on feature files. |
| `format` | Run `behave-format` on feature files. |
| `doctor` | Run `behave-doctor` to diagnose the project. |
| `impact` | Detect scenarios affected by code changes. |
| `report` | Generate and open reports. |
| `trace` | Trace viewer and dashboard. |
| `steps` | Manage step libraries. |
| `generate` | Generate step definitions and feature files. |
| `config` | Manage `behave-runner` configuration. |
| `open` | Open the latest report or trace viewer. |
| `record` | Record a browser session and generate steps. |

## run

Execute behave tests with native and optional flags.

```bash
behave-runner run [OPTIONS] [FEATURES]...
```

| Option | Short | Description |
| ------ | ----- | ----------- |
| `[FEATURES]...` | | Paths to feature files or directories. Defaults to `features/`. |
| `--tags` | `-t` | Filter scenarios by tags. Repeatable. |
| `--dry-run` | | Parse scenarios without executing steps. |
| `--stop-on-failure` | | Stop at the first failing scenario. |
| `--max-fail` | | Maximum number of failures before stopping. |
| `--timeout` | | Global timeout in seconds. |
| `--format` | | Output format passed to `behave`. |
| `--output` | | Output file path for the generated report. |
| `--parallel` | `-n` | Number of parallel workers. Requires `behave-pool`. |
| `--shard` | | CI shard in `i/n` form, e.g. `1/3`. Requires `behave-pool`. |
| `--parallel-scheme` | | Parallel distribution scheme (e.g. `scenario`, `feature`). Requires `behave-pool`. |
| `--parallel-balance` | | Load balancing strategy (e.g. `lpt`, `round`). Requires `behave-pool`. |
| `--parallel-timing-file` | | Timing file for LPT load balancing. Requires `behave-pool`. |
| `--retries` | | Number of retries for failed scenarios. Requires `behave-retry`. |
| `--flaky-report` | | Generate a flakiness report. Requires `--retries`. |
| `--priority-order` | | Run scenarios in priority order. Requires `behave-priority`. |
| `--smoke` | | Run only `@smoke` scenarios (adds `@smoke` tag filter). |
| `--fail-fast` | | Stop at the first failure with priority logic. Requires `behave-priority`. |
| `--profile` | | Load a configuration profile from `pyproject.toml`. |
| `--scenario-timeout` | | Per-scenario timeout in seconds. Requires `behave-kit`. |
| `--ui` | | Launch the `behave-trace` web dashboard. |
| `--debug` | | Enable interactive debugging. Requires `behave-trace`. |
| `--trace` | | Enable trace viewer after the run. Requires `behave-trace`. |

!!! tip "Start with the defaults"
    Running `behave-runner run` with no extra flags runs every scenario in the
    `features/` directory sequentially.

## list

List scenarios without executing them.

```bash
behave-runner list [OPTIONS] [FEATURES]...
```

| Option | Short | Description |
| ------ | ----- | ----------- |
| `[FEATURES]...` | | Feature paths. Defaults to `features/`. |
| `--tags` | `-t` | Filter by tags. |
| `--format` | | Output format: `text`, `json`. Default: `text`. |

## select

Select scenarios with advanced filtering.

```bash
behave-runner select [OPTIONS] [FEATURES]...
```

| Option | Short | Description |
| ------ | ----- | ----------- |
| `[FEATURES]...` | | Feature paths. Defaults to `features/`. |
| `--pattern` | | Regex pattern to match scenario names. |
| `--tags` | `-t` | Filter by tags. Use `~@tag` to exclude. |
| `--feature` | | Filter by feature name, case-insensitive substring. |
| `--format` | | Output format: `text`, `names`, `json`. Default: `text`. |

## watch

Watch files and re-run tests automatically.

```bash
behave-runner watch [OPTIONS] [FEATURES]...
```

| Option | Short | Description |
| ------ | ----- | ----------- |
| `[FEATURES]...` | | Feature paths to watch and run. Defaults to `features/`. |
| `--tags` | `-t` | Filter by tags. |
| `--debounce` | | Debounce time in milliseconds. Default: `500`. |
| `--pattern` | | Glob pattern to filter watched files. |
| `--profile` | | Load a configuration profile from `pyproject.toml`. |
| `--retries` | | Number of retries for failed scenarios. Requires `behave-retry`. |
| `--parallel` | `-n` | Number of parallel processes. Requires `behave-pool`. |
| `--format` | | Output format passed to `behave`. |
| `--ui` | | Use `behave-trace` UI mode when available. Requires `behave-trace`. |
| `--debug` | | Enable debug tracing. Requires `behave-trace`. |
| `--trace` | | Enable trace viewer. Requires `behave-trace`. |
| `--priority-order` | | Run scenarios in priority order. Requires `behave-priority`. |
| `--fail-fast` | | Stop on first failure with priority. Requires `behave-priority`. |
| `--scenario-timeout` | | Per-scenario timeout in seconds. Requires `behave-kit`. |

## init

Initialize a new behave project structure.

```bash
behave-runner init [OPTIONS] [ARGS]...
```

| Option | Description |
| ------ | ----------- |
| `--name` | Project name for the generated structure. **Required.** |
| `[ARGS]...` | Additional arguments for `behave-gen`. |

## lint

Run `behave-lint` static analysis on feature files.

```bash
behave-runner lint [ARGS]...
```

Pass-through arguments are forwarded to `behave-lint`.

## format

Run `behave-format` to format feature files.

```bash
behave-runner format [OPTIONS] [ARGS]...
```

| Option | Description |
| ------ | ----------- |
| `--check` | Check only, do not modify files. |
| `--diff` | Show diff of the changes. |
| `[ARGS]...` | Arguments to pass to `behave-format`. |

## doctor

Run `behave-doctor` to diagnose and fix common issues.

```bash
behave-runner doctor [ARGS]...
```

Pass-through arguments are forwarded to `behave-doctor`.

## impact

Detect scenarios affected by code changes.

```bash
behave-runner impact [OPTIONS] [PATH]
```

| Option | Description |
| ------ | ----------- |
| `[PATH]` | Project root to analyze. Default: `.`. |
| `--format` | Output format: `text`, `json`, `sarif`. Default: `text`. |
| `--run` | Run affected scenarios after detecting them. |

## report

Generate and open reports.

```bash
behave-runner report [COMMAND] [ARGS]...
```

### report generate

```bash
behave-runner report generate [OPTIONS] [FEATURES]...
```

| Option | Description |
| ------ | ----------- |
| `[FEATURES]...` | Feature paths. Defaults to `features/`. |
| `--format` | Report format: `console`, `html`, `md`, `json`, `sheets`, `file`. Default: `console`. |
| `--output` | Output directory for reports. |

### report show

```bash
behave-runner report show [OPTIONS]
```

| Option | Description |
| ------ | ----------- |
| `--output` | Directory containing reports. Default: `reports`. |

## trace

Trace viewer using `behave-trace`.

```bash
behave-runner trace [COMMAND] [ARGS]...
```

### trace show

```bash
behave-runner trace show [ARGS]...
```

Show the trace viewer for post-run analysis.

### trace serve

```bash
behave-runner trace serve [ARGS]...
```

Serve the trace viewer as a web dashboard.

## steps

Manage step libraries using `behave-steplib`.

```bash
behave-runner steps [COMMAND] [ARGS]...
```

### steps list

```bash
behave-runner steps list [ARGS]...
```

List available step libraries.

### steps show

```bash
behave-runner steps show PATTERN [ARGS]...
```

Show details for a specific step pattern.

### steps search

```bash
behave-runner steps search QUERY [ARGS]...
```

Search for step libraries matching the query.

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

Install a step library by name.

## generate

Generate step definitions and feature files using `behave-gen`.

```bash
behave-runner generate [COMMAND] [ARGS]...
```

### generate step

```bash
behave-runner generate step --lib NAME
```

Generate step definitions from a step library.

### generate feature

```bash
behave-runner generate feature [OPTIONS] NAME
```

| Option | Description |
| ------ | ----------- |
| `NAME` | Feature name without the `.feature` extension. |
| `--tags` | Comma or space separated tags. |

## config

Manage `behave-runner` configuration.

```bash
behave-runner config [COMMAND]
```

### config show

```bash
behave-runner config show
```

Display the current `[tool.behave-runner]` configuration.

### config init

```bash
behave-runner config init
```

Create the `[tool.behave-runner]` section in `pyproject.toml`.

### config set

```bash
behave-runner config set KEY VALUE
```

Set a configuration value in `[tool.behave-runner]`. Supports dotted notation
for nested keys (e.g. `profiles.ci.parallel`). Values are parsed as integer,
boolean, or string.

## open

Open the latest report or trace viewer in the browser.

```bash
behave-runner open [OPTIONS] [TARGET]
```

| Option | Description |
| ------ | ----------- |
| `[TARGET]` | `report` (default) or `trace`. |
| `--output` | Directory containing reports. Default: `reports`. |

## record

Record a browser session and generate behave steps.

```bash
behave-runner record [OPTIONS] [URL]
```

| Option | Description |
| ------ | ----------- |
| `[URL]` | URL to record. Default: `about:blank`. |
| `--output` | Directory for recording output. Default: `recordings`. |
| `--name` | Name for the generated step. Default: `recorded_step`. |

## Exit codes

`behave-runner` uses the following exit codes across commands:

| Code | Meaning |
| ---- | ------- |
| `0` | Success. |
| `1` | Test failures or tool-level errors. |
| `2` | Configuration errors, missing optional dependencies, or invalid input. |
