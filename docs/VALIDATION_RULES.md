# Validation Rules Catalog

Every rule ID emitted by the pipeline, with severity, meaning, and remediation.

Severities: **error** (fails pipeline when `fail_on_severity: error`), **warning**, **info**.

---

## DBC — Overlapping signals

| Rule ID | Severity | Meaning | Suggestion |
|---------|----------|---------|------------|
| `DBC.OVERLAP.BIT_COLLISION` | error | Two signals share one or more bits in the same message | Adjust `start_bit` / `length` so ranges do not overlap |
| `DBC.OVERLAP.OUT_OF_BOUNDS` | error | Signal bits fall outside `DLC × 8` | Shorten signal or increase message DLC |
| `DBC.OVERLAP.INVALID_LAYOUT` | error | Bit layout could not be computed | Fix malformed start/length/byte-order |

**Config:** `dbc.rules.overlapping_signals`

---

## DBC — Endianness

| Rule ID | Severity | Meaning | Suggestion |
|---------|----------|---------|------------|
| `DBC.ENDIAN.MIXED_IN_MESSAGE` | warning | Message mixes Intel and Motorola signals | Prefer one byte order per message |
| `DBC.ENDIAN.LONG_MOTOROLA` | info | Long Motorola signal may need OEM layout review | Verify against network design spec |

**Config:** `dbc.rules.endianness_conflicts`

---

## DBC — Initial values

| Rule ID | Severity | Meaning | Suggestion |
|---------|----------|---------|------------|
| `DBC.INIT.MISSING` | error | No `GenSigStartValue` / initial value | Set start value in DBC tool |

**Config:** `dbc.rules.missing_initial_values`, `dbc.require_initial_values`

---

## DBC — Cycle times

| Rule ID | Severity | Meaning | Suggestion |
|---------|----------|---------|------------|
| `DBC.CYCLE.MISSING` | warning | No `GenMsgCycleTime` | Set cycle time attribute |
| `DBC.CYCLE.NON_POSITIVE` | error | Cycle time ≤ 0 | Use a positive period in ms |
| `DBC.CYCLE.MISMATCH` | error | Actual ≠ expected (beyond tolerance) | Align DBC with OEM matrix / `--expected-cycles` |
| `DBC.CYCLE.ID_CONFLICT` | error | Same frame ID, different cycle times | Deduplicate or align attributes |

**Config:** `dbc.rules.cycle_time_mismatch`, `dbc.cycle_time_tolerance_ms`

---

## DBC — J1939

| Rule ID | Severity | Meaning | Suggestion |
|---------|----------|---------|------------|
| `DBC.J1939.NOT_EXTENDED` | error | J1939 message not 29-bit extended | Enable extended frame |
| `DBC.J1939.PRIORITY` | error | Priority field out of range | Priority must be 0–7 |
| `DBC.J1939.PGN_MISSING` | warning | PGN could not be derived | Check ID layout |
| `DBC.J1939.LENGTH` | warning | Classic J1939 DLC > 8 | Confirm TP/BAM intent or use CAN-FD |
| `DBC.J1939.NULL_SA` | warning | Source address is `0xFE` (NULL) | Avoid NULL SA for TX messages |
| `DBC.J1939.PGN_LENGTH_CONFLICT` | error | Same PGN, conflicting lengths | Harmonize DLC for that PGN |

**Config:** `dbc.rules.j1939_compliance`

---

## DBC — CAN / CAN-FD limits

| Rule ID | Severity | Meaning | Suggestion |
|---------|----------|---------|------------|
| `DBC.CANFD.DLC_TOO_LARGE` | error | FD payload > configured max (default 64) | Reduce length |
| `DBC.CANFD.INVALID_DLC` | error | Length not in ISO FD set | Use 0–8,12,16,20,24,32,48,64 |
| `DBC.CAN.DLC_TOO_LARGE` | error | Classic CAN DLC > max (default 8) | Mark FD or reduce DLC |

**Config:** `dbc.rules.can_fd_limits`, `dbc.classic_can_max_dlc`, `dbc.can_fd_max_dlc`

---

## ARXML — Ports & interfaces

| Rule ID | Severity | Meaning | Suggestion |
|---------|----------|---------|------------|
| `ARXML.PORT.DUPLICATE` | error | Duplicate port name on one SWC | Rename or remove duplicate |
| `ARXML.PORT.MISSING_INTERFACE_REF` | error | Port has no interface TREF | Add PROVIDED/REQUIRED-INTERFACE-TREF |
| `ARXML.PORT.UNRESOLVED_INTERFACE` | error | Interface name not found in model | Define interface or fix path |
| `ARXML.IFACE.EMPTY_SR` | error | S/R interface has no data elements | Add VARIABLE-DATA-PROTOTYPE entries |
| `ARXML.IFACE.EMPTY_CS` | error | C/S interface has no operations | Add CLIENT-SERVER-OPERATION entries |
| `ARXML.TYPE.MISSING` | error | Data element has empty type | Set TYPE-TREF |
| `ARXML.TYPE.CUSTOM` | info | Non-primitive application type | Expected for complex types; ensure mapping exists |

**Config:** `arxml.rules.port_consistency`, `interface_completeness`, `data_type_mapping`

---

## Requirements (DOORS)

| Rule ID | Severity | Meaning | Suggestion |
|---------|----------|---------|------------|
| `REQ.SIGNAL.MISSING_IN_DBC` | error | DOORS signal not in DBC | Add signal or fix DOORS name |
| `REQ.SIGNAL.UNTRACED` | warning | DBC signal has no DOORS row | Add requirement or exclude |
| `REQ.PORT.MISSING_IN_ARXML` | error | DOORS port not in ARXML | Add port or fix DOORS name |
| `REQ.PORT.UNTRACED` | warning | ARXML port has no DOORS row | Trace in DOORS export |

**Config:** `requirements.enabled`, `match_mode`, `fuzzy_threshold`

---

## Pipeline / codegen / internal

| Rule ID | Severity | Meaning |
|---------|----------|---------|
| `PIPELINE.FATAL` | error | Unrecoverable stage exception (parse/IO) |
| `CODEGEN.OK` | info | Artifacts generated successfully |
| `CODEGEN.FAIL` | error | Code generation threw an exception |
| `DBC.INTERNAL` / `ARXML.INTERNAL` / `REQ.INTERNAL` | error | Unexpected validator exception (surfaced as finding) |

---

## Severity threshold behavior

`pipeline.fail_on_severity` in config:

| Value | Pipeline fails if findings include… |
|-------|-------------------------------------|
| `error` | any error (default) |
| `warning` | any warning or error |
| `info` | any finding at all |
