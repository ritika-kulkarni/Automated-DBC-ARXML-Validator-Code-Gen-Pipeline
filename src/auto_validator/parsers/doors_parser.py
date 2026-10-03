"""DOORS requirements export parser (CSV / JSON)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from auto_validator.config import RequirementsConfig
from auto_validator.models.requirements import Requirement, RequirementsCatalog
from auto_validator.utils.logging import get_logger
from auto_validator.utils.retry import retryable

logger = get_logger("parsers.doors")


class DoorsParser:
    """Load DOORS CSV/JSON exports into a RequirementsCatalog."""

    def __init__(self, config: RequirementsConfig | None = None) -> None:
        self.config = config or RequirementsConfig()

    @retryable(max_attempts=3, backoff_seconds=0.5)
    def parse_file(self, path: Path | str) -> RequirementsCatalog:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Requirements file not found: {path}")

        suffix = path.suffix.lower()
        logger.info("Parsing requirements: %s", path)
        if suffix == ".json":
            requirements = self._from_json(path)
        elif suffix in {".csv", ".tsv"}:
            requirements = self._from_csv(path, delimiter="\t" if suffix == ".tsv" else ",")
        else:
            raise ValueError(f"Unsupported requirements format: {path.suffix}")

        return RequirementsCatalog(source_files=[str(path)], requirements=requirements)

    def parse_files(self, paths: list[Path | str]) -> RequirementsCatalog:
        catalogs = [self.parse_file(p) for p in paths]
        if not catalogs:
            return RequirementsCatalog()
        merged = catalogs[0]
        for c in catalogs[1:]:
            merged.requirements.extend(c.requirements)
            merged.source_files.extend(c.source_files)
        return merged

    def _normalize_row(self, row: dict[str, Any]) -> Requirement | None:
        # Support both configured column names and common aliases
        def pick(*keys: str) -> str | None:
            lower_map = {k.lower(): v for k, v in row.items() if k is not None}
            for key in keys:
                val = lower_map.get(key.lower())
                if val is not None and str(val).strip():
                    return str(val).strip()
            return None

        req_id = pick(self.config.id_column, "req_id", "id", "object_id", "absolute_number")
        if not req_id:
            return None

        return Requirement(
            req_id=req_id,
            title=pick("title", "object_text", "name") or "",
            description=pick("description", "object_text", "text") or "",
            signal_name=pick(self.config.signal_column, "signal_name", "signal", "can_signal"),
            port_name=pick(self.config.port_column, "port_name", "port", "autosar_port"),
            message_name=pick("message_name", "message", "pdu"),
            status=pick("status", "state") or "approved",
            attributes={k: v for k, v in row.items() if v is not None},
        )

    def _from_json(self, path: Path) -> list[Requirement]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            rows = data.get("requirements") or data.get("items") or data.get("data") or []
        elif isinstance(data, list):
            rows = data
        else:
            raise ValueError("JSON requirements root must be object or array")

        requirements: list[Requirement] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            req = self._normalize_row(row)
            if req:
                requirements.append(req)
        return requirements

    def _from_csv(self, path: Path, delimiter: str = ",") -> list[Requirement]:
        requirements: list[Requirement] = []
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh, delimiter=delimiter)
            for row in reader:
                req = self._normalize_row(dict(row))
                if req:
                    requirements.append(req)
        return requirements
