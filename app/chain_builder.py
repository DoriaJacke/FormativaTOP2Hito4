from functools import lru_cache

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_ollama import ChatOllama

from app.memory import add_memory_to_chain
from app.rag_indexer import format_documents, get_retriever, get_vector_store
from app.settings import Settings, get_settings
from app.system_prompt import SYSTEM_PROMPT


def _resolve_context(data: dict) -> dict:
    if data.get("context"):
        return data
    cfg = get_settings()
    vectorstore = get_vector_store(cfg)
    retriever = get_retriever(vectorstore, cfg)
    documents = retriever.invoke(data["input"])
    return {**data, "context": format_documents(documents)}


def build_llm_chain(settings: Settings | None = None):
    """Cadena hasta el LLM. Acepta contexto precomputado o recupera vía RAG."""
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
                "Documentacion interna recuperada:\n{context}\n\n"
                "Consulta de soporte: {input}",
            ),
        ]
    )

    return (
        RunnableLambda(_resolve_context)
        | RunnablePassthrough.assign(system_prompt=lambda _: SYSTEM_PROMPT)
        | prompt
        | llm
    )


def build_support_chain(settings: Settings | None = None):
    """
    Memoria Redis envuelve solo prompt+LLM.
    JsonOutputParser queda fuera para no guardar dicts en el historial.
    """
    cfg = settings or get_settings()
    llm_chain = build_llm_chain(cfg)
    chain_with_history = add_memory_to_chain(llm_chain, cfg)
    return chain_with_history | JsonOutputParser()


@lru_cache
def get_support_chain():
    return build_support_chain(get_settings())
