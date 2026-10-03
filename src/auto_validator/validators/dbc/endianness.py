"""Flag endianness conflicts and mixed-order packing hazards."""

from __future__ import annotations

from collections import defaultdict

from auto_validator.models.can_models import ByteOrder, CanNetwork
from auto_validator.models.findings import Finding, FindingSeverity


def check_endianness_conflicts(network: CanNetwork, source: str | None = None) -> list[Finding]:
    """Warn when a message mixes Intel and Motorola signals."""
    findings: list[Finding] = []
    src = source or (network.source_files[0] if network.source_files else None)

    for msg in network.messages:
        by_order: dict[ByteOrder, list[str]] = defaultdict(list)
        for sig in msg.signals:
            by_order[sig.byte_order].append(sig.name)

        if len(by_order) > 1:
            findings.append(
                Finding(
                    rule_id="DBC.ENDIAN.MIXED_IN_MESSAGE",
                    severity=FindingSeverity.WARNING,
                    message=(
                        f"Message {msg.name} mixes byte orders: "
                        + ", ".join(f"{k.value}={v}" for k, v in by_order.items())
                    ),
                    file_path=src,
                    location=msg.name,
                    details={k.value: v for k, v in by_order.items()},
                    suggestion="Prefer a single byte order per message (Intel or Motorola).",
                )
            )

        # Multi-byte signals must not start mid-byte inconsistently for Motorola
        for sig in msg.signals:
            if sig.length > 8 and sig.byte_order == ByteOrder.BIG_ENDIAN:
                # Motorola start bit should typically be the MSB position
                if sig.start_bit % 8 == 7 and sig.length > 16:
                    # Informational: unusual long Motorola signals
                    findings.append(
                        Finding(
                            rule_id="DBC.ENDIAN.LONG_MOTOROLA",
                            severity=FindingSeverity.INFO,
                            message=(
                                f"Long Motorola signal {msg.name}.{sig.name} "
                                f"({sig.length} bits) — verify layout against OEM spec."
                            ),
                            file_path=src,
                            location=f"{msg.name}/{sig.name}",
                        )
                    )

    return findings
