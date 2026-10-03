# Automated DBC/ARXML Validator & Code-Gen Pipeline

[![CI](https://github.com/ritika-kulkarni/Automated-DBC-ARXML-Validator-Code-Gen-Pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/ritika-kulkarni/Automated-DBC-ARXML-Validator-Code-Gen-Pipeline/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Python tool that checks DBC and AUTOSAR ARXML files in git hooks / CI, matches them against DOORS exports, and can generate simple RTE-style C stubs.

Useful when signal packing bugs and port/interface mismatches only show up in Tresos or at compile time today.

---

## What it checks

| Input | Checks / outputs |
|-------|------------------|
| **DBC** | Overlapping bits, mixed endianness, missing init values, cycle times, J1939, CAN-FD DLC |
| **ARXML** | Bad/missing port→interface refs, empty interfaces, missing types |
| **DOORS CSV/JSON** | Signal and port names that don't line up with DBC/ARXML |
| **Codegen** | `Rte_<Swc>.h`, `Rte_Type.h`, `rte_interface_map.json`, `Rte_InterfaceMap.c` |

See [docs/FEATURES.md](docs/FEATURES.md) and [docs/VALIDATION_RULES.md](docs/VALIDATION_RULES.md) for the full list.

---

## Install

```bash
git clone https://github.com/ritika-kulkarni/Automated-DBC-ARXML-Validator-Code-Gen-Pipeline.git
cd Automated-DBC-ARXML-Validator-Code-Gen-Pipeline

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Needs Python 3.9+.

---

## Usage

```bash
# Full run (fixtures included in the repo)
auto-validator validate \
  --dbc tests/fixtures/dbc/valid_can.dbc \
  --arxml tests/fixtures/arxml/valid_swc.arxml \
  --requirements tests/fixtures/doors/requirements.csv

# Stubs only
auto-validator codegen \
  --arxml tests/fixtures/arxml/valid_swc.arxml \
  --output output/codegen

# Expect failure (overlapping signals)
auto-validator validate \
  --dbc tests/fixtures/dbc/invalid_overlap.dbc \
  --skip-codegen
```

Exit `0` = ok, `1` = failed (threshold set by `pipeline.fail_on_severity`).

| Command | When to use |
|---------|-------------|
| `validate` | Normal pipeline |
| `codegen` | ARXML → headers/maps only |
| `hook-check` | Called from the git hook on staged files |

More detail: [docs/CLI.md](docs/CLI.md).

---

## Repo layout

```text
configs/default.yaml     rule toggles + report paths
docs/                    longer docs
hooks/pre-commit         native git hook
src/auto_validator/
  parsers/               DBC, ARXML, DOORS
  validators/            rule checks
  requirements/          DOORS matching
  codegen/               C stubs / RTE maps
  pipeline/              runs the stages
tests/                   unit + integration + fixtures
```

---

## Config

Defaults live in [`configs/default.yaml`](configs/default.yaml). Pass another file with `--config`, or use `AUTO_VALIDATOR_` env vars.

```yaml
pipeline:
  fail_on_severity: error

dbc:
  rules:
    overlapping_signals: true
    missing_initial_values: true
    j1939_compliance: true
    can_fd_limits: true

arxml:
  generate_c_stubs: true
  output_dir: output/codegen

requirements:
  match_mode: strict   # or fuzzy

report:
  formats: [console, json, junit]
```

Full key list: [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

---

## Git hook

```bash
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# or
pip install pre-commit && pre-commit install
```

Staged `.dbc` / `.arxml` files get validated before the commit goes through. Notes: [docs/HOOKS_AND_CI.md](docs/HOOKS_AND_CI.md).

---

## CI & tests

GitHub Actions (`.github/workflows/ci.yml`) runs pytest + ruff on Python 3.9–3.12 and smokes the fixtures.

```bash
pytest
pytest -m unit
pytest -m integration
```

Reports land under `output/reports/` (`pipeline_report.json`, `pipeline_junit.xml`).

---

## Docs

| Doc | What's in it |
|-----|----------------|
| [docs/README.md](docs/README.md) | Index |
| [docs/FEATURES.md](docs/FEATURES.md) | Feature list |
| [docs/VALIDATION_RULES.md](docs/VALIDATION_RULES.md) | Rule ids |
| [docs/CLI.md](docs/CLI.md) | CLI options |
| [docs/CODEGEN.md](docs/CODEGEN.md) | Generated files |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How it's put together |
| [docs/TESTING.md](docs/TESTING.md) | How to test |

---

## License

[MIT](LICENSE)
