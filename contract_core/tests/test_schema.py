from datetime import date

from contract_core import Agreement, Evidence, Extracted, Party, validate_agreement


def _ev(page: int = 1) -> Evidence:
    return Evidence(quote="...", page=page)


def test_round_trips_through_json():
    a = Agreement(
        parties=[Party(name="Acme Corp", role="Customer"), Party(name="Globex Inc", role="Supplier")],
        effective_date=Extracted[date](value=date(2024, 1, 1), evidence=_ev()),
    )
    assert Agreement.model_validate_json(a.model_dump_json()) == a


def test_json_schema_is_generated():
    schema = Agreement.model_json_schema()
    assert "effective_date" in schema["properties"]


def test_valid_agreement_has_no_issues():
    a = Agreement(
        parties=[Party(name="A"), Party(name="B")],
        effective_date=Extracted[date](value=date(2024, 1, 1), evidence=_ev()),
        expiry_date=Extracted[date](value=date(2025, 1, 1), evidence=_ev(2)),
    )
    assert validate_agreement(a, page_count=5) == []


def test_flags_missing_party_bad_dates_and_evidence():
    a = Agreement(
        parties=[Party(name="A")],
        effective_date=Extracted[date](value=date(2025, 1, 1), evidence=_ev()),
        expiry_date=Extracted[date](value=date(2024, 1, 1), evidence=_ev(9)),
        governing_law=Extracted[str](value="New York"),
    )
    fields = {i.field for i in validate_agreement(a, page_count=5)}
    assert fields == {"parties", "expiry_date", "governing_law"}
