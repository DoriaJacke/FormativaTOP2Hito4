"""Tareas de arranque: indexacion inicial del corpus RAG."""

import logging

from app.rag_indexer import get_vector_store, index_documents
from app.settings import get_settings

logger = logging.getLogger(__name__)


def ensure_index() -> int:
    settings = get_settings()

    try:
        vectorstore = get_vector_store()
        count = vectorstore._collection.count()
        if count > 0:
            logger.info("Chroma ya indexado con %s fragmentos", count)
            return count
    except Exception:
        logger.info("Chroma vacio o inexistente; iniciando indexacion")

    chunks = index_documents(settings)
    logger.info("Indexacion completada: %s fragmentos", chunks)
    return chunks


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ensure_index()
