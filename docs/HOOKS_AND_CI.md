# Git Hooks & CI

Shift-left strategy: catch DBC/ARXML defects at commit time and again in CI.

---

## Native pre-commit hook

**File:** [`hooks/pre-commit`](../hooks/pre-commit)

### Install

```bash
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Behavior

1. Lists staged files matching `.dbc`, `.arxml`, `.csv`, `.json`
2. If none → exit 0 (allow commit)
3. Resolves `auto-validator` from `PATH` or `.venv/bin/auto-validator`
4. Runs `auto-validator hook-check --config configs/default.yaml <staged…>`
5. Non-zero exit **blocks the commit**

Codegen is intentionally skipped in hooks (fast feedback). Run codegen in CI or locally via `validate` / `codegen`.

---

## pre-commit framework

**File:** [`.pre-commit-config.yaml`](../.pre-commit-config.yaml)

```bash
pip install pre-commit
pre-commit install
pre-commit run auto-validator --all-files   # optional smoke
```

Hooks configured:

| Hook | Purpose |
|------|---------|
| `auto-validator` (local) | DBC/ARXML validation on matching files |
| `ruff` / `ruff-format` | Lint & format |
| `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-added-large-files` | Hygiene |

---

## GitHub Actions CI

**File:** [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

### Triggers

- Push / PR to `main`, `master`, `develop`

### Job: `test`

| Step | Detail |
|------|--------|
| Matrix | Python 3.9, 3.10, 3.11, 3.12 |
| Install | `pip install -e ".[dev]"` |
| Lint | `ruff check src tests` |
| Types | `mypy src/auto_validator` (continue-on-error) |
| Tests | `pytest` with coverage XML |

### Job: `validate-fixtures`

| Check | Expected |
|-------|----------|
| Valid DBC + ARXML + DOORS CSV | exit 0 |
| Overlapping DBC | exit ≠ 0 |

---

## Recommended team workflow

```text
Edit DBC/ARXML
    → pre-commit hook-check (validate only)
    → push
    → CI: full pytest + fixture validation
    → optional: CI job runs `auto-validator validate` with codegen
              and uploads output/codegen as artifact
```

### Example CI codegen step (optional addition)

```yaml
- name: Generate RTE stubs
  run: |
    auto-validator validate \
      --dbc network/Vehicle.dbc \
      --arxml autosar/Swc.arxml \
      --requirements doors/export.csv \
      --config configs/default.yaml
- uses: actions/upload-artifact@v4
  with:
    name: rte-codegen
    path: output/codegen/
```
