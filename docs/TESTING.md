# Testing Strategy

The suite covers **unit**, **integration**, and **edge** cases with pytest markers and a coverage gate (≥ 80%).

---

## How to run

```bash
source .venv/bin/activate
pip install -e ".[dev]"

pytest                         # all tests + coverage
pytest -m unit                 # unit only
pytest -m integration          # orchestrator / CLI
pytest -m edge                 # edge cases
pytest tests/unit/test_dbc_validators.py -q
```

Config: `[tool.pytest.ini_options]` in `pyproject.toml`.

---

## Layout

```text
tests/
├── conftest.py              # shared fixtures (paths, parsers, AppConfig)
├── unit/                    # isolated rules, models, parsers, matcher, retry
├── integration/             # PipelineOrchestrator + Click CLI
└── fixtures/
    ├── dbc/                 # valid, overlap, J1939, invalid CAN-FD
    ├── arxml/               # valid SWC, invalid ports
    └── doors/               # CSV, JSON, expected_cycles.json
```

---

## Markers

| Marker | Intent |
|--------|--------|
| `unit` | Fast, no full pipeline; mock-free pure logic where possible |
| `integration` | Real parsers + orchestrator + filesystem + CLI |
| `edge` | Empty inputs, disabled stages, forced mismatches |

---

## Fixture catalog

| File | Purpose |
|------|---------|
| `dbc/valid_can.dbc` | Clean classic CAN with cycle times + init values |
| `dbc/invalid_overlap.dbc` | Intentional bit overlap (must fail) |
| `dbc/j1939_sample.dbc` | Extended / J1939-style sample |
| `dbc/can_fd_invalid.dbc` | Non-ISO FD length (must fail FD rules) |
| `arxml/valid_swc.arxml` | SWC + S/R + C/S interfaces |
| `arxml/invalid_ports.arxml` | Unresolved iface + empty S/R |
| `doors/requirements.csv` | Aligned with valid DBC/ARXML |
| `doors/requirements.json` | Includes ghost signal for matcher errors |
| `doors/expected_cycles.json` | EngineData=10, VehicleSpeed=20 |

---

## What each level asserts

### Unit

- Bit occupancy for Intel / Motorola
- Overlap, init, cycle, endian, CAN-FD, J1939 checkers
- ARXML parse + port validator + codegen string contents
- DOORS CSV/JSON normalize + matcher missing signal/port
- Config load + retry success/exhaustion

### Integration

- Full pipeline pass on valid fixtures (reports + codegen written)
- Fail on overlap DBC and bad ARXML (codegen gated)
- Click `validate` exit 0; `hook-check` skips unrelated files
- Expected cycle mismatch; CAN-FD invalid fixture

### Edge

- Empty `CanNetwork` → clean
- Matcher disabled → no findings
- Cycle map force-mismatch
- CAN-FD invalid DLC

---

## Coverage policy

- Branch coverage enabled
- `fail_under = 80` in `pyproject.toml`
- CI uploads `coverage.xml` on Python 3.12

---

## Adding a test for a new rule

1. Prefer a **synthetic** `CanNetwork` / `ArxmlModel` in `tests/unit/`
2. Assert specific `rule_id` in findings
3. Optionally add a fixture under `tests/fixtures/` for integration
4. Mark with `@pytest.mark.unit` (and `edge` if appropriate)
