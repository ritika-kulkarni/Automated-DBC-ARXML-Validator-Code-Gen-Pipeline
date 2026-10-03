# Hooks

| File | Purpose |
|------|---------|
| `pre-commit` | Native bash hook → `auto-validator hook-check` |

## Install

```bash
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Or use the repo’s [`.pre-commit-config.yaml`](../.pre-commit-config.yaml):

```bash
pip install pre-commit && pre-commit install
```

Validates staged `.dbc` / `.arxml` (and some requirements files). Does **not** run codegen (kept fast).

Diagram: [DIAGRAMS.md](../docs/DIAGRAMS.md) §6.  
Guide: [HOOKS_AND_CI.md](../docs/HOOKS_AND_CI.md).
