# Getting started

Install the tool, run it on the sample fixtures, then wire a git hook.

---

## 1. Install

```bash
git clone https://github.com/ritika-kulkarni/Automated-DBC-ARXML-Validator-Code-Gen-Pipeline.git
cd Automated-DBC-ARXML-Validator-Code-Gen-Pipeline

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Requires **Python 3.9+**.

Check the CLI:

```bash
auto-validator --version
auto-validator --help
```

---

## 2. First validation run

Use the fixtures that ship with the repo:

```bash
auto-validator validate \
  --dbc tests/fixtures/dbc/valid_can.dbc \
  --arxml tests/fixtures/arxml/valid_swc.arxml \
  --requirements tests/fixtures/doors/requirements.csv
```

Expected:

- Exit code `0`
- Console summary: **PASSED**
- Generated files under `output/codegen/`
- Reports under `output/reports/`

### See a failure on purpose

```bash
auto-validator validate \
  --dbc tests/fixtures/dbc/invalid_overlap.dbc \
  --skip-codegen
```

You should get `DBC.OVERLAP.BIT_COLLISION` findings and exit code `1`.

---

## 3. Generate stubs only

```bash
auto-validator codegen \
  --arxml tests/fixtures/arxml/valid_swc.arxml \
  --output output/codegen
```

Opens as C headers you can `#include` for interface review (declarations only — not a full RTE).

---

## 4. Enable the git hook

```bash
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Or:

```bash
pip install pre-commit
pre-commit install
```

Staging a bad `.dbc` and committing should now be blocked.

---

## 5. Point it at your own files

```bash
auto-validator validate \
  --dbc path/to/Network.dbc \
  --arxml path/to/Swc.arxml \
  --requirements path/to/doors_export.csv \
  --config configs/default.yaml
```

Copy `configs/default.yaml` if you need different rule toggles for local vs CI.

---

## 6. Run tests

```bash
pytest
pytest -m unit
pytest -m integration
```

---

## Next reading

| Doc | Why |
|-----|-----|
| [ARCHITECTURE.md](ARCHITECTURE.md) | How packages fit together |
| [DIAGRAMS.md](DIAGRAMS.md) | Mermaid diagrams |
| [CLI.md](CLI.md) | All CLI flags |
| [VALIDATION_RULES.md](VALIDATION_RULES.md) | Rule ids and fixes |
| [CONFIGURATION.md](CONFIGURATION.md) | YAML knobs |
