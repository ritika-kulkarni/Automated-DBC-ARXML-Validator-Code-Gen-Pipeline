# Architecture diagrams

Mermaid diagrams for the DBC/ARXML validator. GitHub renders these on the docs pages.

Detailed narrative: [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 1. High-level context

Who talks to the tool and what comes out.

```mermaid
flowchart TB
    ENG[ECU / network engineer]
    REV[CI / reviewer]

    TOOL[auto-validator]

    DOORS[(DOORS CSV/JSON)]
    GIT[Git pre-commit]
    GHA[GitHub Actions]

    ENG -->|validate / codegen| TOOL
    ENG --> GIT
    GIT -->|hook-check| TOOL
    REV --> GHA
    GHA -->|CLI + pytest| TOOL
    DOORS --> TOOL
    TOOL --> OUT[Reports + optional RTE stubs]
```

---

## 2. Pipeline stages

```mermaid
flowchart LR
    A[Parse] --> B[Validate DBC]
    B --> C[Validate ARXML]
    C --> D[Match DOORS]
    D --> E{ARXML errors?}
    E -->|no| F[Codegen]
    E -->|yes| G[Skip codegen]
    F --> H[Reports]
    G --> H
```

---

## 3. Component dependencies

```mermaid
flowchart TB
    CLI[cli.py] --> ORCH[pipeline/orchestrator.py]
    ORCH --> CFG[config.py]
    ORCH --> PDBC[parsers/dbc_parser.py]
    ORCH --> PARX[parsers/arxml_parser.py]
    ORCH --> PDOOR[parsers/doors_parser.py]
    ORCH --> EDBC[validators/dbc/engine.py]
    ORCH --> EARX[validators/arxml/port_consistency.py]
    ORCH --> MATCH[requirements/matcher.py]
    ORCH --> CSTUB[codegen/c_stubs.py]
    ORCH --> RTE[codegen/rte_mappings.py]
    ORCH --> RPT[utils/report.py]

    PDBC --> MCAN[models/can_models.py]
    PARX --> MARX[models/arxml_models.py]
    PDOOR --> MREQ[models/requirements.py]
    EDBC --> MCAN
    EARX --> MARX
    MATCH --> MREQ
    MATCH --> MCAN
    MATCH --> MARX
    EDBC --> MF[models/findings.py]
    EARX --> MF
    MATCH --> MF
    ORCH --> MF
```

---

## 4. DBC validation detail

```mermaid
flowchart TD
    DBC[(.dbc)] --> PARSE[DbcParser / cantools]
    PARSE --> NET[CanNetwork]
    NET --> ENG[DbcValidationEngine]

    ENG --> R1[Overlap / OOB bits]
    ENG --> R2[Endianness mix]
    ENG --> R3[Missing init values]
    ENG --> R4[Cycle times]
    ENG --> R5[J1939]
    ENG --> R6[CAN-FD DLC]

    R1 --> F[Findings]
    R2 --> F
    R3 --> F
    R4 --> F
    R5 --> F
    R6 --> F
```

---

## 5. ARXML → codegen

```mermaid
flowchart LR
    ARXML[(.arxml)] --> PAR[ArxmlParser]
    PAR --> MOD[ArxmlModel]
    MOD --> VAL[ArxmlPortValidator]
    VAL --> OK{errors == 0?}
    OK -->|yes| STUB[CStubGenerator]
    OK -->|yes| MAP[RteMappingGenerator]
    OK -->|no| SKIP[No codegen]
    STUB --> H["Rte_Type.h<br/>Rte_&lt;Swc&gt;.h"]
    MAP --> J["rte_interface_map.json<br/>Rte_InterfaceMap.c"]
```

---

## 6. Git hook path

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git
    participant Hook as pre-commit hook
    participant CLI as auto-validator hook-check

    Dev->>Git: git commit
    Git->>Hook: run hooks/pre-commit
    Hook->>Hook: list staged .dbc / .arxml / req files
    alt no relevant files
        Hook-->>Git: exit 0
    else files present
        Hook->>CLI: hook-check paths…
        CLI-->>Hook: exit 0 or 1
        Hook-->>Git: allow or block commit
    end
```

---

## 7. Deploy / consume in an ECU repo

```mermaid
flowchart TB
    subgraph ECU["Application / platform repo"]
        DBC[Network.dbc]
        ARX[Swc.arxml]
        APP[Application SWCs]
    end

    subgraph Tool["This project installed as tool"]
        AV[auto-validator]
    end

    DBC --> AV
    ARX --> AV
    AV -->|findings| CI[CI / PR check]
    AV -->|optional stubs| OUT[generated/rte/]
    OUT -.->|include path review| APP
```

---

## Editing diagrams

- Diagrams use [Mermaid](https://mermaid.js.org/) fenced as ` ```mermaid `.
- Preview in GitHub, VS Code Mermaid extension, or [mermaid.live](https://mermaid.live).
- Keep node labels short; put detail in the surrounding prose.
