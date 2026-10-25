"""Deterministic validation rules applied after extraction.

Issues are fed back to the LLM on retry (LangGraph) and used as
data-quality expectations on the Databricks path.
"""

from pydantic import BaseModel

from contract_core.schema import Agreement, Extracted


class ValidationIssue(BaseModel):
    field: str
    message: str


def validate_agreement(agreement: Agreement, page_count: int | None = None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if len(agreement.parties) < 2:
        issues.append(ValidationIssue(field="parties", message=f"Expected at least 2 parties, found {len(agreement.parties)}."))

    eff, exp = agreement.effective_date.value, agreement.expiry_date.value
    if eff and exp and exp <= eff:
        issues.append(ValidationIssue(field="expiry_date", message=f"Expiry date {exp} is not after effective date {eff}."))

    for name, field in agreement:
        if not isinstance(field, Extracted):
            continue
        if field.value is not None and field.evidence is None:
            issues.append(ValidationIssue(field=name, message="Value has no supporting evidence quote."))
        if page_count and field.evidence and field.evidence.page > page_count:
            issues.append(
                ValidationIssue(field=name, message=f"Evidence page {field.evidence.page} exceeds document length {page_count}.")
            )

    return issues
