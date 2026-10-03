"""Detect overlapping signal bit ranges within a message."""

from __future__ import annotations

from auto_validator.models.can_models import CanMessage, CanNetwork
from auto_validator.models.findings import Finding, FindingSeverity


def check_overlapping_signals(network: CanNetwork, source: str | None = None) -> list[Finding]:
    findings: list[Finding] = []
    for msg in network.messages:
        findings.extend(_check_message(msg, source or (network.source_files[0] if network.source_files else None)))
    return findings


def _check_message(msg: CanMessage, source: str | None) -> list[Finding]:
    findings: list[Finding] = []
    occupied: dict[int, str] = {}

    for signal in msg.signals:
        try:
            bits = signal.bit_positions()
        except Exception as exc:  # noqa: BLE001
            findings.append(
                Finding(
                    rule_id="DBC.OVERLAP.INVALID_LAYOUT",
                    severity=FindingSeverity.ERROR,
                    message=f"Cannot compute bit layout for {msg.name}.{signal.name}: {exc}",
                    file_path=source,
                    location=f"{msg.name}/{signal.name}",
                )
            )
            continue

        # Also flag signals that extend past message DLC
        max_bit = msg.length * 8
        out_of_range = [b for b in bits if b < 0 or b >= max_bit]
        if out_of_range:
            findings.append(
                Finding(
                    rule_id="DBC.OVERLAP.OUT_OF_BOUNDS",
                    severity=FindingSeverity.ERROR,
                    message=(
                        f"Signal {signal.name} in {msg.name} occupies bits outside "
                        f"DLC={msg.length} (bits {sorted(out_of_range)[:8]}…)"
                    ),
                    file_path=source,
                    location=f"{msg.name}/{signal.name}",
                    details={"out_of_range_bits": sorted(out_of_range), "dlc": msg.length},
                    suggestion="Reduce signal length or increase message DLC.",
                )
            )

        for bit in bits:
            if bit in occupied:
                findings.append(
                    Finding(
                        rule_id="DBC.OVERLAP.BIT_COLLISION",
                        severity=FindingSeverity.ERROR,
                        message=(
                            f"Overlapping bit {bit} in message {msg.name}: "
                            f"{occupied[bit]} vs {signal.name}"
                        ),
                        file_path=source,
                        location=f"{msg.name}/{signal.name}",
                        details={
                            "bit": bit,
                            "existing_signal": occupied[bit],
                            "new_signal": signal.name,
                        },
                        suggestion="Adjust start_bit/length so signals do not share bits.",
                    )
                )
            else:
                occupied[bit] = signal.name

    return findings
