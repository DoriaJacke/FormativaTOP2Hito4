# Asistente de Soporte Técnico — Caso 2

Asistente RAG para ayudar a usuarios y técnicos usando documentación interna:

- Manual Docker
- Manual Linux
- Manual Git
- Procedimientos de soporte
- Preguntas frecuentes (FAQ)

## Arquitectura RAG

```
Usuario → Pregunta → Embedding → Base Vectorial → Recuperación de Contexto → LLM → Respuesta + Fuentes
```

Stack tecnológico:

- **Ollama** — inferencia local (LLM + embeddings)
- **LangChain (LCEL)** — orquestación de la cadena
- **Redis** — memoria contextual de sesión por ticket
- **Chroma** — vector store para RAG
- **FastAPI** — API REST con salida JSON validada (Pydantic)
- **React** — panel web con visualización del pipeline RAG

## Requisitos

- Docker Desktop o Docker Engine + Docker Compose v2
- RAM según perfil: **8 GB** (ligero), **16 GB** (medio, recomendado), **16+ GB** (alto)

### Perfiles de hardware

| Perfil | Comando | Modelo | Uso |
|--------|---------|--------|-----|
| Ligero | `make perfil-ligero` | `llama3.2:1b` | 8 GB RAM, sin GPU |
| Medio | `make perfil-medio` | `llama3.2` | 16 GB RAM (default) |
| Alto | `make perfil-alto` | `llama3.1:8b` | GPU / Apple Silicon |

## Inicio rápido

```bash
cp .env.example .env
make up
```

Espera a que termine la descarga de modelos y la indexación RAG. Luego abre:

**[http://localhost:3000](http://localhost:3000)** — panel React

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

## Frontend

El panel web permite:

- Verificar estado de API, Redis, Chroma y Ollama
- Enviar consultas de soporte con ticket_id y nivel de usuario
- Visualizar el pipeline RAG paso a paso
- Cargar escenarios de prueba (Docker, Git, Linux)
- Ver respuesta estructurada con pasos, comandos y fuentes documentales
- Reindexar el corpus desde la UI

## Endpoints principales

### `POST /soporte/consultar`

Consulta de soporte con RAG + LLM.

```bash
curl -X POST http://localhost:8000/soporte/consultar \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-0042",
    "session_id": "soporte:docker",
    "nivel_usuario": "tecnico",
    "consulta": "Mi contenedor no inicia. Error: port is already allocated en puerto 8080."
  }'
```

Respuesta incluye `respuesta` (pasos, comandos, referencias), `fuentes` (chunks RAG) y `pipeline` (metadatos de cada etapa).

### Otros endpoints

| Endpoint | Descripción |
|----------|-------------|
| `GET /health` | Estado básico |
| `GET /health/ready` | Verifica Redis + Chroma + Ollama |
| `POST /admin/reindex` | Reindexa documentación en Chroma |
| `GET /debug/system-prompt` | System prompt activo |
| `GET /debug/rag/corpus` | Fragmentos indexados |
| `POST /debug/rag/retrieve` | Preview de recuperación RAG |

## Corpus documental

Archivos demo en `documentos_soporte/`:

| Archivo | Contenido |
|---------|-----------|
| `manual_docker_demo.txt` | Contenedores, puertos, daemon |
| `manual_linux_demo.txt` | Permisos, procesos, systemd |
| `manual_git_demo.txt` | Merge conflicts, ramas, push |
| `procedimientos_soporte_demo.txt` | Tickets N1/N2, escalamiento |
| `faq_soporte_demo.txt` | Preguntas frecuentes |

Para agregar documentación: coloca `.pdf`, `.txt` o `.md` en `documentos_soporte/` y ejecuta `make reindex`.

## Estructura del proyecto

```text
.
├── app/                    # Backend FastAPI + LangChain
├── frontend/src/           # React + pipeline RAG visual
├── documentos_soporte/     # Corpus RAG
├── scripts/entrypoint.sh
├── docker-compose.yml
└── Makefile
```

## Actividad de memoria (Redis)

Dos consultas del mismo ticket con el mismo `session_id`:

```bash
# Consulta 1: conflicto de merge
curl -X POST http://localhost:8000/soporte/consultar \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"TKT-0103","session_id":"soporte:git","nivel_usuario":"usuario","consulta":"Al hacer git pull me aparece CONFLICT en package.json."}'

# Consulta 2: seguimiento sin repetir contexto
curl -X POST http://localhost:8000/soporte/consultar \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"TKT-0103","session_id":"soporte:git","nivel_usuario":"usuario","consulta":"Ya resolvi el conflicto. Al hacer push dice rejected non-fast-forward."}'
```

Ver historial en Redis:

```bash
docker compose exec redis redis-cli LRANGE support:soporte:git 0 -1
```

## Comandos útiles

```bash
make up        # Levantar stack completo
make down      # Detener stack
make logs      # Logs de la API
make ready     # Readiness check
make demo      # Consulta Docker de ejemplo
make reindex   # Reindexar corpus
make web-dev   # Frontend en desarrollo (Vite)
```

## Detener y limpiar volúmenes

```bash
docker compose down -v
```

Elimina volúmenes de Redis, Ollama y Chroma. Necesario tras cambiar el corpus o la colección Chroma.
