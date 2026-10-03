"""Unit tests for ARXML parsing and port validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from auto_validator.codegen.c_stubs import CStubGenerator
from auto_validator.codegen.rte_mappings import RteMappingGenerator
from auto_validator.parsers.arxml_parser import ArxmlParser
from auto_validator.validators.arxml.port_consistency import ArxmlPortValidator


@pytest.mark.unit
def test_parse_valid_arxml(valid_arxml: Path, arxml_parser: ArxmlParser) -> None:
    model = arxml_parser.parse_file(valid_arxml)
    assert len(model.components) == 1
    assert model.components[0].name == "Swc_Powertrain"
    assert len(model.components[0].ports) == 3
    assert {i.name for i in model.interfaces} >= {
        "If_EngineSpeed",
        "If_VehicleSpeed",
        "If_DiagService",
    }


@pytest.mark.unit
def test_valid_arxml_passes_validation(valid_arxml: Path, arxml_parser: ArxmlParser) -> None:
    model = arxml_parser.parse_file(valid_arxml)
    result = ArxmlPortValidator().run(model)
    errors = [f for f in result.findings if f.severity.value == "error"]
    assert errors == []
    assert result.passed is True


@pytest.mark.unit
def test_invalid_arxml_flags_unresolved_and_empty(
    invalid_arxml: Path, arxml_parser: ArxmlParser
) -> None:
    model = arxml_parser.parse_file(invalid_arxml)
    result = ArxmlPortValidator().run(model)
    rule_ids = {f.rule_id for f in result.findings}
    assert "ARXML.PORT.UNRESOLVED_INTERFACE" in rule_ids
    assert "ARXML.IFACE.EMPTY_SR" in rule_ids
    assert result.passed is False


@pytest.mark.unit
def test_c_stub_generation(valid_arxml: Path, arxml_parser: ArxmlParser, tmp_path: Path) -> None:
    model = arxml_parser.parse_file(valid_arxml)
    paths = CStubGenerator().generate(model, tmp_path)
    names = {p.name for p in paths}
    assert "Rte_Type.h" in names
    assert "Rte_Swc_Powertrain.h" in names
    content = (tmp_path / "Rte_Swc_Powertrain.h").read_text(encoding="utf-8")
    assert "Rte_Write_Pp_EngineSpeed_EngineSpeed" in content
    assert "Rte_Read_Rp_VehicleSpeed_VehicleSpeed" in content
    assert "Rte_Call_Rp_Diag_GetStatus" in content


@pytest.mark.unit
def test_rte_mapping_generation(
    valid_arxml: Path, arxml_parser: ArxmlParser, tmp_path: Path
) -> None:
    model = arxml_parser.parse_file(valid_arxml)
    paths = RteMappingGenerator().generate(model, tmp_path)
    assert (tmp_path / "rte_interface_map.json").exists()
    assert (tmp_path / "Rte_InterfaceMap.c").exists()
    json_text = paths[0].read_text(encoding="utf-8")
    assert "Pp_EngineSpeed" in json_text
