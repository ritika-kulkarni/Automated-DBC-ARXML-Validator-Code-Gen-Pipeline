# Tests

Pytest suite for the DBC/ARXML validator pipeline.

## Layout

| Path | Contents |
|------|----------|
| `conftest.py` | Shared fixtures (fixture paths, parsers, `AppConfig`) |
| `unit/` | Models, DBC/ARXML rules, parsers, matcher, config/retry, J1939 |
| `integration/` | Full pipeline + Click CLI |
| `fixtures/dbc/` | Valid / overlap / J1939 / invalid CAN-FD DBC samples |
| `fixtures/arxml/` | Valid SWC and invalid port ARXML |
| `fixtures/doors/` | CSV, JSON, expected cycle-time map |

## Commands

```bash
pytest
pytest -m unit
pytest -m integration
pytest -m edge
```

## Markers

Defined in `pyproject.toml`: `unit`, `integration`, `edge`.

## Coverage

Branch coverage with `fail_under = 80`. See [`../docs/TESTING.md`](../docs/TESTING.md) for strategy and how to add tests for new rules.
