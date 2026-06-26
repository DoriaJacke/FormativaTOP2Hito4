.PHONY: up down build logs restart health ready reindex shell web-dev web-logs perfil-ligero perfil-medio perfil-alto

up:
	cp -n .env.example .env 2>/dev/null || true
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f api

web-logs:
	docker compose logs -f web

restart:
	docker compose restart api web

health:
	curl -s http://localhost:8000/health | python3 -m json.tool

ready:
	curl -s http://localhost:8000/health/ready | python3 -m json.tool

reindex:
	curl -s -X POST http://localhost:8000/admin/reindex | python3 -m json.tool

demo:
	curl -s -X POST http://localhost:8000/soporte/consultar \
		-H "Content-Type: application/json" \
		-d '{"ticket_id":"TKT-0042","session_id":"soporte:docker","nivel_usuario":"tecnico","consulta":"Mi contenedor web no inicia. Error: port is already allocated en puerto 8080."}' \
		| python3 -m json.tool

shell:
	docker compose exec api bash

web-dev:
	cd frontend && npm install && npm run dev

perfil-ligero:
	cp .env.perfil-ligero .env
	@echo "Perfil LIGERO activo (llama3.2:1b, ctx 2048, k=2). Ejecuta: make up"

perfil-medio:
	cp .env.perfil-medio .env
	@echo "Perfil MEDIO activo (llama3.2, ctx 4096). Ejecuta: make up"

perfil-alto:
	cp .env.perfil-alto .env
	@echo "Perfil ALTO activo (llama3.1:8b, ctx 8192). Ejecuta: make up"
