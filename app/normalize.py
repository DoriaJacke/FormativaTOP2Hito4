"""Normaliza salidas del LLM antes de validar con Pydantic."""

from datetime import datetime, timezone
import re
from typing import Any

_PLACEHOLDER_NINO = frozenset({"string", "nino_id", "id"})
_PLACEHOLDER_SEMANA = frozenset({"yyyy-ww", "yyyy-www", "yyyy-w##"})
_PLACEHOLDER_DATETIME = frozenset(
    {
        "iso-8601 datetime",
        "iso8601 datetime",
        "datetime",
        "fecha",
        "timestamp",
    }
)


def _is_placeholder(value: Any, placeholders: frozenset[str]) -> bool:
    if not isinstance(value, str):
        return False
    return value.strip().lower() in placeholders


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        return None

    text = value.strip()
    if _is_placeholder(text, _PLACEHOLDER_DATETIME):
        return None

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return None


def _current_iso_week() -> str:
    now = datetime.now(timezone.utc)
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"


def _is_invalid_semana(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    text = value.strip().lower()
    if _is_placeholder(text, _PLACEHOLDER_SEMANA):
        return True
    return not re.fullmatch(r"\d{4}-W\d{2}", value.strip(), flags=re.IGNORECASE)


def normalize_minuta_payload(raw_minuta: dict[str, Any], nino_id: str) -> dict[str, Any]:
    """Corrige placeholders comunes que el LLM copia del esquema."""
    data = dict(raw_minuta)

    if _is_placeholder(data.get("nino_id"), _PLACEHOLDER_NINO) or not data.get("nino_id"):
        data["nino_id"] = nino_id

    if _is_invalid_semana(data.get("semana")):
        data["semana"] = _current_iso_week()

    parsed = _parse_datetime(data.get("generada_en"))
    if parsed is None:
        data["generada_en"] = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        )
    else:
        data["generada_en"] = parsed.replace(microsecond=0).isoformat()

    return data
