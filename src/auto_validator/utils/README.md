# Utils

Cross-cutting infrastructure shared by parsers, validators, and the pipeline.

## Modules

| File | Feature |
|------|---------|
| `logging.py` | `setup_logging`, `get_logger`, JSON `StructuredFormatter` |
| `retry.py` | `@retryable` decorator (tenacity, exponential backoff) |
| `report.py` | `ReportWriter` — console (Rich), JSON, JUnit XML |

## Logging

- Namespace: `auto_validator.*`
- Config: `logging.level`, `logging.format`, `logging.file`

## Retry

Retries `OSError`, `TimeoutError`, `ConnectionError` by default. Used by DBC/ARXML/DOORS parsers.

## Reports

Writes under `report.output_dir`:

- `pipeline_report.json`
- `pipeline_junit.xml`

Plus a Rich findings table on stderr when `console` is enabled.
