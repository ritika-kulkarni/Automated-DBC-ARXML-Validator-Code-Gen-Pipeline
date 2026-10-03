# Models

Pydantic types used after parsing. Keeps cantools/lxml details out of the validators.

## Modules

| File | Types |
|------|-------|
| `findings.py` | `FindingSeverity`, `Finding`, `ValidationResult`, `PipelineReport` |
| `can_models.py` | `ByteOrder`, `CanSignal`, `CanMessage`, `CanNetwork` |
| `arxml_models.py` | `PortDirection`, `DataElement`, `Operation`, `ArxmlInterface`, `ArxmlPort`, `ArxmlSoftwareComponent`, `ArxmlModel` |
| `requirements.py` | `Requirement`, `RequirementsCatalog` |

## Notable behaviors

- `CanSignal.bit_positions()` — Intel consecutive bits; Motorola DBC/SAE layout
- `CanMessage.pgn` — J1939 PGN derivation from 29-bit ID
- `Finding.exceeds(threshold)` — used for pipeline fail-on-severity
- `PipelineReport.to_summary()` — compact status for logs/CI

Models are serialized into `pipeline_report.json` via pydantic.
