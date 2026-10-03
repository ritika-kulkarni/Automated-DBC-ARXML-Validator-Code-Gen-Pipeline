"""Match ARXML ports / DBC signals against DOORS requirement exports."""

from __future__ import annotations

import difflib

from auto_validator.config import RequirementsConfig
from auto_validator.models.arxml_models import ArxmlModel
from auto_validator.models.can_models import CanNetwork
from auto_validator.models.findings import Finding, FindingSeverity
from auto_validator.models.requirements import RequirementsCatalog
from auto_validator.validators.base import BaseValidator


class RequirementsMatchTarget:
    """Bundle of artifacts to match against requirements."""

    def __init__(
        self,
        catalog: RequirementsCatalog,
        network: CanNetwork | None = None,
        arxml: ArxmlModel | None = None,
    ) -> None:
        self.catalog = catalog
        self.network = network
        self.arxml = arxml


class RequirementsMatcher(BaseValidator[RequirementsMatchTarget]):
    """Compare DOORS signal/port names against DBC and ARXML."""

    rule_prefix = "REQ"
    stage_name = "requirements_match"

    def __init__(self, config: RequirementsConfig | None = None) -> None:
        super().__init__()
        self.config = config or RequirementsConfig()

    def validate(self, target: RequirementsMatchTarget) -> list[Finding]:
        if not self.config.enabled:
            return []

        findings: list[Finding] = []
        if target.network is not None:
            findings.extend(self._match_signals(target))
        if target.arxml is not None:
            findings.extend(self._match_ports(target))
        return findings

    def _match_signals(self, target: RequirementsMatchTarget) -> list[Finding]:
        findings: list[Finding] = []
        assert target.network is not None
        dbc_signals = {
            sig.name for msg in target.network.messages for sig in msg.signals
        }
        req_signals = target.catalog.signal_names()

        for sig in sorted(req_signals):
            if sig not in dbc_signals:
                suggestion = self._suggest(sig, dbc_signals)
                findings.append(
                    Finding(
                        rule_id="REQ.SIGNAL.MISSING_IN_DBC",
                        severity=FindingSeverity.ERROR,
                        message=f"DOORS signal '{sig}' not found in DBC",
                        location=sig,
                        suggestion=suggestion,
                    )
                )

        # Orphan DBC signals that have req coverage expectations
        covered = req_signals
        if self.config.match_mode == "strict" and covered:
            for sig in sorted(dbc_signals - covered):
                findings.append(
                    Finding(
                        rule_id="REQ.SIGNAL.UNTRACED",
                        severity=FindingSeverity.WARNING,
                        message=f"DBC signal '{sig}' has no DOORS requirement trace",
                        location=sig,
                        suggestion="Add a DOORS requirement mapping or exclude from matrix.",
                    )
                )
        return findings

    def _match_ports(self, target: RequirementsMatchTarget) -> list[Finding]:
        findings: list[Finding] = []
        assert target.arxml is not None
        arxml_ports = {p.name for p in target.arxml.all_ports()}
        req_ports = target.catalog.port_names()

        for port in sorted(req_ports):
            if port not in arxml_ports:
                suggestion = self._suggest(port, arxml_ports)
                findings.append(
                    Finding(
                        rule_id="REQ.PORT.MISSING_IN_ARXML",
                        severity=FindingSeverity.ERROR,
                        message=f"DOORS port '{port}' not found in ARXML",
                        location=port,
                        suggestion=suggestion,
                    )
                )

        if self.config.match_mode == "strict" and req_ports:
            for port in sorted(arxml_ports - req_ports):
                findings.append(
                    Finding(
                        rule_id="REQ.PORT.UNTRACED",
                        severity=FindingSeverity.WARNING,
                        message=f"ARXML port '{port}' has no DOORS requirement trace",
                        location=port,
                    )
                )
        return findings

    def _suggest(self, name: str, candidates: set[str]) -> str | None:
        if self.config.match_mode != "fuzzy" and not candidates:
            return None
        matches = difflib.get_close_matches(
            name, list(candidates), n=3, cutoff=self.config.fuzzy_threshold
        )
        if matches:
            return f"Did you mean: {', '.join(matches)}?"
        # Also suggest under looser cutoff for helpfulness
        loose = difflib.get_close_matches(name, list(candidates), n=3, cutoff=0.6)
        if loose:
            return f"Closest matches: {', '.join(loose)}"
        return None
