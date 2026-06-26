"""Utilidades de depuración: pre-prompt y recuperación RAG."""

from typing import Any

from app.rag_indexer import get_vector_store, retrieve_with_sources
from app.settings import Settings, get_settings
from app.system_prompt import SYSTEM_PROMPT


def get_system_prompt() -> dict[str, str]:
    return {"system_prompt": SYSTEM_PROMPT}


def get_corpus_debug_info(settings: Settings | None = None) -> dict[str, Any]:
    cfg = settings or get_settings()
    vectorstore = get_vector_store(cfg)
    collection = vectorstore._collection
    total = collection.count()

    if total == 0:
        return {
            "total_chunks": 0,
            "embed_model": cfg.embed_model,
            "chunk_size": cfg.chunk_size,
            "chunk_overlap": cfg.chunk_overlap,
            "chunks": [],
        }

    data = collection.get(
        limit=min(total, 50),
        include=["documents", "metadatas", "embeddings"],
    )

    chunks = []
    raw_embeddings = data.get("embeddings")
    for index, doc_id in enumerate(data["ids"]):
        embedding = (
            raw_embeddings[index] if raw_embeddings is not None else None
        )
        preview = None
        dimensions = None
        if embedding is not None:
            dimensions = len(embedding)
            preview = [round(float(value), 6) for value in embedding[:12]]

        chunks.append(
            {
                "id": doc_id,
                "metadata": data["metadatas"][index] if data.get("metadatas") else {},
                "content": data["documents"][index],
                "length": len(data["documents"][index]),
                "embedding": {
                    "dimensions": dimensions,
                    "preview": preview,
                },
            }
        )

    return {
        "total_chunks": total,
        "embed_model": cfg.embed_model,
        "chunk_size": cfg.chunk_size,
        "chunk_overlap": cfg.chunk_overlap,
        "collection": cfg.chroma_collection,
        "chunks": chunks,
    }


def retrieve_debug_info(consulta: str, settings: Settings | None = None) -> dict[str, Any]:
    cfg = settings or get_settings()
    rag = retrieve_with_sources(consulta, cfg)
    return {
        **rag,
        "system_prompt": SYSTEM_PROMPT,
        "chunks_recuperados": len(rag["sources"]),
        "chunks": rag["sources"],
    }
