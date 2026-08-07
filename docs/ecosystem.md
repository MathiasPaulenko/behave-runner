# Ecosystem

`behave-runner` is the entry point for the BehaveLib ecosystem. The table
below maps the 21 libraries to their purpose and the corresponding
optional extras.

## Library map

| Library | Category | Purpose | Extra |
| --- | --- | --- | --- |
| behave | Core | BDD framework. | core |
| behave-kit | Core | Timeouts and config profiles. | core |
| behave-model | Core | Feature and scenario parsing. | core |
| behave-pool | Execution | Parallel and sharded runs. | parallel |
| behave-priority | Execution | Priority ordering. | priority |
| behave-retry | Execution | Retry and flaky reports. | retry |
| behave-trace | Debug | Trace viewer and UI. | trace |
| behave-doctor | Quality | Project health and impact. | doctor |
| behave-lint | Quality | Feature file linting. | lint |
| behave-format | Quality | Feature file formatting. | format |
| behave-gen | Scaffolding | Project and feature generation. | gen |
| behave-steplib | Steps | Step library management. | steplib |
| behave-comments | Utility | Comment extraction. | comments |
| behave-tables | Utility | Table helpers. | — |
| wavexis | Recording | Browser session recording. | record |
| behave-modern-console-report | Reporting | Console. | report-console |
| behave-modern-html-report | Reporting | HTML report. | report-html |
| behave-modern-md-report | Reporting | Markdown report. | report-md |
| behave-modern-json-report | Reporting | JSON report. | report-json |
| behave-modern-sheets-report | Reporting | XLSX/CSV report. | report-sheets |
| behave-modern-file-report | Reporting | File report. | report-file |

## Installing groups

You can install libraries individually or use extras that bundle them:

```bash
# Core only
pip install behave-runner

# Execution extras
pip install "behave-runner[parallel,priority,retry]"

# Reporting extras
pip install "behave-runner[report-html,report-json]"

# Everything
pip install "behave-runner[all]"
```

## Graceful degradation

If a flag needs a library that is not installed, `behave-runner` prints a
warning and falls back to the nearest safe behavior instead of crashing.
