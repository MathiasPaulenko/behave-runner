# Contributing

Contributions are welcome and appreciated. This page covers the basics — for
the full guidelines, please read
[CONTRIBUTING.md](https://github.com/MathiasPaulenko/behave-runner/blob/main/CONTRIBUTING.md)
in the repository.

## Setup

```bash
git clone https://github.com/MathiasPaulenko/behave-runner.git
cd behave-runner
make dev
pre-commit install
```

## Workflow

1. Create a feature branch from `main`
2. Make your changes
3. Run `make check` (lint + format check + tests)
4. Run `make test-cov` (coverage must be >= 90%)
5. Update `CHANGELOG.md` under the `[Unreleased]` section
6. Submit a pull request

## Code style

- **Linter**: Ruff (check + format, line length 100)
- **Type checker**: Mypy `--strict`
- **Tests**: Required for new features and bug fixes
- **Docstrings**: Google style for all public APIs
- **Imports**: `from __future__ import annotations` in every module

## Pre-commit hooks

The repository includes a `.pre-commit-config.yaml` with Ruff, Mypy, and
standard hygiene hooks. Run `pre-commit install` after cloning to enable
automatic checks on every commit.

## Reporting issues

- **Bugs**: Use the [bug report template](https://github.com/MathiasPaulenko/behave-runner/issues/new?template=bug_report.yml)
- **Features**: Use the [feature request template](https://github.com/MathiasPaulenko/behave-runner/issues/new?template=feature_request.yml)
- **Questions**: Use [GitHub Discussions](https://github.com/MathiasPaulenko/behave-runner/discussions)
