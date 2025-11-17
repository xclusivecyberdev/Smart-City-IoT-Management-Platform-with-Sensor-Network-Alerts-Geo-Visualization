.PHONY: help build up down restart logs clean test install dev-setup

help:
	@echo "Smart City IoT Platform - Make Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install       - Install all dependencies"
	@echo "  make dev-setup     - Set up development environment"
	@echo "  make build         - Build all Docker containers"
	@echo "  make up            - Start all services"
	@echo "  make down          - Stop all services"
	@echo "  make restart       - Restart all services"
	@echo "  make logs          - View logs from all services"
	@echo "  make clean         - Clean up containers and volumes"
	@echo "  make test          - Run tests"
	@echo "  make migrate       - Run database migrations"
	@echo "  make admin         - Create admin user"
	@echo "  make simulators    - Run device simulators"

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installing simulator dependencies..."
	cd device-simulators && pip install -r requirements.txt

dev-setup:
	@echo "Setting up development environment..."
	cp .env.example .env
	@echo "✓ Environment file created (.env)"
	@echo "Please edit .env with your configuration"
	mkdir -p config/mosquitto uploads firmware ml_models
	@echo "✓ Directories created"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started. Access:"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  API Docs:  http://localhost:8000/api/docs"
	@echo "  Grafana:   http://localhost:3001"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

clean:
	docker-compose down -v
	docker system prune -f

clean-all:
	docker-compose down -v --rmi all
	docker system prune -af

test:
	cd backend && pytest tests/ -v --cov

test-watch:
	cd backend && pytest-watch

migrate:
	docker-compose exec backend alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	docker-compose exec backend alembic revision --autogenerate -m "$$msg"

admin:
	docker-compose exec backend python scripts/create_admin.py

admin-default:
	docker-compose exec backend python scripts/create_admin.py --non-interactive

shell-backend:
	docker-compose exec backend bash

shell-db:
	docker-compose exec postgres psql -U smartcity -d smartcity_iot

simulators:
	cd device-simulators && ./run_simulators.sh

backup-db:
	@mkdir -p backups
	docker-compose exec -T postgres pg_dump -U smartcity smartcity_iot | \
		gzip > backups/backup_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "Database backup created in backups/"

restore-db:
	@read -p "Enter backup file path: " file; \
	gunzip -c $$file | docker-compose exec -T postgres psql -U smartcity smartcity_iot

status:
	docker-compose ps

health:
	@curl -s http://localhost:8000/health | python -m json.tool

# Development shortcuts
dev-backend:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm start

format:
	cd backend && black . && isort .

lint:
	cd backend && flake8 . && mypy .
	cd frontend && npm run lint

docs:
	@echo "Opening documentation..."
	@echo "README:        README.md"
	@echo "Architecture:  docs/ARCHITECTURE.md"
	@echo "Deployment:    docs/DEPLOYMENT.md"
	@echo "API Docs:      http://localhost:8000/api/docs"
