"""Integration tests for the full pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from auto_validator.cli import main
from auto_validator.config import AppConfig
from auto_validator.pipeline.orchestrator import PipelineOrchestrator


@pytest.mark.integration
def test_pipeline_valid_end_to_end(
    valid_dbc: Path,
    valid_arxml: Path,
    doors_csv: Path,
    tmp_path: Path,
    app_config: AppConfig,
) -> None:
    app_config.arxml.output_dir = str(tmp_path / "codegen")
    app_config.report.output_dir = str(tmp_path / "reports")
    # valid_can.dbc has signals not all in CSV as untraced warnings — fail only on error
    app_config.pipeline.fail_on_severity = "error"
    app_config.requirements.match_mode = "strict"

    orch = PipelineOrchestrator(app_config)
    report = orch.run(
        dbc_files=[valid_dbc],
        arxml_files=[valid_arxml],
        requirements_files=[doors_csv],
    )

    assert report.total_errors == 0
    assert report.overall_passed is True
    assert (tmp_path / "codegen" / "Rte_Swc_Powertrain.h").exists()
    assert (tmp_path / "reports" / "pipeline_report.json").exists()
    assert (tmp_path / "reports" / "pipeline_junit.xml").exists()


@pytest.mark.integration
def test_pipeline_fails_on_overlap(
    overlap_dbc: Path, tmp_path: Path, app_config: AppConfig
) -> None:
    app_config.arxml.enabled = False
    app_config.requirements.enabled = False
    app_config.report.output_dir = str(tmp_path / "reports")

    report = PipelineOrchestrator(app_config).run(dbc_files=[overlap_dbc], skip_codegen=True)
    assert report.overall_passed is False
    assert any("OVERLAP" in f.rule_id for f in report.all_findings)


@pytest.mark.integration
def test_pipeline_fails_on_bad_arxml(
    invalid_arxml: Path, tmp_path: Path, app_config: AppConfig
) -> None:
    app_config.dbc.enabled = False
    app_config.requirements.enabled = False
    app_config.arxml.output_dir = str(tmp_path / "codegen")
    app_config.report.output_dir = str(tmp_path / "reports")

    report = PipelineOrchestrator(app_config).run(arxml_files=[invalid_arxml])
    assert report.overall_passed is False
    # Codegen should be skipped when ARXML has errors
    assert not (tmp_path / "codegen").exists() or not list((tmp_path / "codegen").glob("*.h"))


@pytest.mark.integration
def test_cli_validate_valid(
    valid_dbc: Path, valid_arxml: Path, doors_csv: Path, tmp_path: Path
) -> None:
    runner = CliRunner()
    config = tmp_path / "cfg.yaml"
    config.write_text(
        f"""
pipeline:
  fail_on_severity: error
dbc:
  enabled: true
arxml:
  enabled: true
  output_dir: {tmp_path / "codegen"}
requirements:
  enabled: true
  match_mode: strict
report:
  formats: [json]
  output_dir: {tmp_path / "reports"}
""",
        encoding="utf-8",
    )
    result = runner.invoke(
        main,
        [
            "validate",
            "--dbc",
            str(valid_dbc),
            "--arxml",
            str(valid_arxml),
            "--requirements",
            str(doors_csv),
            "--config",
            str(config),
            "--quiet",
        ],
    )
    assert result.exit_code == 0, result.output


@pytest.mark.integration
def test_cli_hook_check_skips_unrelated(tmp_path: Path) -> None:
    runner = CliRunner()
    dummy = tmp_path / "readme.md"
    dummy.write_text("hi", encoding="utf-8")
    result = runner.invoke(main, ["hook-check", str(dummy)])
    assert result.exit_code == 0
    assert "skipping" in result.output.lower()


@pytest.mark.integration
@pytest.mark.edge
def test_expected_cycle_times(
    valid_dbc: Path, fixtures_dir: Path, tmp_path: Path, app_config: AppConfig
) -> None:
    app_config.arxml.enabled = False
    app_config.requirements.enabled = False
    app_config.report.output_dir = str(tmp_path / "reports")
    cycles = json.loads(
        (fixtures_dir / "doors" / "expected_cycles.json").read_text(encoding="utf-8")
    )
    # Mutate expected to force mismatch
    cycles["EngineData"] = 999
    report = PipelineOrchestrator(app_config).run(
        dbc_files=[valid_dbc], expected_cycle_times=cycles, skip_codegen=True
    )
    assert any(f.rule_id == "DBC.CYCLE.MISMATCH" for f in report.all_findings)


@pytest.mark.integration
@pytest.mark.edge
def test_can_fd_invalid_fixture(can_fd_dbc: Path, tmp_path: Path, app_config: AppConfig) -> None:
    app_config.arxml.enabled = False
    app_config.requirements.enabled = False
    app_config.report.output_dir = str(tmp_path / "reports")
    # Missing init may also fire depending on parse — focus on CAN-FD
    report = PipelineOrchestrator(app_config).run(dbc_files=[can_fd_dbc], skip_codegen=True)
    assert any("CANFD" in f.rule_id or "CAN." in f.rule_id for f in report.all_findings)
