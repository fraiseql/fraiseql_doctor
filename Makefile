.PHONY: install dev test lint format clean build

install:
	uv sync

dev:
	uv sync --dev

test:
	uv run pytest

test-cov:
	uv run pytest --cov=src --cov-report=html

lint:
	uv run ruff check .
	uv run mypy src

format:
	uv run ruff format .
	uv run ruff check --fix .

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:
	uv build

run:
	uv run fraiseql-doctor

db-upgrade:
	uv run alembic upgrade head

db-downgrade:
	uv run alembic downgrade -1

db-migration:
	uv run alembic revision --autogenerate -m "$(message)"