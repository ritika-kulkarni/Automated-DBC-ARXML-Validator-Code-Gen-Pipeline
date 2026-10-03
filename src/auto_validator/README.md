# `auto_validator` package

Python package implementing the Automated DBC/ARXML Validator & Code-Gen Pipeline.

## Entry points

| Entry | Module |
|-------|--------|
| Console script `auto-validator` | `auto_validator.cli:main` |
| `python -m auto_validator` | `auto_validator.__main__` |

## Subpackages

| Package | Role |
|---------|------|
| [`models/`](models/README.md) | Typed domain models (CAN, ARXML, findings, DOORS) |
| [`parsers/`](parsers/README.md) | DBC (cantools), ARXML (lxml), DOORS (CSV/JSON) |
| [`validators/`](validators/README.md) | Rule engines for DBC and ARXML |
| [`requirements/`](requirements/README.md) | Traceability matcher |
| [`codegen/`](codegen/README.md) | C stubs + RTE maps |
| [`pipeline/`](pipeline/README.md) | Runs the full validate/codegen flow |
| [`utils/`](utils/README.md) | Logging, retry, reports |

## Top-level modules

| File | Role |
|------|------|
| `cli.py` | Click commands: `validate`, `codegen`, `hook-check` |
| `config.py` | YAML + pydantic settings |
| `__init__.py` | Package version |

## Docs

Full feature documentation: [`../../docs/FEATURES.md`](../../docs/FEATURES.md)
