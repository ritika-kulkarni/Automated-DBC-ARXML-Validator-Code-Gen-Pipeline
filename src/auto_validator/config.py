"""Configuration loading and validation (YAML + env overrides)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DbcRulesConfig(BaseModel):
    overlapping_signals: bool = True
    endianness_conflicts: bool = True
    missing_initial_values: bool = True
    cycle_time_mismatch: bool = True
    j1939_compliance: bool = True
    can_fd_limits: bool = True


class DbcConfig(BaseModel):
    enabled: bool = True
    rules: DbcRulesConfig = Field(default_factory=DbcRulesConfig)
    cycle_time_tolerance_ms: int = 0
    classic_can_max_dlc: int = 8
    can_fd_max_dlc: int = 64
    require_initial_values: bool = True


class ArxmlRulesConfig(BaseModel):
    port_consistency: bool = True
    interface_completeness: bool = True
    data_type_mapping: bool = True


class ArxmlConfig(BaseModel):
    enabled: bool = True
    rules: ArxmlRulesConfig = Field(default_factory=ArxmlRulesConfig)
    generate_c_stubs: bool = True
    generate_rte_mappings: bool = True
    output_dir: str = "output/codegen"


class RequirementsConfig(BaseModel):
    enabled: bool = True
    match_mode: Literal["strict", "fuzzy"] = "strict"
    fuzzy_threshold: float = 0.85
    id_column: str = "req_id"
    signal_column: str = "signal_name"
    port_column: str = "port_name"


class PipelineConfig(BaseModel):
    fail_on_severity: Literal["error", "warning", "info"] = "error"
    parallel: bool = False
    max_retries: int = 3
    retry_backoff_seconds: float = 1.0


class LoggingConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    format: Literal["structured", "plain"] = "structured"
    file: str | None = None


class ReportConfig(BaseModel):
    formats: list[Literal["console", "json", "junit"]] = Field(
        default_factory=lambda: ["console", "json", "junit"]
    )
    output_dir: str = "output/reports"


class AppConfig(BaseSettings):
    """Root application configuration."""

    model_config = SettingsConfigDict(env_prefix="AUTO_VALIDATOR_", extra="ignore")

    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    dbc: DbcConfig = Field(default_factory=DbcConfig)
    arxml: ArxmlConfig = Field(default_factory=ArxmlConfig)
    requirements: RequirementsConfig = Field(default_factory=RequirementsConfig)
    report: ReportConfig = Field(default_factory=ReportConfig)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {path}")
    return data


def load_config(path: Path | str | None = None) -> AppConfig:
    """Load AppConfig from YAML path, falling back to package defaults."""
    if path is None:
        default = Path(__file__).resolve().parents[2] / "configs" / "default.yaml"
        path = default if default.exists() else None

    if path is None:
        return AppConfig()

    raw = load_yaml(Path(path))
    return AppConfig(**raw)
