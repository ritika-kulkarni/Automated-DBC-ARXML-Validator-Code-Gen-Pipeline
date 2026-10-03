# Architecture

How the DBC/ARXML validator is put together: packages, data flow, and extension points.

For a diagram-only view, see [DIAGRAMS.md](DIAGRAMS.md).

---

## Goals

1. Fail fast on bad DBC/ARXML in git hooks and CI (before Tresos / compile).
2. Keep parse → validate → match → codegen → report as separate steps.
3. Prefer findings over hard crashes so one bad file does not kill the run.
4. Make new DBC/ARXML rules easy to add without rewriting the CLI.

---

## System overview

```mermaid
flowchart TB
    subgraph Inputs
        DBC[".dbc files"]
        ARXML[".arxml files"]
        DOORS["DOORS CSV / JSON"]
        CFG["configs/*.yaml"]
    end

    subgraph Entry
        CLI["CLI<br/>validate / codegen / hook-check"]
        HOOK["Git pre-commit"]
        CI["GitHub Actions"]
    end

    subgraph Core["auto_validator"]
        ORCH["PipelineOrchestrator"]
        PAR["parsers/"]
        VAL["validators/"]
        REQ["requirements/"]
        GEN["codegen/"]
        RPT["utils/report"]
    end

    subgraph Outputs
        CON["Console findings"]
        JSON["pipeline_report.json"]
        JUNIT["pipeline_junit.xml"]
        STUBS["Rte_*.h / maps"]
    end

    DBC --> CLI
    ARXML --> CLI
    DOORS --> CLI
    CFG --> ORCH
    HOOK --> CLI
    CI --> CLI
    CLI --> ORCH
    ORCH --> PAR
    ORCH --> VAL
    ORCH --> REQ
    ORCH --> GEN
    ORCH --> RPT
    RPT --> CON
    RPT --> JSON
    RPT --> JUNIT
    GEN --> STUBS
```

---

## Package layout

```text
src/auto_validator/
├── cli.py                 # Click commands
├── config.py              # YAML + pydantic settings
├── models/                # CanNetwork, ArxmlModel, Finding, …
├── parsers/               # DBC (cantools), ARXML (lxml), DOORS
├── validators/
│   ├── base.py            # Shared run() wrapper
│   ├── dbc/               # Overlap, endian, init, cycle, J1939, CAN-FD
│   └── arxml/             # Port / interface checks
├── requirements/          # DOORS ↔ artifact matcher
├── codegen/               # C stubs + RTE map files
├── pipeline/              # Orchestrator
└── utils/                 # Logging, retry, reports
```

| Package | Responsibility |
|---------|----------------|
| `parsers/` | Disk → typed models |
| `validators/` | Models → `Finding` list |
| `requirements/` | DOORS names vs DBC/ARXML |
| `codegen/` | ARXML → headers / JSON / C map |
| `pipeline/` | Call stages in order, build `PipelineReport` |
| `utils/` | Cross-cutting helpers |
| `models/` | Shared types (no I/O) |

---

## Runtime sequence (`validate`)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant CLI
    participant Orch as PipelineOrchestrator
    participant DBC as DbcParser + Engine
    participant ARX as ArxmlParser + Validator
    participant REQ as DoorsParser + Matcher
    participant GEN as Codegen
    participant RPT as ReportWriter

    User->>CLI: auto-validator validate …
    CLI->>Orch: run(dbc, arxml, requirements)
    opt DBC provided
        Orch->>DBC: parse + validate
        DBC-->>Orch: ValidationResult
    end
    opt ARXML provided
        Orch->>ARX: parse + validate
        ARX-->>Orch: ValidationResult
    end
    opt Requirements provided
        Orch->>REQ: parse + match
        REQ-->>Orch: ValidationResult
    end
    alt ARXML clean and codegen enabled
        Orch->>GEN: C stubs + RTE maps
        GEN-->>Orch: artifacts
    else ARXML has errors
        Note over Orch: skip codegen
    end
    Orch->>RPT: write console / JSON / JUnit
    Orch-->>CLI: PipelineReport
    CLI-->>User: exit 0 or 1
```

---

## Data model (simplified)

```mermaid
classDiagram
    class CanNetwork {
        +messages: CanMessage[]
        +nodes: str[]
        +source_files: str[]
    }
    class CanMessage {
        +name: str
        +frame_id: int
        +length: int
        +cycle_time_ms: int?
        +signals: CanSignal[]
    }
    class CanSignal {
        +name: str
        +start_bit: int
        +length: int
        +byte_order: ByteOrder
        +bit_positions()
    }
    class ArxmlModel {
        +components: ArxmlSoftwareComponent[]
        +interfaces: ArxmlInterface[]
    }
    class ArxmlPort {
        +name: str
        +direction: PortDirection
        +interface_name: str
    }
    class Finding {
        +rule_id: str
        +severity: FindingSeverity
        +message: str
        +location: str?
    }
    class ValidationResult {
        +stage: str
        +passed: bool
        +findings: Finding[]
    }
    class PipelineReport {
        +results: ValidationResult[]
        +overall_passed: bool
    }

    CanNetwork "1" *-- "*" CanMessage
    CanMessage "1" *-- "*" CanSignal
    ArxmlModel "1" *-- "*" ArxmlPort
    ValidationResult "1" *-- "*" Finding
    PipelineReport "1" *-- "*" ValidationResult
```

---

## Validation engines

```mermaid
flowchart LR
    subgraph DBC["DbcValidationEngine"]
        O[overlapping_signals]
        E[endianness]
        I[initial_values]
        C[cycle_times]
        J[j1939_rules]
        F[can_fd_limits]
    end

    subgraph ARXML["ArxmlPortValidator"]
        P[port consistency]
        IF[interface completeness]
        T[data types]
    end

    NET[CanNetwork] --> DBC
    AX[ArxmlModel] --> ARXML
    DBC --> FIND[Findings]
    ARXML --> FIND
```

Each DBC checker is a plain function `check_*(network) -> list[Finding]`.  
`DbcValidationEngine` turns them on/off from `configs/default.yaml`.

---

## Failure & retry behavior

| Layer | Behavior |
|-------|----------|
| Parsers | `@retryable` on transient `OSError` / timeouts |
| Validators | Unexpected exceptions → `*.INTERNAL` finding |
| Orchestrator | Stage parse failures → `PIPELINE.FATAL`; continue other stages when possible |
| Codegen | Skipped if ARXML stage has errors |
| CLI exit | Based on `pipeline.fail_on_severity` vs all findings |

```mermaid
flowchart TD
    A[Stage starts] --> B{Success?}
    B -->|yes| C[Add ValidationResult]
    B -->|no| D[Add PIPELINE.FATAL / INTERNAL finding]
    C --> E[Next stage]
    D --> E
    E --> F{More stages?}
    F -->|yes| A
    F -->|no| G[Apply fail_on_severity]
    G --> H[Write reports]
    H --> I[Exit 0 / 1]
```

---

## How to add a DBC rule

1. Add `validators/dbc/my_rule.py` with `check_*(network) -> list[Finding]`.
2. Call it from `DbcValidationEngine.validate` behind a config flag.
3. Document the rule id in [VALIDATION_RULES.md](VALIDATION_RULES.md).
4. Add a unit test under `tests/unit/`.
5. Optionally add a fixture under `tests/fixtures/dbc/`.

Same idea for ARXML: extend `ArxmlPortValidator` or add a sibling validator.

---

## Related docs

- [DIAGRAMS.md](DIAGRAMS.md) — all Mermaid diagrams in one place  
- [DATA_FLOW.md](DATA_FLOW.md) — inputs → models → outputs  
- [GETTING_STARTED.md](GETTING_STARTED.md) — install and first run  
- [FEATURES.md](FEATURES.md) — feature catalog  
- [CONFIGURATION.md](CONFIGURATION.md) — config keys  
