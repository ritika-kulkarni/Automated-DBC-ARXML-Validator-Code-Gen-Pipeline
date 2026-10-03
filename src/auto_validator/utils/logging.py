"""Structured logging setup for the pipeline."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from auto_validator.config import LoggingConfig


class StructuredFormatter(logging.Formatter):
    """Emit JSON log lines suitable for CI log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key in ("stage", "file_path", "rule_id", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, default=str)


def setup_logging(config: LoggingConfig | None = None) -> None:
    config = config or LoggingConfig()
    root = logging.getLogger("auto_validator")
    root.handlers.clear()
    root.setLevel(getattr(logging, config.level))

    handler: logging.Handler = logging.StreamHandler(sys.stderr)
    if config.format == "structured":
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
    root.addHandler(handler)

    if config.file:
        file_handler = logging.FileHandler(config.file, encoding="utf-8")
        file_handler.setFormatter(StructuredFormatter())
        root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    if not name.startswith("auto_validator"):
        name = f"auto_validator.{name}"
    return logging.getLogger(name)
