# Validators

Rule engines that produce `Finding` lists. All validators share `BaseValidator[T]` (template method: time, catch, aggregate).

## Structure

```text
validators/
├── base.py                 # BaseValidator[T]
├── dbc/
│   ├── engine.py           # DbcValidationEngine (composite)
│   ├── overlapping_signals.py
│   ├── endianness.py
│   ├── initial_values.py
│   ├── cycle_times.py
│   ├── j1939_rules.py
│   └── can_fd_limits.py
└── arxml/
    └── port_consistency.py # ArxmlPortValidator
```

## DBC engine

`DbcValidationEngine` runs enabled checkers from `DbcConfig.rules`:

1. Overlapping signals  
2. Endianness conflicts  
3. Missing initial values  
4. Cycle times (+ optional expected map)  
5. J1939 compliance  
6. CAN-FD / classic limits  

## ARXML validator

`ArxmlPortValidator` checks:

1. Port consistency (duplicate / missing / unresolved interface)  
2. Interface completeness (empty S/R or C/S)  
3. Data-type mapping (missing / custom)

## Adding a rule

1. Implement `check_*(target) -> list[Finding]` in a new module  
2. Call it from the engine/validator when the config flag is on  
3. Document the rule ID in [`../../../docs/VALIDATION_RULES.md`](../../../docs/VALIDATION_RULES.md)  
4. Add unit tests under `tests/unit/`

Full rule catalog: [`../../../docs/VALIDATION_RULES.md`](../../../docs/VALIDATION_RULES.md)
