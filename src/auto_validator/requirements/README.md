# Requirements matching

Compare DOORS exports to DBC signals and ARXML ports.

| Symbol | Role |
|--------|------|
| `RequirementsMatchTarget` | catalog + optional network + optional arxml |
| `RequirementsMatcher` | emits `REQ.*` findings |

| Mode | Behavior |
|------|----------|
| `strict` | Exact names; warn on untraced artifacts when catalog has coverage |
| `fuzzy` | Same checks + `difflib` suggestions |

Config: `requirements.*` in [configs/default.yaml](../../../configs/default.yaml).  
Rules: [VALIDATION_RULES.md](../../../docs/VALIDATION_RULES.md).
