# Minutas IA — Proyecto base dockerizado

Sistema de generación de minutas alimentarias para niños menores de 3 años con alergias, integrando:

- **Ollama** — inferencia local (LLM + embeddings)
- **LangChain (LCEL)** — orquestación de la cadena
- **Redis** — memoria contextual de sesión
- **Chroma** — vector store para RAG
- **FastAPI** — API REST con salida JSON validada (Pydantic)
- **React** — panel web de pruebas

## Requisitos

- Docker Desktop o Docker Engine + Docker Compose v2
- RAM según perfil: **8 GB** (ligero), **16 GB** (medio, recomendado), **16+ GB** (alto)
- La primera ejecución descarga modelos Ollama (~0.7 GB a ~5 GB según perfil)

### Perfiles de hardware (heterogeneidad en el curso)

| Perfil | Comando | Modelo | Uso |
|--------|---------|--------|-----|
| Ligero | `make perfil-ligero` | `llama3.2:1b` | 8 GB RAM, sin GPU |
| Medio | `make perfil-medio` | `llama3.2` | 16 GB RAM (default) |
| Alto | `make perfil-alto` | `llama3.1:8b` | GPU / Apple Silicon |

Ver guía completa: **[ACTIVIDAD_FORMATIVA.md](./ACTIVIDAD_FORMATIVA.md)** o PDF desde **`actividad_formativa.tex`**

## Inicio rápido

```bash
cp .env.example .env
make up
```

Espera a que termine la descarga de modelos y la indexación RAG. Luego abre:

**[http://localhost:3000](http://localhost:3000)** — panel React de pruebas

Verificación por CLI:

```bash
make ready
make demo
```

## Servicios

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| `web`    | 3000   | Frontend React (nginx) |
| `api`    | 8000   | FastAPI + LangChain |
| `redis`  | 6379   | Memoria de sesión |
| `ollama` | 11434  | Motor LLM local |

Documentación interactiva API: [http://localhost:8000/docs](http://localhost:8000/docs)

## Frontend React

El panel web permite:

- Verificar estado de API, Redis, Chroma y Ollama
- Generar minutas con formulario interactivo
- Cargar escenarios de las actividades de clase (María, Pedro memoria Redis)
- Ver resultado estructurado + JSON crudo
- Reindexar el corpus RAG desde la UI
- **Inspeccionar pre-prompt y vectorización RAG** (system prompt, corpus Chroma, embeddings y fragmentos recuperados)

### Desarrollo local del frontend (sin Docker)

Con la API corriendo en `:8000`:

```bash
make web-dev
```

Vite levanta el frontend en [http://localhost:3000](http://localhost:3000) y hace proxy de `/api` hacia la API.

## Endpoints principales

### `GET /health`
Estado básico del servicio.

### `GET /health/ready`
Verifica Redis, Chroma y Ollama.

### `POST /minuta/generar`
Genera una minuta estructurada en JSON.

```bash
curl -X POST http://localhost:8000/minuta/generar \
  -H "Content-Type: application/json" \
  -d '{
    "nino_id": "maria_001",
    "session_id": "jard01:maria",
    "consulta": "Maria, 2 anios, alergia lactosa. Genera almuerzo del lunes."
  }'
```

### `POST /admin/reindex`
Reindexa el corpus normativo en Chroma (útil tras agregar PDFs).

### `GET /debug/system-prompt`
Devuelve el pre-prompt (system prompt) activo.

### `GET /debug/rag/corpus`
Lista fragmentos indexados con preview de vectores almacenados.

### `POST /debug/rag/retrieve`
Recupera fragmentos MMR para una consulta y muestra el embedding de la consulta.

```bash
make reindex
```

## Estructura del proyecto

```text
.
├── app/
│   ├── main.py           # FastAPI
│   ├── chain_builder.py  # Cadena LCEL
│   ├── memory.py         # RedisChatMessageHistory
│   ├── rag_indexer.py    # Indexación y retriever MMR
│   ├── models.py         # Esquemas Pydantic
│   ├── system_prompt.py  # Pre-prompt del dominio
│   ├── settings.py       # Configuración por variables de entorno
│   └── bootstrap.py      # Indexación al arranque
├── frontend/
│   ├── src/              # React + Vite
│   ├── Dockerfile        # build + nginx
│   └── nginx.conf        # proxy /api -> api:8000
├── documentos_normativos/  # Corpus RAG (.pdf, .txt, .md)
├── scripts/
│   └── entrypoint.sh     # Pull de modelos + bootstrap + uvicorn
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── Makefile
```

## Agregar documentos normativos

1. Coloca PDFs o archivos `.txt`/`.md` en `documentos_normativos/`
2. Ejecuta `make reindex`

## Variables de entorno

Copia `.env.example` a `.env` y ajusta según necesidad:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | URL del servidor Ollama |
| `LLM_MODEL` | `llama3.2` | Modelo de generación |
| `EMBED_MODEL` | `nomic-embed-text` | Modelo de embeddings |
| `REDIS_URL` | `redis://redis:6379` | Conexión Redis |
| `CHROMA_DIR` | `/app/data/chroma_db` | Persistencia del vector store |

## Comandos útiles

```bash
make up        # Levantar stack completo (incluye web)
make down      # Detener stack
make logs      # Ver logs de la API
make web-logs  # Ver logs del frontend
make health    # Healthcheck
make ready     # Readiness (Redis + Chroma + Ollama)
make demo      # Consulta de ejemplo por curl
make web-dev   # Frontend en modo desarrollo (Vite)
make shell     # Shell dentro del contenedor api
```

## Actividad de memoria (Redis)

Consulta 1 y 2 con el mismo `session_id`:

```bash
# Consulta 1: declarar alergias
curl -X POST http://localhost:8000/minuta/generar \
  -H "Content-Type: application/json" \
  -d '{"nino_id":"pedro_001","session_id":"test:pedro","consulta":"Pedro, 2 anios, alergico a mariscos y huevo. Genera desayuno del lunes."}'

# Consulta 2: sin repetir alergias
curl -X POST http://localhost:8000/minuta/generar \
  -H "Content-Type: application/json" \
  -d '{"nino_id":"pedro_001","session_id":"test:pedro","consulta":"Genera almuerzo del lunes respetando sus restricciones."}'
```

Ver historial en Redis:

```bash
docker compose exec redis redis-cli LRANGE minuta:test:pedro 0 -1
```

## Notas para la clase

- El LLM es un **componente** del sistema, no la aplicación completa.
- RAG aporta contexto normativo actualizable sin reentrenar.
- Redis mantiene memoria de sesión entre consultas.
- Pydantic valida el contrato JSON antes de responder al cliente.
- Cambiar `LLM_MODEL` en `.env` permite sustituir el motor sin tocar la cadena.

## Detener y limpiar volúmenes

```bash
docker compose down -v
```

Esto elimina los volúmenes de Redis, Ollama y Chroma.
