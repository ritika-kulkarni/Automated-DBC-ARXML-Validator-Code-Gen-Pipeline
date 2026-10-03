"""Unit tests for J1939 compliance rules."""

from __future__ import annotations

import pytest

from auto_validator.models.can_models import CanMessage, CanNetwork
from auto_validator.validators.dbc.j1939_rules import check_j1939_compliance


def _j1939_id(priority: int, pgn: int, sa: int) -> int:
    """Build a 29-bit J1939 CAN ID."""
    return ((priority & 0x7) << 26) | ((pgn & 0x3FFFF) << 8) | (sa & 0xFF)


@pytest.mark.unit
def test_j1939_requires_extended_frame() -> None:
    network = CanNetwork(
        messages=[
            CanMessage(
                name="Bad",
                frame_id=0x100,
                length=8,
                is_extended=False,
                is_j1939=True,
            )
        ]
    )
    findings = check_j1939_compliance(network)
    assert any(f.rule_id == "DBC.J1939.NOT_EXTENDED" for f in findings)


@pytest.mark.unit
def test_j1939_null_source_address_warning() -> None:
    frame_id = _j1939_id(6, 0xF004, 0xFE)
    network = CanNetwork(
        messages=[
            CanMessage(
                name="EEC1",
                frame_id=frame_id,
                length=8,
                is_extended=True,
                is_j1939=True,
            )
        ]
    )
    findings = check_j1939_compliance(network)
    assert any(f.rule_id == "DBC.J1939.NULL_SA" for f in findings)


@pytest.mark.unit
def test_j1939_pgn_length_conflict() -> None:
    # Same PGN (PDU2 style), different lengths
    pgn = 0xF004
    network = CanNetwork(
        messages=[
            CanMessage(
                name="A",
                frame_id=_j1939_id(6, pgn, 0x00),
                length=8,
                is_extended=True,
                is_j1939=True,
            ),
            CanMessage(
                name="B",
                frame_id=_j1939_id(6, pgn, 0x01),
                length=4,
                is_extended=True,
                is_j1939=True,
            ),
        ]
    )
    findings = check_j1939_compliance(network)
    assert any(f.rule_id == "DBC.J1939.PGN_LENGTH_CONFLICT" for f in findings)


@pytest.mark.unit
@pytest.mark.edge
def test_non_j1939_messages_ignored() -> None:
    network = CanNetwork(
        messages=[CanMessage(name="Classic", frame_id=0x100, length=8, is_j1939=False)]
    )
    assert check_j1939_compliance(network) == []
