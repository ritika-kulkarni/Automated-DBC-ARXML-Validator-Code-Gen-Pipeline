# Documentation Index

Complete documentation for the **Automated DBC/ARXML Validator & Code-Gen Pipeline**.

| Document | Description |
|----------|-------------|
| [FEATURES.md](FEATURES.md) | Every implemented feature, explained end-to-end |
| [VALIDATION_RULES.md](VALIDATION_RULES.md) | Full catalog of DBC / ARXML / requirements rule IDs |
| [CONFIGURATION.md](CONFIGURATION.md) | YAML config reference and environment overrides |
| [CLI.md](CLI.md) | Command-line interface (`validate`, `codegen`, `hook-check`) |
| [CODEGEN.md](CODEGEN.md) | C stub headers and RTE mapping generation |
| [HOOKS_AND_CI.md](HOOKS_AND_CI.md) | Git pre-commit hooks and GitHub Actions CI |
| [TESTING.md](TESTING.md) | Unit, integration, edge-case strategy and how to run tests |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Layering, SOLID mapping, extension points |

## Package READMEs

| Path | Focus |
|------|-------|
| [`../src/auto_validator/README.md`](../src/auto_validator/README.md) | Package overview |
| [`../src/auto_validator/parsers/README.md`](../src/auto_validator/parsers/README.md) | DBC, ARXML, DOORS parsers |
| [`../src/auto_validator/validators/README.md`](../src/auto_validator/validators/README.md) | Validation engines and rules |
| [`../src/auto_validator/validators/dbc/README.md`](../src/auto_validator/validators/dbc/README.md) | DBC / J1939 / CAN-FD checkers |
| [`../src/auto_validator/validators/arxml/README.md`](../src/auto_validator/validators/arxml/README.md) | ARXML port/interface checks |
| [`../src/auto_validator/codegen/README.md`](../src/auto_validator/codegen/README.md) | Code generators |
| [`../src/auto_validator/requirements/README.md`](../src/auto_validator/requirements/README.md) | DOORS requirements matching |
| [`../src/auto_validator/pipeline/README.md`](../src/auto_validator/pipeline/README.md) | Orchestrator |
| [`../src/auto_validator/models/README.md`](../src/auto_validator/models/README.md) | Domain models |
| [`../src/auto_validator/utils/README.md`](../src/auto_validator/utils/README.md) | Logging, retry, reports |
| [`../configs/README.md`](../configs/README.md) | Config files |
| [`../hooks/README.md`](../hooks/README.md) | Native git hooks |
| [`../tests/README.md`](../tests/README.md) | Test suite |
| [`../tests/fixtures/README.md`](../tests/fixtures/README.md) | Fixture catalog |
| [`../.github/README.md`](../.github/README.md) | CI workflow pointer |

## Quick links

- Root project README: [`../README.md`](../README.md)
- Default config: [`../configs/default.yaml`](../configs/default.yaml)
