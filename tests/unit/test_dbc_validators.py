"""Unit tests for DBC rule checkers."""

from __future__ import annotations

from pathlib import Path

import pytest

from auto_validator.models.can_models import ByteOrder, CanMessage, CanNetwork, CanSignal
from auto_validator.parsers.dbc_parser import DbcParser
from auto_validator.validators.dbc.can_fd_limits import check_can_fd_limits
from auto_validator.validators.dbc.cycle_times import check_cycle_times
from auto_validator.validators.dbc.endianness import check_endianness_conflicts
from auto_validator.validators.dbc.engine import DbcValidationEngine
from auto_validator.validators.dbc.initial_values import check_missing_initial_values
from auto_validator.validators.dbc.overlapping_signals import check_overlapping_signals


@pytest.mark.unit
def test_overlapping_signals_detected() -> None:
    network = CanNetwork(
        messages=[
            CanMessage(
                name="M",
                frame_id=1,
                length=8,
                signals=[
                    CanSignal(
                        name="A", start_bit=0, length=16, byte_order=ByteOrder.LITTLE_ENDIAN
                    ),
                    CanSignal(
                        name="B", start_bit=8, length=16, byte_order=ByteOrder.LITTLE_ENDIAN
                    ),
                ],
            )
        ]
    )
    findings = check_overlapping_signals(network)
    assert any(f.rule_id == "DBC.OVERLAP.BIT_COLLISION" for f in findings)


@pytest.mark.unit
def test_no_overlap_on_adjacent_signals() -> None:
    network = CanNetwork(
        messages=[
            CanMessage(
                name="M",
                frame_id=1,
                length=8,
                signals=[
                    CanSignal(
                        name="A", start_bit=0, length=8, byte_order=ByteOrder.LITTLE_ENDIAN
                    ),
                    CanSignal(
                        name="B", start_bit=8, length=8, byte_order=ByteOrder.LITTLE_ENDIAN
                    ),
                ],
            )
        ]
    )
    assert check_overlapping_signals(network) == []


@pytest.mark.unit
def test_out_of_bounds_signal() -> None:
    network = CanNetwork(
        messages=[
            CanMessage(
                name="M",
                frame_id=1,
                length=1,
                signals=[
                    CanSignal(
                        name="A", start_bit=0, length=16, byte_order=ByteOrder.LITTLE_ENDIAN
                    ),
                ],
            )
        ]
    )
    findings = check_overlapping_signals(network)
    assert any(f.rule_id == "DBC.OVERLAP.OUT_OF_BOUNDS" for f in findings)


@pytest.mark.unit
def test_missing_initial_values() -> None:
    network = CanNetwork(
        messages=[
            CanMessage(
                name="M",
                frame_id=1,
                length=8,
                signals=[
                    CanSignal(
                        name="A",
                        start_bit=0,
                        length=8,
                        byte_order=ByteOrder.LITTLE_ENDIAN,
                        initial_value=None,
                    )
                ],
            )
        ]
    )
    findings = check_missing_initial_values(network, require=True)
    assert len(findings) == 1
    assert findings[0].rule_id == "DBC.INIT.MISSING"


@pytest.mark.unit
def test_cycle_time_mismatch() -> None:
    network = CanNetwork(
        messages=[CanMessage(name="M", frame_id=1, length=8, cycle_time_ms=10)]
    )
    findings = check_cycle_times(network, expected_cycle_times={"M": 20})
    assert any(f.rule_id == "DBC.CYCLE.MISMATCH" for f in findings)


@pytest.mark.unit
def test_mixed_endianness_warning() -> None:
    network = CanNetwork(
        messages=[
            CanMessage(
                name="M",
                frame_id=1,
                length=8,
                signals=[
                    CanSignal(
                        name="A", start_bit=0, length=8, byte_order=ByteOrder.LITTLE_ENDIAN
                    ),
                    CanSignal(
                        name="B", start_bit=15, length=8, byte_order=ByteOrder.BIG_ENDIAN
                    ),
                ],
            )
        ]
    )
    findings = check_endianness_conflicts(network)
    assert any(f.rule_id == "DBC.ENDIAN.MIXED_IN_MESSAGE" for f in findings)


@pytest.mark.unit
def test_can_fd_invalid_dlc() -> None:
    network = CanNetwork(
        messages=[CanMessage(name="Fd", frame_id=1, length=50, is_fd=True)]
    )
    findings = check_can_fd_limits(network)
    assert any(f.rule_id == "DBC.CANFD.INVALID_DLC" for f in findings)


@pytest.mark.unit
def test_engine_runs_all_rules_on_fixture(overlap_dbc: Path, dbc_parser: DbcParser) -> None:
    network = dbc_parser.parse_file(overlap_dbc)
    result = DbcValidationEngine().run(network)
    assert result.passed is False
    assert any("OVERLAP" in f.rule_id for f in result.findings)


@pytest.mark.unit
@pytest.mark.edge
def test_empty_network_is_clean() -> None:
    result = DbcValidationEngine().run(CanNetwork())
    assert result.passed is True
    assert result.findings == []
