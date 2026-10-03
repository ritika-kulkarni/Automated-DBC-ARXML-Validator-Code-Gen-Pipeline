# Codegen

Generate reviewable AUTOSAR-style RTE artifacts from a validated `ArxmlModel`.

## Generators

| Class | File | Outputs |
|-------|------|---------|
| `CStubGenerator` | `c_stubs.py` | `Rte_Type.h`, `Rte_<Swc>.h` |
| `RteMappingGenerator` | `rte_mappings.py` | `rte_interface_map.json`, `Rte_InterfaceMap.c` |

## When it runs

Invoked by `PipelineOrchestrator` after successful ARXML validation (no error findings), unless `--skip-codegen` or config disables generation flags.

## Design notes

- Declarations only (no runnable RTE implementation)
- Stable naming: `Rte_Write_<Port>_<Element>`, `Rte_Read_*`, `Rte_Call_*`, `Rte_Entry_*`
- Custom application types stubbed as `uint32` in `Rte_Type.h`

Details: [`../../../docs/CODEGEN.md`](../../../docs/CODEGEN.md)
