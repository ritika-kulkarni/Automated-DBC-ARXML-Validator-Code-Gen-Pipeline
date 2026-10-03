# Utils

Shared helpers used by parsers, validators, and the pipeline.

| File | Role |
|------|------|
| `logging.py` | JSON or plain logs under `auto_validator.*` |
| `retry.py` | `@retryable` (tenacity) for transient I/O |
| `report.py` | Console / JSON / JUnit writers |

Reports default to `output/reports/` (`report.output_dir` in config).
