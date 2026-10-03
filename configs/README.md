# Configs

Runtime configuration for the pipeline.

| File | Purpose |
|------|---------|
| `default.yaml` | Default rules, logging, codegen paths, report formats |

Load with:

```bash
auto-validator validate --config configs/default.yaml ...
```

Or in Python:

```python
from auto_validator.config import load_config
cfg = load_config("configs/default.yaml")
```

Full key reference: [`../docs/CONFIGURATION.md`](../docs/CONFIGURATION.md)

### Tips

- Copy `default.yaml` to `configs/ci.yaml` or `configs/local.yaml` for environment-specific toggles
- Prefer disabling heavy rules in pre-commit if needed; keep full rules in CI
- Set `report.formats: [junit]` in CI-only configs for quieter logs
