# Phase 2: CLI Implementation
**Timeline: 5-7 days | Priority: HIGH - User Experience**

## 🎯 Objective
Transform placeholder CLI stubs into a complete, functional command-line interface with rich user experience and comprehensive GraphQL endpoint management capabilities.

## 📋 Current State Assessment

**Existing CLI Structure:**
```
src/fraiseql_doctor/cli/main.py - Basic Typer app with placeholder subcommands
├─ query_app    - Empty Typer group
├─ endpoint_app - Empty Typer group  
├─ health_app   - Empty Typer group
└─ config_app   - Empty Typer group
```

**Problem:** All commands exist but do nothing when executed.

## 🛠️ Implementation Plan

### Day 1-3: Core Command Implementation

#### 1. Query Management Commands
**File:** `src/fraiseql_doctor/cli/commands/query.py`

**Commands to implement:**
```bash
fraiseql-doctor query create --name "User Profile" --file query.graphql --endpoint api
fraiseql-doctor query list --status active --endpoint api --format table
fraiseql-doctor query show --name "User Profile" --format json  
fraiseql-doctor query execute --name "User Profile" --variables vars.json
fraiseql-doctor query update --name "User Profile" --file new_query.graphql
fraiseql-doctor query delete --name "User Profile" --confirm
```

**Required Implementation:**
```python
import typer
from typing import Optional, List
from pathlib import Path
from rich.console import Console
from rich.table import Table

query_app = typer.Typer(name="query", help="Manage GraphQL queries")

@query_app.command("create")
def create_query(
    name: str = typer.Option(..., "--name", "-n", help="Query name"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="GraphQL file path"),
    endpoint: str = typer.Option(..., "--endpoint", "-e", help="Target endpoint"),
    description: Optional[str] = typer.Option(None, "--description", help="Query description"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", help="Query tags"),
):
    """Create a new GraphQL query."""
    # Implementation using core.query_collection module
    pass

@query_app.command("list") 
def list_queries(
    endpoint: Optional[str] = typer.Option(None, "--endpoint", "-e", help="Filter by endpoint"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    format: str = typer.Option("table", "--format", help="Output format: table, json, csv"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", help="Filter by tags"),
):
    """List all queries with optional filtering."""
    pass

@query_app.command("execute")
def execute_query(
    name: str = typer.Option(..., "--name", "-n", help="Query name to execute"),
    variables: Optional[Path] = typer.Option(None, "--variables", "-v", help="JSON/YAML variables file"),
    endpoint: Optional[str] = typer.Option(None, "--endpoint", "-e", help="Override endpoint"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to file"),
    format: str = typer.Option("json", "--format", help="Output format: json, table, raw"),
):
    """Execute a GraphQL query."""
    pass
```

#### 2. Endpoint Management Commands  
**File:** `src/fraiseql_doctor/cli/commands/endpoint.py`

**Commands to implement:**
```bash
fraiseql-doctor endpoint add --name "Production API" --url https://api.example.com/graphql --auth bearer
fraiseql-doctor endpoint list --format table
fraiseql-doctor endpoint test --name "Production API" --verbose
fraiseql-doctor endpoint update --name "Production API" --timeout 30  
fraiseql-doctor endpoint remove --name "Production API" --confirm
```

**Required Implementation:**
```python
@endpoint_app.command("add")
def add_endpoint(
    name: str = typer.Option(..., "--name", "-n", help="Endpoint name"),
    url: str = typer.Option(..., "--url", "-u", help="GraphQL endpoint URL"),
    auth: Optional[str] = typer.Option(None, "--auth", help="Auth type: bearer, apikey, basic"),
    token: Optional[str] = typer.Option(None, "--token", help="Auth token/key"),
    username: Optional[str] = typer.Option(None, "--username", help="Basic auth username"),
    password: Optional[str] = typer.Option(None, "--password", help="Basic auth password"),
    timeout: int = typer.Option(30, "--timeout", help="Request timeout in seconds"),
    headers: Optional[List[str]] = typer.Option(None, "--header", help="Custom headers (key:value)"),
):
    """Add a new GraphQL endpoint."""
    pass

@endpoint_app.command("test")
def test_endpoint(
    name: str = typer.Option(..., "--name", "-n", help="Endpoint name to test"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="Override timeout"),
):
    """Test endpoint connectivity and health."""
    pass
```

### Day 3-5: Advanced Features

#### 3. Health Monitoring Commands
**File:** `src/fraiseql_doctor/cli/commands/health.py`

**Commands to implement:**
```bash
fraiseql-doctor health check --endpoint "Production API" --query "Health Check"
fraiseql-doctor health monitor --continuous --interval 30s --endpoints all
fraiseql-doctor health report --format html --output report.html --since "1 day ago"
fraiseql-doctor health dashboard --port 8080 --host 0.0.0.0
```

**Required Implementation:**
```python
@health_app.command("check")
def health_check(
    endpoint: Optional[str] = typer.Option(None, "--endpoint", "-e", help="Specific endpoint"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Health check query name"),
    timeout: int = typer.Option(10, "--timeout", help="Health check timeout"),
    format: str = typer.Option("table", "--format", help="Output format"),
):
    """Perform health check on endpoints."""
    pass

@health_app.command("monitor")
def monitor_health(
    continuous: bool = typer.Option(False, "--continuous", "-c", help="Continuous monitoring"),
    interval: str = typer.Option("30s", "--interval", "-i", help="Check interval"),
    endpoints: List[str] = typer.Option(["all"], "--endpoint", help="Endpoints to monitor"),
    alerts: bool = typer.Option(False, "--alerts", help="Enable alerting"),
):
    """Monitor endpoint health continuously."""
    pass

@health_app.command("dashboard")
def health_dashboard(
    port: int = typer.Option(8080, "--port", "-p", help="Dashboard port"),
    host: str = typer.Option("127.0.0.1", "--host", help="Dashboard host"),
    auto_refresh: int = typer.Option(30, "--refresh", help="Auto-refresh interval"),
):
    """Start web-based health dashboard."""
    pass
```

#### 4. Batch Operations
**File:** `src/fraiseql_doctor/cli/commands/batch.py`

**Commands to implement:**
```bash
fraiseql-doctor batch execute --collection "API Tests" --parallel 5 --output results/
fraiseql-doctor batch import --file queries.yaml --endpoint "Production API" 
fraiseql-doctor batch export --endpoint "Production API" --output backup.yaml
fraiseql-doctor batch schedule --collection "Daily Checks" --cron "0 9 * * *"
```

### Day 5-7: User Experience Enhancement

#### 5. Rich Terminal Output
**Dependencies to add:**
```toml
rich = ">=13.0.0"          # Already included
click-spinner = ">=0.1.10"  # Progress indicators  
tabulate = ">=0.9.0"       # Table formatting alternatives
```

**Features to implement:**
- **Progress bars** for long-running operations
- **Colored status indicators** (green=success, red=error, yellow=warning)
- **Interactive tables** with sorting and filtering
- **Confirmation prompts** for destructive operations
- **Syntax highlighting** for GraphQL queries and JSON responses

#### 6. File Format Support
**File handlers to implement:**
```python
# src/fraiseql_doctor/cli/utils/file_handlers.py

class GraphQLFileHandler:
    @staticmethod
    def parse_graphql_file(file_path: Path) -> str:
        """Parse .graphql/.gql files with validation."""
        pass
    
    @staticmethod
    def validate_query_syntax(query: str) -> bool:
        """Validate GraphQL query syntax."""
        pass

class VariableFileHandler:
    @staticmethod  
    def load_variables(file_path: Path) -> dict:
        """Load variables from JSON/YAML file."""
        pass
    
    @staticmethod
    def validate_variables(variables: dict, query: str) -> bool:
        """Validate variables match query requirements.""" 
        pass

class ExportHandler:
    @staticmethod
    def export_queries(queries: List[Query], format: str, output: Path):
        """Export queries to various formats."""
        pass
    
    @staticmethod
    def export_results(results: List[Result], format: str, output: Path):
        """Export results to various formats."""
        pass
```

**Supported formats:**
- **Input**: `.graphql`, `.gql`, `.json`, `.yaml`, `.yml`
- **Output**: `json`, `yaml`, `csv`, `html`, `markdown`
- **Configuration**: `.env`, `.toml`, `.yaml`

#### 7. Configuration Management
**File:** `src/fraiseql_doctor/cli/commands/config.py`

**Commands to implement:**
```bash
fraiseql-doctor config init --database-url postgresql://localhost/fraiseql_doctor
fraiseql-doctor config show --section database --format yaml
fraiseql-doctor config validate --fix-permissions
fraiseql-doctor config migrate --backup
fraiseql-doctor config reset --confirm
```

**Configuration features:**
- **Interactive setup wizard** for first-time users
- **Environment-specific configurations** (dev/staging/prod)
- **Configuration file validation** with helpful error messages  
- **Automatic database migration** integration
- **Backup and restore** configuration

## 🧪 Testing Requirements

### CLI Command Tests
**New test directory:** `tests/cli/`

**Required test files:**
```
tests/cli/
├── test_query_commands.py      # Query CRUD operations
├── test_endpoint_commands.py   # Endpoint management
├── test_health_commands.py     # Health monitoring  
├── test_batch_commands.py      # Batch operations
├── test_config_commands.py     # Configuration management
├── test_file_handlers.py       # File parsing/export
└── test_cli_integration.py     # End-to-end CLI workflows
```

**Testing approach:**
- **Unit tests** for individual commands
- **Integration tests** for command workflows
- **Mock external dependencies** (database, HTTP calls)
- **Test CLI output formatting** and user experience
- **Error handling** and user-friendly error messages

### CLI User Experience Testing
```python
# Example test pattern for CLI commands
def test_query_create_command(cli_runner, mock_database):
    """Test query creation via CLI."""
    result = cli_runner.invoke(app, [
        'query', 'create',
        '--name', 'Test Query',
        '--file', 'test_query.graphql',
        '--endpoint', 'test-endpoint'
    ])
    
    assert result.exit_code == 0
    assert "Query 'Test Query' created successfully" in result.output
    assert mock_database.create_query.called
```

## 📋 Implementation Checklist

### Day 1-2: Foundation
- [ ] Restructure CLI module with command separation
- [ ] Implement query management commands (create, list, show, execute, update, delete)
- [ ] Add basic error handling and validation
- [ ] Create file handler utilities for GraphQL/JSON/YAML

### Day 3-4: Core Features  
- [ ] Implement endpoint management commands (add, list, test, update, remove)
- [ ] Add health monitoring commands (check, monitor, report)
- [ ] Implement batch operations (execute, import, export, schedule)
- [ ] Add configuration management commands

### Day 5-6: User Experience
- [ ] Rich terminal output with progress bars and colors
- [ ] Interactive confirmation prompts
- [ ] Comprehensive help system with examples
- [ ] File format validation and helpful error messages

### Day 6-7: Testing & Integration
- [ ] Complete CLI test coverage
- [ ] Integration testing for command workflows
- [ ] Documentation for each command with examples
- [ ] Performance testing for large operations

## ✅ Success Criteria

**Phase 2 is complete when:**
1. **All CLI commands functional** - no placeholder stubs remaining
2. **Rich user experience** - progress bars, colors, interactive prompts
3. **File format support** - GraphQL, JSON, YAML input/output
4. **Comprehensive help system** - detailed help for every command
5. **CLI test coverage >90%** - thorough testing of user workflows
6. **Error handling** - user-friendly error messages and suggestions

## 🚀 Handoff to Phase 3

**Deliverables for next phase:**
- Complete, functional CLI with rich user experience
- Comprehensive command test coverage
- File import/export capabilities  
- Interactive help and error handling
- Foundation for documentation and examples

**Ready for Phase 3:** Documentation phase can use working CLI for examples and screenshots.

---

**Phase 2 Agent Prompt:** "Implement complete CLI functionality for FraiseQL Doctor. Transform placeholder command stubs into full-featured commands with rich terminal UX, file handling, and comprehensive GraphQL endpoint management. Follow implementation plan in PHASE2_CLI.md and maintain 100% test success rate."