# 🔍 FraiseQL Doctor

**Health monitoring and query execution tool for FraiseQL/GraphQL endpoints**

FraiseQL Doctor is a comprehensive CLI tool designed to monitor, test, and manage GraphQL/FraiseQL endpoints. It provides query storage, health monitoring, performance analysis, and automated execution capabilities.

## ✨ Features

- 🏥 **Health Monitoring**: Continuous endpoint health checking with detailed metrics
- 📝 **Query Management**: Store, organize, and execute GraphQL queries with variables
- ⚡ **Performance Analysis**: Response time tracking and complexity analysis
- 🔄 **Scheduled Execution**: Cron-based query scheduling for monitoring
- 📊 **Rich CLI**: Beautiful command-line interface with tables and progress bars
- 🔐 **Authentication**: Support for Bearer tokens, API keys, and Basic auth
- 📈 **Metrics Collection**: Comprehensive performance and reliability metrics
- 🎯 **Batch Operations**: Execute multiple queries concurrently
- 📦 **Import/Export**: Share query collections via JSON/YAML

## 🚀 Quick Start

### Installation

```bash
# Install from source (development)
git clone https://github.com/your-org/fraiseql-doctor
cd fraiseql-doctor
make dev

# Test the installation
make run
```

### Example Usage

```bash
# Show version
fraiseql-doctor --version

# Test CLI
fraiseql-doctor hello

# Get help
fraiseql-doctor --help
```

## 🏗️ Development Status

This project is currently in active development. The basic CLI infrastructure is in place, and we're working on implementing the core features:

- [x] Project foundation and CLI structure
- [ ] Database models and schemas
- [ ] GraphQL client infrastructure
- [ ] Core business services
- [ ] Complete CLI commands
- [ ] Testing suite
- [ ] Documentation

## 🛠️ Development

### Prerequisites

- Python 3.11+
- uv (recommended) or pip

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/fraiseql-doctor
cd fraiseql-doctor

# Install dependencies
make dev

# Run tests
make test

# Run linting
make lint

# Format code
make format
```

### Project Structure

```
fraiseql_doctor/
├── src/
│   └── fraiseql_doctor/
│       ├── cli/          # CLI commands and interface
│       ├── core/         # Core configuration and exceptions
│       ├── models/       # Database models
│       ├── services/     # Business logic services
│       └── utils/        # Utility functions
├── tests/                # Test suite
├── docs/                 # Documentation
└── scripts/              # Build and deployment scripts
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.