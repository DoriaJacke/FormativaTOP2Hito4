from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from app.settings import Settings, get_settings


def get_session_history(
    session_id: str,
    settings: Settings | None = None,
) -> RedisChatMessageHistory:
    cfg = settings or get_settings()
    return RedisChatMessageHistory(
        session_id=session_id,
        url=cfg.redis_url,
        ttl=cfg.redis_ttl_seconds,
        key_prefix=cfg.redis_key_prefix,
    )


def add_memory_to_chain(base_chain, settings: Settings | None = None):
    cfg = settings or get_settings()

    def factory(session_id: str) -> RedisChatMessageHistory:
        return get_session_history(session_id, cfg)

    return RunnableWithMessageHistory(
        base_chain,
        factory,
        input_messages_key="input",
        history_messages_key="history",
    )
