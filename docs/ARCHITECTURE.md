# Architecture

## Goals

1. **Shift-left**: catch DBC/ARXML defects at commit time, not Tresos/compiler.
2. **Separation of concerns**: parse → validate → match → codegen → report.
3. **Reliability**: typed models, retry on I/O, findings instead of uncaught crashes.
4. **Extensibility**: add a new DBC rule without touching the orchestrator.

## Layering

```text
┌─────────────────────────────────────────────┐
│  CLI / Git hook / CI                         │
├─────────────────────────────────────────────┤
│  PipelineOrchestrator (Facade)               │
├──────────┬──────────┬──────────┬────────────┤
│ Parsers  │Validators│ Matcher  │ Codegen    │
├──────────┴──────────┴──────────┴────────────┤
│  Domain models (pydantic)                    │
├─────────────────────────────────────────────┤
│  cantools / lxml / stdlib CSV-JSON           │
└─────────────────────────────────────────────┘
```

## SOLID mapping

| Principle | Application |
|-----------|-------------|
| **S** | Each rule module (`overlapping_signals.py`, …) has one responsibility |
| **O** | New rules register in `DbcValidationEngine` without changing existing checkers |
| **L** | All validators subclass `BaseValidator[T]` and are interchangeable in the pipeline |
| **I** | Narrow target types (`CanNetwork`, `ArxmlModel`, `RequirementsMatchTarget`) |
| **D** | Orchestrator depends on abstractions/config, not concrete file formats |

## Design patterns

| Pattern | Where |
|---------|-------|
| **Facade** | `PipelineOrchestrator` hides parser/validator/codegen wiring |
| **Strategy** | Pluggable DBC checkers selected by config flags |
| **Template Method** | `BaseValidator.run` times execution and normalizes errors to findings |
| **Anti-corruption layer** | `models/*` isolate cantools/lxml quirks from business rules |

## Validation rules (DBC) — summary

| Rule ID prefix | Check |
|----------------|-------|
| `DBC.OVERLAP.*` | Bit occupancy collisions & out-of-bounds vs DLC |
| `DBC.ENDIAN.*` | Mixed Intel/Motorola in one message |
| `DBC.INIT.*` | Missing `GenSigStartValue` |
| `DBC.CYCLE.*` | Missing/invalid/mismatched cycle times; ID conflicts |
| `DBC.J1939.*` | Extended ID, priority, PGN length consistency |
| `DBC.CANFD.*` / `DBC.CAN.*` | Valid FD payload lengths / classic DLC |

Full catalog (including ARXML + REQ): [VALIDATION_RULES.md](VALIDATION_RULES.md).

## Error handling strategy

- Parsers: `@retryable` for transient `OSError` / timeouts
- Validators: unexpected exceptions → `*.INTERNAL` error finding (pipeline continues)
- Orchestrator: stage failures become `PIPELINE.FATAL`; codegen gated on clean ARXML
- CLI: process exit code mirrors `PipelineReport.overall_passed` after severity threshold

## Extension points

1. Add `validators/dbc/my_rule.py` with `check_*(network) -> list[Finding]`
2. Wire into `DbcValidationEngine.validate` + config flag
3. Document the rule in [VALIDATION_RULES.md](VALIDATION_RULES.md) and [FEATURES.md](FEATURES.md)
4. Add unit tests under `tests/unit/`
5. Optionally add a fixture under `tests/fixtures/dbc/`

## Related docs

- [FEATURES.md](FEATURES.md) — feature-by-feature walkthrough  
- [CONFIGURATION.md](CONFIGURATION.md) — config knobs  
- [CODEGEN.md](CODEGEN.md) — generated artifacts  
- Package READMEs under `src/auto_validator/*/README.md`
