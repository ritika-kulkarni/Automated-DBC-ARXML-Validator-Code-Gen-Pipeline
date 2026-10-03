"""End-to-end pipeline orchestrator (Facade over parsers/validators/codegen)."""

from __future__ import annotations

import time
from pathlib import Path

from auto_validator.codegen.c_stubs import CStubGenerator
from auto_validator.codegen.rte_mappings import RteMappingGenerator
from auto_validator.config import AppConfig, load_config
from auto_validator.models.findings import (
    Finding,
    FindingSeverity,
    PipelineReport,
    ValidationResult,
)
from auto_validator.parsers.arxml_parser import ArxmlParser
from auto_validator.parsers.dbc_parser import DbcParser
from auto_validator.parsers.doors_parser import DoorsParser
from auto_validator.requirements.matcher import RequirementsMatchTarget, RequirementsMatcher
from auto_validator.utils.logging import get_logger, setup_logging
from auto_validator.utils.report import ReportWriter
from auto_validator.validators.arxml.port_consistency import ArxmlPortValidator
from auto_validator.validators.dbc.engine import DbcValidationEngine

logger = get_logger("pipeline")


class PipelineOrchestrator:
    """
    Runs the full automation workflow:

    1. Parse DBC / ARXML / DOORS inputs
    2. Validate DBC rules (overlap, endianness, init, cycle, J1939, CAN-FD)
    3. Validate ARXML port/interface consistency
    4. Match against DOORS requirements
    5. Generate C stubs + RTE mappings (if enabled and prior stages allow)
    6. Emit reports
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()
        setup_logging(self.config.logging)
        self.dbc_parser = DbcParser()
        self.arxml_parser = ArxmlParser()
        self.doors_parser = DoorsParser(self.config.requirements)
        self.dbc_engine = DbcValidationEngine(self.config.dbc)
        self.arxml_validator = ArxmlPortValidator(self.config.arxml)
        self.req_matcher = RequirementsMatcher(self.config.requirements)
        self.c_stub_gen = CStubGenerator()
        self.rte_gen = RteMappingGenerator()
        self.report_writer = ReportWriter(self.config.report)

    def run(
        self,
        *,
        dbc_files: list[Path | str] | None = None,
        arxml_files: list[Path | str] | None = None,
        requirements_files: list[Path | str] | None = None,
        expected_cycle_times: dict[str, int] | None = None,
        skip_codegen: bool = False,
    ) -> PipelineReport:
        report = PipelineReport(
            metadata={
                "dbc_files": [str(p) for p in (dbc_files or [])],
                "arxml_files": [str(p) for p in (arxml_files or [])],
                "requirements_files": [str(p) for p in (requirements_files or [])],
            }
        )

        if expected_cycle_times:
            self.dbc_engine.expected_cycle_times = expected_cycle_times

        network = None
        arxml_model = None
        catalog = None

        # --- Parse + validate DBC ---
        if dbc_files and self.config.dbc.enabled:
            try:
                network = self.dbc_parser.parse_files(list(dbc_files))
                result = self.dbc_engine.run(network)
                report.add_result(result)
            except Exception as exc:  # noqa: BLE001
                logger.exception("DBC stage failed")
                report.add_result(self._fatal("dbc_parse", str(exc)))

        # --- Parse + validate ARXML ---
        if arxml_files and self.config.arxml.enabled:
            try:
                arxml_model = self.arxml_parser.parse_files(list(arxml_files))
                result = self.arxml_validator.run(arxml_model)
                report.add_result(result)
            except Exception as exc:  # noqa: BLE001
                logger.exception("ARXML stage failed")
                report.add_result(self._fatal("arxml_parse", str(exc)))

        # --- Requirements matching ---
        if requirements_files and self.config.requirements.enabled:
            try:
                catalog = self.doors_parser.parse_files(list(requirements_files))
                match_target = RequirementsMatchTarget(
                    catalog=catalog, network=network, arxml=arxml_model
                )
                result = self.req_matcher.run(match_target)
                report.add_result(result)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Requirements stage failed")
                report.add_result(self._fatal("requirements_parse", str(exc)))

        # --- Codegen (only if ARXML available and no blocking errors when fail_on=error) ---
        if (
            not skip_codegen
            and arxml_model is not None
            and self.config.arxml.enabled
            and self._codegen_allowed(report)
        ):
            report.add_result(self._run_codegen(arxml_model))

        # Apply fail-on-severity threshold to overall_passed
        threshold = FindingSeverity(self.config.pipeline.fail_on_severity)
        if any(f.exceeds(threshold) for f in report.all_findings):
            report.overall_passed = False

        report.finalize()
        self.report_writer.write(report)
        return report

    def _codegen_allowed(self, report: PipelineReport) -> bool:
        # Block codegen when ARXML validation had errors
        for result in report.results:
            if result.stage == "arxml_validation" and result.error_count > 0:
                logger.warning("Skipping codegen due to ARXML validation errors")
                return False
        return True

    def _run_codegen(self, arxml_model: object) -> ValidationResult:
        from auto_validator.models.arxml_models import ArxmlModel

        assert isinstance(arxml_model, ArxmlModel)
        start = time.perf_counter()
        result = ValidationResult(stage="codegen", passed=True)
        out = Path(self.config.arxml.output_dir)
        artifacts: dict[str, str] = {}

        try:
            if self.config.arxml.generate_c_stubs:
                paths = self.c_stub_gen.generate(arxml_model, out)
                for p in paths:
                    artifacts[p.name] = str(p)
            if self.config.arxml.generate_rte_mappings:
                paths = self.rte_gen.generate(arxml_model, out)
                for p in paths:
                    artifacts[p.name] = str(p)
            result.artifacts = artifacts
            result.add(
                Finding(
                    rule_id="CODEGEN.OK",
                    severity=FindingSeverity.INFO,
                    message=f"Generated {len(artifacts)} artifact(s) under {out}",
                    details=artifacts,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Codegen failed")
            result.add(
                Finding(
                    rule_id="CODEGEN.FAIL",
                    severity=FindingSeverity.ERROR,
                    message=f"Code generation failed: {exc}",
                )
            )
        result.duration_ms = (time.perf_counter() - start) * 1000
        return result

    @staticmethod
    def _fatal(stage: str, message: str) -> ValidationResult:
        result = ValidationResult(stage=stage, passed=False)
        result.add(
            Finding(
                rule_id="PIPELINE.FATAL",
                severity=FindingSeverity.ERROR,
                message=message,
            )
        )
        return result
