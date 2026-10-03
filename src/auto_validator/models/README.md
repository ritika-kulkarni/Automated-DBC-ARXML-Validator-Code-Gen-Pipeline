# Models

Pydantic types used after parsing. Keeps cantools/lxml quirks out of the validators.

| File | Types |
|------|-------|
| `findings.py` | `Finding`, `ValidationResult`, `PipelineReport` |
| `can_models.py` | `CanSignal`, `CanMessage`, `CanNetwork` |
| `arxml_models.py` | ports, interfaces, SWCs, `ArxmlModel` |
| `requirements.py` | `Requirement`, `RequirementsCatalog` |

Useful bits:

- `CanSignal.bit_positions()` — Intel vs Motorola occupancy
- `CanMessage.pgn` — J1939 PGN from 29-bit ID
- `Finding.exceeds(threshold)` — fail-on-severity helper

Class diagram: [ARCHITECTURE.md](../../../docs/ARCHITECTURE.md#data-model-simplified).
