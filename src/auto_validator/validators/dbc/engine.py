"""Runs the configured DBC checks and returns one finding list."""

from __future__ import annotations

from auto_validator.config import DbcConfig
from auto_validator.models.can_models import CanNetwork
from auto_validator.models.findings import Finding
from auto_validator.validators.base import BaseValidator
from auto_validator.validators.dbc.can_fd_limits import check_can_fd_limits
from auto_validator.validators.dbc.cycle_times import check_cycle_times
from auto_validator.validators.dbc.endianness import check_endianness_conflicts
from auto_validator.validators.dbc.initial_values import check_missing_initial_values
from auto_validator.validators.dbc.j1939_rules import check_j1939_compliance
from auto_validator.validators.dbc.overlapping_signals import check_overlapping_signals


class DbcValidationEngine(BaseValidator[CanNetwork]):
    """DBC / J1939 / CAN-FD checks controlled by DbcConfig.rules."""

    rule_prefix = "DBC"
    stage_name = "dbc_validation"

    def __init__(
        self,
        config: DbcConfig | None = None,
        expected_cycle_times: dict[str, int] | None = None,
    ) -> None:
        super().__init__()
        self.config = config or DbcConfig()
        self.expected_cycle_times = expected_cycle_times or {}

    def validate(self, target: CanNetwork) -> list[Finding]:
        if not self.config.enabled:
            return []

        rules = self.config.rules
        findings: list[Finding] = []

        if rules.overlapping_signals:
            findings.extend(check_overlapping_signals(target))
        if rules.endianness_conflicts:
            findings.extend(check_endianness_conflicts(target))
        if rules.missing_initial_values:
            findings.extend(
                check_missing_initial_values(
                    target, require=self.config.require_initial_values
                )
            )
        if rules.cycle_time_mismatch:
            findings.extend(
                check_cycle_times(
                    target,
                    tolerance_ms=self.config.cycle_time_tolerance_ms,
                    expected_cycle_times=self.expected_cycle_times,
                )
            )
        if rules.j1939_compliance:
            findings.extend(check_j1939_compliance(target))
        if rules.can_fd_limits:
            findings.extend(
                check_can_fd_limits(
                    target,
                    classic_max_dlc=self.config.classic_can_max_dlc,
                    can_fd_max_dlc=self.config.can_fd_max_dlc,
                )
            )

        return findings
