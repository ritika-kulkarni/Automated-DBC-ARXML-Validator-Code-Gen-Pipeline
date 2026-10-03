# Hooks

Git hooks that run the validator before a commit is accepted.

| File | Purpose |
|------|---------|
| `pre-commit` | Native bash hook → `auto-validator hook-check` |

## Install (native)

```bash
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Install (framework)

From repo root (uses [`.pre-commit-config.yaml`](../.pre-commit-config.yaml)):

```bash
pip install pre-commit
pre-commit install
```

## What gets checked

Staged files ending in `.dbc`, `.arxml`, and requirements-like `.csv`/`.json`.

Codegen is **not** run in the hook path (kept fast). Use CI or `auto-validator validate` for generation.

Full guide: [`../docs/HOOKS_AND_CI.md`](../docs/HOOKS_AND_CI.md)
