"""Shared core for Agreement Intelligence.

Plain Python with no framework coupling, so the same code runs in a
Databricks pandas UDF and in the FastAPI worker.
"""

from contract_core.schema import (
    Agreement,
    Evidence,
    Extracted,
    LiabilityCap,
    Party,
    Signatory,
    SignatureType,
)
from contract_core.validation import ValidationIssue, validate_agreement
from contract_core.versions import SCHEMA_VERSION

__all__ = [
    "Agreement",
    "Evidence",
    "Extracted",
    "LiabilityCap",
    "Party",
    "Signatory",
    "SignatureType",
    "ValidationIssue",
    "validate_agreement",
    "SCHEMA_VERSION",
]
