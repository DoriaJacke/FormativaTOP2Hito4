from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.settings import Settings, get_settings


def _load_documents(documents_dir: str):
    path = Path(documents_dir)
    if not path.exists():
        raise FileNotFoundError(f"No existe el directorio de documentos: {documents_dir}")

    documents = []

    if list(path.glob("**/*.pdf")):
        pdf_loader = DirectoryLoader(
            documents_dir,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
            show_progress=True,
            use_multithreading=True,
        )
        documents.extend(pdf_loader.load())

    for pattern in ("**/*.txt", "**/*.md"):
        if list(path.glob(pattern)):
            text_loader = DirectoryLoader(
                documents_dir,
                glob=pattern,
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"},
                show_progress=True,
            )
            documents.extend(text_loader.load())

    if not documents:
        raise FileNotFoundError(
            f"No hay documentos indexables en {documents_dir}. "
            "Agrega archivos .pdf, .txt o .md."
        )

    return documents


def build_vector_store(settings: Settings | None = None) -> Chroma:
    cfg = settings or get_settings()
    documents = _load_documents(cfg.documents_dir)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg.chunk_size,
        chunk_overlap=cfg.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_documents(documents)

    embeddings = OllamaEmbeddings(
        model=cfg.embed_model,
        base_url=cfg.ollama_base_url,
    )

    Path(cfg.chroma_dir).mkdir(parents=True, exist_ok=True)

    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=cfg.chroma_dir,
        collection_name=cfg.chroma_collection,
    )


def get_vector_store(settings: Settings | None = None) -> Chroma:
    cfg = settings or get_settings()
    embeddings = OllamaEmbeddings(
        model=cfg.embed_model,
        base_url=cfg.ollama_base_url,
    )
    return Chroma(
        persist_directory=cfg.chroma_dir,
        embedding_function=embeddings,
        collection_name=cfg.chroma_collection,
    )


def get_retriever(vectorstore: Chroma, settings: Settings | None = None):
    cfg = settings or get_settings()
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": cfg.retriever_k,
            "fetch_k": cfg.retriever_fetch_k,
            "lambda_mult": cfg.retriever_lambda_mult,
        },
    )


def index_documents(settings: Settings | None = None) -> int:
    cfg = settings or get_settings()
    vectorstore = build_vector_store(cfg)
    return vectorstore._collection.count()
