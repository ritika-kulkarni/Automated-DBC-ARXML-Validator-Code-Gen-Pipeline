# Automated DBC/ARXML Validator & Code-Gen Pipeline

[![CI](https://github.com/ritika-kulkarni/Automated-DBC-ARXML-Validator-Code-Gen-Pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/ritika-kulkarni/Automated-DBC-ARXML-Validator-Code-Gen-Pipeline/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![pytest](https://img.shields.io/badge/tests-pytest-green.svg)](docs/TESTING.md)

**Catch CAN / J1939 / CAN-FD DBC defects and AUTOSAR ARXML port mismatches before EB Tresos or compile time** — then auto-generate C RTE stubs and match them against DOORS requirements.

Built for automotive ECU teams who need shift-left validation in Git hooks and CI.

---

## The problem

Manual DBC signal mapping and ARXML port mismatches are usually found **late**:

- During EB Tresos generation  
- At the compiler / linker stage  
- Or worse, during HIL / vehicle integration  

By then, the fix is expensive and the feedback loop is slow.

## The solution

A Python pipeline that runs on every commit and in CI:

```text
DBC / ARXML / DOORS
        │
        ▼
┌───────────────────┐
│  Parse & validate │  ← overlapping bits, endianness, init values,
│  (cantools/lxml)  │    cycle times, J1939, CAN-FD, port refs
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ DOORS traceability│  ← signal & port coverage (strict / fuzzy)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  C / RTE codegen  │  ← Rte_<Swc>.h, Rte_Type.h, interface maps
└─────────┬─────────┘
          │
          ▼
   Console · JSON · JUnit reports
```

---

## Features

| Area | What you get |
|------|----------------|
| **DBC rules** | Overlapping signal bits, endianness conflicts, missing initial values, cycle-time mismatches, J1939 compliance, CAN-FD DLC limits |
| **ARXML rules** | Unresolved port→interface refs, empty S/R or C/S interfaces, data-type gaps |
| **DOORS match** | CSV/JSON requirement exports ↔ DBC signals & ARXML ports |
| **Code-gen** | `Rte_<Swc>.h`, `Rte_Type.h`, `rte_interface_map.json`, `Rte_InterfaceMap.c` |
| **Git hooks** | Block bad DBC/ARXML at commit time |
| **CI ready** | GitHub Actions + JUnit/JSON reports |
| **Reliable** | Structured logging, I/O retries, typed models (pydantic) |

Full feature walkthrough → **[docs/FEATURES.md](docs/FEATURES.md)**  
Rule ID catalog → **[docs/VALIDATION_RULES.md](docs/VALIDATION_RULES.md)**

---

## Quick start

### Requirements

- Python **3.9+**
- `pip` / venv

### Install

```bash
git clone https://github.com/ritika-kulkarni/Automated-DBC-ARXML-Validator-Code-Gen-Pipeline.git
cd Automated-DBC-ARXML-Validator-Code-Gen-Pipeline

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Validate (end-to-end)

```bash
auto-validator validate \
  --dbc tests/fixtures/dbc/valid_can.dbc \
  --arxml tests/fixtures/arxml/valid_swc.arxml \
  --requirements tests/fixtures/doors/requirements.csv
```

| Exit code | Meaning |
|-----------|---------|
| `0` | Passed (per `pipeline.fail_on_severity`) |
| `1` | Failed — see console / `output/reports/` |

### Generate RTE stubs only

```bash
auto-validator codegen \
  --arxml tests/fixtures/arxml/valid_swc.arxml \
  --output output/codegen
```

### Run tests

```bash
pytest
```

---

## Example: catch overlapping signals before commit

```bash
auto-validator validate \
  --dbc tests/fixtures/dbc/invalid_overlap.dbc \
  --skip-codegen
```

Output (abbreviated):

```text
Pipeline Result: FAILED
Errors: 8  Warnings: 0

[error] DBC.OVERLAP.BIT_COLLISION  BadMsg/SignalB
  Overlapping bit 8 in message BadMsg: SignalA vs SignalB
```

---

## CLI at a glance

| Command | Purpose |
|---------|---------|
| `auto-validator validate` | Full pipeline: DBC + ARXML + DOORS + optional codegen |
| `auto-validator codegen` | Generate C stubs / RTE maps from ARXML |
| `auto-validator hook-check` | Used by git pre-commit / CI on changed files |

```bash
auto-validator validate --help
```

Full CLI reference → **[docs/CLI.md](docs/CLI.md)**

---

## Project structure

```text
├── configs/default.yaml          # Pipeline & rule toggles
├── docs/                         # Full documentation
├── hooks/pre-commit              # Native git hook
├── src/auto_validator/
│   ├── cli.py                    # Click entrypoint
│   ├── parsers/                  # DBC · ARXML · DOORS
│   ├── validators/               # Rule engines
│   ├── requirements/             # Traceability matcher
│   ├── codegen/                  # C stubs & RTE maps
│   ├── pipeline/                 # Orchestrator
│   └── utils/                    # Logging, retry, reports
└── tests/                        # Unit + integration + fixtures
```

Architecture details → **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**

---

## Configuration

Default config: [`configs/default.yaml`](configs/default.yaml)

```yaml
pipeline:
  fail_on_severity: error          # error | warning | info

dbc:
  rules:
    overlapping_signals: true
    endianness_conflicts: true
    missing_initial_values: true
    cycle_time_mismatch: true
    j1939_compliance: true
    can_fd_limits: true

arxml:
  generate_c_stubs: true
  generate_rte_mappings: true
  output_dir: output/codegen

requirements:
  match_mode: strict               # strict | fuzzy

report:
  formats: [console, json, junit]
  output_dir: output/reports
```

Override with `--config path/to.yaml` or env prefix `AUTO_VALIDATOR_`.  
Full reference → **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)**

---

## Git hooks (shift-left)

Block invalid DBC/ARXML **before** they land on the branch:

```bash
# Option A — native hook
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Option B — pre-commit framework
pip install pre-commit
pre-commit install
```

Guide → **[docs/HOOKS_AND_CI.md](docs/HOOKS_AND_CI.md)**

---

## CI

GitHub Actions runs on push/PR to `main` / `master` / `develop`:

- Python **3.9 – 3.12** test matrix  
- `ruff` lint + `pytest` (coverage gate ≥ 80%)  
- Fixture smoke: valid inputs must pass; overlapping DBC must fail  

Workflow: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

---

## Reports

After each run, artifacts land under `output/reports/` (configurable):

| File | Use |
|------|-----|
| `pipeline_report.json` | Structured findings for tooling |
| `pipeline_junit.xml` | CI test reporters |
| Console (Rich) | Human-readable table of rule hits |

---

## Typical workflow in an ECU repo

1. Engineer edits `Network.dbc` / `Swc.arxml`  
2. **Pre-commit** validates → blocks overlapping bits / bad ports  
3. **CI** re-validates and optionally regenerates RTE stubs  
4. **DOORS** export is matched so untraced signals/ports surface early  
5. Generated headers support interface review and compile-time checks  

---

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/FEATURES.md](docs/FEATURES.md) | Every feature explained |
| [docs/VALIDATION_RULES.md](docs/VALIDATION_RULES.md) | Rule IDs & remediations |
| [docs/CLI.md](docs/CLI.md) | Command reference |
| [docs/CODEGEN.md](docs/CODEGEN.md) | Generated C / RTE artifacts |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Config keys |
| [docs/TESTING.md](docs/TESTING.md) | How to run & extend tests |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Design & extension points |

---

## Tech stack

- **Python 3.9+** · Click · pydantic · PyYAML · Rich · tenacity  
- **cantools** (DBC) · **lxml** (ARXML)  
- **pytest** · ruff · mypy · pre-commit · GitHub Actions  

---

## Contributing

1. Fork / branch from `main`  
2. `pip install -e ".[dev]"`  
3. Add or update tests under `tests/`  
4. `pytest` and `ruff check src tests`  
5. Open a PR  

When adding a new validation rule, document the rule ID in [docs/VALIDATION_RULES.md](docs/VALIDATION_RULES.md).

---

## License

This project is licensed under the [MIT License](LICENSE).
