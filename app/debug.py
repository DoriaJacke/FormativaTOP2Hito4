"""Utilidades de depuración: pre-prompt y recuperación RAG."""

from typing import Any

from langchain_ollama import OllamaEmbeddings

from app.rag_indexer import get_retriever, get_vector_store
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
    vectorstore = get_vector_store(cfg)
    retriever = get_retriever(vectorstore, cfg)

    embeddings = OllamaEmbeddings(
        model=cfg.embed_model,
        base_url=cfg.ollama_base_url,
    )
    query_vector = embeddings.embed_query(consulta)
    documents = retriever.invoke(consulta)

    scored = vectorstore.similarity_search_with_score(consulta, k=cfg.retriever_k)
    scores_by_content = {doc.page_content: round(score, 6) for doc, score in scored}

    chunks = []
    for rank, document in enumerate(documents, start=1):
        chunks.append(
            {
                "rank": rank,
                "content": document.page_content,
                "metadata": document.metadata,
                "length": len(document.page_content),
                "similarity_score": scores_by_content.get(document.page_content),
            }
        )

    return {
        "consulta": consulta,
        "system_prompt": SYSTEM_PROMPT,
        "embed_model": cfg.embed_model,
        "retriever": {
            "type": "mmr",
            "k": cfg.retriever_k,
            "fetch_k": cfg.retriever_fetch_k,
            "lambda_mult": cfg.retriever_lambda_mult,
        },
        "query_embedding": {
            "dimensions": len(query_vector),
            "preview": [round(value, 6) for value in query_vector[:12]],
        },
        "chunks_recuperados": len(chunks),
        "chunks": chunks,
    }
