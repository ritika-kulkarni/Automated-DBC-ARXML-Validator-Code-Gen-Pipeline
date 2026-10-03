# Requirements matching

Traceability between DOORS exports and DBC/ARXML artifacts.

## Components

| Symbol | Role |
|--------|------|
| `RequirementsMatchTarget` | Bundle: catalog + optional `CanNetwork` + optional `ArxmlModel` |
| `RequirementsMatcher` | `BaseValidator` that emits `REQ.*` findings |

## Modes

| Mode | Behavior |
|------|----------|
| `strict` | Exact names; also warns on untraced DBC signals / ARXML ports when the catalog defines coverage |
| `fuzzy` | Same checks; suggestions via `difflib` using `fuzzy_threshold` |

## Typical findings

- `REQ.SIGNAL.MISSING_IN_DBC` / `REQ.SIGNAL.UNTRACED`
- `REQ.PORT.MISSING_IN_ARXML` / `REQ.PORT.UNTRACED`

Config: `requirements.*` in [`../../../configs/default.yaml`](../../../configs/default.yaml)  
Rules: [`../../../docs/VALIDATION_RULES.md`](../../../docs/VALIDATION_RULES.md)
