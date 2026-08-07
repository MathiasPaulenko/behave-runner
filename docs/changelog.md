# Changelog

The project changelog is also maintained in
[CHANGELOG.md](https://github.com/MathiasPaulenko/behave-runner/blob/main/CHANGELOG.md)
at the repository root.

## Unreleased

## [1.1.0] - 2026-08-07

### Fixed

- Fixed `load_config` not falling back to `behave.ini` when `pyproject.toml`
  exists but lacks `[tool.behave-runner]` section.
- Fixed `_format_value` not escaping double quotes and backslashes in TOML
  string values, which could produce invalid TOML.
- Fixed `run.py` only loading 4 config values from profiles. Now loads all
  supported values: parallel, retries, dry_run, stop_on_failure,
  scenario_timeout, priority_order, fail_fast, flaky_report, max_failures.
- Fixed `report.py` not supporting "file" format even though
  `behave-modern-file-report` is listed as an optional extra.
- Fixed `orchestrator.py` not passing environment variables to subprocess
  fallback paths.
- Fixed README CLI option names and watch command quit instructions.
- Translated `mkdocs.yml` site description and `docs/index.md` to English.
- Fixed `docs/index.md` incorrect examples and non-existent config keys.
- Updated `pyproject.toml` development status from Alpha to Production/Stable.
- Fixed `.pre-commit-config.yaml` mypy hook missing project dependencies.
- Added `SECURITY.md`.
- Improved `orchestrator.py` by reducing duplicated subprocess fallback code.
- Improved `output.py` symlink safety in `clean_output_dir`.
- Improved `watcher.py` error handling to log instead of silently suppressing.
- Added `TypedDict` for scenario info in `features.py`.
- Added regression tests for all bug fixes.
- Fixed `config_cmd.py` exit code for missing pyproject.toml (1 → 2).
- Fixed all Spanish text in docs command reference.
- Fixed `docs/cli.md` report format names (xlsx → sheets, pdf → file).
- Fixed `docs/cli.md` --smoke flag incorrectly listed as requiring
  behave-priority.
- Fixed `docs/commands/report.md` format names and added "file" to format
  list.
- Fixed `docs/commands/run.md` --smoke dependency listing.
- Fixed `docs/commands/init.md` positional arg example to use --name flag.
- Fixed `docs/quickstart.md` init example to use --name flag.
- Fixed `docs/index.md` init example and report format example.
- Fixed `docs/configuration.md` fallback and merge scope descriptions.
- Fixed `docs/installation.md` and `docs/ecosystem.md` priority extra
  description.
- Added `sdist` build target to `pyproject.toml` to include tests and docs.
- Refactored `orchestrator.py` to eliminate duplicated subprocess fallback
  code via `_try_optional` and `_run_behave_subprocess` helpers.
- Added Codecov badge to README.
- Added Dependabot configuration for pip and GitHub Actions.
- Upgraded `codecov-action` to v5 in CI workflow.
- Simplified CI pip caching to use `setup-python` built-in cache.
- Added `SECURITY.md` to sdist include list.
- Added Requirements and Acknowledgements sections to README.
- Added `bandit` and `pip-audit` to dev dependencies for security scanning.
- Added `Framework :: Pytest` classifier to `pyproject.toml`.
- Added security job to CI workflow (bandit + pip-audit).
- Added GitHub funding configuration file.
- Added bandit configuration to `pyproject.toml`.
- Added `make security` target to Makefile.
- Fixed `docs/ecosystem.md` library count (22 → 21).
- Fixed `docs/configuration.md` incorrect `behave.ini` profile example.
- Updated `docs/ci-cd.md` to reflect codecov-action v5.
- Fixed `config.py` `load_config` crashing with `AttributeError` if `[tool]`
  is not a dictionary in `pyproject.toml`.
- Fixed `config.py` `load_config` not catching `UnicodeDecodeError` from
  `configparser` for non-decodable `behave.ini` files.
- Fixed `output.py` `clean_output_dir` crashing on `OSError` from `iterdir()`.
- Fixed `run.py` `flaky_report` check not accounting for profile-defined
  retries.
- Fixed `run.py` profile `max_fail` key being silently ignored.
- Fixed `run.py` profile `smoke` key being silently ignored.
- Fixed `config_cmd.py` `_set_config_value` corrupting TOML when setting
  dotted keys that conflict with existing subtables.
- Fixed `config_cmd.py` `config set` not catching `ConfigError`.
- Fixed `orchestrator.py` `RunConfig.parallel=0` being allowed but silently
  falling back to sequential execution.
- Fixed `features.py` `feature.name` and `scenario.name` being `None`
  crashing with `AttributeError` / `TypeError`.
- Fixed `features.py` `ScenarioInfo` TypedDict contract being violated when
  names are `None`.
- Fixed `watch.py` negative `--debounce` causing the watcher to never trigger.
- Fixed `output.py` `ensure_output_dir` crashing if path exists as a file.
- Fixed `orchestrator.py` `_try_optional` not catching non-`ImportError`
  exceptions from optional dependencies.
- Fixed `config.py` `_ini_flat_to_nested` silently overwriting leaf values
  with dicts on key conflicts.
- Fixed `Makefile` `test` and `test-cov` targets not excluding e2e tests.
- Fixed `.github/workflows/ci.yml` `bandit` and `pip-audit` not declared as
  `dev` dependencies.
- Fixed `orchestrator.py` `run()` saving/restoring all environment variables
  instead of only behave-specific ones.
- Fixed `output.py` race condition in `find_latest_report` when calling
  `stat()`.
- Fixed `select.py` and `list_cmd.py` lacking validation for the `fmt`
  argument.
- Fixed `config_cmd.py` `_parse_value` not stripping whitespace from string
  values.
- Fixed `run.py` shard values from profiles not being type-validated.

### Added

- `AGENTS.md` with project-specific conventions and verification steps.
- `behave_runner/core/features.py` with `collect_scenarios` and `matches_tags`
  utilities extracted from `select.py` and `list_cmd.py`.
- Comprehensive regression test suite (`tests/unit/test_regression.py`).

## [1.0.1] - 2026-08-07

- Updated README and package description to English.
- Added repository topics on GitHub.
- No functional changes.

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
