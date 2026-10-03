"""Lightweight AUTOSAR ARXML parser (ports, interfaces, SWCs).

Uses lxml for namespace-tolerant XPath over AUTOSAR 4.x schemas.
Does not require EB Tresos — extracts the subset needed for
port consistency checks and RTE/C stub generation.
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from auto_validator.models.arxml_models import (
    ArxmlInterface,
    ArxmlModel,
    ArxmlPort,
    ArxmlSoftwareComponent,
    DataElement,
    Operation,
    OperationArgument,
    PortDirection,
)
from auto_validator.utils.logging import get_logger
from auto_validator.utils.retry import retryable

logger = get_logger("parsers.arxml")

# AUTOSAR namespaces commonly seen in industry exports
_NS_CANDIDATES = (
    "http://autosar.org/schema/r4.0",
    "http://autosar.org/3.0.1",
    "http://autosar.org/schema/r4.2",
)


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _text(el: etree._Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def _child(parent: etree._Element, name: str) -> etree._Element | None:
    for child in parent:
        if _local(child.tag) == name:
            return child
    return None


def _children(parent: etree._Element, name: str) -> list[etree._Element]:
    return [c for c in parent if _local(c.tag) == name]


def _find_descendants(root: etree._Element, name: str) -> list[etree._Element]:
    return [el for el in root.iter() if _local(el.tag) == name]


class ArxmlParser:
    """Parse AUTOSAR ARXML into a normalized ArxmlModel."""

    @retryable(max_attempts=3, backoff_seconds=0.5)
    def parse_file(self, path: Path | str) -> ArxmlModel:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"ARXML file not found: {path}")
        if path.suffix.lower() not in {".arxml", ".xml"}:
            raise ValueError(f"Expected .arxml/.xml file, got: {path}")

        logger.info("Parsing ARXML: %s", path)
        # recover=True tolerates minor XML issues from tool exports
        parser = etree.XMLParser(remove_blank_text=True, recover=True, huge_tree=True)
        tree = etree.parse(str(path), parser)
        root = tree.getroot()
        model = self._extract(root)
        model.source_files = [str(path)]
        return model

    def parse_files(self, paths: list[Path | str]) -> ArxmlModel:
        models = [self.parse_file(p) for p in paths]
        if not models:
            return ArxmlModel()
        merged = models[0]
        for m in models[1:]:
            merged.components.extend(m.components)
            merged.interfaces.extend(m.interfaces)
            merged.source_files.extend(m.source_files)
        return merged

    def _extract(self, root: etree._Element) -> ArxmlModel:
        interfaces = self._extract_interfaces(root)
        components = self._extract_components(root, interfaces)
        return ArxmlModel(components=components, interfaces=interfaces)

    def _extract_interfaces(self, root: etree._Element) -> list[ArxmlInterface]:
        interfaces: list[ArxmlInterface] = []

        for el in _find_descendants(root, "SENDER-RECEIVER-INTERFACE"):
            name = _text(_child(el, "SHORT-NAME"))
            if not name:
                continue
            data_elements: list[DataElement] = []
            de_container = _child(el, "DATA-ELEMENTS")
            if de_container is not None:
                for de in _children(de_container, "VARIABLE-DATA-PROTOTYPE"):
                    de_name = _text(_child(de, "SHORT-NAME"))
                    type_ref = _child(de, "TYPE-TREF")
                    type_name = _text(type_ref)
                    if type_ref is not None and type_name:
                        type_name = type_name.rstrip("/").split("/")[-1]
                    else:
                        type_name = "uint8"
                    init = None
                    init_el = _child(de, "INIT-VALUE")
                    if init_el is not None:
                        num = _find_descendants(init_el, "NUMERICAL-VALUE-SPECIFICATION")
                        if num:
                            init = _text(_child(num[0], "VALUE")) or None
                    data_elements.append(
                        DataElement(name=de_name, data_type=type_name or "uint8", init_value=init)
                    )
            interfaces.append(
                ArxmlInterface(
                    name=name,
                    interface_type="sender-receiver",
                    data_elements=data_elements,
                )
            )

        for el in _find_descendants(root, "CLIENT-SERVER-INTERFACE"):
            name = _text(_child(el, "SHORT-NAME"))
            if not name:
                continue
            operations: list[Operation] = []
            ops = _child(el, "OPERATIONS")
            if ops is not None:
                for op in _children(ops, "CLIENT-SERVER-OPERATION"):
                    op_name = _text(_child(op, "SHORT-NAME"))
                    args: list[OperationArgument] = []
                    args_el = _child(op, "ARGUMENTS")
                    if args_el is not None:
                        for arg in _children(args_el, "ARGUMENT-DATA-PROTOTYPE"):
                            arg_name = _text(_child(arg, "SHORT-NAME"))
                            type_ref = _child(arg, "TYPE-TREF")
                            type_name = (
                                _text(type_ref).rstrip("/").split("/")[-1]
                                if type_ref is not None and _text(type_ref)
                                else "uint8"
                            )
                            direction = _text(_child(arg, "DIRECTION")) or "IN"
                            args.append(
                                OperationArgument(
                                    name=arg_name, data_type=type_name, direction=direction
                                )
                            )
                    operations.append(Operation(name=op_name, arguments=args))
            interfaces.append(
                ArxmlInterface(
                    name=name,
                    interface_type="client-server",
                    operations=operations,
                )
            )

        logger.debug("Extracted %d interfaces", len(interfaces))
        return interfaces

    def _extract_components(
        self, root: etree._Element, interfaces: list[ArxmlInterface]
    ) -> list[ArxmlSoftwareComponent]:
        iface_names = {i.name for i in interfaces}
        components: list[ArxmlSoftwareComponent] = []

        for el in _find_descendants(root, "APPLICATION-SW-COMPONENT-TYPE"):
            name = _text(_child(el, "SHORT-NAME"))
            if not name:
                continue
            ports: list[ArxmlPort] = []
            ports_el = _child(el, "PORTS")
            if ports_el is not None:
                for p_port in _children(ports_el, "P-PORT-PROTOTYPE"):
                    ports.append(self._to_port(p_port, PortDirection.PROVIDED, name, iface_names))
                for r_port in _children(ports_el, "R-PORT-PROTOTYPE"):
                    ports.append(self._to_port(r_port, PortDirection.REQUIRED, name, iface_names))
                for pr_port in _children(ports_el, "PR-PORT-PROTOTYPE"):
                    ports.append(
                        self._to_port(pr_port, PortDirection.PROVIDED_REQUIRED, name, iface_names)
                    )
            components.append(
                ArxmlSoftwareComponent(name=name, ports=[p for p in ports if p.name])
            )

        logger.debug("Extracted %d SWCs", len(components))
        return components

    def _to_port(
        self,
        el: etree._Element,
        direction: PortDirection,
        swc_name: str,
        iface_names: set[str],
    ) -> ArxmlPort:
        name = _text(_child(el, "SHORT-NAME"))
        iface_ref_el = _child(el, "PROVIDED-INTERFACE-TREF")
        if iface_ref_el is None:
            iface_ref_el = _child(el, "REQUIRED-INTERFACE-TREF")
        # PR ports may use either naming convention
        if iface_ref_el is None:
            for child in el:
                if "INTERFACE-TREF" in _local(child.tag):
                    iface_ref_el = child
                    break
        iface_ref = _text(iface_ref_el)
        iface_name = iface_ref.rstrip("/").split("/")[-1] if iface_ref else ""
        return ArxmlPort(
            name=name,
            direction=direction,
            interface_ref=iface_ref,
            interface_name=iface_name if iface_name in iface_names or iface_name else iface_name,
            swc_name=swc_name,
        )
