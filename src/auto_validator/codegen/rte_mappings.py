"""Generate RTE interface mapping tables (JSON + C) from ARXML."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from auto_validator.models.arxml_models import ArxmlModel
from auto_validator.utils.logging import get_logger

logger = get_logger("codegen.rte_mappings")


class RteMappingGenerator:
    """Emit machine-readable RTE port↔interface mappings."""

    def generate(self, model: ArxmlModel, output_dir: Path | str) -> list[Path]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        mapping = self._build_mapping(model)
        json_path = output_dir / "rte_interface_map.json"
        json_path.write_text(json.dumps(mapping, indent=2), encoding="utf-8")

        c_path = output_dir / "Rte_InterfaceMap.c"
        c_path.write_text(self._render_c(mapping), encoding="utf-8")

        logger.info("Generated RTE mappings: %s, %s", json_path, c_path)
        return [json_path, c_path]

    def _build_mapping(self, model: ArxmlModel) -> dict[str, Any]:
        ports: list[dict[str, Any]] = []
        for swc in model.components:
            for port in swc.ports:
                iface = model.interface_by_name(port.interface_name) or model.interface_by_ref(
                    port.interface_ref
                )
                entry: dict[str, Any] = {
                    "swc": swc.name,
                    "port": port.name,
                    "direction": port.direction.value,
                    "interface": port.interface_name,
                    "interface_ref": port.interface_ref,
                    "interface_type": iface.interface_type if iface else None,
                    "data_elements": (
                        [{"name": d.name, "type": d.data_type} for d in iface.data_elements]
                        if iface
                        else []
                    ),
                    "operations": (
                        [op.name for op in iface.operations] if iface else []
                    ),
                }
                ports.append(entry)

        return {
            "version": "1.0",
            "generator": "auto-validator",
            "source_files": model.source_files,
            "ports": ports,
            "interface_count": len(model.interfaces),
            "component_count": len(model.components),
        }

    def _render_c(self, mapping: dict[str, Any]) -> str:
        lines = [
            "/**",
            " * @file Rte_InterfaceMap.c",
            " * @brief Auto-generated RTE interface mapping table — DO NOT EDIT",
            " */",
            "",
            "#include <stddef.h>",
            "",
            "typedef struct {",
            "    const char *swc;",
            "    const char *port;",
            "    const char *direction;",
            "    const char *interface_name;",
            "} Rte_PortMapEntry;",
            "",
            "const Rte_PortMapEntry Rte_PortMap[] = {",
        ]
        for p in mapping["ports"]:
            lines.append(
                f'    {{ "{p["swc"]}", "{p["port"]}", "{p["direction"]}", '
                f'"{p["interface"]}" }},'
            )
        lines.extend(
            [
                "};",
                "",
                f"const size_t Rte_PortMap_Size = {len(mapping['ports'])};",
                "",
            ]
        )
        return "\n".join(lines)
