import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.chain_builder import get_minuta_chain
from app.debug import get_corpus_debug_info, get_system_prompt, retrieve_debug_info
from app.models import ConsultaRagDebug, Minuta, SolicitudMinuta
from app.normalize import normalize_minuta_payload
from app.rag_indexer import get_vector_store, index_documents
from app.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "API de generacion de minutas alimentarias con Ollama, LangChain, "
        "Redis y RAG."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def readiness() -> dict[str, Any]:
    checks: dict[str, Any] = {"redis": False, "chroma": False, "ollama": False}

    try:
        import redis

        client = redis.from_url(settings.redis_url)
        client.ping()
        checks["redis"] = True
    except Exception as exc:
        checks["redis_error"] = str(exc)

    try:
        vectorstore = get_vector_store()
        checks["chroma"] = vectorstore._collection.count() > 0
        checks["chroma_chunks"] = vectorstore._collection.count()
    except Exception as exc:
        checks["chroma_error"] = str(exc)

    try:
        import httpx

        response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
        response.raise_for_status()
        checks["ollama"] = True
        checks["ollama_models"] = [
            model["name"] for model in response.json().get("models", [])
        ]
    except Exception as exc:
        checks["ollama_error"] = str(exc)

    ready = all(checks[key] for key in ("redis", "chroma", "ollama"))
    if not ready:
        raise HTTPException(status_code=503, detail=checks)

    return {"status": "ready", "checks": checks}


@app.get("/debug/system-prompt")
def debug_system_prompt():
    return get_system_prompt()


@app.get("/debug/rag/corpus")
def debug_rag_corpus():
    try:
        return get_corpus_debug_info()
    except Exception as exc:
        logger.exception("Error al obtener corpus RAG")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/debug/rag/retrieve")
def debug_rag_retrieve(body: ConsultaRagDebug):
    try:
        return retrieve_debug_info(body.consulta)
    except Exception as exc:
        logger.exception("Error al recuperar fragmentos RAG")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/minuta/generar")
def generar_minuta(solicitud: SolicitudMinuta):
    chain = get_minuta_chain()

    consulta = (
        f"ID del nino: {solicitud.nino_id}\n"
        f"{solicitud.consulta}"
    )

    try:
        raw: dict = chain.invoke(
            {"input": consulta},
            config={"configurable": {"session_id": solicitud.session_id}},
        )
    except Exception as exc:
        logger.exception("Error al invocar la cadena LangChain")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if "minuta" not in raw:
        raise HTTPException(
            status_code=422,
            detail={
                "mensaje": "La respuesta no contiene la clave 'minuta'",
                "raw": raw,
            },
        )

    raw["minuta"] = normalize_minuta_payload(raw["minuta"], solicitud.nino_id)

    try:
        minuta = Minuta(**raw["minuta"])
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "mensaje": (
                    "El LLM devolvio JSON que no cumple el esquema Pydantic. "
                    "Reintenta la consulta o revisa el prompt."
                ),
                "errores": exc.errors(),
                "raw": raw,
            },
        ) from exc

    alergenos = raw["minuta"].get("alergenos_excluidos", [])
    if alergenos and not minuta.verificar_alergenos(alergenos):
        raise HTTPException(
            status_code=422,
            detail="Se detecto un alergeno en los ingredientes generados",
        )

    return JSONResponse(content=raw)


@app.post("/admin/reindex")
def reindex_corpus():
    try:
        chunks = index_documents()
    except Exception as exc:
        logger.exception("Error al reindexar documentos")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    get_minuta_chain.cache_clear()
    return {"status": "ok", "chunks_indexados": chunks}
