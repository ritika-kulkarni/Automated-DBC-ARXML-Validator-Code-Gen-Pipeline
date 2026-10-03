# Documentation

Guides for the **Automated DBC/ARXML Validator & Code-Gen Pipeline**.

## Start here

| Doc | Description |
|-----|-------------|
| [GETTING_STARTED.md](GETTING_STARTED.md) | Install, first run, git hook |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Packages, sequence, failure handling |
| [DIAGRAMS.md](DIAGRAMS.md) | Mermaid architecture diagrams |
| [DATA_FLOW.md](DATA_FLOW.md) | Inputs → models → reports / stubs |

## Reference

| Doc | Description |
|-----|-------------|
| [FEATURES.md](FEATURES.md) | Feature catalog by module |
| [VALIDATION_RULES.md](VALIDATION_RULES.md) | Rule IDs, severity, remediations |
| [CONFIGURATION.md](CONFIGURATION.md) | YAML / env config keys |
| [CLI.md](CLI.md) | `validate`, `codegen`, `hook-check` |
| [CODEGEN.md](CODEGEN.md) | Generated C / RTE artifacts |
| [HOOKS_AND_CI.md](HOOKS_AND_CI.md) | Pre-commit + GitHub Actions |
| [TESTING.md](TESTING.md) | Unit / integration / fixtures |

## Package READMEs

| Path | Focus |
|------|-------|
| [../src/auto_validator/README.md](../src/auto_validator/README.md) | Package map |
| [../src/auto_validator/parsers/README.md](../src/auto_validator/parsers/README.md) | DBC / ARXML / DOORS parsers |
| [../src/auto_validator/validators/README.md](../src/auto_validator/validators/README.md) | Validation engines |
| [../src/auto_validator/validators/dbc/README.md](../src/auto_validator/validators/dbc/README.md) | DBC / J1939 / CAN-FD rules |
| [../src/auto_validator/validators/arxml/README.md](../src/auto_validator/validators/arxml/README.md) | ARXML port checks |
| [../src/auto_validator/codegen/README.md](../src/auto_validator/codegen/README.md) | Stub / map generators |
| [../src/auto_validator/requirements/README.md](../src/auto_validator/requirements/README.md) | DOORS matcher |
| [../src/auto_validator/pipeline/README.md](../src/auto_validator/pipeline/README.md) | Orchestrator |
| [../src/auto_validator/models/README.md](../src/auto_validator/models/README.md) | Domain models |
| [../src/auto_validator/utils/README.md](../src/auto_validator/utils/README.md) | Logging, retry, reports |
| [../configs/README.md](../configs/README.md) | Config files |
| [../hooks/README.md](../hooks/README.md) | Git hooks |
| [../tests/README.md](../tests/README.md) | Test suite |
| [../tests/fixtures/README.md](../tests/fixtures/README.md) | Fixture catalog |

## Root README

Project landing page (shown on GitHub): [../README.md](../README.md)

> Do **not** add a `.github/README.md` — GitHub prefers that file over the root README and will hide the project page.
