"""Validate message cycle times and detect mismatches."""

from __future__ import annotations

from collections import defaultdict

from auto_validator.models.can_models import CanNetwork
from auto_validator.models.findings import Finding, FindingSeverity


def check_cycle_times(
    network: CanNetwork,
    *,
    tolerance_ms: int = 0,
    expected_cycle_times: dict[str, int] | None = None,
    source: str | None = None,
) -> list[Finding]:
    """Check GenMsgCycleTime presence, validity, and optional expected values."""
    findings: list[Finding] = []
    src = source or (network.source_files[0] if network.source_files else None)
    expected_cycle_times = expected_cycle_times or {}

    by_id: dict[int, list[tuple[str, int | None]]] = defaultdict(list)

    for msg in network.messages:
        by_id[msg.frame_id].append((msg.name, msg.cycle_time_ms))

        if msg.cycle_time_ms is None:
            findings.append(
                Finding(
                    rule_id="DBC.CYCLE.MISSING",
                    severity=FindingSeverity.WARNING,
                    message=f"Message {msg.name} (0x{msg.frame_id:X}) has no cycle time",
                    file_path=src,
                    location=msg.name,
                    suggestion="Set GenMsgCycleTime attribute on the message.",
                )
            )
        elif msg.cycle_time_ms <= 0:
            findings.append(
                Finding(
                    rule_id="DBC.CYCLE.NON_POSITIVE",
                    severity=FindingSeverity.ERROR,
                    message=(
                        f"Message {msg.name} has invalid cycle time: {msg.cycle_time_ms} ms"
                    ),
                    file_path=src,
                    location=msg.name,
                )
            )

        if msg.name in expected_cycle_times and msg.cycle_time_ms is not None:
            expected = expected_cycle_times[msg.name]
            if abs(msg.cycle_time_ms - expected) > tolerance_ms:
                findings.append(
                    Finding(
                        rule_id="DBC.CYCLE.MISMATCH",
                        severity=FindingSeverity.ERROR,
                        message=(
                            f"Message {msg.name} cycle time {msg.cycle_time_ms} ms "
                            f"!= expected {expected} ms (tol={tolerance_ms})"
                        ),
                        file_path=src,
                        location=msg.name,
                        details={"actual": msg.cycle_time_ms, "expected": expected},
                    )
                )

    for frame_id, entries in by_id.items():
        if len(entries) < 2:
            continue
        times = {t for _, t in entries}
        if len(times) > 1:
            findings.append(
                Finding(
                    rule_id="DBC.CYCLE.ID_CONFLICT",
                    severity=FindingSeverity.ERROR,
                    message=(
                        f"Frame ID 0x{frame_id:X} used by multiple messages with "
                        f"differing cycle times: {entries}"
                    ),
                    file_path=src,
                    location=f"0x{frame_id:X}",
                    details={"entries": [{"name": n, "cycle_ms": t} for n, t in entries]},
                )
            )

    return findings
