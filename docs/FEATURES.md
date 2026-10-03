# Feature Reference

What's in the tool, keyed to the modules that implement it.

---

## 1. Pipeline runner

**Where:** `src/auto_validator/pipeline/orchestrator.py`  
**CLI:** `auto-validator validate`

Stages, in order:

1. **Parse** DBC / ARXML / DOORS inputs (optional per stage)
2. **Validate** DBC rules (J1939 / CAN-FD / classic CAN)
3. **Validate** ARXML port and interface consistency
4. **Match** artifacts against DOORS requirements exports
5. **Generate** C RTE stubs and interface maps (when ARXML is clean)
6. **Report** findings to console, JSON, and JUnit XML

### Behaviors

| Behavior | Detail |
|----------|--------|
| Stage isolation | A parse failure in one stage becomes a `PIPELINE.FATAL` finding; other stages still run when possible |
| Codegen gate | C/RTE generation is skipped if ARXML validation produced errors |
| Severity threshold | `pipeline.fail_on_severity` controls overall pass/fail (`error` / `warning` / `info`) |
| Metadata | Report records which input files were processed |

---

## 2. DBC parsing (cantools)

**Where:** `src/auto_validator/parsers/dbc_parser.py`

Loads one or more `.dbc` files into a normalized `CanNetwork` model:

- Messages: name, frame ID, DLC, senders, cycle time, FD/J1939 flags
- Signals: start bit, length, byte order, scale/offset, min/max, unit, initial value, receivers
- Nodes and source file provenance

### Features

- **Multi-file merge** — `parse_files()` concatenates messages/nodes across DBCs
- **Retry on I/O** — transient `OSError` / timeouts retried via tenacity
- **Attribute extraction** — reads `GenMsgCycleTime`, `GenSigStartValue`, `VFrameFormat` when present
- **J1939 / CAN-FD heuristics** — extended IDs and FD frame-format attributes normalized into model flags

---

## 3. DBC validation rules

**Where:** `src/auto_validator/validators/dbc/`  
**Engine:** `DbcValidationEngine` (composite of individual checkers)

Each rule can be toggled in `configs/default.yaml` under `dbc.rules.*`.

### 3.1 Overlapping signal bit-starts

**Module:** `overlapping_signals.py`  
**Rule IDs:** `DBC.OVERLAP.BIT_COLLISION`, `DBC.OVERLAP.OUT_OF_BOUNDS`, `DBC.OVERLAP.INVALID_LAYOUT`

- Computes absolute bit occupancy for Intel (little-endian) and Motorola (big-endian) layouts
- Flags any shared bit between two signals in the same message
- Flags signals that extend past message DLC (`length * 8`)

**Why it matters:** Overlaps are a common silent corruptionsource caught late in Tresos/compile.

### 3.2 Endianness conflicts

**Module:** `endianness.py`  
**Rule IDs:** `DBC.ENDIAN.MIXED_IN_MESSAGE`, `DBC.ENDIAN.LONG_MOTOROLA`

- Warns when a single message mixes Intel and Motorola signals
- Emits info for unusually long Motorola signals (layout review hint)

### 3.3 Missing initial values

**Module:** `initial_values.py`  
**Rule ID:** `DBC.INIT.MISSING`

- Requires `GenSigStartValue` / cantools raw initial when `dbc.require_initial_values: true`
- Prevents undefined startup values on the bus / in RTE

### 3.4 Message cycle times

**Module:** `cycle_times.py`  
**Rule IDs:** `DBC.CYCLE.MISSING`, `DBC.CYCLE.NON_POSITIVE`, `DBC.CYCLE.MISMATCH`, `DBC.CYCLE.ID_CONFLICT`

- Warns when `GenMsgCycleTime` is absent
- Errors on non-positive cycle times
- Compares against an optional expected map (`--expected-cycles` JSON)
- Detects duplicate frame IDs with conflicting cycle times

### 3.5 J1939 compliance

**Module:** `j1939_rules.py`  
**Rule IDs:** `DBC.J1939.NOT_EXTENDED`, `DBC.J1939.PRIORITY`, `DBC.J1939.PGN_MISSING`, `DBC.J1939.LENGTH`, `DBC.J1939.NULL_SA`, `DBC.J1939.PGN_LENGTH_CONFLICT`

- Requires 29-bit extended framing for J1939 messages
- Validates priority field and derives PGN
- Warns on DLC > 8 without FD (TP may be intended)
- Warns on NULL source address `0xFE`
- Errors when the same PGN appears with conflicting lengths

### 3.6 CAN-FD / classic DLC limits

**Module:** `can_fd_limits.py`  
**Rule IDs:** `DBC.CANFD.DLC_TOO_LARGE`, `DBC.CANFD.INVALID_DLC`, `DBC.CAN.DLC_TOO_LARGE`

- Enforces ISO 11898-1 valid CAN-FD payload lengths: 0–8, 12, 16, 20, 24, 32, 48, 64
- Caps classic CAN at configurable max DLC (default 8)

---

## 4. ARXML parsing (lxml)

**Where:** `src/auto_validator/parsers/arxml_parser.py`

Lightweight AUTOSAR 4.x parser (no EB Tresos dependency). Extracts:

| Element | Model type |
|---------|------------|
| `APPLICATION-SW-COMPONENT-TYPE` | `ArxmlSoftwareComponent` |
| `P-PORT-PROTOTYPE` / `R-PORT-PROTOTYPE` / `PR-PORT-PROTOTYPE` | `ArxmlPort` |
| `SENDER-RECEIVER-INTERFACE` | `ArxmlInterface` + `DataElement` |
| `CLIENT-SERVER-INTERFACE` | `ArxmlInterface` + `Operation` / args |
| Init values | `DataElement.init_value` when present |

Namespace-tolerant (`r4.0`, common variants). Uses `recover=True` for minor tool-export XML issues.

---

## 5. ARXML validation

**Where:** `src/auto_validator/validators/arxml/port_consistency.py`  
**Class:** `ArxmlPortValidator`

| Rule area | Rule IDs | What it checks |
|-----------|----------|----------------|
| Port consistency | `ARXML.PORT.DUPLICATE`, `MISSING_INTERFACE_REF`, `UNRESOLVED_INTERFACE` | Duplicate ports; missing or dangling interface TREF |
| Interface completeness | `ARXML.IFACE.EMPTY_SR`, `EMPTY_CS` | Empty S/R data elements or C/S operations |
| Data types | `ARXML.TYPE.MISSING`, `ARXML.TYPE.CUSTOM` | Missing types (error); custom app types (info) |

Toggle via `arxml.rules.*` in config.

---

## 6. DOORS requirements parsing

**Where:** `src/auto_validator/parsers/doors_parser.py`

Loads requirements from:

- **CSV / TSV** — header row with configurable column names
- **JSON** — array, or object with `requirements` / `items` / `data`

Normalized fields: `req_id`, `title`, `description`, `signal_name`, `port_name`, `message_name`, `status`.

Column aliases supported (e.g. `object_id`, `can_signal`, `autosar_port`).

---

## 7. Requirements matching (traceability)

**Where:** `src/auto_validator/requirements/matcher.py`  
**Class:** `RequirementsMatcher`

| Direction | Rule ID | Severity |
|-----------|---------|----------|
| DOORS signal missing in DBC | `REQ.SIGNAL.MISSING_IN_DBC` | error |
| DBC signal with no DOORS trace | `REQ.SIGNAL.UNTRACED` | warning (strict mode) |
| DOORS port missing in ARXML | `REQ.PORT.MISSING_IN_ARXML` | error |
| ARXML port with no DOORS trace | `REQ.PORT.UNTRACED` | warning (strict mode) |

### Match modes

- **`strict`** — exact name match; also reports untraced artifacts when the catalog has coverage expectations
- **`fuzzy`** — suggestions via `difflib` using `fuzzy_threshold` (default 0.85); also loose suggestions at 0.6 for helpfulness

---

## 8. C stub header generation

**Where:** `src/auto_validator/codegen/c_stubs.py`  
**Class:** `CStubGenerator`

From each SWC, generates:

| File | Contents |
|------|----------|
| `Rte_Type.h` | AUTOSAR-style typedefs (`uint8`…`float64`, `boolean`, `Std_ReturnType`, `E_OK` / `E_NOT_OK`); stubs for custom app types |
| `Rte_<SwcName>.h` | `Rte_Write_*` / `Rte_Read_*` for S/R ports; `Rte_Call_*` / `Rte_Entry_*` for C/S |

Guarded with include guards; marked `DO NOT EDIT`.

See [CODEGEN.md](CODEGEN.md).

---

## 9. RTE interface mapping generation

**Where:** `src/auto_validator/codegen/rte_mappings.py`  
**Class:** `RteMappingGenerator`

| File | Purpose |
|------|---------|
| `rte_interface_map.json` | Machine-readable SWC/port/interface/data-element table |
| `Rte_InterfaceMap.c` | C array `Rte_PortMap[]` + `Rte_PortMap_Size` for tooling / diagnostics |

---

## 10. Configuration system

**Where:** `src/auto_validator/config.py` + `configs/default.yaml`

- YAML load via PyYAML
- Validated with **pydantic** / **pydantic-settings**
- Env prefix: `AUTO_VALIDATOR_`
- Sensible defaults if no file is provided

Full reference: [CONFIGURATION.md](CONFIGURATION.md).

---

## 11. CLI

**Where:** `src/auto_validator/cli.py`  
**Entry points:** `auto-validator`, `python -m auto_validator`

| Command | Purpose |
|---------|---------|
| `validate` | Full pipeline (DBC + ARXML + requirements + optional codegen) |
| `codegen` | ARXML-only stub/RTE generation |
| `hook-check` | Classify paths from git/CI and validate (codegen skipped) |

Details: [CLI.md](CLI.md).

---

## 12. Structured logging

**Where:** `src/auto_validator/utils/logging.py`

- Logger namespace: `auto_validator.*`
- Formats: **structured** (JSON lines) or **plain**
- Optional file handler via `logging.file`
- Levels: DEBUG / INFO / WARNING / ERROR

---

## 13. Retry mechanism

**Where:** `src/auto_validator/utils/retry.py`

- Decorator `@retryable` built on **tenacity**
- Retries `OSError`, `TimeoutError`, `ConnectionError`
- Exponential backoff; attempts/backoff driven by `pipeline.max_retries` and `retry_backoff_seconds` (parsers use small defaults; orchestrator config documents the policy)

Applied to DBC, ARXML, and DOORS file parsers.

---

## 14. Reporting

**Where:** `src/auto_validator/utils/report.py`  
**Class:** `ReportWriter`

| Format | Output |
|--------|--------|
| `console` | Rich table (severity, rule, location, message) |
| `json` | `output/reports/pipeline_report.json` |
| `junit` | `output/reports/pipeline_junit.xml` (CI-friendly) |

Formats selected via `report.formats` in config.

---

## 15. Domain models (typed)

**Where:** `src/auto_validator/models/`

| Module | Models |
|--------|--------|
| `findings.py` | `Finding`, `FindingSeverity`, `ValidationResult`, `PipelineReport` |
| `can_models.py` | `CanSignal`, `CanMessage`, `CanNetwork`, `ByteOrder` |
| `arxml_models.py` | `ArxmlPort`, `ArxmlInterface`, `ArxmlSoftwareComponent`, `ArxmlModel` |
| `requirements.py` | `Requirement`, `RequirementsCatalog` |

Pydantic models provide validation (e.g. positive signal length) and serialization for reports.

---

## 16. Git hooks

**Where:** `hooks/pre-commit`, `.pre-commit-config.yaml`

- Native bash hook for staged `.dbc` / `.arxml` / requirements files
- Optional [pre-commit](https://pre-commit.com) framework integration
- Invokes `auto-validator hook-check` (validate-only; no codegen in the hook path)

See [HOOKS_AND_CI.md](HOOKS_AND_CI.md).

---

## 17. CI (GitHub Actions)

**Where:** `.github/workflows/ci.yml`

Jobs:

1. **test** — Python 3.9–3.12 matrix: install, ruff, mypy (non-blocking), pytest + coverage
2. **validate-fixtures** — known-good fixtures must pass; overlapping DBC must fail

---

## 18. Test suite & fixtures

**Where:** `tests/`

| Kind | Marker | Coverage focus |
|------|--------|----------------|
| Unit | `@pytest.mark.unit` | Models, individual rules, parsers, matcher, retry |
| Integration | `@pytest.mark.integration` | Full orchestrator + Click CLI |
| Edge | `@pytest.mark.edge` | Empty network, disabled matcher, cycle mismatch, CAN-FD invalid DLC |

Fixtures under `tests/fixtures/{dbc,arxml,doors}/`.

See [TESTING.md](TESTING.md).

---

## 19. Extensibility hooks (by design)

| Extension | How |
|-----------|-----|
| New DBC rule | Add checker module → wire in `DbcValidationEngine` + config flag + unit test |
| New ARXML check | Extend `ArxmlPortValidator.validate` or add sibling validator |
| New report format | Extend `ReportWriter.write` |
| New requirements source | Extend `DoorsParser` format dispatch |

---

## Feature → module map (quick index)

| Feature | Primary module(s) |
|---------|-------------------|
| Pipeline | `pipeline/orchestrator.py` |
| CLI | `cli.py` |
| Config | `config.py`, `configs/default.yaml` |
| DBC parse | `parsers/dbc_parser.py` |
| ARXML parse | `parsers/arxml_parser.py` |
| DOORS parse | `parsers/doors_parser.py` |
| DBC rules | `validators/dbc/*.py` |
| ARXML rules | `validators/arxml/port_consistency.py` |
| Requirements | `requirements/matcher.py` |
| C stubs | `codegen/c_stubs.py` |
| RTE maps | `codegen/rte_mappings.py` |
| Logging | `utils/logging.py` |
| Retry | `utils/retry.py` |
| Reports | `utils/report.py` |
| Git hook | `hooks/pre-commit` |
| CI | `.github/workflows/ci.yml` |
