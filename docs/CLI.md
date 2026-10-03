# CLI Reference

Install entry point: `auto-validator`  
Module form: `python -m auto_validator`

```text
auto-validator [OPTIONS] COMMAND [ARGS]
```

Global:

| Option | Description |
|--------|-------------|
| `--version` | Print package version |
| `-h`, `--help` | Help |

Exit codes: **0** = passed (per severity threshold), **1** = failed.

---

## `validate`

Run DBC/ARXML validation, optional DOORS match, and optional codegen.

```bash
auto-validator validate \
  --dbc path/to/network.dbc \
  --arxml path/to/swc.arxml \
  --requirements path/to/doors.csv \
  --config configs/default.yaml \
  --expected-cycles tests/fixtures/doors/expected_cycles.json
```

| Option | Required | Description |
|--------|----------|-------------|
| `--dbc` | at least one of `--dbc` / `--arxml` | DBC path(s); repeatable or comma-separated |
| `--arxml` | at least one of `--dbc` / `--arxml` | ARXML path(s) |
| `--requirements` | no | DOORS CSV/JSON path(s) |
| `--config` | no | YAML config path |
| `--skip-codegen` | no | Skip C stub / RTE generation |
| `--expected-cycles` | no | JSON map `{ "MessageName": cycle_ms }` |
| `--quiet` | no | Set log level to ERROR |

---

## `codegen`

Generate stubs/mappings from ARXML only (DBC and requirements stages disabled).

```bash
auto-validator codegen \
  --arxml tests/fixtures/arxml/valid_swc.arxml \
  --output output/codegen
```

| Option | Required | Description |
|--------|----------|-------------|
| `--arxml` | yes | ARXML input(s) |
| `--output` | no | Output directory (default `output/codegen`) |
| `--config` | no | YAML config |

Still runs ARXML validation; exit non-zero if validation errors occur. Codegen is skipped when ARXML has errors (orchestrator gate).

---

## `hook-check`

Used by git hooks / CI file lists. Classifies paths and validates; **does not** run codegen.

```bash
auto-validator hook-check --config configs/default.yaml file1.dbc file2.arxml
```

| Input | Behavior |
|-------|----------|
| `*.dbc` | DBC validation |
| `*.arxml` | ARXML validation |
| `*.csv` / `*.json` with `door` or `req` in the name | Requirements matching |
| Other files only | Prints skip message, exit 0 |

| Option | Description |
|--------|-------------|
| `--config` | YAML config |
| `FILES…` | Positional paths (from `git` / pre-commit) |

---

## Examples

**Fail the build on overlapping signals:**

```bash
auto-validator validate --dbc tests/fixtures/dbc/invalid_overlap.dbc --skip-codegen
# exit 1
```

**Full happy path:**

```bash
auto-validator validate \
  --dbc tests/fixtures/dbc/valid_can.dbc \
  --arxml tests/fixtures/arxml/valid_swc.arxml \
  --requirements tests/fixtures/doors/requirements.csv
# exit 0 → see output/codegen and output/reports
```
