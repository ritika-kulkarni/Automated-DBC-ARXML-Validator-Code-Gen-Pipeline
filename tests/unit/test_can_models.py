"""Unit tests for CAN signal bit layout models."""

import pytest

from auto_validator.models.can_models import ByteOrder, CanSignal


@pytest.mark.unit
def test_little_endian_bit_positions() -> None:
    sig = CanSignal(name="A", start_bit=0, length=16, byte_order=ByteOrder.LITTLE_ENDIAN)
    assert sig.bit_positions() == set(range(0, 16))


@pytest.mark.unit
def test_big_endian_bit_positions_single_byte() -> None:
    # Motorola: start at bit 7, length 8 → bits 7..0
    sig = CanSignal(name="B", start_bit=7, length=8, byte_order=ByteOrder.BIG_ENDIAN)
    assert sig.bit_positions() == {7, 6, 5, 4, 3, 2, 1, 0}


@pytest.mark.unit
def test_signal_validation_rejects_bad_length() -> None:
    with pytest.raises(ValueError):
        CanSignal(name="X", start_bit=0, length=0, byte_order=ByteOrder.LITTLE_ENDIAN)


@pytest.mark.unit
def test_signal_validation_rejects_negative_start() -> None:
    with pytest.raises(ValueError):
        CanSignal(name="X", start_bit=-1, length=8, byte_order=ByteOrder.LITTLE_ENDIAN)
