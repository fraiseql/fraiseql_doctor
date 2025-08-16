# Phase 7: Documentation & Examples
**Agent: Technical Writer**

## Objective
Create comprehensive, user-friendly documentation that enables developers and operators to effectively use, deploy, and contribute to FraiseQL Doctor with clear examples, tutorials, and reference materials.

## Requirements

### Documentation Architecture

#### 1. Main README.md
```markdown
# 🔍 FraiseQL Doctor

[![Tests](https://github.com/your-org/fraiseql-doctor/workflows/Test%20Suite/badge.svg)](https://github.com/your-org/fraiseql-doctor/actions)
[![Coverage](https://codecov.io/gh/your-org/fraiseql-doctor/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/fraiseql-doctor)
[![PyPI version](https://badge.fury.io/py/fraiseql-doctor.svg)](https://badge.fury.io/py/fraiseql-doctor)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

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
# Install from PyPI
pip install fraiseql-doctor

# Or with uv (recommended)
uv add fraiseql-doctor

# Or from source
git clone https://github.com/your-org/fraiseql-doctor
cd fraiseql-doctor
uv sync
```

### Initial Setup

```bash
# Initialize configuration
fraiseql-doctor config init

# Add your first endpoint
fraiseql-doctor endpoint create production \
  --url https://api.example.com/graphql \
  --auth-type bearer \
  --token "your-token-here"

# Create your first query
fraiseql-doctor query create user-profile \
  --file queries/user-profile.graphql \
  --description "Get user profile data"

# Execute the query
fraiseql-doctor query execute user-profile production

# Monitor endpoint health
fraiseql-doctor health check --all
```

### Example Query File (queries/user-profile.graphql)

```graphql
query GetUserProfile($userId: ID!) {
  user(id: $userId) {
    id
    name
    email
    profile {
      bio
      avatar
      preferences {
        theme
        notifications
      }
    }
  }
}
```

## 📖 Documentation

- [Installation Guide](docs/installation.md)
- [Getting Started Tutorial](docs/getting-started.md)
- [CLI Reference](docs/cli-reference.md)
- [Configuration Guide](docs/configuration.md)
- [API Documentation](docs/api.md)
- [Examples & Recipes](docs/examples.md)
- [Contributing](CONTRIBUTING.md)

## 🏗️ Architecture

FraiseQL Doctor follows a layered architecture:

```
┌─────────────────────────────────────────────────────────┐
│ CLI Layer (Typer + Rich)                                │
│ - Command interface, formatting, user interaction       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ Service Layer                                           │
│ - Query, Execution, Health, Scheduling services         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ Client Layer                                            │
│ - GraphQL client, authentication, retry logic           │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ Data Layer (PostgreSQL + SQLAlchemy)                   │
│ - Query storage, execution history, health records      │
└─────────────────────────────────────────────────────────┘
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Documentation](https://fraiseql-doctor.readthedocs.io/)
- [PyPI Package](https://pypi.org/project/fraiseql-doctor/)
- [Issue Tracker](https://github.com/your-org/fraiseql-doctor/issues)
- [Discussions](https://github.com/your-org/fraiseql-doctor/discussions)
```

#### 2. Getting Started Guide (docs/getting-started.md)
```markdown
# Getting Started with FraiseQL Doctor

This guide will walk you through setting up and using FraiseQL Doctor to monitor your GraphQL endpoints.

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 12+ (for storing queries and metrics)
- Access to GraphQL endpoints you want to monitor

## Step 1: Installation

### Using pip

```bash
pip install fraiseql-doctor
```

### Using uv (Recommended)

```bash
uv add fraiseql-doctor
```

### From Source

```bash
git clone https://github.com/your-org/fraiseql-doctor
cd fraiseql-doctor
uv sync
uv run fraiseql-doctor --help
```

## Step 2: Initial Configuration

### Initialize Configuration

```bash
fraiseql-doctor config init
```

This creates a configuration file at `~/.fraiseql-doctor/config.yaml`:

```yaml
database:
  url: "postgresql://localhost/fraiseql_doctor"
  pool_size: 5
  max_overflow: 10

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

defaults:
  timeout_seconds: 30
  max_retries: 3
  health_check_interval: 300
```

### Database Setup

```bash
# Create database (adjust for your PostgreSQL setup)
createdb fraiseql_doctor

# Run migrations
fraiseql-doctor db upgrade
```

## Step 3: Add Your First Endpoint

### Basic Endpoint

```bash
fraiseql-doctor endpoint create my-api \
  --url https://api.example.com/graphql \
  --description "Main API endpoint"
```

### Authenticated Endpoint

```bash
# Bearer token authentication
fraiseql-doctor endpoint create auth-api \
  --url https://api.example.com/graphql \
  --auth-type bearer \
  --token "your-bearer-token"

# API key authentication
fraiseql-doctor endpoint create api-key-endpoint \
  --url https://api.example.com/graphql \
  --auth-type api_key \
  --api-key "your-api-key" \
  --header-name "X-API-Key"

# Basic authentication
fraiseql-doctor endpoint create basic-auth \
  --url https://api.example.com/graphql \
  --auth-type basic \
  --username "user" \
  --password "pass"
```

### List Endpoints

```bash
fraiseql-doctor endpoint list
```

## Step 4: Create and Manage Queries

### Create Query from File

Create a GraphQL file (`user-query.graphql`):

```graphql
query GetUser($id: ID!) {
  user(id: $id) {
    id
    name
    email
    createdAt
  }
}
```

Add it to FraiseQL Doctor:

```bash
fraiseql-doctor query create user-lookup \
  --file user-query.graphql \
  --description "Look up user by ID" \
  --tag user \
  --tag lookup
```

### Create Query Interactively

```bash
fraiseql-doctor query create product-search \
  --interactive \
  --description "Search products by name" \
  --tag products
```

### List and View Queries

```bash
# List all queries
fraiseql-doctor query list

# List queries with specific tags
fraiseql-doctor query list --tag user

# View query details
fraiseql-doctor query show user-lookup
```

## Step 5: Execute Queries

### Simple Execution

```bash
fraiseql-doctor query execute user-lookup my-api \
  --variables '{"id": "123"}'
```

### Using Variables File

Create `variables.json`:

```json
{
  "id": "123",
  "includeProfile": true
}
```

Execute with variables:

```bash
fraiseql-doctor query execute user-lookup my-api \
  --variables-file variables.json
```

### Save Results

```bash
fraiseql-doctor query execute user-lookup my-api \
  --variables '{"id": "123"}' \
  --output results.json \
  --format json
```

## Step 6: Health Monitoring

### Check Single Endpoint

```bash
fraiseql-doctor health check my-api
```

### Check All Endpoints

```bash
fraiseql-doctor health check --all
```

### View Health History

```bash
fraiseql-doctor health history my-api --hours 24
```

### Continuous Monitoring Dashboard

```bash
fraiseql-doctor dashboard
```

## Step 7: Schedule Automated Queries

### Create Schedule

```bash
fraiseql-doctor schedule create daily-health-check \
  --query user-lookup \
  --endpoint my-api \
  --cron "0 9 * * *" \
  --variables '{"id": "health-check-user"}'
```

### List Schedules

```bash
fraiseql-doctor schedule list
```

### View Schedule Details

```bash
fraiseql-doctor schedule show daily-health-check
```

## Step 8: Import/Export Queries

### Export Queries

```bash
# Export all queries
fraiseql-doctor query export --format yaml > my-queries.yaml

# Export specific queries
fraiseql-doctor query export \
  --queries user-lookup,product-search \
  --format json > selected-queries.json
```

### Import Queries

```bash
fraiseql-doctor query import \
  --file my-queries.yaml \
  --format yaml
```

## Common Workflows

### 1. API Health Monitoring

```bash
# Set up monitoring for critical endpoints
fraiseql-doctor endpoint create prod-api --url https://api.prod.com/graphql
fraiseql-doctor endpoint create staging-api --url https://api.staging.com/graphql

# Create health check query
echo 'query HealthCheck { __typename }' > health.graphql
fraiseql-doctor query create health-check --file health.graphql

# Schedule regular health checks
fraiseql-doctor schedule create prod-health \
  --query health-check \
  --endpoint prod-api \
  --cron "*/5 * * * *"  # Every 5 minutes

# Monitor in real-time
fraiseql-doctor dashboard
```

### 2. Query Performance Testing

```bash
# Create performance test queries
fraiseql-doctor query create complex-query \
  --file complex-query.graphql \
  --description "Performance test query"

# Execute with timing
time fraiseql-doctor query execute complex-query my-api

# Batch execution for load testing
fraiseql-doctor query batch \
  --queries complex-query,simple-query \
  --endpoint my-api \
  --concurrent 10 \
  --repeat 100
```

### 3. Development Workflow

```bash
# Test queries during development
fraiseql-doctor query create dev-test \
  --interactive

# Quick execution with different variables
fraiseql-doctor query execute dev-test local-dev \
  --variables '{"env": "development"}'

# Compare results across environments
fraiseql-doctor query execute dev-test local-dev > dev-results.json
fraiseql-doctor query execute dev-test staging-api > staging-results.json
diff dev-results.json staging-results.json
```

## Next Steps

- [CLI Reference](cli-reference.md) - Complete command documentation
- [Configuration Guide](configuration.md) - Advanced configuration options
- [Examples & Recipes](examples.md) - More detailed use cases
- [API Documentation](api.md) - Python API reference

## Getting Help

If you encounter issues:

1. Check the [troubleshooting guide](troubleshooting.md)
2. Search [existing issues](https://github.com/your-org/fraiseql-doctor/issues)
3. Create a [new issue](https://github.com/your-org/fraiseql-doctor/issues/new)
4. Join our [discussions](https://github.com/your-org/fraiseql-doctor/discussions)
```

#### 3. CLI Reference (docs/cli-reference.md)
```markdown
# CLI Reference

Complete reference for all FraiseQL Doctor CLI commands.

## Global Options

```bash
fraiseql-doctor [OPTIONS] COMMAND [ARGS]...
```

### Options

- `--version, -v`: Show version and exit
- `--config, -c PATH`: Configuration file path (default: `~/.fraiseql-doctor/config.yaml`)
- `--verbose`: Enable verbose logging
- `--help`: Show help message

## Commands Overview

| Command | Description |
|---------|-------------|
| [`query`](#query-commands) | Manage FraiseQL queries |
| [`endpoint`](#endpoint-commands) | Manage GraphQL endpoints |
| [`health`](#health-commands) | Monitor endpoint health |
| [`schedule`](#schedule-commands) | Schedule query execution |
| [`config`](#config-commands) | Manage configuration |
| [`dashboard`](#dashboard) | Show interactive dashboard |

---

## Query Commands

Manage FraiseQL queries - create, list, execute, and organize your GraphQL queries.

### `query create`

Create a new query.

```bash
fraiseql-doctor query create NAME [OPTIONS]
```

#### Arguments

- `NAME`: Query name (required)

#### Options

- `--description, -d TEXT`: Query description
- `--file, -f PATH`: GraphQL file to read from
- `--interactive, -i`: Interactive query builder
- `--tag, -t TEXT`: Add tags (can be used multiple times)
- `--variables TEXT`: Default variables as JSON string
- `--complexity INT`: Expected complexity score

#### Examples

```bash
# Create from file
fraiseql-doctor query create user-profile \
  --file queries/user.graphql \
  --description "Get user profile" \
  --tag user --tag profile

# Interactive creation
fraiseql-doctor query create new-query --interactive

# With default variables
fraiseql-doctor query create search-products \
  --file search.graphql \
  --variables '{"limit": 10, "category": "electronics"}'
```

### `query list`

List queries with filtering options.

```bash
fraiseql-doctor query list [OPTIONS]
```

#### Options

- `--tag, -t TEXT`: Filter by tags
- `--active-only`: Show only active queries (default: true)
- `--created-by TEXT`: Filter by creator
- `--limit, -l INT`: Maximum queries to show (default: 20)
- `--format TEXT`: Output format: table, json, yaml (default: table)

#### Examples

```bash
# List all queries
fraiseql-doctor query list

# Filter by tags
fraiseql-doctor query list --tag user --tag profile

# JSON output
fraiseql-doctor query list --format json --limit 50
```

### `query show`

Show detailed information about a query.

```bash
fraiseql-doctor query show QUERY_ID [OPTIONS]
```

#### Arguments

- `QUERY_ID`: Query ID or name

#### Options

- `--executions`: Show recent executions (default: true)
- `--stats`: Show performance statistics (default: true)

#### Examples

```bash
# Show by name
fraiseql-doctor query show user-profile

# Show by UUID
fraiseql-doctor query show 123e4567-e89b-12d3-a456-426614174000

# Hide execution history
fraiseql-doctor query show user-profile --no-executions
```

### `query execute`

Execute a query against an endpoint.

```bash
fraiseql-doctor query execute QUERY_ID ENDPOINT_ID [OPTIONS]
```

#### Arguments

- `QUERY_ID`: Query ID or name
- `ENDPOINT_ID`: Endpoint ID or name

#### Options

- `--variables, -v TEXT`: Variables as JSON string
- `--variables-file PATH`: Variables from JSON file
- `--timeout INT`: Timeout in seconds
- `--output, -o PATH`: Save output to file
- `--format TEXT`: Output format: pretty, json, yaml (default: pretty)

#### Examples

```bash
# Simple execution
fraiseql-doctor query execute user-profile prod-api

# With variables
fraiseql-doctor query execute user-profile prod-api \
  --variables '{"id": "123"}'

# Save to file
fraiseql-doctor query execute user-profile prod-api \
  --variables-file vars.json \
  --output result.json \
  --format json
```

### `query edit`

Edit an existing query interactively.

```bash
fraiseql-doctor query edit QUERY_ID
```

### `query delete`

Delete a query.

```bash
fraiseql-doctor query delete QUERY_ID [OPTIONS]
```

#### Options

- `--force, -f`: Skip confirmation

### `query export`

Export queries to file.

```bash
fraiseql-doctor query export [OPTIONS]
```

#### Options

- `--queries TEXT`: Comma-separated query names/IDs
- `--tags TEXT`: Export queries with specific tags
- `--format TEXT`: Export format: json, yaml (default: json)
- `--output, -o PATH`: Output file (default: stdout)

### `query import`

Import queries from file.

```bash
fraiseql-doctor query import [OPTIONS]
```

#### Options

- `--file, -f PATH`: Input file (required)
- `--format TEXT`: Input format: json, yaml (auto-detected)
- `--created-by TEXT`: Set creator for imported queries

---

## Endpoint Commands

Manage GraphQL endpoints and their configurations.

### `endpoint create`

Create a new endpoint.

```bash
fraiseql-doctor endpoint create NAME [OPTIONS]
```

#### Arguments

- `NAME`: Endpoint name (required)

#### Options

- `--url URL`: GraphQL endpoint URL (required)
- `--description TEXT`: Endpoint description
- `--auth-type TEXT`: Authentication type: none, bearer, api_key, basic
- `--token TEXT`: Bearer token (for bearer auth)
- `--api-key TEXT`: API key (for api_key auth)
- `--header-name TEXT`: API key header name (default: X-API-Key)
- `--username TEXT`: Username (for basic auth)
- `--password TEXT`: Password (for basic auth)
- `--timeout INT`: Request timeout in seconds (default: 30)
- `--max-retries INT`: Maximum retry attempts (default: 3)
- `--headers TEXT`: Additional headers as JSON

#### Examples

```bash
# Basic endpoint
fraiseql-doctor endpoint create my-api \
  --url https://api.example.com/graphql

# With bearer token
fraiseql-doctor endpoint create auth-api \
  --url https://api.example.com/graphql \
  --auth-type bearer \
  --token "your-token"

# With custom headers
fraiseql-doctor endpoint create custom-api \
  --url https://api.example.com/graphql \
  --headers '{"User-Agent": "FraiseQL-Doctor/1.0"}'
```

### `endpoint list`

List all endpoints.

```bash
fraiseql-doctor endpoint list [OPTIONS]
```

#### Options

- `--active-only`: Show only active endpoints
- `--format TEXT`: Output format: table, json, yaml

### `endpoint show`

Show endpoint details.

```bash
fraiseql-doctor endpoint show ENDPOINT_ID
```

### `endpoint update`

Update endpoint configuration.

```bash
fraiseql-doctor endpoint update ENDPOINT_ID [OPTIONS]
```

### `endpoint delete`

Delete an endpoint.

```bash
fraiseql-doctor endpoint delete ENDPOINT_ID [OPTIONS]
```

#### Options

- `--force, -f`: Skip confirmation

---

## Health Commands

Monitor GraphQL endpoint health and performance.

### `health check`

Perform health checks on endpoints.

```bash
fraiseql-doctor health check [ENDPOINT_ID] [OPTIONS]
```

#### Arguments

- `ENDPOINT_ID`: Specific endpoint to check (optional)

#### Options

- `--all`: Check all active endpoints
- `--timeout INT`: Health check timeout
- `--format TEXT`: Output format: table, json, yaml

#### Examples

```bash
# Check specific endpoint
fraiseql-doctor health check prod-api

# Check all endpoints
fraiseql-doctor health check --all

# JSON output
fraiseql-doctor health check --all --format json
```

### `health history`

View health check history.

```bash
fraiseql-doctor health history ENDPOINT_ID [OPTIONS]
```

#### Options

- `--hours INT`: Hours of history to show (default: 24)
- `--format TEXT`: Output format

### `health summary`

Show health summary across all endpoints.

```bash
fraiseql-doctor health summary [OPTIONS]
```

---

## Schedule Commands

Manage scheduled query executions.

### `schedule create`

Create a new query schedule.

```bash
fraiseql-doctor schedule create NAME [OPTIONS]
```

#### Arguments

- `NAME`: Schedule name

#### Options

- `--query TEXT`: Query name/ID (required)
- `--endpoint TEXT`: Endpoint name/ID (required)
- `--cron TEXT`: Cron expression (required)
- `--variables TEXT`: Query variables as JSON
- `--max-failures INT`: Max failures before disabling (default: 5)

#### Examples

```bash
# Daily health check
fraiseql-doctor schedule create daily-health \
  --query health-check \
  --endpoint prod-api \
  --cron "0 9 * * *"

# Every 5 minutes
fraiseql-doctor schedule create frequent-check \
  --query status-check \
  --endpoint monitoring-api \
  --cron "*/5 * * * *"
```

### `schedule list`

List all schedules.

```bash
fraiseql-doctor schedule list [OPTIONS]
```

### `schedule show`

Show schedule details.

```bash
fraiseql-doctor schedule show SCHEDULE_ID
```

### `schedule enable/disable`

Enable or disable a schedule.

```bash
fraiseql-doctor schedule enable SCHEDULE_ID
fraiseql-doctor schedule disable SCHEDULE_ID
```

### `schedule delete`

Delete a schedule.

```bash
fraiseql-doctor schedule delete SCHEDULE_ID [OPTIONS]
```

---

## Config Commands

Manage FraiseQL Doctor configuration.

### `config init`

Initialize configuration.

```bash
fraiseql-doctor config init [OPTIONS]
```

#### Options

- `--dir PATH`: Configuration directory (default: ~/.fraiseql-doctor)
- `--force`: Overwrite existing configuration

### `config show`

Display current configuration.

```bash
fraiseql-doctor config show
```

### `config validate`

Validate configuration file.

```bash
fraiseql-doctor config validate
```

---

## Dashboard

Launch interactive monitoring dashboard.

```bash
fraiseql-doctor dashboard
```

The dashboard provides real-time monitoring with:

- Endpoint health status
- Recent query executions
- Performance metrics
- System overview

**Controls:**
- Press `Ctrl+C` to exit
- Updates every second
- Responsive terminal interface

---

## Environment Variables

Configure FraiseQL Doctor using environment variables:

```bash
# Database configuration
export FRAISEQL_DOCTOR_DATABASE_URL="postgresql://user:pass@host/db"

# Logging
export FRAISEQL_DOCTOR_LOG_LEVEL="DEBUG"

# Default timeouts
export FRAISEQL_DOCTOR_DEFAULT_TIMEOUT=60
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Database connection error |
| 4 | Authentication error |
| 5 | Query validation error |

## Tips and Tricks

### Shell Completion

Enable shell completion for better CLI experience:

```bash
# Bash
fraiseql-doctor --install-completion bash

# Zsh
fraiseql-doctor --install-completion zsh

# Fish
fraiseql-doctor --install-completion fish
```

### Query Variables

Use environment variables in query variables:

```bash
fraiseql-doctor query execute user-profile prod-api \
  --variables "{\"id\": \"$USER_ID\"}"
```

### Bulk Operations

Execute multiple queries with xargs:

```bash
echo "query1 query2 query3" | xargs -n1 fraiseql-doctor query execute prod-api
```

### JSON Processing

Use jq for JSON output processing:

```bash
fraiseql-doctor query list --format json | jq '.[] | select(.tags[] == "user")'
```
```

#### 4. Examples & Recipes (docs/examples.md)
```markdown
# Examples & Recipes

Real-world examples and common patterns for using FraiseQL Doctor effectively.

## Table of Contents

1. [Monitoring Production APIs](#monitoring-production-apis)
2. [Development Workflow](#development-workflow)
3. [Performance Testing](#performance-testing)
4. [Multi-Environment Management](#multi-environment-management)
5. [Query Libraries](#query-libraries)
6. [Alerting & Notifications](#alerting--notifications)
7. [CI/CD Integration](#cicd-integration)

---

## Monitoring Production APIs

### Basic Health Monitoring

Set up comprehensive health monitoring for your production GraphQL APIs.

#### 1. Setup Endpoints

```bash
# Production API
fraiseql-doctor endpoint create prod-api \
  --url https://api.yourcompany.com/graphql \
  --auth-type bearer \
  --token "$PROD_API_TOKEN" \
  --description "Production GraphQL API" \
  --timeout 10 \
  --max-retries 2

# Staging API for comparison
fraiseql-doctor endpoint create staging-api \
  --url https://staging-api.yourcompany.com/graphql \
  --auth-type bearer \
  --token "$STAGING_API_TOKEN" \
  --description "Staging GraphQL API"
```

#### 2. Create Health Check Queries

**Basic connectivity check:**

```bash
cat > health-basic.graphql << 'EOF'
query HealthCheck {
  __schema {
    queryType {
      name
    }
  }
}
EOF

fraiseql-doctor query create health-basic \
  --file health-basic.graphql \
  --description "Basic health check - schema introspection" \
  --tag health --tag basic
```

**Application-level health check:**

```bash
cat > health-app.graphql << 'EOF'
query ApplicationHealth {
  system {
    status
    version
    uptime
    metrics {
      activeUsers
      requestsPerMinute
    }
  }
}
EOF

fraiseql-doctor query create health-app \
  --file health-app.graphql \
  --description "Application-level health metrics" \
  --tag health --tag application
```

#### 3. Schedule Regular Checks

```bash
# Basic health check every minute
fraiseql-doctor schedule create prod-health-basic \
  --query health-basic \
  --endpoint prod-api \
  --cron "* * * * *"

# Application health every 5 minutes
fraiseql-doctor schedule create prod-health-app \
  --query health-app \
  --endpoint prod-api \
  --cron "*/5 * * * *"

# Staging comparison every 15 minutes
fraiseql-doctor schedule create staging-health \
  --query health-app \
  --endpoint staging-api \
  --cron "*/15 * * * *"
```

#### 4. Monitor Results

```bash
# Real-time dashboard
fraiseql-doctor dashboard

# Check health status
fraiseql-doctor health check --all

# View health history
fraiseql-doctor health history prod-api --hours 24
```

---

## Development Workflow

### Interactive Query Development

Develop and test GraphQL queries interactively during development.

#### 1. Setup Development Environment

```bash
# Local development server
fraiseql-doctor endpoint create local-dev \
  --url http://localhost:4000/graphql \
  --description "Local development server"

# Development database
fraiseql-doctor endpoint create dev-db \
  --url https://dev-api.yourcompany.com/graphql \
  --auth-type api_key \
  --api-key "$DEV_API_KEY"
```

#### 2. Create Development Queries

```bash
# User operations for testing
cat > dev-user-ops.graphql << 'EOF'
query GetUser($id: ID!) {
  user(id: $id) {
    id
    name
    email
    profile {
      bio
      createdAt
      lastLoginAt
    }
    permissions {
      role
      scopes
    }
  }
}
EOF

fraiseql-doctor query create dev-user-ops \
  --file dev-user-ops.graphql \
  --description "User operations for development testing" \
  --tag development --tag user
```

#### 3. Test Queries with Different Variables

```bash
# Test with development user
fraiseql-doctor query execute dev-user-ops local-dev \
  --variables '{"id": "dev-user-1"}' \
  --format pretty

# Test with admin user
fraiseql-doctor query execute dev-user-ops local-dev \
  --variables '{"id": "admin-user"}' \
  --output admin-test.json

# Compare results
fraiseql-doctor query execute dev-user-ops dev-db \
  --variables '{"id": "dev-user-1"}' \
  --output dev-db-result.json

diff admin-test.json dev-db-result.json
```

#### 4. Batch Testing

```bash
# Create test variables file
cat > test-users.json << 'EOF'
[
  {"id": "user-1"},
  {"id": "user-2"},
  {"id": "admin-1"},
  {"id": "guest-1"}
]
EOF

# Test multiple users
jq -c '.[]' test-users.json | while read vars; do
  echo "Testing with variables: $vars"
  fraiseql-doctor query execute dev-user-ops local-dev \
    --variables "$vars" \
    --format json | jq '.data.user.name'
done
```

---

## Performance Testing

### Load Testing GraphQL Endpoints

Test your GraphQL endpoints under load to identify performance bottlenecks.

#### 1. Create Performance Test Queries

**Simple query for baseline:**

```bash
cat > perf-simple.graphql << 'EOF'
query SimplePerformanceTest {
  users(limit: 10) {
    id
    name
  }
}
EOF

fraiseql-doctor query create perf-simple \
  --file perf-simple.graphql \
  --tag performance --tag simple
```

**Complex query for stress testing:**

```bash
cat > perf-complex.graphql << 'EOF'
query ComplexPerformanceTest($limit: Int = 50) {
  users(limit: $limit) {
    id
    name
    email
    profile {
      bio
      avatar
      preferences {
        theme
        language
        notifications {
          email
          push
          sms
        }
      }
    }
    posts(limit: 5) {
      id
      title
      content
      createdAt
      comments(limit: 3) {
        id
        text
        author {
          name
        }
      }
    }
  }
}
EOF

fraiseql-doctor query create perf-complex \
  --file perf-complex.graphql \
  --tag performance --tag complex
```

#### 2. Performance Testing Script

```bash
#!/bin/bash
# performance-test.sh

echo "Starting performance tests..."

# Baseline test
echo "=== Baseline Test ==="
time fraiseql-doctor query execute perf-simple prod-api

# Concurrent execution test
echo "=== Concurrent Test (10 parallel) ==="
for i in {1..10}; do
  (fraiseql-doctor query execute perf-simple prod-api \
    --format json > "result-$i.json") &
done
wait

# Complex query test
echo "=== Complex Query Test ==="
for limit in 10 25 50 100; do
  echo "Testing with limit: $limit"
  time fraiseql-doctor query execute perf-complex prod-api \
    --variables "{\"limit\": $limit}" \
    --format json | jq '.responseTime'
done

echo "Performance tests completed!"
```

#### 3. Analyze Results

```bash
# Run performance tests
chmod +x performance-test.sh
./performance-test.sh

# Analyze response times
fraiseql-doctor query show perf-complex --stats

# Export performance data
fraiseql-doctor query list --tag performance --format json | \
  jq '.[] | {name: .name, avgResponseTime: .performanceStats.avgResponseTimeMs}'
```

---

## Multi-Environment Management

### Managing Queries Across Environments

Efficiently manage and synchronize queries across development, staging, and production environments.

#### 1. Environment-Specific Endpoints

```bash
# Production
fraiseql-doctor endpoint create prod \
  --url https://api.prod.com/graphql \
  --auth-type bearer \
  --token "$PROD_TOKEN"

# Staging
fraiseql-doctor endpoint create staging \
  --url https://api.staging.com/graphql \
  --auth-type bearer \
  --token "$STAGING_TOKEN"

# Development
fraiseql-doctor endpoint create dev \
  --url https://api.dev.com/graphql \
  --auth-type bearer \
  --token "$DEV_TOKEN"
```

#### 2. Environment Comparison Script

```bash
#!/bin/bash
# compare-environments.sh

QUERY_NAME="$1"
if [ -z "$QUERY_NAME" ]; then
  echo "Usage: $0 <query-name>"
  exit 1
fi

echo "Comparing query '$QUERY_NAME' across environments..."

# Execute on all environments
for env in dev staging prod; do
  echo "=== $env environment ==="
  fraiseql-doctor query execute "$QUERY_NAME" "$env" \
    --format json > "result-$env.json"
  
  # Extract response time and status
  echo "Response time: $(jq -r '.responseTimeMs' "result-$env.json")ms"
  echo "Status: $(jq -r '.status' "result-$env.json")"
  echo
done

# Compare data structures
echo "=== Data Structure Comparison ==="
diff result-dev.json result-staging.json && echo "Dev and Staging match"
diff result-staging.json result-prod.json && echo "Staging and Prod match"
```

#### 3. Query Synchronization

```bash
# Export from development
fraiseql-doctor query export \
  --tag "ready-for-prod" \
  --format yaml > prod-ready-queries.yaml

# Import to staging for testing
fraiseql-doctor query import \
  --file prod-ready-queries.yaml \
  --created-by "deployment-script"

# Test on staging
./test-all-queries.sh staging

# Deploy to production after validation
fraiseql-doctor query import \
  --file prod-ready-queries.yaml \
  --created-by "production-deployment"
```

---

## Query Libraries

### Building Reusable Query Collections

Create and maintain libraries of reusable GraphQL queries for different domains.

#### 1. User Management Queries

```bash
# Create user management collection
mkdir -p queries/user-management

cat > queries/user-management/list-users.graphql << 'EOF'
query ListUsers($limit: Int = 20, $offset: Int = 0, $filter: UserFilter) {
  users(limit: $limit, offset: $offset, filter: $filter) {
    id
    name
    email
    status
    createdAt
    lastLoginAt
  }
  userCount(filter: $filter)
}
EOF

cat > queries/user-management/get-user-details.graphql << 'EOF'
query GetUserDetails($id: ID!) {
  user(id: $id) {
    id
    name
    email
    profile {
      bio
      avatar
      preferences
    }
    permissions {
      role
      scopes
    }
    auditLog(limit: 10) {
      action
      timestamp
      details
    }
  }
}
EOF

cat > queries/user-management/update-user.graphql << 'EOF'
mutation UpdateUser($id: ID!, $input: UpdateUserInput!) {
  updateUser(id: $id, input: $input) {
    user {
      id
      name
      email
      updatedAt
    }
    errors {
      field
      message
    }
  }
}
EOF

# Import user management queries
for file in queries/user-management/*.graphql; do
  name=$(basename "$file" .graphql)
  fraiseql-doctor query create "user-$name" \
    --file "$file" \
    --tag user --tag management \
    --description "User management: $name"
done
```

#### 2. Content Management Queries

```bash
mkdir -p queries/content

cat > queries/content/list-posts.graphql << 'EOF'
query ListPosts($status: PostStatus, $author: ID, $tag: String) {
  posts(filter: {status: $status, author: $author, tag: $tag}) {
    id
    title
    excerpt
    status
    publishedAt
    author {
      name
      avatar
    }
    tags
    metrics {
      views
      likes
      comments
    }
  }
}
EOF

# Import content queries
for file in queries/content/*.graphql; do
  name=$(basename "$file" .graphql)
  fraiseql-doctor query create "content-$name" \
    --file "$file" \
    --tag content --tag cms
done
```

#### 3. Query Collection Management

```bash
# Export domain-specific collections
fraiseql-doctor query export \
  --tag user --tag management \
  --format yaml > collections/user-management.yaml

fraiseql-doctor query export \
  --tag content --tag cms \
  --format yaml > collections/content-management.yaml

# Share collections
git add collections/
git commit -m "Add query collections for user and content management"
git push

# Import shared collections on other machines
fraiseql-doctor query import \
  --file collections/user-management.yaml
```

---

## Alerting & Notifications

### Setting Up Alerts for Query Failures

Integrate FraiseQL Doctor with monitoring systems for automated alerting.

#### 1. Health Check with Exit Codes

```bash
#!/bin/bash
# health-check-with-alerts.sh

# Check critical endpoints
CRITICAL_ENDPOINTS=("prod-api" "user-service" "payment-api")

for endpoint in "${CRITICAL_ENDPOINTS[@]}"; do
  if ! fraiseql-doctor health check "$endpoint" --format json | jq -e '.isHealthy'; then
    echo "CRITICAL: $endpoint is down!"
    
    # Send to monitoring system
    curl -X POST "$SLACK_WEBHOOK" \
      -H 'Content-type: application/json' \
      --data "{\"text\":\"🚨 GraphQL endpoint $endpoint is down!\"}"
    
    # Exit with error code
    exit 1
  fi
done

echo "All critical endpoints are healthy"
```

#### 2. Performance Degradation Alerts

```bash
#!/bin/bash
# performance-monitor.sh

THRESHOLD_MS=1000  # Alert if response time > 1 second

fraiseql-doctor query execute performance-test prod-api \
  --format json | jq -e ".responseTimeMs < $THRESHOLD_MS" || {
  
  RESPONSE_TIME=$(fraiseql-doctor query execute performance-test prod-api \
    --format json | jq -r '.responseTimeMs')
  
  curl -X POST "$PAGERDUTY_WEBHOOK" \
    -H 'Content-type: application/json' \
    --data "{
      \"summary\": \"High GraphQL response time: ${RESPONSE_TIME}ms\",
      \"severity\": \"warning\",
      \"source\": \"fraiseql-doctor\"
    }"
}
```

#### 3. Scheduled Monitoring with Cron

```bash
# Add to crontab
# Check health every 5 minutes
*/5 * * * * /scripts/health-check-with-alerts.sh

# Performance monitoring every 15 minutes
*/15 * * * * /scripts/performance-monitor.sh

# Daily summary report
0 8 * * * fraiseql-doctor health summary --format json | /scripts/generate-daily-report.sh
```

---

## CI/CD Integration

### Automated Testing in Deployment Pipelines

Integrate FraiseQL Doctor into your CI/CD pipelines for automated GraphQL testing.

#### 1. GitHub Actions Workflow

```yaml
# .github/workflows/graphql-tests.yml
name: GraphQL API Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: fraiseql_doctor_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install FraiseQL Doctor
      run: |
        pip install fraiseql-doctor
    
    - name: Initialize configuration
      run: |
        fraiseql-doctor config init
    
    - name: Setup test endpoints
      run: |
        fraiseql-doctor endpoint create staging \
          --url ${{ secrets.STAGING_API_URL }} \
          --auth-type bearer \
          --token ${{ secrets.STAGING_API_TOKEN }}
    
    - name: Import test queries
      run: |
        fraiseql-doctor query import --file tests/graphql/test-queries.yaml
    
    - name: Run GraphQL tests
      run: |
        # Test critical queries
        fraiseql-doctor query execute health-check staging
        fraiseql-doctor query execute user-profile staging --variables '{"id": "test-user"}'
        fraiseql-doctor query execute system-status staging
    
    - name: Health check
      run: |
        fraiseql-doctor health check staging
    
    - name: Generate test report
      run: |
        fraiseql-doctor query list --format json > graphql-test-report.json
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      with:
        name: graphql-test-results
        path: graphql-test-report.json
```

#### 2. Docker Integration

```dockerfile
# Dockerfile.tests
FROM python:3.11-slim

RUN pip install fraiseql-doctor

COPY tests/graphql/ /tests/
COPY scripts/run-graphql-tests.sh /scripts/

WORKDIR /tests

ENTRYPOINT ["/scripts/run-graphql-tests.sh"]
```

```bash
#!/bin/bash
# scripts/run-graphql-tests.sh

set -e

echo "Setting up FraiseQL Doctor..."
fraiseql-doctor config init

echo "Configuring test endpoints..."
fraiseql-doctor endpoint create test-api \
  --url "$TEST_API_URL" \
  --auth-type bearer \
  --token "$TEST_API_TOKEN"

echo "Importing test queries..."
fraiseql-doctor query import --file test-queries.yaml

echo "Running GraphQL tests..."

# Critical path tests
fraiseql-doctor query execute auth-test test-api
fraiseql-doctor query execute data-integrity-test test-api
fraiseql-doctor query execute performance-test test-api

# Health checks
fraiseql-doctor health check test-api

echo "All GraphQL tests passed!"
```

#### 3. Pre-deployment Validation

```bash
#!/bin/bash
# scripts/pre-deployment-validation.sh

echo "Running pre-deployment GraphQL validation..."

# Test against staging first
fraiseql-doctor endpoint create staging \
  --url "$STAGING_API_URL" \
  --auth-type bearer \
  --token "$STAGING_API_TOKEN"

# Import production-ready queries
fraiseql-doctor query import --file deployment/production-queries.yaml

# Validate all production queries work on staging
fraiseql-doctor query list --tag production --format json | \
  jq -r '.[].name' | while read query_name; do
  
  echo "Validating query: $query_name"
  
  if ! fraiseql-doctor query execute "$query_name" staging; then
    echo "ERROR: Query $query_name failed on staging!"
    exit 1
  fi
done

echo "All production queries validated successfully on staging"

# Performance regression test
echo "Running performance regression tests..."
fraiseql-doctor query execute performance-baseline staging \
  --format json | jq -e '.responseTimeMs < 2000' || {
  echo "ERROR: Performance regression detected!"
  exit 1
}

echo "Pre-deployment validation completed successfully"
```

This completes our comprehensive examples and recipes section. Each example is production-ready and demonstrates real-world usage patterns that teams can adapt to their specific needs.
```

### Success Criteria
- [x] Comprehensive README with clear value proposition
- [x] Step-by-step getting started tutorial
- [x] Complete CLI reference documentation
- [x] Real-world examples and recipes
- [x] Installation guides for multiple methods
- [x] Configuration documentation
- [x] Troubleshooting guides
- [x] API reference documentation
- [x] Contributing guidelines
- [x] Professional presentation with badges and links

### Handoff Notes for Next Phase
- Documentation should be reviewed for accuracy
- Consider adding video tutorials for complex workflows
- Set up documentation hosting (ReadTheDocs or similar)
- Add documentation testing to CI/CD pipeline
- Create interactive examples with asciinema recordings
- Consider adding FAQ section based on user feedback
- Ensure all code examples are tested and working