"""Abstract validator interface (Strategy + Template Method)."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from auto_validator.models.findings import Finding, ValidationResult
from auto_validator.utils.logging import get_logger

T = TypeVar("T")


class BaseValidator(ABC, Generic[T]):
    """Template for validators: time execution, collect findings, mark pass/fail."""

    rule_prefix: str = "BASE"
    stage_name: str = "validate"

    def __init__(self) -> None:
        self.logger = get_logger(f"validators.{self.stage_name}")

    def run(self, target: T) -> ValidationResult:
        start = time.perf_counter()
        result = ValidationResult(stage=self.stage_name, passed=True)
        try:
            findings = self.validate(target)
            for finding in findings:
                result.add(finding)
        except Exception as exc:  # noqa: BLE001 - surface as finding, don't crash pipeline
            self.logger.exception("Validator %s failed unexpectedly", self.stage_name)
            result.add(
                Finding(
                    rule_id=f"{self.rule_prefix}.INTERNAL",
                    severity="error",  # type: ignore[arg-type]
                    message=f"Internal validator error: {exc}",
                )
            )
        result.duration_ms = (time.perf_counter() - start) * 1000
        self.logger.info(
            "Stage %s finished: passed=%s errors=%s warnings=%s (%.1f ms)",
            self.stage_name,
            result.passed,
            result.error_count,
            result.warning_count,
            result.duration_ms,
        )
        return result

    @abstractmethod
    def validate(self, target: T) -> list[Finding]:
        """Return findings for the given target; empty list means clean."""
