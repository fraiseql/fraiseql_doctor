.PHONY: install dev test test-unit test-integration test-performance lint format clean build tdd-cycle red green refactor

install:
	uv sync

dev:
	uv sync --dev

# Testing commands - Primary focus
test: test-unit test-integration
	@echo "All tests completed successfully!"

test-unit:
	uv run pytest tests/unit/ -v

test-integration: 
	uv run pytest tests/integration/ -v

test-performance:
	uv run pytest tests/ -m performance -v

test-coverage:
	uv run pytest --cov=src --cov-report=html --cov-report=term

test-watch:
	uv run pytest-watch -- tests/

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

# TDD workflow helpers
tdd-cycle:
	@echo "🔴 RED: Write failing test"
	@echo "🟢 GREEN: Make test pass"  
	@echo "🔵 REFACTOR: Improve code"

red:
	@echo "🔴 RED Phase: Write a failing test first!"
	uv run pytest tests/ -x -v

green:
	@echo "🟢 GREEN Phase: Make the test pass!"
	uv run pytest tests/ -x -v

refactor:
	@echo "🔵 REFACTOR Phase: Improve code while keeping tests green!"
	uv run pytest tests/ -v
	make lint
	make format

# Database operations
db-test-start:
	@echo "Starting test database container..."
	docker-compose -f docker-compose.test.yml up -d
	@echo "Waiting for database to be ready..."
	sleep 5

db-test-stop:
	@echo "Stopping test database container..."
	docker-compose -f docker-compose.test.yml down

db-test-setup: db-test-start
	@echo "Setting up test database..."
	sleep 2
	# Database is created automatically by container

db-test-reset: db-test-stop db-test-start
	@echo "Test database reset complete"