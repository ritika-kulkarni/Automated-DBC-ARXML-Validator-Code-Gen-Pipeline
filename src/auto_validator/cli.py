"""CLI entrypoints: validate, codegen, hook-check."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from auto_validator import __version__
from auto_validator.config import load_config
from auto_validator.pipeline.orchestrator import PipelineOrchestrator
from auto_validator.utils.logging import setup_logging


def _split_paths(values: tuple[str, ...]) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part:
                paths.append(Path(part))
    return paths


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="auto-validator")
def main() -> None:
    """Automated DBC/ARXML Validator & Code-Gen Pipeline."""


@main.command("validate")
@click.option(
    "--dbc",
    "dbc_files",
    multiple=True,
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    help="DBC file(s). Repeat or comma-separate.",
)
@click.option(
    "--arxml",
    "arxml_files",
    multiple=True,
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    help="ARXML file(s). Repeat or comma-separate.",
)
@click.option(
    "--requirements",
    "req_files",
    multiple=True,
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    help="DOORS CSV/JSON export(s).",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    default=None,
    help="YAML config (defaults to configs/default.yaml).",
)
@click.option("--skip-codegen", is_flag=True, help="Skip C stub / RTE generation.")
@click.option(
    "--expected-cycles",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    default=None,
    help="JSON map of message_name → cycle_time_ms for mismatch checks.",
)
@click.option("--quiet", is_flag=True, help="Suppress non-error console noise.")
def validate_cmd(
    dbc_files: tuple[str, ...],
    arxml_files: tuple[str, ...],
    req_files: tuple[str, ...],
    config_path: str | None,
    skip_codegen: bool,
    expected_cycles: str | None,
    quiet: bool,
) -> None:
    """Run DBC/ARXML validation, requirements match, and optional codegen."""
    if not dbc_files and not arxml_files:
        raise click.UsageError("Provide at least one --dbc or --arxml input.")

    config = load_config(config_path)
    if quiet:
        config.logging.level = "ERROR"
    setup_logging(config.logging)

    cycles: dict[str, int] | None = None
    if expected_cycles:
        cycles = json.loads(Path(expected_cycles).read_text(encoding="utf-8"))

    orchestrator = PipelineOrchestrator(config)
    report = orchestrator.run(
        dbc_files=_split_paths(dbc_files),
        arxml_files=_split_paths(arxml_files),
        requirements_files=_split_paths(req_files),
        expected_cycle_times=cycles,
        skip_codegen=skip_codegen,
    )

    sys.exit(0 if report.overall_passed else 1)


@main.command("codegen")
@click.option(
    "--arxml",
    "arxml_files",
    multiple=True,
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=str),
)
@click.option(
    "--output",
    "output_dir",
    type=click.Path(file_okay=False, path_type=str),
    default="output/codegen",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    default=None,
)
def codegen_cmd(
    arxml_files: tuple[str, ...],
    output_dir: str,
    config_path: str | None,
) -> None:
    """Generate C stubs and RTE mappings from ARXML only (no DBC checks)."""
    config = load_config(config_path)
    config.dbc.enabled = False
    config.requirements.enabled = False
    config.arxml.output_dir = output_dir
    # Allow codegen even if validation finds issues — user asked for codegen
    setup_logging(config.logging)

    orch = PipelineOrchestrator(config)
    report = orch.run(arxml_files=_split_paths(arxml_files), skip_codegen=False)
    # For pure codegen, still exit non-zero on ARXML errors
    sys.exit(0 if report.overall_passed else 1)


@main.command("hook-check")
@click.argument("files", nargs=-1, type=click.Path(exists=True, dir_okay=False, path_type=str))
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    default=None,
)
def hook_check_cmd(files: tuple[str, ...], config_path: str | None) -> None:
    """
    Git pre-commit / CI helper: classify staged files and validate accordingly.

    Accepts a list of paths (as passed by pre-commit). Non-DBC/ARXML files are ignored.
    """
    dbc = [f for f in files if f.lower().endswith(".dbc")]
    arxml = [f for f in files if f.lower().endswith(".arxml")]
    reqs = [
        f
        for f in files
        if f.lower().endswith((".csv", ".json"))
        and ("door" in f.lower() or "req" in f.lower())
    ]

    if not dbc and not arxml:
        click.echo("No DBC/ARXML files in change set — skipping.")
        sys.exit(0)

    config = load_config(config_path)
    orch = PipelineOrchestrator(config)
    report = orch.run(
        dbc_files=dbc or None,
        arxml_files=arxml or None,
        requirements_files=reqs or None,
        skip_codegen=True,  # hooks: validate only; codegen in CI job
    )
    sys.exit(0 if report.overall_passed else 1)


if __name__ == "__main__":
    main()
