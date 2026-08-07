---
title: Configuration
description: Configure behave-runner with pyproject.toml, behave.ini, profiles, and CLI flags.
---

## Supported files

`behave-runner` reads configuration from these files, in order of preference:

1. `pyproject.toml` under `[tool.behave-runner]`
2. `behave.ini` under `[behave-runner]`

If `pyproject.toml` exists but has no `[tool.behave-runner]` section,
`behave.ini` is used as a fallback.

## pyproject.toml

Add a `[tool.behave-runner]` section to store project-wide defaults.

```toml
[tool.behave-runner]
parallel = 4
format = "json"
output = "reports/results.json"
timeout = 300
```

`behave-runner` recognizes these top-level keys:

| Key | Type | Description |
| --- | ---- | ----------- |
| `parallel` | integer | Default number of parallel workers. |
| `retries` | integer | Number of retries for failed scenarios. |
| `format` | string | Default output format. |
| `output` | string | Default output file path. |
| `timeout` | integer | Global timeout in seconds. |
| `scenario_timeout` | integer | Per-scenario timeout in seconds. |
| `tags` | list of strings | Default scenario tags. |
| `features` | list of strings | Default feature paths. |
| `name` | list of strings | Scenario name filters. |
| `dry_run` | boolean | Parse scenarios without executing steps. |
| `stop_on_failure` | boolean | Stop at the first failing scenario. |
| `max_failures` | integer | Maximum failures before stopping. |
| `flaky_report` | boolean | Generate a flakiness report. |
| `priority_order` | boolean | Run scenarios in priority order. |
| `fail_fast` | boolean | Stop at first failure with priority logic. |
| `smoke` | boolean | Run only `@smoke` scenarios. |
| `shard` | string | CI shard in `i/n` form. |
| `no_color` | boolean | Disable colored output. |
| `verbose` | boolean | Enable verbose output. |
| `ui` | boolean | Launch the trace web dashboard. |
| `debug` | boolean | Enable interactive debugging. |
| `trace` | boolean | Enable trace viewer after the run. |
| `profiles` | table | Named configuration profiles. |

!!! note "List syntax"
    TOML lists for tags are quoted strings inside square brackets.

```toml
tags = ["@smoke", "@fast"]
```

## Profiles

Profiles let you switch between complete configuration presets. Define them
under `[tool.behave-runner.profiles.<name>]`:

```toml
[tool.behave-runner.profiles.ci]
parallel = 8
format = "json"
output = "reports/ci.json"
tags = ["@ci"]

[tool.behave-runner.profiles.fast]
parallel = 1
tags = ["@smoke"]
```

Use a profile with the `--profile` flag:

```bash
behave-runner run --profile ci features/
```

!!! tip "Keep CI settings in a profile"
    Store long or environment-specific flag combinations in a profile. This
keeps your CI commands short and makes the settings reviewable in version
control.

## Merge rules

When a profile is selected, `behave-runner` merges configuration from three
sources, in increasing priority:

1. **Base config file** — values from `[tool.behave-runner]`.
2. **Profile** — values from `[tool.behave-runner.profiles.<name>]`.
3. **CLI flags** — flags passed on the command line.

The highest-priority source wins. For example, a profile may set `format` to
`json`, but passing `--format html` on the command line uses `html`.

```toml
[tool.behave-runner]
format = "console"
parallel = 2

[tool.behave-runner.profiles.ci]
format = "json"
parallel = 8
```

```bash
# Uses format="json" and parallel=8 from the ci profile
behave-runner run --profile ci features/

# Uses parallel=8 from the ci profile but overrides format to html
behave-runner run --profile ci --format html features/
```

!!! note "Current merge scope"
    The `run` command merges all supported config values from the profile:
    `features`, `tags`, `name`, `format`, `output`, `timeout`, `parallel`,
    `retries`, `dry_run`, `stop_on_failure`, `scenario_timeout`,
    `priority_order`, `fail_fast`, `flaky_report`, `max_failures` (or
    `max_fail`), `smoke`, `shard`, `no_color`, `verbose`, `ui`, `debug`,
    and `trace`. CLI flags always win over profile values. Boolean flags
    (`dry_run`, `stop_on_failure`, etc.) are OR-merged: if either the CLI
    flag or the profile sets `true`, the result is `true`.

## behave.ini

If you are not using `pyproject.toml`, place the same keys in `behave.ini`:

```ini
[behave-runner]
parallel = 4
format = json
output = reports/results.json
```

Note that `behave.ini` is only loaded when `pyproject.toml` has no
`[tool.behave-runner]` section.

!!! note "Profiles in behave.ini"
    Profiles are also supported in `behave.ini` using flat dot-notation keys:

    ```ini
    [behave-runner]
    profiles.default.parallel = 4
    profiles.default.dry_run = false
    profiles.default.tags = @smoke, @fast
    ```

    These are automatically converted to nested dictionaries. However,
    `pyproject.toml` is recommended for profiles because TOML's native
    table syntax is more readable.

## Using the config command

`behave-runner` includes a small helper to inspect and modify configuration.

### Show current config

```bash
behave-runner config show
```

### Initialize the section

```bash
behave-runner config init
```

This creates an empty `[tool.behave-runner]` section in `pyproject.toml` if it
does not already exist.

### Set a value

```bash
behave-runner config set parallel 4
behave-runner config set format json
```

!!! tip "Prefer editing the file"
    `config set` is useful for quick experiments, but for version-controlled
projects it is usually cleaner to edit `pyproject.toml` directly.
