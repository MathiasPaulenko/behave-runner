# Architecture

`behave-runner` is a thin CLI and orchestration layer on top of the
BehaveLib ecosystem. It does not reimplement the behavior logic of any
library; it translates user flags into the right sequence of calls and
gracefully degrades when optional dependencies are missing.

## Overview

The architecture has three layers:

1. **CLI** — `Typer` parses the user input and dispatches to one of the
   command modules in `behave_runner.commands`.
2. **Orchestrator** — `behave_runner.core` collects configuration, resolves
   optional extras, merges config files with CLI flags, and builds the
   final `behave` invocation.
3. **Backends** — the actual runner libraries (`behave`, `behave-pool`,
   `behave-priority`, etc.) execute the tests.

## Orchestrator flow

For the `run` command, the orchestrator performs the following steps:

1. Parse CLI flags into `RunConfig`.
2. Load the base config from `pyproject.toml` or `behave.ini`.
3. If a `--profile` is selected, merge the profile values.
4. For each optional flag, check whether the required extra is installed.
   - If missing, print a warning and degrade gracefully.
5. Build the final `behave` command list.
6. Dispatch to the appropriate execution path:
   - sequential
   - parallel (`behave-pool`)
   - priority-ordered (`behave-priority`)
   - retry (`behave-retry`)
   - trace/UI/debug (`behave-trace`)
   - sharded CI (`behave-pool`)
7. Return the same exit code as the underlying runner.

## Component diagram

```text
┌─────────────────────────────────────────────────────────┐
│                    behave-runner CLI                    │
│                      (Typer + Rich)                     │
│                                                         │
│  ┌──────┐ ┌───────┐ ┌───────┐ ┌──────┐ ┌──────┐       │
│  │ run  │ │ watch │ │ list  │ │select│ │ lint │  ...  │
│  └──┬───┘ └───┬───┘ └───┬───┘ └──┬───┘ └──┬───┘        │
│     │         │         │        │        │             │
│  ┌──┴─────────┴─────────┴────────┴────────┴────────┐   │
│  │              Orchestrator (core)                 │   │
│  │   - Build behave command                         │   │
│  │   - Merge config and CLI flags                   │   │
│  │   - Check optional dependencies                  │   │
│  │   - Manage output directory                      │   │
│  └────────────────────┬─────────────────────────────┘   │
│                       │                                  │
└───────────────────────┼──────────────────────────────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ behave   │ │ behave-  │ │ behave-  │
    │ (native) │ │  pool    │ │priority  │
    └──────────┘ └──────────┘ └──────────┘
          │             │             │
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ behave-  │ │ behave-  │ │ behave-  │
    │  retry   │ │  trace   │ │   kit    │
    └──────────┘ └──────────┘ └──────────┘
          │             │             │
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ behave-  │ │ behave-  │ │ behave-  │
    │  model   │ │  doctor  │ │   gen    │
    └──────────┘ └──────────┘ └──────────┘
          │             │             │
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ behave-  │ │ behave-  │ │ behave-  │
    │  lint    │ │  format  │ │ steplib  │
    └──────────┘ └──────────┘ └──────────┘
          │             │             │
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ behave-  │ │ behave-  │ │ wavexis  │
    │ comments │ │  tables  │ │          │
    └──────────┘ └──────────┘ └──────────┘
          │
    ┌─────────────────────────────────┐
    │   behave-modern-*-report (x6)   │
    │  console / html / md / json /   │
    │  sheets / file                  │
    └─────────────────────────────────┘
```

## Core modules

| Module | Responsibility |
| --- | --- |
| `cli/app.py` | Register CLI commands and the `main` entry point. |
| `core/orchestrator.py` | Build and execute the final `behave` command. |
| `core/config.py` | Load config files and profiles. |
| `core/deps.py` | Check optional extras gracefully. |
| `core/output.py` | Manage output directories. |
| `core/watcher.py` | File watcher for the `watch` command. |
| `exceptions.py` | Custom exceptions. |
| `utils.py` | Browser, editor, and project-root helpers. |

## Design principles

- **Orchestrator, not implementor**: every feature is delegated.
- **Optional extras**: missing libraries are a warning, not a crash.
- **One command to rule them all**: `run` accepts flags from every library.
- **Consistent output**: `rich` powers tables, colors, and progress messages.
- **Python only**: no Node build steps.

## Exit codes

`behave-runner` propagates the exit code of the underlying command:

| Code | Meaning |
| --- | --- |
| `0` | Success. |
| `1` | Test failures or tool errors. |
| `2` | Missing base `behave` or a configuration error. |
