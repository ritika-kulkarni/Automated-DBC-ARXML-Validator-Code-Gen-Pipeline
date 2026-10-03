# Automated DBC/ARXML Validator & Code-Gen Pipeline

Python + Git-hooks CI tool that catches CAN/J1939/CAN-FD DBC defects and AUTOSAR ARXML port mismatches **before** EB Tresos generation or compile time — and auto-generates C RTE stub headers matched against DOORS requirements.

---

## Documentation

| Document | Description |
|----------|-------------|
| **[docs/README.md](docs/README.md)** | Documentation index |
| **[docs/FEATURES.md](docs/FEATURES.md)** | Every implemented feature, explained |
| **[docs/VALIDATION_RULES.md](docs/VALIDATION_RULES.md)** | Full rule-ID catalog with remediations |
| **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** | YAML / env config reference |
| **[docs/CLI.md](docs/CLI.md)** | `validate`, `codegen`, `hook-check` |
| **[docs/CODEGEN.md](docs/CODEGEN.md)** | C stubs & RTE mapping outputs |
| **[docs/HOOKS_AND_CI.md](docs/HOOKS_AND_CI.md)** | Pre-commit + GitHub Actions |
| **[docs/TESTING.md](docs/TESTING.md)** | Unit / integration / edge strategy |
| **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** | Layering, SOLID, extension points |

### Package & folder READMEs

| Path | Focus |
|------|-------|
| [src/auto_validator/README.md](src/auto_validator/README.md) | Package map |
| [src/auto_validator/parsers/README.md](src/auto_validator/parsers/README.md) | DBC / ARXML / DOORS parsers |
| [src/auto_validator/validators/README.md](src/auto_validator/validators/README.md) | Validation engines |
| [src/auto_validator/codegen/README.md](src/auto_validator/codegen/README.md) | Code generators |
| [src/auto_validator/requirements/README.md](src/auto_validator/requirements/README.md) | DOORS matcher |
| [src/auto_validator/pipeline/README.md](src/auto_validator/pipeline/README.md) | Orchestrator |
| [src/auto_validator/models/README.md](src/auto_validator/models/README.md) | Domain models |
| [src/auto_validator/utils/README.md](src/auto_validator/utils/README.md) | Logging, retry, reports |
| [configs/README.md](configs/README.md) | Config files |
| [hooks/README.md](hooks/README.md) | Git hooks |
| [tests/README.md](tests/README.md) | Test suite |

---

## Why this exists

Manual DBC signal mapping and ARXML port mismatches are typically found late (Tresos / compiler). This pipeline shifts those checks left into pre-commit and CI.

| Stage | What it catches / produces |
|-------|----------------------------|
| **DBC validation** | Overlapping bit-starts, endianness conflicts, missing initial values, cycle-time mismatches, J1939 rules, CAN-FD DLC limits |
| **ARXML validation** | Unresolved port→interface refs, empty S/R or C/S interfaces, data-type gaps |
| **Requirements match** | DOORS CSV/JSON signals & ports vs DBC/ARXML (strict or fuzzy) |
| **Code-gen** | `Rte_<Swc>.h`, `Rte_Type.h`, `rte_interface_map.json`, `Rte_InterfaceMap.c` |
| **Reporting** | Rich console, JSON, JUnit XML |
| **Reliability** | Structured logging, I/O retries, findings instead of hard crashes |

---

## Architecture (summary)

```text
src/auto_validator/
├── cli.py                 # Click CLI
├── config.py              # YAML + pydantic
├── models/                # Domain models
├── parsers/               # DBC, ARXML, DOORS
├── validators/dbc|arxml/  # Rule engines
├── requirements/          # Traceability matcher
├── codegen/               # C stubs + RTE maps
├── pipeline/              # Orchestrator (Facade)
└── utils/                 # Logging, retry, reports
```

Design patterns: Strategy (pluggable validators), Template Method (`BaseValidator.run`), Facade (`PipelineOrchestrator`). Details in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# End-to-end on fixtures
auto-validator validate \
  --dbc tests/fixtures/dbc/valid_can.dbc \
  --arxml tests/fixtures/arxml/valid_swc.arxml \
  --requirements tests/fixtures/doors/requirements.csv

# Codegen only
auto-validator codegen \
  --arxml tests/fixtures/arxml/valid_swc.arxml \
  --output output/codegen

# Tests
pytest
```

Exit code `0` = passed (per `pipeline.fail_on_severity`), `1` = failed.

More CLI examples: [docs/CLI.md](docs/CLI.md).

---

## Configuration

Default: [`configs/default.yaml`](configs/default.yaml). Override with `--config` or env prefix `AUTO_VALIDATOR_`.

Key knobs:

- `dbc.rules.*` — enable/disable individual DBC checks  
- `dbc.require_initial_values` — missing `GenSigStartValue` → error  
- `arxml.generate_c_stubs` / `generate_rte_mappings`  
- `requirements.match_mode`: `strict` \| `fuzzy`  
- `pipeline.fail_on_severity`: `error` \| `warning` \| `info`  

Full reference: [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

---

## Git hooks

```bash
# Native
cp hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

# Or pre-commit framework
pip install pre-commit && pre-commit install
```

See [hooks/README.md](hooks/README.md) and [docs/HOOKS_AND_CI.md](docs/HOOKS_AND_CI.md).

---

## CI

GitHub Actions: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

- Python 3.9–3.12 matrix: pytest, ruff, mypy  
- Fixture smoke: known-good must pass; overlapping DBC must fail  

---

## Reports

Written to `output/reports/` (configurable):

- `pipeline_report.json` — structured findings  
- `pipeline_junit.xml` — CI reporters  
- Rich console table on stderr  

Rule IDs explained in [docs/VALIDATION_RULES.md](docs/VALIDATION_RULES.md).

---

## Typical ECU-repo workflow

1. Engineer edits `Network.dbc` / `Swc.arxml`  
2. Pre-commit runs DBC + ARXML rules → blocks overlapping bits / bad ports  
3. CI re-runs validation (+ optional codegen)  
4. DOORS export matched so untraced signals/ports surface as warnings/errors  
5. Generated headers used for interface review / compile checks  

---

## License

MIT — see [LICENSE](LICENSE).
