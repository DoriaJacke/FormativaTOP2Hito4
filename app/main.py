import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.chain_builder import get_support_chain
from app.debug import get_corpus_debug_info, get_system_prompt, retrieve_debug_info
from app.models import (
    ConsultaRagDebug,
    FuenteRag,
    PipelineRag,
    RespuestaSoporte,
    SolicitudSoporte,
)
from app.normalize import (
    apply_coverage_guard,
    build_sin_documentacion_respuesta,
    coerce_llm_output,
    normalize_respuesta_payload,
)
from app.rag_indexer import get_vector_store, index_documents, retrieve_with_sources
from app.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "Asistente de soporte tecnico con Ollama, LangChain, Redis y RAG "
        "sobre documentacion interna (Docker, Linux, Git, procedimientos, FAQ)."
    ),
    version="0.2.0",
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


@app.post("/soporte/consultar")
def consultar_soporte(solicitud: SolicitudSoporte):
    chain = get_support_chain()

    consulta = (
        f"Ticket: {solicitud.ticket_id}\n"
        f"Nivel usuario: {solicitud.nivel_usuario}\n"
        f"{solicitud.consulta}"
    )

    try:
        rag = retrieve_with_sources(consulta)
    except Exception as exc:
        logger.exception("Error en recuperacion RAG")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    try:
        raw: dict = chain.invoke(
            {"input": consulta, "context": rag["context"]},
            config={"configurable": {"session_id": solicitud.session_id}},
        )
    except Exception as exc:
        logger.exception("Error al invocar la cadena LangChain")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    raw = apply_coverage_guard(raw, consulta, solicitud.ticket_id, rag["sources"])

    raw = coerce_llm_output(raw, solicitud.ticket_id)

    if "respuesta" not in raw or not isinstance(raw["respuesta"], dict):
        raw = {
            "respuesta": build_sin_documentacion_respuesta(solicitud.ticket_id)
        }

    raw["respuesta"] = normalize_respuesta_payload(
        raw["respuesta"], solicitud.ticket_id
    )

    try:
        respuesta = RespuestaSoporte(**raw["respuesta"])
    except ValidationError:
        logger.warning("Validacion fallida tras normalizar; usando respuesta de respaldo")
        raw["respuesta"] = build_sin_documentacion_respuesta(
            solicitud.ticket_id,
            mensaje=raw["respuesta"].get("resumen"),
        )
        raw["respuesta"] = normalize_respuesta_payload(
            raw["respuesta"], solicitud.ticket_id
        )
        respuesta = RespuestaSoporte(**raw["respuesta"])

    fuentes = [FuenteRag(**source) for source in rag["sources"]]
    pipeline = PipelineRag(
        pregunta=consulta,
        embed_model=rag["embed_model"],
        query_embedding=rag["query_embedding"],
        vector_store=rag["vector_store"],
        retriever=rag["retriever"],
        llm_model=settings.llm_model,
        chunks_recuperados=len(fuentes),
    )

    response = {
        "respuesta": respuesta.model_dump(mode="json"),
        "fuentes": [fuente.model_dump() for fuente in fuentes],
        "pipeline": pipeline.model_dump(),
    }
    return JSONResponse(content=response)


@app.post("/admin/reindex")
def reindex_corpus():
    try:
        chunks = index_documents()
    except Exception as exc:
        logger.exception("Error al reindexar documentos")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    get_support_chain.cache_clear()
    return {"status": "ok", "chunks_indexados": chunks}
