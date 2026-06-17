from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Sistema de Minutas Alimentarias IA"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    ollama_base_url: str = "http://ollama:11434"
    llm_model: str = "llama3.2"
    embed_model: str = "nomic-embed-text"
    llm_temperature: float = 0.1
    llm_num_ctx: int = 4096

    redis_url: str = "redis://redis:6379"
    redis_key_prefix: str = "minuta:"
    redis_ttl_seconds: int = 86400

    chroma_dir: str = "/app/data/chroma_db"
    chroma_collection: str = "normativa_junji"
    documents_dir: str = "/app/documentos_normativos"

    retriever_k: int = 4
    retriever_fetch_k: int = 20
    retriever_lambda_mult: float = 0.7

    chunk_size: int = 512
    chunk_overlap: int = 64

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
