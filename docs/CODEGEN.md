# Code Generation Guide

Generated artifacts live under `arxml.output_dir` (default `output/codegen`).

Codegen runs only when:

1. ARXML inputs were provided and `arxml.enabled` is true  
2. `--skip-codegen` was **not** passed  
3. ARXML validation produced **zero errors**

---

## C stub headers (`CStubGenerator`)

### `Rte_Type.h`

Shared type stubs:

- `uint8` … `uint64`, `sint8` … `sint64`, `float32`, `float64`, `boolean`
- `Std_ReturnType`, `E_OK`, `E_NOT_OK`
- `typedef uint32 <AppType>;` for non-primitive interface data types

### `Rte_<SwcName>.h`

Per software component:

| Port / interface | Generated API |
|------------------|---------------|
| P-Port + S/R data element | `Std_ReturnType Rte_Write_<Port>_<Element>(<type> data);` |
| R-Port + S/R data element | `Std_ReturnType Rte_Read_<Port>_<Element>(<type> *data);` |
| PR-Port + S/R | Both Write and Read |
| R-Port + C/S operation | `Std_ReturnType Rte_Call_<Port>_<Op>(…);` |
| P-Port + C/S operation | `Std_ReturnType Rte_Entry_<Port>_<Op>(…);` |

Unresolved interfaces become `/* WARNING: … */` comments in the header.

Headers include include-guards and `extern "C"` wrappers for C++.

---

## RTE mappings (`RteMappingGenerator`)

### `rte_interface_map.json`

```json
{
  "version": "1.0",
  "generator": "auto-validator",
  "source_files": ["…"],
  "ports": [
    {
      "swc": "Swc_Powertrain",
      "port": "Pp_EngineSpeed",
      "direction": "provided",
      "interface": "If_EngineSpeed",
      "interface_ref": "/Interfaces/If_EngineSpeed",
      "interface_type": "sender-receiver",
      "data_elements": [{"name": "EngineSpeed", "type": "uint16"}],
      "operations": []
    }
  ],
  "interface_count": 3,
  "component_count": 1
}
```

Use this for DOORS diffs, Tresos review checklists, or custom dashboards.

### `Rte_InterfaceMap.c`

C table:

```c
typedef struct {
    const char *swc;
    const char *port;
    const char *direction;
    const char *interface_name;
} Rte_PortMapEntry;

const Rte_PortMapEntry Rte_PortMap[];
const size_t Rte_PortMap_Size;
```

---

## Enabling / disabling

```yaml
arxml:
  generate_c_stubs: true
  generate_rte_mappings: true
  output_dir: output/codegen
```

Or CLI-only generation:

```bash
auto-validator codegen --arxml path/to/swc.arxml --output generated/rte
```

---

## Important limitations

- Stubs are **declarations only** (no `.c` bodies) — suitable for compile-time interface checks and reviews
- Not a full EB Tresos / Vector MICROSAR replacement
- Application data types are stubbed as `uint32` unless primitive
- Names follow a conventional RTE naming pattern; OEM naming conventions may differ
