#!/bin/sh
set -e

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
REDIS_URL="${REDIS_URL:-redis://redis:6379}"
LLM_MODEL="${LLM_MODEL:-llama3.2}"
EMBED_MODEL="${EMBED_MODEL:-nomic-embed-text}"

echo ">> Esperando Ollama en ${OLLAMA_BASE_URL}..."
until curl -sf "${OLLAMA_BASE_URL}/api/tags" > /dev/null; do
  sleep 2
done

echo ">> Descargando modelos Ollama (puede tardar varios minutos la primera vez)..."
for model in "${LLM_MODEL}" "${EMBED_MODEL}"; do
  echo "   - ${model}"
  curl -sf "${OLLAMA_BASE_URL}/api/pull" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"${model}\"}" > /dev/null
done

echo ">> Esperando Redis en ${REDIS_URL}..."
until python -c "import redis; redis.from_url('${REDIS_URL}').ping()" 2>/dev/null; do
  sleep 1
done

echo ">> Verificando indice RAG..."
python -m app.bootstrap

echo ">> Iniciando API FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
