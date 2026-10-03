# Pipeline

Wires parsers → validators → matcher → codegen → reports.

## `PipelineOrchestrator`

Public API:

```python
from auto_validator.config import load_config
from auto_validator.pipeline import PipelineOrchestrator

orch = PipelineOrchestrator(load_config("configs/default.yaml"))
report = orch.run(
    dbc_files=["network.dbc"],
    arxml_files=["swc.arxml"],
    requirements_files=["doors.csv"],
    expected_cycle_times={"EngineData": 10},
    skip_codegen=False,
)
assert report.overall_passed
```

## Stage order

1. DBC parse + `DbcValidationEngine`  
2. ARXML parse + `ArxmlPortValidator`  
3. DOORS parse + `RequirementsMatcher`  
4. Codegen (gated on clean ARXML)  
5. Severity threshold → `overall_passed`  
6. `ReportWriter.write(report)`

See [`../../../docs/FEATURES.md`](../../../docs/FEATURES.md) §1.
