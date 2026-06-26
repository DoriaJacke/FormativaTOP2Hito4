"""Normaliza salidas del LLM antes de validar con Pydantic."""

from datetime import datetime, timezone
import re
from typing import Any

_PLACEHOLDER_TICKET = frozenset({"string", "ticket_id", "id", "tkt-xxxx"})
_PLACEHOLDER_DATETIME = frozenset(
    {
        "iso-8601 datetime",
        "iso8601 datetime",
        "datetime",
        "fecha",
        "timestamp",
    }
)
_CATEGORIAS_VALIDAS = frozenset(
    {"docker", "linux", "git", "infra", "acceso", "faq", "general"}
)
_NIVELES_VALIDOS = frozenset({"alta", "media", "baja"})

_MENSAJE_SIN_DOCUMENTACION = (
    "Lo siento, la documentacion interna actual no registra el procedimiento "
    "solicitado. Por favor, escala este caso con el Administrador de Sistemas "
    "o abre un ticket de soporte general."
)

_TOPICS_SIN_CORPUS = (
    "azure",
    "saml",
    "sso",
    "kubernetes",
    "k8s",
    "active directory",
    "windows server",
    "sql server",
    "terraform",
    "ansible",
    "jenkins",
    "postgresql",
    "mongodb",
    "vmware",
    "exchange",
)


def _source_filename(source: dict[str, Any]) -> str:
    raw = source.get("source") or source.get("metadata", {}).get("source") or ""
    return raw.replace("\\", "/").split("/")[-1].lower()


def _topic_in_text(topic: str, text: str) -> bool:
    """Evita falsos positivos con terminos cortos (ej. 'sso' dentro de otras palabras)."""
    if " " in topic:
        return topic in text
    return re.search(rf"\b{re.escape(topic)}\b", text) is not None


def lacks_documentation_coverage(consulta: str, sources: list[dict[str, Any]]) -> bool:
    """True si la consulta pide temas ausentes en los fragmentos recuperados."""
    consulta_lower = consulta.lower()
    corpus_text = " ".join(
        f"{source.get('content', '')} {_source_filename(source)}" for source in sources
    ).lower()

    for topic in _TOPICS_SIN_CORPUS:
        if _topic_in_text(topic, consulta_lower) and not _topic_in_text(
            topic, corpus_text
        ):
            return True

    return False


def _match_fuente_disponible(fuente: str, disponibles: set[str]) -> str | None:
    fuente = fuente.strip().lower()
    if not fuente or fuente == "sin_fuente":
        return None
    if fuente in disponibles:
        return fuente

    for nombre in disponibles:
        if fuente in nombre or nombre in fuente:
            return nombre
        if fuente.replace("_demo", "") in nombre or nombre.replace("_demo", "") in fuente:
            return nombre
    return None


def sanitize_referencias(
    referencias: list[dict[str, Any]], sources: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Conserva referencias validas y corrige nombres de archivo aproximados."""
    if not referencias:
        return []

    disponibles = {_source_filename(source) for source in sources}
    saneadas = []

    for referencia in referencias:
        if not isinstance(referencia, dict):
            continue
        fuente = str(referencia.get("fuente_documento", "")).strip()
        coincidencia = _match_fuente_disponible(fuente, disponibles)
        if coincidencia:
            saneadas.append({**referencia, "fuente_documento": coincidencia})

    return saneadas


def apply_coverage_guard(
    raw: dict[str, Any],
    consulta: str,
    ticket_id: str,
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    """Fuerza respuesta de incertidumbre solo cuando el corpus no cubre la consulta."""
    raw = coerce_llm_output(raw, ticket_id)
    respuesta = raw.get("respuesta", {})

    if lacks_documentation_coverage(consulta, sources):
        tema = "el tema solicitado"
        consulta_lower = consulta.lower()
        for topic in _TOPICS_SIN_CORPUS:
            if _topic_in_text(topic, consulta_lower):
                tema = topic
                break

        mensaje = (
            f"Lo siento, la documentacion interna actual no registra el procedimiento "
            f"para {tema}. Por favor, escala este caso con el Administrador de Sistemas "
            f"o abre un ticket de soporte general."
        )
        return {"respuesta": build_sin_documentacion_respuesta(ticket_id, mensaje=mensaje)}

    referencias = sanitize_referencias(
        respuesta.get("referencias_documentales", []), sources
    )
    respuesta["referencias_documentales"] = referencias
    raw["respuesta"] = respuesta
    return raw


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


def _normalize_categoria(value: Any) -> str:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in _CATEGORIAS_VALIDAS:
            return normalized
    return "general"


def _normalize_nivel_confianza(value: Any) -> str:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in _NIVELES_VALIDOS:
            return normalized
    return "baja"


def _normalize_pasos(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    pasos = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            continue
        pasos.append(
            {
                "orden": int(item.get("orden", index)),
                "descripcion": str(item.get("descripcion", "")).strip(),
                "comando": item.get("comando"),
            }
        )
    return [paso for paso in pasos if paso["descripcion"]]


def _normalize_referencias(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    referencias = []
    for item in value:
        if not isinstance(item, dict):
            continue
        documento = str(item.get("documento", "")).strip()
        seccion = str(item.get("seccion", "")).strip()
        fuente = str(item.get("fuente_documento", "")).strip()
        if documento or seccion or fuente:
            referencias.append(
                {
                    "documento": documento or "Documento interno",
                    "seccion": seccion or "Sin seccion",
                    "fuente_documento": fuente or "sin_fuente",
                }
            )
    return referencias


def build_sin_documentacion_respuesta(
    ticket_id: str,
    mensaje: str | None = None,
    alternativas: list[str] | None = None,
) -> dict[str, Any]:
    """Respuesta estructurada cuando no hay cobertura documental."""
    opciones = alternativas or [
        "Abrir ticket de escalamiento a Nivel 2",
        "Contactar al Administrador de Sistemas",
    ]
    pasos = [
        {
            "orden": index,
            "descripcion": alternativa,
            "comando": None,
        }
        for index, alternativa in enumerate(opciones, start=1)
    ]

    return {
        "ticket_id": ticket_id,
        "categoria": "general",
        "resumen": mensaje or _MENSAJE_SIN_DOCUMENTACION,
        "nivel_confianza": "baja",
        "generada_en": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "pasos": pasos,
        "referencias_documentales": [],
        "notas_adicionales": (
            "No se encontro procedimiento aplicable en los manuales Docker, Linux, Git, "
            "procedimientos de soporte ni FAQ indexados. Escala el caso segun los "
            "procedimientos internos de Nivel 1."
        ),
    }


def coerce_llm_output(raw: dict[str, Any], ticket_id: str) -> dict[str, Any]:
    """Unifica salidas del LLM al formato {\"respuesta\": {...}}."""
    if "respuesta" in raw and isinstance(raw["respuesta"], dict):
        return raw

    if "error" in raw:
        mensaje = raw["error"] if isinstance(raw["error"], str) else str(raw["error"])
        alternativas = raw.get("alternativas")
        if not isinstance(alternativas, list):
            alternativas = None
        return {
            "respuesta": build_sin_documentacion_respuesta(
                ticket_id=ticket_id,
                mensaje=mensaje,
                alternativas=alternativas,
            )
        }

    if isinstance(raw.get("resumen"), str):
        return {"respuesta": raw}

    return {
        "respuesta": build_sin_documentacion_respuesta(
            ticket_id=ticket_id,
            mensaje=_MENSAJE_SIN_DOCUMENTACION,
        )
    }


def normalize_respuesta_payload(
    raw_respuesta: dict[str, Any], ticket_id: str
) -> dict[str, Any]:
    """Corrige placeholders y valores fuera del esquema que el LLM suele devolver."""
    data = dict(raw_respuesta)

    if _is_placeholder(data.get("ticket_id"), _PLACEHOLDER_TICKET) or not data.get(
        "ticket_id"
    ):
        data["ticket_id"] = ticket_id

    data["categoria"] = _normalize_categoria(data.get("categoria"))
    data["nivel_confianza"] = _normalize_nivel_confianza(data.get("nivel_confianza"))
    data["resumen"] = str(data.get("resumen", "")).strip() or _MENSAJE_SIN_DOCUMENTACION
    data["pasos"] = _normalize_pasos(data.get("pasos"))
    data["referencias_documentales"] = _normalize_referencias(
        data.get("referencias_documentales")
    )

    notas = data.get("notas_adicionales")
    data["notas_adicionales"] = str(notas).strip() if notas else None

    parsed = _parse_datetime(data.get("generada_en"))
    if parsed is None:
        data["generada_en"] = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        )
    else:
        data["generada_en"] = parsed.replace(microsecond=0).isoformat()

    if _MENSAJE_SIN_DOCUMENTACION.split(".")[0].lower() in data["resumen"].lower():
        data["nivel_confianza"] = "baja"
        data["categoria"] = "general"

    return data
