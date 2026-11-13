"""Unit tests for deterministic DataFingerprintService."""

from uuid import uuid4

from src.intelligence.application.services.data_fingerprint_service import (
    compute_intelligence_data_hash,
)
from src.shared.domain.value_objects import Period, SupportedLanguage


def test_should_generate_deterministic_hash_for_identical_inputs() -> None:
    p = Period.from_string("2026-11")
    hash1 = compute_intelligence_data_hash(
        period=p,
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        indicators=[{"code": "CC1", "amount": 100}],
        anomalies=[],
    )
    hash2 = compute_intelligence_data_hash(
        period=p,
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        indicators=[{"code": "CC1", "amount": 100}],
        anomalies=[],
    )
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256


def test_should_change_hash_when_data_changes() -> None:
    p = Period.from_string("2026-11")
    hash1 = compute_intelligence_data_hash(
        period=p,
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        indicators=[{"code": "CC1", "amount": 100}],
        anomalies=[],
    )
    hash2 = compute_intelligence_data_hash(
        period=p,
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        indicators=[{"code": "CC1", "amount": 200}],
        anomalies=[],
    )
    assert hash1 != hash2


def test_should_change_hash_when_scope_filter_changes() -> None:
    p = Period.from_string("2026-11")
    cc_id = uuid4()
    hash_global = compute_intelligence_data_hash(
        period=p,
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        indicators=[{"code": "CC1", "amount": 100}],
        anomalies=[],
    )
    hash_scoped = compute_intelligence_data_hash(
        period=p,
        language=SupportedLanguage.PT_BR,
        cost_center_id=cc_id,
        accounting_account_id=None,
        indicators=[{"code": "CC1", "amount": 100}],
        anomalies=[],
    )
    assert hash_global != hash_scoped
