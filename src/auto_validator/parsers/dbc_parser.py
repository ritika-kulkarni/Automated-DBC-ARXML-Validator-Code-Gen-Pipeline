"""DBC parsing via cantools → normalized CanNetwork models."""

from __future__ import annotations

from pathlib import Path

import cantools
from cantools.database.can.signal import Signal as CtSignal

from auto_validator.models.can_models import (
    ByteOrder,
    CanMessage,
    CanNetwork,
    CanSignal,
)
from auto_validator.utils.logging import get_logger
from auto_validator.utils.retry import retryable

logger = get_logger("parsers.dbc")


def _byte_order(signal: CtSignal) -> ByteOrder:
    order = getattr(signal, "byte_order", "little_endian")
    if order in ("big_endian", "motorola"):
        return ByteOrder.BIG_ENDIAN
    return ByteOrder.LITTLE_ENDIAN


def _initial_value(signal: CtSignal) -> float | None:
    # cantools exposes raw initial via attributes / GenSigStartValue
    raw = getattr(signal, "raw_initial", None)
    if raw is not None:
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None
    attrs = getattr(signal, "dbc", None)
    if attrs is not None:
        start = attrs.attributes.get("GenSigStartValue")
        if start is not None:
            try:
                return float(start.value if hasattr(start, "value") else start)
            except (TypeError, ValueError, AttributeError):
                return None
    return None


def _cycle_time_ms(message: object) -> int | None:
    cycle = getattr(message, "cycle_time", None)
    if cycle is not None:
        try:
            return int(cycle)
        except (TypeError, ValueError):
            pass
    dbc = getattr(message, "dbc", None)
    if dbc is not None:
        attr = dbc.attributes.get("GenMsgCycleTime")
        if attr is not None:
            try:
                return int(attr.value if hasattr(attr, "value") else attr)
            except (TypeError, ValueError, AttributeError):
                return None
    return None


def _is_j1939(message: object, frame_id: int, is_extended: bool) -> bool:
    if getattr(message, "protocol", None) == "j1939":
        return True
    # Heuristic: extended 29-bit IDs with J1939-like structure
    return is_extended and frame_id > 0x7FF


def _is_fd(message: object) -> bool:
    if getattr(message, "is_fd", False):
        return True
    dbc = getattr(message, "dbc", None)
    if dbc is not None:
        attr = dbc.attributes.get("VFrameFormat")
        if attr is not None:
            val = str(attr.value if hasattr(attr, "value") else attr).lower()
            return "fd" in val or "canfd" in val.replace("_", "")
    return False


class DbcParser:
    """Parse one or more DBC files into a CanNetwork."""

    @retryable(max_attempts=3, backoff_seconds=0.5)
    def parse_file(self, path: Path | str) -> CanNetwork:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"DBC file not found: {path}")
        if path.suffix.lower() != ".dbc":
            raise ValueError(f"Expected .dbc file, got: {path}")

        logger.info("Parsing DBC: %s", path)
        db = cantools.database.load_file(str(path), strict=False)
        return self._to_network(db, source_files=[str(path)])

    def parse_files(self, paths: list[Path | str]) -> CanNetwork:
        networks = [self.parse_file(p) for p in paths]
        if not networks:
            return CanNetwork()
        merged = networks[0]
        for net in networks[1:]:
            merged.messages.extend(net.messages)
            merged.source_files.extend(net.source_files)
            for node in net.nodes:
                if node not in merged.nodes:
                    merged.nodes.append(node)
            merged.is_can_fd = merged.is_can_fd or net.is_can_fd
        return merged

    def _to_network(self, db: object, source_files: list[str]) -> CanNetwork:
        messages: list[CanMessage] = []
        is_can_fd = False

        for msg in getattr(db, "messages", []):
            signals = [self._to_signal(s) for s in msg.signals]
            is_extended = bool(getattr(msg, "is_extended_frame", False))
            frame_id = int(msg.frame_id)
            fd = _is_fd(msg)
            is_can_fd = is_can_fd or fd
            messages.append(
                CanMessage(
                    name=msg.name,
                    frame_id=frame_id,
                    length=int(msg.length),
                    is_extended=is_extended,
                    is_fd=fd,
                    is_j1939=_is_j1939(msg, frame_id, is_extended),
                    cycle_time_ms=_cycle_time_ms(msg),
                    senders=list(getattr(msg, "senders", []) or []),
                    signals=signals,
                    comment=str(getattr(msg, "comment", "") or ""),
                )
            )

        nodes = [n.name for n in getattr(db, "nodes", [])]
        return CanNetwork(
            name=getattr(db, "name", None) or "network",
            source_files=source_files,
            messages=messages,
            nodes=nodes,
            is_can_fd=is_can_fd,
        )

    def _to_signal(self, signal: CtSignal) -> CanSignal:
        return CanSignal(
            name=signal.name,
            start_bit=int(signal.start),
            length=int(signal.length),
            byte_order=_byte_order(signal),
            is_signed=bool(getattr(signal, "is_signed", False)),
            scale=float(getattr(signal, "scale", 1.0) or 1.0),
            offset=float(getattr(signal, "offset", 0.0) or 0.0),
            minimum=getattr(signal, "minimum", None),
            maximum=getattr(signal, "maximum", None),
            unit=str(getattr(signal, "unit", "") or ""),
            initial_value=_initial_value(signal),
            receivers=list(getattr(signal, "receivers", []) or []),
            comment=str(getattr(signal, "comment", "") or ""),
        )
