# Configs

| File | Purpose |
|------|---------|
| `default.yaml` | Default rules, logging, codegen paths, report formats |

```bash
auto-validator validate --config configs/default.yaml ...
```

```python
from auto_validator.config import load_config
cfg = load_config("configs/default.yaml")
```

Tip: copy to `configs/ci.yaml` or `configs/local.yaml` for environment-specific toggles.  
Do not put a README under `.github/` that would replace the root project README.

Full key list: [CONFIGURATION.md](../docs/CONFIGURATION.md).
