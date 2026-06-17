from functools import lru_cache
from operator import itemgetter

from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama

from app.memory import add_memory_to_chain
from app.rag_indexer import get_retriever, get_vector_store
from app.settings import Settings, get_settings
from app.system_prompt import SYSTEM_PROMPT


def _format_docs(documents: list[Document]) -> str:
    return "\n\n".join(document.page_content for document in documents)


def build_llm_chain(settings: Settings | None = None):
    """Cadena hasta el LLM. La salida es AIMessage (compatible con Redis history)."""
    cfg = settings or get_settings()

    llm = ChatOllama(
        model=cfg.llm_model,
        temperature=cfg.llm_temperature,
        format="json",
        num_ctx=cfg.llm_num_ctx,
        base_url=cfg.ollama_base_url,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}"),
            ("placeholder", "{history}"),
            (
                "human",
                "Contexto normativo recuperado:\n{context}\n\n"
                "Solicitud: {input}",
            ),
        ]
    )

    vectorstore = get_vector_store(cfg)
    retriever = get_retriever(vectorstore, cfg)

    return (
        RunnablePassthrough.assign(
            context=(itemgetter("input") | retriever | _format_docs),
            system_prompt=lambda _: SYSTEM_PROMPT,
        )
        | prompt
        | llm
    )


def build_minuta_chain(settings: Settings | None = None):
    """
    Memoria Redis envuelve solo prompt+LLM.
    JsonOutputParser queda fuera para no guardar dicts en el historial.
    """
    cfg = settings or get_settings()
    llm_chain = build_llm_chain(cfg)
    chain_with_history = add_memory_to_chain(llm_chain, cfg)
    return chain_with_history | JsonOutputParser()


@lru_cache
def get_minuta_chain():
    return build_minuta_chain(get_settings())
