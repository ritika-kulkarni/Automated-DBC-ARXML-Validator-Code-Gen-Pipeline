"""Flag signals missing initial / start values."""

from __future__ import annotations

from auto_validator.models.can_models import CanNetwork
from auto_validator.models.findings import Finding, FindingSeverity


def check_missing_initial_values(
    network: CanNetwork,
    *,
    require: bool = True,
    source: str | None = None,
) -> list[Finding]:
    if not require:
        return []

    findings: list[Finding] = []
    src = source or (network.source_files[0] if network.source_files else None)

    for msg in network.messages:
        for sig in msg.signals:
            if sig.initial_value is None:
                findings.append(
                    Finding(
                        rule_id="DBC.INIT.MISSING",
                        severity=FindingSeverity.ERROR,
                        message=f"Signal {msg.name}.{sig.name} has no initial/start value",
                        file_path=src,
                        location=f"{msg.name}/{sig.name}",
                        suggestion="Set GenSigStartValue (or equivalent) in the DBC.",
                    )
                )
    return findings
