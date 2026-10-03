"""ARXML port / interface consistency validation."""

from __future__ import annotations

from auto_validator.config import ArxmlConfig
from auto_validator.models.arxml_models import ArxmlModel, PortDirection
from auto_validator.models.findings import Finding, FindingSeverity
from auto_validator.validators.base import BaseValidator


class ArxmlPortValidator(BaseValidator[ArxmlModel]):
    """Validate port↔interface refs, completeness, and data-type presence."""

    rule_prefix = "ARXML"
    stage_name = "arxml_validation"

    def __init__(self, config: ArxmlConfig | None = None) -> None:
        super().__init__()
        self.config = config or ArxmlConfig()

    def validate(self, target: ArxmlModel) -> list[Finding]:
        if not self.config.enabled:
            return []

        findings: list[Finding] = []
        src = target.source_files[0] if target.source_files else None
        rules = self.config.rules

        if rules.port_consistency:
            findings.extend(self._port_consistency(target, src))
        if rules.interface_completeness:
            findings.extend(self._interface_completeness(target, src))
        if rules.data_type_mapping:
            findings.extend(self._data_type_mapping(target, src))

        return findings

    def _port_consistency(self, model: ArxmlModel, src: str | None) -> list[Finding]:
        findings: list[Finding] = []
        iface_names = {i.name for i in model.interfaces}

        for swc in model.components:
            port_names: set[str] = set()
            for port in swc.ports:
                if port.name in port_names:
                    findings.append(
                        Finding(
                            rule_id="ARXML.PORT.DUPLICATE",
                            severity=FindingSeverity.ERROR,
                            message=f"Duplicate port '{port.name}' on SWC '{swc.name}'",
                            file_path=src,
                            location=f"{swc.name}/{port.name}",
                        )
                    )
                port_names.add(port.name)

                if not port.interface_ref and not port.interface_name:
                    findings.append(
                        Finding(
                            rule_id="ARXML.PORT.MISSING_INTERFACE_REF",
                            severity=FindingSeverity.ERROR,
                            message=f"Port '{swc.name}.{port.name}' has no interface reference",
                            file_path=src,
                            location=f"{swc.name}/{port.name}",
                            suggestion="Add PROVIDED/REQUIRED-INTERFACE-TREF in ARXML.",
                        )
                    )
                elif port.interface_name and port.interface_name not in iface_names:
                    findings.append(
                        Finding(
                            rule_id="ARXML.PORT.UNRESOLVED_INTERFACE",
                            severity=FindingSeverity.ERROR,
                            message=(
                                f"Port '{swc.name}.{port.name}' references unknown "
                                f"interface '{port.interface_name}'"
                            ),
                            file_path=src,
                            location=f"{swc.name}/{port.name}",
                            details={"interface_ref": port.interface_ref},
                            suggestion="Ensure the interface is defined in the ARXML package.",
                        )
                    )

                if port.direction == PortDirection.PROVIDED and not port.interface_ref:
                    # Already covered; keep direction-specific hint
                    pass

        return findings

    def _interface_completeness(self, model: ArxmlModel, src: str | None) -> list[Finding]:
        findings: list[Finding] = []
        for iface in model.interfaces:
            if iface.interface_type == "sender-receiver" and not iface.data_elements:
                findings.append(
                    Finding(
                        rule_id="ARXML.IFACE.EMPTY_SR",
                        severity=FindingSeverity.ERROR,
                        message=f"Sender-receiver interface '{iface.name}' has no data elements",
                        file_path=src,
                        location=iface.name,
                    )
                )
            if iface.interface_type == "client-server" and not iface.operations:
                findings.append(
                    Finding(
                        rule_id="ARXML.IFACE.EMPTY_CS",
                        severity=FindingSeverity.ERROR,
                        message=f"Client-server interface '{iface.name}' has no operations",
                        file_path=src,
                        location=iface.name,
                    )
                )
        return findings

    def _data_type_mapping(self, model: ArxmlModel, src: str | None) -> list[Finding]:
        findings: list[Finding] = []
        known_primitive = {
            "boolean",
            "uint8",
            "uint16",
            "uint32",
            "uint64",
            "sint8",
            "sint16",
            "sint32",
            "sint64",
            "float32",
            "float64",
            "bool",
        }
        for iface in model.interfaces:
            for de in iface.data_elements:
                if not de.data_type:
                    findings.append(
                        Finding(
                            rule_id="ARXML.TYPE.MISSING",
                            severity=FindingSeverity.ERROR,
                            message=(
                                f"Data element '{iface.name}.{de.name}' has no data type"
                            ),
                            file_path=src,
                            location=f"{iface.name}/{de.name}",
                        )
                    )
                elif de.data_type.lower() not in known_primitive:
                    # Custom application types are OK — info only
                    findings.append(
                        Finding(
                            rule_id="ARXML.TYPE.CUSTOM",
                            severity=FindingSeverity.INFO,
                            message=(
                                f"Data element '{iface.name}.{de.name}' uses "
                                f"application type '{de.data_type}'"
                            ),
                            file_path=src,
                            location=f"{iface.name}/{de.name}",
                        )
                    )
        return findings
