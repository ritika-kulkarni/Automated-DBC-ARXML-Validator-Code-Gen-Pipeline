"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from auto_validator.config import AppConfig, load_config
from auto_validator.parsers.arxml_parser import ArxmlParser
from auto_validator.parsers.dbc_parser import DbcParser
from auto_validator.parsers.doors_parser import DoorsParser

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def valid_dbc(fixtures_dir: Path) -> Path:
    return fixtures_dir / "dbc" / "valid_can.dbc"


@pytest.fixture
def overlap_dbc(fixtures_dir: Path) -> Path:
    return fixtures_dir / "dbc" / "invalid_overlap.dbc"


@pytest.fixture
def j1939_dbc(fixtures_dir: Path) -> Path:
    return fixtures_dir / "dbc" / "j1939_sample.dbc"


@pytest.fixture
def can_fd_dbc(fixtures_dir: Path) -> Path:
    return fixtures_dir / "dbc" / "can_fd_invalid.dbc"


@pytest.fixture
def valid_arxml(fixtures_dir: Path) -> Path:
    return fixtures_dir / "arxml" / "valid_swc.arxml"


@pytest.fixture
def invalid_arxml(fixtures_dir: Path) -> Path:
    return fixtures_dir / "arxml" / "invalid_ports.arxml"


@pytest.fixture
def doors_csv(fixtures_dir: Path) -> Path:
    return fixtures_dir / "doors" / "requirements.csv"


@pytest.fixture
def doors_json(fixtures_dir: Path) -> Path:
    return fixtures_dir / "doors" / "requirements.json"


@pytest.fixture
def app_config() -> AppConfig:
    default = Path(__file__).resolve().parents[1] / "configs" / "default.yaml"
    return load_config(default)


@pytest.fixture
def dbc_parser() -> DbcParser:
    return DbcParser()


@pytest.fixture
def arxml_parser() -> ArxmlParser:
    return ArxmlParser()


@pytest.fixture
def doors_parser() -> DoorsParser:
    return DoorsParser()
