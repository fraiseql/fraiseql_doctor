# FraiseQL Doctor

A comprehensive health monitoring and testing tool for FraiseQL endpoints with a modern Vue.js dashboard.

## 📁 Project Structure (Monorepo)

This is a monorepo containing both backend and frontend applications:

```
fraiseql_doctor/
├── backend/           # Python backend (FastAPI + SQLAlchemy)
│   ├── src/          # Source code
│   ├── tests/        # Test suite (100% TDD coverage)
│   ├── alembic/      # Database migrations
│   └── pyproject.toml
├── frontend/         # Vue.js dashboard (Vue 3 + TypeScript)
│   ├── src/          # Vue components and services
│   ├── tests/        # Frontend tests
│   └── package.json
├── docs/             # Shared documentation
├── scripts/          # Build and deployment scripts
└── docker-compose.yml # Multi-service orchestration
```

## 🎯 Current Implementation Status

**Backend Status:** ✅ **COMPLETE** - TDD Implementation Phase 1-4  
**Frontend Status:** 🚧 **IN PROGRESS** - Phase 2.5 Vue.js Dashboard Implementation

## 🔄 TDD Development Phases

This project follows a strict Test-Driven Development approach across six phases:

### Phase 1: TDD Foundation Setup ⏳
**Status:** Ready to start  
**File:** `prompts/01_project_foundation_tdd.md`

- Test infrastructure established FIRST
- Project structure driven by failing tests
- Quality gates and development workflow
- Modern tooling: uv, ruff, pytest, docker

### Phase 2: Database Schema with TDD ⏳
**Status:** Pending  
**File:** `prompts/02_database_schema_tdd.md`

- Every model defined by failing tests
- Real database integration testing
- Performance benchmarks established
- Migration testing with Alembic

### Phase 3: FraiseQL Client with TDD ⏳
**Status:** Pending  
**File:** `prompts/03_fraiseql_client_tdd.md`

- HTTP behavior tested before implementation
- Authentication mechanisms validated
- Error handling and retry logic
- Performance and reliability testing

### Phase 4: Query Management with TDD ⏳
**Status:** Pending  
**File:** `prompts/04_query_management_tdd.md`

- Business logic driven by tests
- CRUD operations with validation
- Execution tracking and metrics
- Health monitoring workflows

### Phase 5: CLI Interface with TDD ⏳
**Status:** Pending  
**File:** `prompts/05_cli_interface_tdd.md`

- User experience validated through tests
- Command structure and help system
- Interactive features and dashboard
- Error handling and user guidance

### Phase 6: Testing Foundation ⏳
**Status:** Pending  
**File:** `prompts/06_testing_foundation.md`

- Advanced testing patterns
- Load and stress testing
- Performance baselines
- Quality assurance automation

## 🚀 Getting Started with TDD

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker (for test environment)
- uv package manager

### TDD Development Workflow

```bash
# 1. Start with Phase 1
cat prompts/01_project_foundation_tdd.md

# 2. Follow RED-GREEN-REFACTOR cycle
make red      # Write failing tests
make green    # Implement minimum to pass
make refactor # Improve while keeping tests green

# 3. Quality validation
make test     # Run all tests
make lint     # Code quality check
make coverage # Coverage validation
```

### TDD Principles

- **TESTS FIRST**: Every line of code justified by a failing test
- **RED-GREEN-REFACTOR**: Strict cycle enforcement
- **Real Testing**: No mocking of core business logic
- **Quality Gates**: Automated coverage and performance requirements
- **Production Ready**: Every feature thoroughly validated

## 📊 Quality Targets

- **Code Coverage**: 85%+ overall, 90%+ for core modules
- **Type Safety**: 100% type checking with mypy --strict
- **Code Quality**: Zero ruff errors, minimal warnings
- **Performance**: Database ops < 100ms, HTTP ops < 1s
- **Security**: Zero high-severity security issues
- **Reliability**: All stress tests pass

## 🏗️ Planned Architecture

### Technology Stack
- **Language**: Python 3.11+ with strict typing
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0+ async
- **HTTP Client**: aiohttp with connection pooling
- **CLI**: Typer with Rich formatting
- **Testing**: pytest with comprehensive fixtures
- **Quality**: ruff, mypy, bandit, coverage
- **Development**: uv, pre-commit, docker

### Core Components
- **Query Storage**: PostgreSQL with JSONB for flexible schemas
- **HTTP Client**: Production-ready GraphQL client with auth
- **Health Monitoring**: Continuous endpoint health tracking
- **CLI Interface**: Rich interactive command-line experience
- **Performance**: Built-in metrics and monitoring
- **Testing**: Comprehensive test infrastructure

## 🗃️ Archive Reference

The previous implementation (pre-TDD) is preserved in:
- **Branch**: `archive/20250816_first_try_without_tdd`
- **Status**: 43 passing tests, 60% coverage, basic functionality
- **Usage**: Reference for domain logic only, not implementation patterns

## 📚 Documentation

- **TDD Prompts**: `prompts/` directory contains phase-by-phase instructions
- **Development Workflow**: Follow prompts in sequence
- **Quality Standards**: Built into each phase
- **Archive Documentation**: `ARCHIVE_README.md` in archive branch

## 🎯 Success Criteria

This TDD implementation succeeds when:

1. **Every feature driven by failing tests first**
2. **90%+ test coverage with real database operations**
3. **Production-ready error handling and security**
4. **Performance validated through benchmarks**
5. **Comprehensive integration and stress testing**
6. **Clean, maintainable, well-documented codebase**

---

**Ready to start? Begin with Phase 1: `prompts/01_project_foundation_tdd.md`**