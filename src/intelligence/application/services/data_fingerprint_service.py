"""Service for computing deterministic data fingerprints of intelligence inputs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields, is_dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.shared.domain.value_objects import Period, SupportedLanguage


def _normalize_item(obj: Any) -> Any:
    """Recursively normalize objects to JSON-serializable deterministic primitives."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, (Period, SupportedLanguage)):
        return str(obj.value if hasattr(obj, "value") else obj)
    if is_dataclass(obj) and not isinstance(obj, type):
        return {
            f.name: _normalize_item(getattr(obj, f.name))
            for f in sorted(fields(obj), key=lambda x: x.name)
        }
    if hasattr(obj, "__dict__"):
        return {k: _normalize_item(v) for k, v in sorted(vars(obj).items())}
    if isinstance(obj, dict):
        return {str(k): _normalize_item(v) for k, v in sorted(obj.items())}
    if isinstance(obj, (list, tuple, set)):
        return [_normalize_item(v) for v in obj]
    return str(obj)


def compute_intelligence_data_hash(
    period: Period,
    language: SupportedLanguage,
    cost_center_id: UUID | None,
    accounting_account_id: UUID | None,
    indicators: list[Any],
    anomalies: list[Any],
) -> str:
    """Compute a deterministic SHA-256 fingerprint for strategic intelligence inputs.

    Args:
        period: Fiscal period analyzed.
        language: Language requested.
        cost_center_id: Optional scope cost center ID.
        accounting_account_id: Optional scope accounting account ID.
        indicators: Computed indicators data list.
        anomalies: Detected anomalies data list.

    Returns:
        str: 64-character SHA-256 hex digest.
    """
    payload = {
        "period": str(period),
        "language": language.value,
        "cost_center_id": str(cost_center_id) if cost_center_id else None,
        "accounting_account_id": (
            str(accounting_account_id) if accounting_account_id else None
        ),
        "indicators": _normalize_item(indicators),
        "anomalies": _normalize_item(anomalies),
    }

    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
