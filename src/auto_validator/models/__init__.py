"""Domain models for validation findings and automotive artifacts."""

from auto_validator.models.arxml_models import (
    ArxmlInterface,
    ArxmlPort,
    ArxmlSoftwareComponent,
)
from auto_validator.models.can_models import CanMessage, CanNetwork, CanSignal
from auto_validator.models.findings import (
    Finding,
    FindingSeverity,
    PipelineReport,
    ValidationResult,
)
from auto_validator.models.requirements import Requirement, RequirementsCatalog

__all__ = [
    "ArxmlInterface",
    "ArxmlPort",
    "ArxmlSoftwareComponent",
    "CanMessage",
    "CanNetwork",
    "CanSignal",
    "Finding",
    "FindingSeverity",
    "PipelineReport",
    "Requirement",
    "RequirementsCatalog",
    "ValidationResult",
]
