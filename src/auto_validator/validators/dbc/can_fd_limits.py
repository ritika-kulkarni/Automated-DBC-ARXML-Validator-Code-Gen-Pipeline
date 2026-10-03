"""CAN-FD / classic CAN DLC and payload limit checks."""

from __future__ import annotations

from auto_validator.models.can_models import CanNetwork
from auto_validator.models.findings import Finding, FindingSeverity

# Valid CAN-FD DLCs map to these payload sizes
CAN_FD_VALID_LENGTHS = {0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 20, 24, 32, 48, 64}


def check_can_fd_limits(
    network: CanNetwork,
    *,
    classic_max_dlc: int = 8,
    can_fd_max_dlc: int = 64,
    source: str | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    src = source or (network.source_files[0] if network.source_files else None)

    for msg in network.messages:
        if msg.is_fd:
            if msg.length > can_fd_max_dlc:
                findings.append(
                    Finding(
                        rule_id="DBC.CANFD.DLC_TOO_LARGE",
                        severity=FindingSeverity.ERROR,
                        message=(
                            f"CAN-FD message {msg.name} DLC={msg.length} "
                            f"exceeds max {can_fd_max_dlc}"
                        ),
                        file_path=src,
                        location=msg.name,
                    )
                )
            elif msg.length not in CAN_FD_VALID_LENGTHS:
                findings.append(
                    Finding(
                        rule_id="DBC.CANFD.INVALID_DLC",
                        severity=FindingSeverity.ERROR,
                        message=(
                            f"CAN-FD message {msg.name} has non-standard payload "
                            f"length {msg.length} (valid: {sorted(CAN_FD_VALID_LENGTHS)})"
                        ),
                        file_path=src,
                        location=msg.name,
                        suggestion="Use ISO 11898-1 CAN-FD valid DLC mapping.",
                    )
                )
        else:
            if msg.length > classic_max_dlc:
                findings.append(
                    Finding(
                        rule_id="DBC.CAN.DLC_TOO_LARGE",
                        severity=FindingSeverity.ERROR,
                        message=(
                            f"Classic CAN message {msg.name} DLC={msg.length} "
                            f"> {classic_max_dlc}; mark as CAN-FD or reduce length"
                        ),
                        file_path=src,
                        location=msg.name,
                    )
                )

    return findings
