"""Unit tests for config loading and retry helper."""

from __future__ import annotations

from pathlib import Path

import pytest

from auto_validator.config import load_config
from auto_validator.utils.retry import retryable


@pytest.mark.unit
def test_load_default_config() -> None:
    cfg_path = Path(__file__).resolve().parents[2] / "configs" / "default.yaml"
    cfg = load_config(cfg_path)
    assert cfg.dbc.enabled is True
    assert cfg.arxml.generate_c_stubs is True
    assert cfg.pipeline.max_retries >= 1


@pytest.mark.unit
def test_load_missing_config_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nope.yaml")


@pytest.mark.unit
def test_retry_eventually_succeeds() -> None:
    state = {"n": 0}

    @retryable(max_attempts=3, backoff_seconds=0.01)
    def flaky() -> str:
        state["n"] += 1
        if state["n"] < 3:
            raise OSError("transient")
        return "ok"

    assert flaky() == "ok"
    assert state["n"] == 3


@pytest.mark.unit
@pytest.mark.edge
def test_retry_exhaustion() -> None:
    @retryable(max_attempts=2, backoff_seconds=0.01)
    def always_fail() -> None:
        raise OSError("still broken")

    with pytest.raises(OSError):
        always_fail()
