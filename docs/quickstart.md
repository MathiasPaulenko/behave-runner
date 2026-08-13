---
title: Quick Start
description: Get up and running with behave-runner in five minutes.
---

This guide walks you through a minimal `behave-runner` workflow. You will
initialize a project, run a feature, list scenarios, and start the file watcher.

## 1. Initialize a project

Use the `init` command to scaffold a new Behave project:

```bash
behave-runner init --name my-project
cd my-project
```

The command creates a standard layout with a `features/` directory,
`steps/`, and an `environment.py` file.

!!! note "Project name"
    `--name` is required. The command creates a standard layout with a
    `features/` directory, `steps/`, and an `environment.py` file inside the
    named project directory.

## 2. Add a feature

Create `features/login.feature` with a simple scenario:

```gherkin
Feature: User login

  Scenario: Valid login
    Given the user is on the login page
    When the user enters valid credentials
    Then the user is redirected to the dashboard
```

Add matching step definitions in `steps/login_steps.py` if you want the
test to be executable. For this quickstart, listing the scenario is enough.

## 3. List scenarios

Preview every scenario before running anything:

```bash
behave-runner list features/
```

The output shows the feature, scenario, location, and tags in a table. You can
also export the list to JSON:

```bash
behave-runner list features/ --format json
```

## 4. Run the tests

Run every scenario in the `features/` directory:

```bash
behave-runner run features/
```

Filter the run by tag:

```bash
behave-runner run --tags @smoke features/
```

!!! note "Where is the @smoke tag?"
    Add `@smoke` above a `Scenario:` line to see `behave-runner` pick only
    those scenarios.

## 5. Watch for changes

Start the watcher to re-run the suite whenever feature or step files change:

```bash
behave-runner watch features/
```

By default, the watcher polls `features/`, `steps/`, `environment.py`,
`behave.ini`, and `pyproject.toml` with a 500 ms debounce. Press `Ctrl+C` to
stop.

## Next steps

- Read the [CLI reference](cli.md) for every command and option.
- Learn how [profiles and CLI flags merge](configuration.md) to keep your
central configuration tidy.
- Explore the per-command guides under `Commands` in the navigation.
