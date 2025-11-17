.PHONY: help build up down re logs clean dev embed web

help:
	@echo "=== NADA AI RAG ==="
	@echo ""
	@echo "Commands:"
	@echo "  make build       - Build Docker image"
	@echo "  make up          - Start containers"
	@echo "  make down        - Stop and remove containers"
	@echo "  make re          - Restart containers"
	@echo "  make logs        - Show container logs"
	@echo "  make clean       - Remove containers, volumes, and image"
	@echo "  make dev         - Run API locally with uvicorn (requires pip install)"
	@echo "  make embed       - Run embedding script"
	@echo "  make web         - Run web frontend development server"
	@echo ""

build:
	docker compose build

up:
	docker compose up -d
	@echo "✅ API running at http://localhost:8000"
	@echo "📚 API docs at http://localhost:8000/docs"

down:
	docker compose down

re: down up

logs:
	docker compose logs -f api

clean:
	docker compose down -v
	docker rmi nada:latest 2>/dev/null || true

dev:
	cd api && source .env && uvicorn app.main:app --reload

embed:
	cd api && source .env && python scripts/embed_papers.py

web:
	cd web && python server.py
