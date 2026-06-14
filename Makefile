# Define default shell environment flags
.PHONY: help build up down restart logs status shell-api shell-ui clean test

help:
	@echo "=========================================================================="
	@echo "                 Enterprise Research Agent Automation Makefile            "
	@echo "=========================================================================="
	@echo "Commands:"
	@echo "  make build      - Build or re-build all service containers"
	@echo "  make up         - Start all containers in decoupled detached background mode"
	@echo "  make down       - Tear down environment, stop execution, preserve volumes"
	@echo "  make restart    - Force rebuild orchestration layers and restart systems"
	@echo "  make logs       - Stream composite service logs across container nodes"
	@echo "  make status     - Check current runtime status of active containers"
	@echo "  make test       - Execute backend unit test suites using localized pytest"
	@echo "  make clean      - Complete purge of cache systems, docker volumes, and artifacts"
	@echo "=========================================================================="

build:
	docker compose build

up:
	docker compose up -d
	@echo "🚀 Systems Active!"
	@echo "   - API Gateway: http://localhost:8000"
	@echo "   - Chatbot UI:  http://localhost:8501"

down:
	docker compose down

restart:
	docker compose down
	docker compose up -d --build

logs:
	docker compose logs -f

status:
	docker compose ps

shell-api:
	docker exec -it research_api_gateway /bin/bash

shell-ui:
	docker exec -it research_streamlit_ui /bin/bash

test:
	pytest tests/ -v

clean:
	docker compose down -v
	rm -rf .pytest_cache .streamlit
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "🧹 Complete environment state cleaned."