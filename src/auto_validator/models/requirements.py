"""DOORS / requirements traceability models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """Single requirement from DOORS CSV/JSON export."""

    req_id: str
    title: str = ""
    description: str = ""
    signal_name: str | None = None
    port_name: str | None = None
    message_name: str | None = None
    status: str = "approved"
    attributes: dict[str, Any] = Field(default_factory=dict)


class RequirementsCatalog(BaseModel):
    """Collection of requirements loaded from export files."""

    source_files: list[str] = Field(default_factory=list)
    requirements: list[Requirement] = Field(default_factory=list)

    def by_signal(self, signal_name: str) -> list[Requirement]:
        key = signal_name.lower()
        return [r for r in self.requirements if r.signal_name and r.signal_name.lower() == key]

    def by_port(self, port_name: str) -> list[Requirement]:
        key = port_name.lower()
        return [r for r in self.requirements if r.port_name and r.port_name.lower() == key]

    def signal_names(self) -> set[str]:
        return {r.signal_name for r in self.requirements if r.signal_name}

    def port_names(self) -> set[str]:
        return {r.port_name for r in self.requirements if r.port_name}
