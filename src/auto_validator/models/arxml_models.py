"""AUTOSAR ARXML domain models (ports, interfaces, SWCs)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PortDirection(str, Enum):
    PROVIDED = "provided"  # P-Port
    REQUIRED = "required"  # R-Port
    PROVIDED_REQUIRED = "provided_required"


class DataElement(BaseModel):
    """Sender-receiver interface data element."""

    name: str
    data_type: str
    is_queued: bool = False
    init_value: str | None = None


class OperationArgument(BaseModel):
    name: str
    data_type: str
    direction: str = "IN"  # IN | OUT | INOUT


class Operation(BaseModel):
    name: str
    arguments: list[OperationArgument] = Field(default_factory=list)


class ArxmlInterface(BaseModel):
    """AUTOSAR port interface (S/R or C/S)."""

    name: str
    interface_type: str  # sender-receiver | client-server
    data_elements: list[DataElement] = Field(default_factory=list)
    operations: list[Operation] = Field(default_factory=list)
    package_path: str = ""


class ArxmlPort(BaseModel):
    """SWC port prototype referencing an interface."""

    name: str
    direction: PortDirection
    interface_ref: str
    interface_name: str = ""
    swc_name: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)


class ArxmlSoftwareComponent(BaseModel):
    """Application software component type."""

    name: str
    component_type: str = "APPLICATION"
    ports: list[ArxmlPort] = Field(default_factory=list)
    package_path: str = ""

    def port_by_name(self, name: str) -> ArxmlPort | None:
        return next((p for p in self.ports if p.name == name), None)


class ArxmlModel(BaseModel):
    """Normalized ARXML model for validation and codegen."""

    source_files: list[str] = Field(default_factory=list)
    components: list[ArxmlSoftwareComponent] = Field(default_factory=list)
    interfaces: list[ArxmlInterface] = Field(default_factory=list)

    def interface_by_name(self, name: str) -> ArxmlInterface | None:
        return next((i for i in self.interfaces if i.name == name), None)

    def interface_by_ref(self, ref: str) -> ArxmlInterface | None:
        short = ref.rstrip("/").split("/")[-1]
        return self.interface_by_name(short)

    def all_ports(self) -> list[ArxmlPort]:
        return [p for c in self.components for p in c.ports]
