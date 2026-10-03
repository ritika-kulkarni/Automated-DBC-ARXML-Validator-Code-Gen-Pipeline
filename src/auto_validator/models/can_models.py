"""CAN / J1939 / CAN-FD domain models (DBC-normalized)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ByteOrder(str, Enum):
    LITTLE_ENDIAN = "little_endian"
    BIG_ENDIAN = "big_endian"


class SignalType(str, Enum):
    UNSIGNED = "unsigned"
    SIGNED = "signed"
    FLOAT = "float"
    DOUBLE = "double"


class CanSignal(BaseModel):
    """Normalized CAN signal definition."""

    name: str
    start_bit: int
    length: int
    byte_order: ByteOrder
    is_signed: bool = False
    scale: float = 1.0
    offset: float = 0.0
    minimum: float | None = None
    maximum: float | None = None
    unit: str = ""
    initial_value: float | None = None
    receivers: list[str] = Field(default_factory=list)
    comment: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("length")
    @classmethod
    def length_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("signal length must be positive")
        return v

    @field_validator("start_bit")
    @classmethod
    def start_bit_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("start_bit must be >= 0")
        return v

    def bit_positions(self) -> set[int]:
        """Bits this signal occupies (Intel = linear; Motorola = DBC layout)."""
        if self.byte_order == ByteOrder.LITTLE_ENDIAN:
            return set(range(self.start_bit, self.start_bit + self.length))

        # Motorola (big-endian) bit layout as used by cantools / Vector DBC
        positions: set[int] = set()
        bit = self.start_bit
        for _ in range(self.length):
            positions.add(bit)
            if bit % 8 == 0:
                bit += 15
            else:
                bit -= 1
        return positions


class CanMessage(BaseModel):
    """Normalized CAN message definition."""

    name: str
    frame_id: int
    length: int  # DLC in bytes
    is_extended: bool = False
    is_fd: bool = False
    is_j1939: bool = False
    cycle_time_ms: int | None = None
    senders: list[str] = Field(default_factory=list)
    signals: list[CanSignal] = Field(default_factory=list)
    comment: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)

    @property
    def pgn(self) -> int | None:
        """Extract J1939 PGN from 29-bit extended ID if applicable."""
        if not (self.is_extended or self.is_j1939):
            return None
        # J1939: PDU Format in bits 16-23, PDU Specific in bits 8-15
        pf = (self.frame_id >> 16) & 0xFF
        ps = (self.frame_id >> 8) & 0xFF
        if pf < 240:
            return pf << 8  # PDU1: PGN ignores PS (destination)
        return (pf << 8) | ps  # PDU2


class CanNetwork(BaseModel):
    """Collection of messages from one or more DBC files."""

    name: str = "network"
    source_files: list[str] = Field(default_factory=list)
    messages: list[CanMessage] = Field(default_factory=list)
    nodes: list[str] = Field(default_factory=list)
    bus_speed_kbps: int | None = None
    is_can_fd: bool = False

    def message_by_name(self, name: str) -> CanMessage | None:
        return next((m for m in self.messages if m.name == name), None)

    def message_by_id(self, frame_id: int) -> CanMessage | None:
        return next((m for m in self.messages if m.frame_id == frame_id), None)
