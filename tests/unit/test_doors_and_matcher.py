"""Unit tests for DOORS parsing and requirements matching."""

from __future__ import annotations

from pathlib import Path

import pytest

from auto_validator.config import RequirementsConfig
from auto_validator.models.arxml_models import (
    ArxmlInterface,
    ArxmlModel,
    ArxmlPort,
    ArxmlSoftwareComponent,
    PortDirection,
)
from auto_validator.models.can_models import ByteOrder, CanMessage, CanNetwork, CanSignal
from auto_validator.parsers.doors_parser import DoorsParser
from auto_validator.requirements.matcher import RequirementsMatchTarget, RequirementsMatcher


@pytest.mark.unit
def test_parse_doors_csv(doors_csv: Path, doors_parser: DoorsParser) -> None:
    catalog = doors_parser.parse_file(doors_csv)
    assert len(catalog.requirements) >= 5
    assert "EngineSpeed" in catalog.signal_names()
    assert "Pp_EngineSpeed" in catalog.port_names()


@pytest.mark.unit
def test_parse_doors_json(doors_json: Path, doors_parser: DoorsParser) -> None:
    catalog = doors_parser.parse_file(doors_json)
    assert any(r.req_id == "REQ-100" for r in catalog.requirements)


@pytest.mark.unit
def test_matcher_flags_missing_signal(doors_json: Path, doors_parser: DoorsParser) -> None:
    catalog = doors_parser.parse_file(doors_json)
    network = CanNetwork(
        messages=[
            CanMessage(
                name="M",
                frame_id=1,
                length=8,
                signals=[
                    CanSignal(
                        name="EngineSpeed",
                        start_bit=0,
                        length=16,
                        byte_order=ByteOrder.LITTLE_ENDIAN,
                    )
                ],
            )
        ]
    )
    result = RequirementsMatcher().run(
        RequirementsMatchTarget(catalog=catalog, network=network)
    )
    assert any(f.rule_id == "REQ.SIGNAL.MISSING_IN_DBC" for f in result.findings)


@pytest.mark.unit
def test_matcher_flags_missing_port() -> None:
    from auto_validator.models.requirements import Requirement, RequirementsCatalog

    cat = RequirementsCatalog(
        requirements=[Requirement(req_id="R1", port_name="GhostPort")]
    )
    arxml = ArxmlModel(
        components=[
            ArxmlSoftwareComponent(
                name="Swc",
                ports=[
                    ArxmlPort(
                        name="RealPort",
                        direction=PortDirection.PROVIDED,
                        interface_ref="/I/If",
                        interface_name="If",
                        swc_name="Swc",
                    )
                ],
            )
        ],
        interfaces=[ArxmlInterface(name="If", interface_type="sender-receiver")],
    )
    result = RequirementsMatcher(RequirementsConfig(match_mode="strict")).run(
        RequirementsMatchTarget(catalog=cat, arxml=arxml)
    )
    assert any(f.rule_id == "REQ.PORT.MISSING_IN_ARXML" for f in result.findings)


@pytest.mark.unit
@pytest.mark.edge
def test_matcher_disabled_returns_empty() -> None:
    from auto_validator.models.requirements import RequirementsCatalog

    result = RequirementsMatcher(RequirementsConfig(enabled=False)).run(
        RequirementsMatchTarget(catalog=RequirementsCatalog())
    )
    assert result.findings == []
    assert result.passed is True
