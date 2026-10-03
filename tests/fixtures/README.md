# Test fixtures

Sample automotive artifacts used by unit and integration tests.

## DBC (`dbc/`)

| File | Intent |
|------|--------|
| `valid_can.dbc` | Clean classic CAN: init values + cycle times |
| `invalid_overlap.dbc` | Overlapping signals (must fail `DBC.OVERLAP.*`) |
| `j1939_sample.dbc` | Extended / J1939-style message sample |
| `can_fd_invalid.dbc` | Non-ISO CAN-FD length (must fail FD rules) |

## ARXML (`arxml/`)

| File | Intent |
|------|--------|
| `valid_swc.arxml` | SWC with S/R + C/S ports (codegen source) |
| `invalid_ports.arxml` | Unresolved interface + empty S/R |

## DOORS (`doors/`)

| File | Intent |
|------|--------|
| `requirements.csv` | Aligned with valid DBC/ARXML |
| `requirements.json` | Includes ghost signal for matcher errors |
| `expected_cycles.json` | Message → cycle_ms map for mismatch tests |

Testing guide: [`../../docs/TESTING.md`](../../docs/TESTING.md).
