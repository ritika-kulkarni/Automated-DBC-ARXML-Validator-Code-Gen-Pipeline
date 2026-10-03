# Parsers

Convert on-disk automotive artifacts into normalized domain models. All parsers use `@retryable` for transient I/O failures.

## Components

| Class | File | Input | Output |
|-------|------|-------|--------|
| `DbcParser` | `dbc_parser.py` | `.dbc` | `CanNetwork` |
| `ArxmlParser` | `arxml_parser.py` | `.arxml` / `.xml` | `ArxmlModel` |
| `DoorsParser` | `doors_parser.py` | `.csv` / `.tsv` / `.json` | `RequirementsCatalog` |

## DBC (`DbcParser`)

- Backend: **cantools** (`strict=False` for industrial DBC quirks)
- Extracts cycle time, signal start values, FD/J1939 flags
- `parse_files()` merges multiple networks

## ARXML (`ArxmlParser`)

- Backend: **lxml** (namespace-tolerant AUTOSAR 4.x)
- Extracts SWCs, P/R/PR ports, S/R and C/S interfaces, init values
- No Tresos dependency — subset needed for validation + stub codegen

## DOORS (`DoorsParser`)

- Configurable column names via `RequirementsConfig`
- Alias-friendly (`object_id`, `can_signal`, `autosar_port`, …)
- JSON root may be a list or `{ "requirements": [...] }`

See also: [`../../../docs/FEATURES.md`](../../../docs/FEATURES.md) §§2, 4, 6.
