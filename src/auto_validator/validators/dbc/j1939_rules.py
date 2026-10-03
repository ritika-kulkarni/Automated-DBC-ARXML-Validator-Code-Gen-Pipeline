"""J1939-specific DBC compliance checks."""

from __future__ import annotations

from auto_validator.models.can_models import CanNetwork
from auto_validator.models.findings import Finding, FindingSeverity

# Common J1939 constraints
J1939_MAX_DATA_LENGTH = 8  # classic J1939; BAM/TP used for longer
J1939_PRIORITY_MAX = 7


def check_j1939_compliance(network: CanNetwork, source: str | None = None) -> list[Finding]:
    findings: list[Finding] = []
    src = source or (network.source_files[0] if network.source_files else None)

    for msg in network.messages:
        if not msg.is_j1939:
            continue

        if not msg.is_extended:
            findings.append(
                Finding(
                    rule_id="DBC.J1939.NOT_EXTENDED",
                    severity=FindingSeverity.ERROR,
                    message=f"J1939 message {msg.name} must use 29-bit extended ID",
                    file_path=src,
                    location=msg.name,
                )
            )

        # Priority is bits 26-28 of the 29-bit ID
        priority = (msg.frame_id >> 26) & 0x7
        if priority > J1939_PRIORITY_MAX:
            findings.append(
                Finding(
                    rule_id="DBC.J1939.PRIORITY",
                    severity=FindingSeverity.ERROR,
                    message=f"J1939 message {msg.name} has invalid priority {priority}",
                    file_path=src,
                    location=msg.name,
                )
            )

        pgn = msg.pgn
        if pgn is None:
            findings.append(
                Finding(
                    rule_id="DBC.J1939.PGN_MISSING",
                    severity=FindingSeverity.WARNING,
                    message=f"Could not derive PGN for {msg.name}",
                    file_path=src,
                    location=msg.name,
                )
            )

        if not msg.is_fd and msg.length > J1939_MAX_DATA_LENGTH:
            findings.append(
                Finding(
                    rule_id="DBC.J1939.LENGTH",
                    severity=FindingSeverity.WARNING,
                    message=(
                        f"J1939 message {msg.name} DLC={msg.length} > 8; "
                        "ensure Transport Protocol (TP) is intended"
                    ),
                    file_path=src,
                    location=msg.name,
                )
            )

        # Source address = bits 0-7
        sa = msg.frame_id & 0xFF
        if sa == 0xFE:  # NULL address misuse in TX
            findings.append(
                Finding(
                    rule_id="DBC.J1939.NULL_SA",
                    severity=FindingSeverity.WARNING,
                    message=f"J1939 message {msg.name} uses NULL source address 0xFE",
                    file_path=src,
                    location=msg.name,
                )
            )

    # Duplicate PGNs with conflicting lengths
    pgn_map: dict[int, list[tuple[str, int]]] = {}
    for msg in network.messages:
        if msg.is_j1939 and msg.pgn is not None:
            pgn_map.setdefault(msg.pgn, []).append((msg.name, msg.length))

    for pgn, entries in pgn_map.items():
        lengths = {length for _, length in entries}
        if len(entries) > 1 and len(lengths) > 1:
            findings.append(
                Finding(
                    rule_id="DBC.J1939.PGN_LENGTH_CONFLICT",
                    severity=FindingSeverity.ERROR,
                    message=f"PGN 0x{pgn:X} has conflicting lengths: {entries}",
                    file_path=src,
                    location=f"PGN:0x{pgn:X}",
                    details={"entries": [{"name": n, "length": L} for n, L in entries]},
                )
            )

    return findings
