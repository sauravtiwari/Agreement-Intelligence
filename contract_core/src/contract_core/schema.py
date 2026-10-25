"""Pydantic schema for structured agreement extraction.

Every extracted field carries its value plus the verbatim source quote and
page it came from, so the UI can show evidence and highlight the PDF.
"""

from datetime import date
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Evidence(BaseModel):
    quote: str = Field(description="Verbatim text from the contract that supports the value.")
    page: int = Field(ge=1, description="1-based page number where the quote appears.")


class Extracted(BaseModel, Generic[T]):
    value: T | None = Field(default=None, description="The extracted value, or null if the contract does not state it.")
    evidence: Evidence | None = Field(default=None, description="Source quote and page; required whenever value is not null.")
    confidence: float | None = Field(default=None, ge=0, le=1, description="Model confidence from 0 to 1.")


class Party(BaseModel):
    name: str = Field(description="Legal name of the party as written in the contract.")
    role: str | None = Field(default=None, description="Role in the contract, e.g. 'Licensor', 'Customer', 'Supplier'.")
    evidence: Evidence | None = None


class SignatureType(str, Enum):
    digital = "digital"
    wet_ink = "wet_ink"
    typed = "typed"
    none = "none"
    unknown = "unknown"


class Signatory(BaseModel):
    party_name: str = Field(description="Name of the party this signature block belongs to.")
    signer_name: str | None = None
    signer_title: str | None = None
    signed_date: date | None = None
    signature_type: SignatureType = SignatureType.unknown
    page: int | None = Field(default=None, ge=1)


class LiabilityCap(BaseModel):
    amount: float | None = Field(default=None, description="Numeric cap amount if a fixed figure is stated.")
    currency: str | None = Field(default=None, description="ISO 4217 code, e.g. 'USD'.")
    description: str = Field(description="Plain-language summary, e.g. 'fees paid in prior 12 months'.")


class Agreement(BaseModel):
    title: Extracted[str] = Field(default_factory=Extracted)
    agreement_type: Extracted[str] = Field(
        default_factory=Extracted,
        description="e.g. 'Master Services Agreement', 'License Agreement', 'NDA'.",
    )
    parties: list[Party] = Field(default_factory=list)
    effective_date: Extracted[date] = Field(default_factory=Extracted)
    expiry_date: Extracted[date] = Field(default_factory=Extracted)
    initial_term: Extracted[str] = Field(default_factory=Extracted, description="Initial term as stated, e.g. '3 years'.")
    auto_renewal: Extracted[bool] = Field(default_factory=Extracted)
    renewal_term: Extracted[str] = Field(default_factory=Extracted, description="Length of each renewal period.")
    termination_notice_days: Extracted[int] = Field(
        default_factory=Extracted,
        description="Days of notice required to terminate or prevent renewal.",
    )
    payment_terms: Extracted[str] = Field(default_factory=Extracted, description="e.g. 'Net 30 from invoice date'.")
    liability_cap: Extracted[LiabilityCap] = Field(default_factory=Extracted)
    governing_law: Extracted[str] = Field(default_factory=Extracted, description="Jurisdiction, e.g. 'State of New York'.")
    signatories: list[Signatory] = Field(default_factory=list)
