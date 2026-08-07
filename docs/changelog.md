# Changelog

The project changelog is also maintained in
[CHANGELOG.md](https://github.com/MathiasPaulenko/behave-runner/blob/main/CHANGELOG.md)
at the repository root.

## Unreleased

## [1.0.0] - 2026-08-07

- Stable release of `behave-runner`.
- All 16 CLI commands implemented and documented.
- MkDocs documentation site with architecture, ecosystem, Python API,
  CI/CD and FAQ pages.
- Community files and README.
- Fixed CI coverage threshold for environments without optional extras.
- Fixed cross-platform `find_project_root` test.
- Added `BEHAVE_RUNNER_NO_BROWSER` to prevent browser opening during tests.

## [0.1.0] - 2026-07-08

- Initial release of `behave-runner` CLI.
- Commands: `run`, `list`, `select`, `lint`, `format`, `doctor`, `impact`,
  `watch`, `report`, `trace`, `steps`, `generate`, `init`, `config`, `open`,
  `record`.
- E2E test fixtures for `saucedemo.com` and `pokeapi.co`.
- CI workflow with matrix testing across Python 3.11-3.14.
- MkDocs Material documentation site.
- Community files: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`,
  `SUPPORT.md`, issue and pull request templates.
