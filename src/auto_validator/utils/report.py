"""Report writers: console (rich), JSON, JUnit XML."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from rich.console import Console
from rich.table import Table

from auto_validator.config import ReportConfig
from auto_validator.models.findings import FindingSeverity, PipelineReport
from auto_validator.utils.logging import get_logger

logger = get_logger("report")


class ReportWriter:
    """Write pipeline reports in one or more formats."""

    def __init__(self, config: ReportConfig, console: Console | None = None) -> None:
        self.config = config
        self.console = console or Console(stderr=True)

    def write(self, report: PipelineReport) -> dict[str, Path]:
        out_dir = Path(self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        written: dict[str, Path] = {}

        if "console" in self.config.formats:
            self._write_console(report)
        if "json" in self.config.formats:
            path = out_dir / "pipeline_report.json"
            self._write_json(report, path)
            written["json"] = path
        if "junit" in self.config.formats:
            path = out_dir / "pipeline_junit.xml"
            self._write_junit(report, path)
            written["junit"] = path

        logger.info("Reports written: %s", list(written.keys()))
        return written

    def _write_console(self, report: PipelineReport) -> None:
        summary = report.to_summary()
        status = "[green]PASSED[/green]" if report.overall_passed else "[red]FAILED[/red]"
        self.console.print(f"\n[bold]Pipeline Result:[/bold] {status}")
        self.console.print(
            f"Errors: {summary['errors']}  Warnings: {summary['warnings']}  "
            f"Stages: {summary['stages']}"
        )

        table = Table(title="Findings", show_lines=False)
        table.add_column("Severity", style="bold")
        table.add_column("Rule")
        table.add_column("Location")
        table.add_column("Message")

        severity_style = {
            FindingSeverity.ERROR: "red",
            FindingSeverity.WARNING: "yellow",
            FindingSeverity.INFO: "cyan",
        }
        for finding in report.all_findings:
            table.add_row(
                f"[{severity_style[finding.severity]}]{finding.severity.value}[/]",
                finding.rule_id,
                finding.location or finding.file_path or "-",
                finding.message,
            )
        if report.all_findings:
            self.console.print(table)
        else:
            self.console.print("[green]No findings.[/green]")

    def _write_json(self, report: PipelineReport, path: Path) -> None:
        path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    def _write_junit(self, report: PipelineReport, path: Path) -> None:
        testsuites = ET.Element("testsuites")
        testsuites.set("tests", str(len(report.results)))
        testsuites.set("failures", str(sum(1 for r in report.results if not r.passed)))
        testsuites.set("errors", str(report.total_errors))

        for result in report.results:
            suite = ET.SubElement(testsuites, "testsuite")
            suite.set("name", result.stage)
            suite.set("tests", "1")
            suite.set("failures", "0" if result.passed else "1")
            suite.set("time", f"{result.duration_ms / 1000:.3f}")

            case = ET.SubElement(suite, "testcase")
            case.set("classname", "auto_validator")
            case.set("name", result.stage)
            case.set("time", f"{result.duration_ms / 1000:.3f}")

            if not result.passed:
                failure = ET.SubElement(case, "failure")
                failure.set("message", f"{result.error_count} error(s)")
                failure.text = "\n".join(
                    f"[{f.severity.value}] {f.rule_id}: {f.message}"
                    for f in result.findings
                    if f.severity == FindingSeverity.ERROR
                )

        tree = ET.ElementTree(testsuites)
        ET.indent(tree, space="  ")
        tree.write(path, encoding="utf-8", xml_declaration=True)
