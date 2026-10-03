# Tests

| Path | Contents |
|------|----------|
| `conftest.py` | Shared fixtures |
| `unit/` | Rules, models, parsers, matcher, retry |
| `integration/` | Orchestrator + Click CLI |
| `fixtures/` | Sample DBC / ARXML / DOORS — see [fixtures/README.md](fixtures/README.md) |

```bash
pytest
pytest -m unit
pytest -m integration
pytest -m edge
```

Markers and coverage policy: [TESTING.md](../docs/TESTING.md).
