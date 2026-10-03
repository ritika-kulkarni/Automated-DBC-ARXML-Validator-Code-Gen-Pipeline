# Architecture

## What this tool does

Take DBC / ARXML / DOORS inputs, run checks early (git hook + CI), optionally emit RTE-ish C stubs, and dump a report.

Rough flow:

```text
CLI / git hook / CI
        │
        ▼
PipelineOrchestrator
        │
   ┌────┼────┬────────┐
   ▼    ▼    ▼        ▼
Parsers Validators Matcher Codegen
   │
   ▼
models (CanNetwork, ArxmlModel, Finding, …)
   │
   ▼
cantools / lxml / csv+json
```

## Layout

| Package | Job |
|---------|-----|
| `parsers/` | File → model |
| `validators/` | Model → findings |
| `requirements/` | DOORS names vs DBC/ARXML |
| `codegen/` | ARXML → headers / map files |
| `pipeline/` | Call the above in order |
| `utils/` | Logging, retries, report writers |

## Adding a DBC rule

1. Write `check_*(network) -> list[Finding]` under `validators/dbc/`
2. Call it from `DbcValidationEngine` behind a config flag
3. Document the rule id in `VALIDATION_RULES.md`
4. Drop a unit test in `tests/unit/`

## Failure handling

- File I/O: retry a few times on `OSError` / timeouts
- Validator bugs: turned into a `*.INTERNAL` finding instead of killing the process
- Bad ARXML: skip codegen
- Process exit code follows `pipeline.fail_on_severity`

## Related

- [FEATURES.md](FEATURES.md)
- [VALIDATION_RULES.md](VALIDATION_RULES.md)
- [CONFIGURATION.md](CONFIGURATION.md)
