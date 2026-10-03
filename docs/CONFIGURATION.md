# Configuration Reference

Primary file: [`configs/default.yaml`](../configs/default.yaml)  
Loader: `auto_validator.config.load_config(path)`

Override on CLI with `--config path/to.yaml`.  
Environment overrides use prefix `AUTO_VALIDATOR_` (pydantic-settings).

---

## `pipeline`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `fail_on_severity` | `error` \| `warning` \| `info` | `error` | Minimum severity that fails the run |
| `parallel` | bool | `false` | Reserved for future parallel stage execution |
| `max_retries` | int | `3` | Policy for retryable I/O (documented; parsers use `@retryable`) |
| `retry_backoff_seconds` | float | `1.0` | Backoff base for retries |

---

## `logging`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `level` | `DEBUG`…`ERROR` | `INFO` | Root logger level for `auto_validator` |
| `format` | `structured` \| `plain` | `structured` | JSON lines vs human-readable |
| `file` | string \| null | `null` | Optional log file path |

---

## `dbc`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | `true` | Run DBC parse + validation |
| `rules.overlapping_signals` | bool | `true` | Bit collision / OOB checks |
| `rules.endianness_conflicts` | bool | `true` | Mixed byte-order warnings |
| `rules.missing_initial_values` | bool | `true` | Missing start values |
| `rules.cycle_time_mismatch` | bool | `true` | Cycle time rules |
| `rules.j1939_compliance` | bool | `true` | J1939 rules |
| `rules.can_fd_limits` | bool | `true` | Classic/FD DLC rules |
| `cycle_time_tolerance_ms` | int | `0` | Allowed delta vs expected cycles |
| `classic_can_max_dlc` | int | `8` | Max classic payload bytes |
| `can_fd_max_dlc` | int | `64` | Max FD payload bytes |
| `require_initial_values` | bool | `true` | Treat missing init as error when rule enabled |

---

## `arxml`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | `true` | Run ARXML parse + validation |
| `rules.port_consistency` | bool | `true` | Port/interface ref checks |
| `rules.interface_completeness` | bool | `true` | Empty interface checks |
| `rules.data_type_mapping` | bool | `true` | Data type presence / custom info |
| `generate_c_stubs` | bool | `true` | Emit `Rte_*.h` |
| `generate_rte_mappings` | bool | `true` | Emit JSON + `Rte_InterfaceMap.c` |
| `output_dir` | string | `output/codegen` | Codegen destination |

---

## `requirements`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | `true` | Run DOORS matching |
| `match_mode` | `strict` \| `fuzzy` | `strict` | Exact vs suggestion-oriented |
| `fuzzy_threshold` | float | `0.85` | `difflib` cutoff for close matches |
| `id_column` | string | `req_id` | CSV/JSON key for requirement ID |
| `signal_column` | string | `signal_name` | Column for CAN signal name |
| `port_column` | string | `port_name` | Column for AUTOSAR port name |

---

## `report`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `formats` | list | `[console, json, junit]` | Output channels |
| `output_dir` | string | `output/reports` | Where JSON/JUnit are written |

---

## Example: validate-only, fail on warnings

```yaml
pipeline:
  fail_on_severity: warning

dbc:
  enabled: true
  require_initial_values: true

arxml:
  enabled: true
  generate_c_stubs: false
  generate_rte_mappings: false

requirements:
  enabled: true
  match_mode: fuzzy
  fuzzy_threshold: 0.8

report:
  formats: [console, junit]
  output_dir: ci-reports
```

---

## Loading order

1. Built-in pydantic defaults  
2. YAML file (if provided / `configs/default.yaml` exists)  
3. Environment variables with `AUTO_VALIDATOR_` prefix (where supported by nested settings)
