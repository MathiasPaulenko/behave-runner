# CI/CD

`behave-runner` is designed to be run the same way locally and in CI. The
repository already includes GitHub Actions workflows; this page also
provides templates for GitLab CI and Jenkins.

## GitHub Actions

The `.github/workflows/ci.yml` workflow runs lint, type checks, and tests
across a matrix of Python versions and operating systems.

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: ruff format --check .
      - run: mypy --strict behave_runner

  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.11", "3.12", "3.13", "3.14"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest --cov=behave_runner --cov-report=xml
      - uses: codecov/codecov-action@v5
        with:
          files: ./coverage.xml
          fail_ci_if_error: false
```

### Docs and release

- `.github/workflows/docs.yml` builds and deploys MkDocs to GitHub Pages.
- `.github/workflows/release.yml` builds a new release when the version
  in `pyproject.toml` is bumped on `main`.

## GitLab CI

The following `.gitlab-ci.yml` runs lint and tests in two stages.

```yaml
stages:
  - lint
  - test

lint:
  stage: lint
  image: python:3.13
  script:
    - pip install -e ".[dev]"
    - ruff check .
    - ruff format --check .
    - mypy --strict behave_runner

test:
  stage: test
  image: python:3.13
  script:
    - pip install -e ".[dev]"
    - pytest --cov=behave_runner --cov-report=term-missing
  coverage: '/TOTAL.*? (\d+)%/'
```

## Jenkins

A minimal `Jenkinsfile` with a scripted pipeline:

```groovy
pipeline {
    agent any

    stages {
        stage('Install') {
            steps {
                sh 'python -m venv .venv'
                sh '.venv/bin/pip install -e ".[dev]"'
            }
        }

        stage('Lint') {
            steps {
                sh '.venv/bin/ruff check .'
                sh '.venv/bin/ruff format --check .'
                sh '.venv/bin/mypy --strict behave_runner'
            }
        }

        stage('Test') {
            steps {
                sh '.venv/bin/pytest --cov=behave_runner'
            }
        }
    }
}
```

## Running behave-runner in CI

Use the same commands you run locally. Example for a smoke test stage:

```bash
behave-runner run --tags @smoke
```

For CI profiles, store the flags in `pyproject.toml` and run:

```bash
behave-runner run --profile ci
```
