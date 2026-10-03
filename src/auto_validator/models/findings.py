"""Validation findings and pipeline report models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FindingSeverity(str, Enum):
    """Severity levels for validation findings."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    def rank(self) -> int:
        return {FindingSeverity.INFO: 0, FindingSeverity.WARNING: 1, FindingSeverity.ERROR: 2}[self]


class Finding(BaseModel):
    """A single validation finding (rule violation or observation)."""

    rule_id: str
    severity: FindingSeverity
    message: str
    file_path: str | None = None
    location: str | None = None  # e.g. message/signal/port path
    details: dict[str, Any] = Field(default_factory=dict)
    suggestion: str | None = None

    def exceeds(self, threshold: FindingSeverity) -> bool:
        return self.severity.rank() >= threshold.rank()


class ValidationResult(BaseModel):
    """Aggregated result from one validator or pipeline stage."""

    stage: str
    passed: bool
    findings: list[Finding] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)
    duration_ms: float = 0.0

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.WARNING)

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)
        if finding.severity == FindingSeverity.ERROR:
            self.passed = False


class PipelineReport(BaseModel):
    """End-to-end pipeline execution report."""

    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    overall_passed: bool = True
    results: list[ValidationResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_result(self, result: ValidationResult) -> None:
        self.results.append(result)
        if not result.passed:
            self.overall_passed = False

    def finalize(self) -> None:
        self.finished_at = datetime.now(timezone.utc)

    @property
    def all_findings(self) -> list[Finding]:
        return [f for r in self.results for f in r.findings]

    @property
    def total_errors(self) -> int:
        return sum(r.error_count for r in self.results)

    @property
    def total_warnings(self) -> int:
        return sum(r.warning_count for r in self.results)

    def to_summary(self) -> dict[str, Any]:
        return {
            "passed": self.overall_passed,
            "errors": self.total_errors,
            "warnings": self.total_warnings,
            "stages": len(self.results),
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }
