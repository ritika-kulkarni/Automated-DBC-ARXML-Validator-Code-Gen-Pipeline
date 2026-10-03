# DBC validators

Individual CAN / J1939 / CAN-FD rule checkers composed by `DbcValidationEngine`.

| Module | Rules |
|--------|-------|
| `overlapping_signals.py` | Bit collisions, out-of-bounds |
| `endianness.py` | Mixed Intel/Motorola |
| `initial_values.py` | Missing start values |
| `cycle_times.py` | Missing / invalid / mismatched cycles |
| `j1939_rules.py` | Extended ID, PGN, SA, length |
| `can_fd_limits.py` | Classic & FD DLC limits |
| `engine.py` | Config-driven composite runner |

Rule IDs: [`../../../../docs/VALIDATION_RULES.md`](../../../../docs/VALIDATION_RULES.md)
