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
| `format` | string | Default output format. |
| `output` | string | Default output file path. |
| `timeout` | integer | Global timeout in seconds. |
| `tags` | list of strings | Default scenario tags. |
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
    `format`, `output`, `timeout`, `tags`, `parallel`, `retries`, `dry_run`,
    `stop_on_failure`, `scenario_timeout`, `priority_order`, `fail_fast`,
    `flaky_report`, and `max_failures`. CLI flags always win over profile values.

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

!!! warning "Profiles require pyproject.toml"
    Configuration profiles are only supported in `pyproject.toml`. The
    `behave.ini` format does not support nested tables, so profiles cannot
    be defined there.

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
