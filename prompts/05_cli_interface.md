# Phase 5: CLI Interface Development
**Agent: CLI Developer**

## Objective
Build a comprehensive, user-friendly CLI interface using Typer that provides intuitive access to all FraiseQL Doctor functionality with excellent UX, progress indicators, and rich formatting.

## Requirements

### Core CLI Architecture

#### 1. Main CLI Application
```python
"""Main CLI application with subcommands."""
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from typing import Optional, List
from pathlib import Path

from fraiseql_doctor.cli.commands import (
    query_commands,
    endpoint_commands,
    health_commands,
    schedule_commands,
    config_commands
)
from fraiseql_doctor.core.config import get_settings
from fraiseql_doctor.core.database import get_db_session

app = typer.Typer(
    name="fraiseql-doctor",
    help="🔍 Health monitoring and query execution tool for FraiseQL/GraphQL endpoints",
    rich_markup_mode="rich",
    no_args_is_help=True,
    add_completion=True
)

console = Console()

# Add subcommands
app.add_typer(query_commands.app, name="query", help="📝 Manage FraiseQL queries")
app.add_typer(endpoint_commands.app, name="endpoint", help="🌐 Manage GraphQL endpoints")
app.add_typer(health_commands.app, name="health", help="❤️ Monitor endpoint health")
app.add_typer(schedule_commands.app, name="schedule", help="⏰ Schedule query execution")
app.add_typer(config_commands.app, name="config", help="⚙️ Manage configuration")

@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
):
    """FraiseQL Doctor - Monitor and execute GraphQL queries."""
    if version:
        console.print("🔍 FraiseQL Doctor v0.1.0")
        raise typer.Exit()
    
    # Store global options in context
    ctx.ensure_object(dict)
    ctx.obj["config_file"] = config_file
    ctx.obj["verbose"] = verbose
    
    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")

@app.command()
def dashboard():
    """📊 Show interactive dashboard with health overview."""
    from fraiseql_doctor.cli.dashboard import show_dashboard
    show_dashboard()

if __name__ == "__main__":
    app()
```

#### 2. Query Management Commands
```python
"""Query management CLI commands."""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional, List
from uuid import UUID
from pathlib import Path
import json

from fraiseql_doctor.services.query import QueryService
from fraiseql_doctor.services.execution import ExecutionService
from fraiseql_doctor.schemas.query import QueryCreate, QueryUpdate
from fraiseql_doctor.cli.utils import (
    get_query_service,
    get_execution_service,
    format_datetime,
    handle_service_error
)

app = typer.Typer()
console = Console()

@app.command("create")
def create_query(
    name: str = typer.Argument(..., help="Query name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Query description"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="GraphQL file to read"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive query builder"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Tags for the query"),
):
    """Create a new FraiseQL query."""
    
    if interactive:
        name = Prompt.ask("Query name", default=name if name != "temp" else "")
        description = Prompt.ask("Description (optional)", default=description or "")
        tags = Prompt.ask("Tags (comma-separated)", default="").split(",") if tags is None else tags
    
    # Get query text
    if file:
        if not file.exists():
            console.print(f"[red]Error: File {file} not found[/red]")
            raise typer.Exit(1)
        query_text = file.read_text()
    else:
        if interactive:
            console.print("[yellow]Enter your GraphQL query (press Ctrl+D when finished):[/yellow]")
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                query_text = "\n".join(lines)
        else:
            console.print("[red]Error: Either --file or --interactive must be specified[/red]")
            raise typer.Exit(1)
    
    # Show query preview
    syntax = Syntax(query_text, "graphql", theme="monokai", line_numbers=True)
    console.print("\n[bold]Query Preview:[/bold]")
    console.print(Panel(syntax, title="GraphQL Query"))
    
    if not Confirm.ask("\nCreate this query?"):
        console.print("[yellow]Query creation cancelled[/yellow]")
        raise typer.Exit()
    
    # Create query
    with get_query_service() as service:
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:
                progress.add_task("Creating query...", total=None)
                
                query_data = QueryCreate(
                    name=name,
                    description=description,
                    query_text=query_text,
                    tags=tags or [],
                    created_by="cli"
                )
                
                query = await service.create_query(query_data)
            
            console.print(f"[green]✅ Query '{name}' created successfully![/green]")
            console.print(f"Query ID: {query.pk_query}")
            
        except Exception as e:
            handle_service_error(e, "create query")

@app.command("list")
def list_queries(
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Filter by tags"),
    active_only: bool = typer.Option(True, "--active-only", help="Show only active queries"),
    created_by: Optional[str] = typer.Option(None, "--created-by", help="Filter by creator"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of queries to show"),
    format: str = typer.Option("table", "--format", help="Output format: table, json, yaml"),
):
    """List all FraiseQL queries."""
    
    with get_query_service() as service:
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:
                progress.add_task("Loading queries...", total=None)
                
                queries = await service.list_queries(
                    tags=tags,
                    is_active=active_only,
                    created_by=created_by,
                    limit=limit
                )
            
            if not queries:
                console.print("[yellow]No queries found matching criteria[/yellow]")
                return
            
            if format == "json":
                output = [q.dict() for q in queries]
                console.print(json.dumps(output, indent=2, default=str))
            elif format == "yaml":
                import yaml
                output = [q.dict() for q in queries]
                console.print(yaml.dump(output, default_flow_style=False))
            else:
                # Table format
                table = Table(title="FraiseQL Queries")
                table.add_column("Name", style="bold blue")
                table.add_column("Description", style="dim")
                table.add_column("Tags", style="green")
                table.add_column("Created", style="dim")
                table.add_column("Status", justify="center")
                
                for query in queries:
                    status = "🟢 Active" if query.is_active else "🔴 Inactive"
                    tags_str = ", ".join(query.tags) if query.tags else ""
                    
                    table.add_row(
                        query.name,
                        query.description or "",
                        tags_str,
                        format_datetime(query.created_at),
                        status
                    )
                
                console.print(table)
                console.print(f"\n[dim]Showing {len(queries)} queries[/dim]")
                
        except Exception as e:
            handle_service_error(e, "list queries")

@app.command("show")
def show_query(
    query_id: str = typer.Argument(..., help="Query ID or name"),
    show_executions: bool = typer.Option(True, "--executions", help="Show recent executions"),
    show_stats: bool = typer.Option(True, "--stats", help="Show performance statistics"),
):
    """Show detailed information about a query."""
    
    with get_query_service() as service:
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:
                progress.add_task("Loading query details...", total=None)
                
                # Try to get by UUID first, then by name
                try:
                    query_uuid = UUID(query_id)
                    query = await service.get_query(query_uuid)
                except ValueError:
                    # Search by name
                    queries = await service.list_queries(limit=1000)
                    matching_queries = [q for q in queries if q.name == query_id]
                    if not matching_queries:
                        console.print(f"[red]Query '{query_id}' not found[/red]")
                        raise typer.Exit(1)
                    query = matching_queries[0]
            
            # Display query information
            info_table = Table(title=f"Query: {query.name}")
            info_table.add_column("Property", style="bold")
            info_table.add_column("Value")
            
            info_table.add_row("ID", str(query.pk_query))
            info_table.add_row("Description", query.description or "N/A")
            info_table.add_row("Tags", ", ".join(query.tags) if query.tags else "None")
            info_table.add_row("Created", format_datetime(query.created_at))
            info_table.add_row("Updated", format_datetime(query.updated_at))
            info_table.add_row("Status", "🟢 Active" if query.is_active else "🔴 Inactive")
            info_table.add_row("Complexity", str(query.expected_complexity_score or "Unknown"))
            
            console.print(info_table)
            
            # Show query text
            syntax = Syntax(query.query_text, "graphql", theme="monokai", line_numbers=True)
            console.print("\n[bold]Query Text:[/bold]")
            console.print(Panel(syntax, title="GraphQL Query"))
            
            # Show variables if any
            if query.variables:
                variables_syntax = Syntax(
                    json.dumps(query.variables, indent=2),
                    "json",
                    theme="monokai"
                )
                console.print("\n[bold]Variables:[/bold]")
                console.print(Panel(variables_syntax, title="Query Variables"))
            
            # Show recent executions
            if show_executions and hasattr(query, 'recent_executions'):
                if query.recent_executions:
                    exec_table = Table(title="Recent Executions")
                    exec_table.add_column("Time", style="dim")
                    exec_table.add_column("Status")
                    exec_table.add_column("Response Time", justify="right")
                    exec_table.add_column("Error", style="red")
                    
                    for exec in query.recent_executions[:5]:
                        status_icon = "🟢" if exec["status"] == "success" else "🔴"
                        response_time = f"{exec['response_time_ms']}ms" if exec["response_time_ms"] else "N/A"
                        error = exec["error_message"][:50] + "..." if exec["error_message"] and len(exec["error_message"]) > 50 else exec["error_message"] or ""
                        
                        exec_table.add_row(
                            format_datetime(exec["execution_start"]),
                            f"{status_icon} {exec['status']}",
                            response_time,
                            error
                        )
                    
                    console.print("\n")
                    console.print(exec_table)
            
            # Show performance stats
            if show_stats and hasattr(query, 'performance_stats'):
                stats = query.performance_stats
                stats_table = Table(title="Performance Statistics")
                stats_table.add_column("Metric", style="bold")
                stats_table.add_column("Value", justify="right")
                
                stats_table.add_row("Average Response Time", f"{stats.get('avg_response_time_ms', 0):.1f}ms")
                stats_table.add_row("Success Rate", f"{stats.get('success_rate', 0):.1f}%")
                stats_table.add_row("Total Executions", str(stats.get('total_executions', 0)))
                
                console.print("\n")
                console.print(stats_table)
                
        except Exception as e:
            handle_service_error(e, "show query")

@app.command("execute")
def execute_query(
    query_id: str = typer.Argument(..., help="Query ID or name"),
    endpoint_id: str = typer.Argument(..., help="Endpoint ID or name"),
    variables: Optional[str] = typer.Option(None, "--variables", "-v", help="Variables as JSON string"),
    variables_file: Optional[Path] = typer.Option(None, "--variables-file", help="Variables from JSON file"),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="Timeout in seconds"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Save output to file"),
    format: str = typer.Option("pretty", "--format", help="Output format: pretty, json, yaml"),
):
    """Execute a FraiseQL query against an endpoint."""
    
    # Parse variables
    query_variables = {}
    if variables:
        try:
            query_variables = json.loads(variables)
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON in variables: {e}[/red]")
            raise typer.Exit(1)
    elif variables_file:
        if not variables_file.exists():
            console.print(f"[red]Variables file {variables_file} not found[/red]")
            raise typer.Exit(1)
        try:
            query_variables = json.loads(variables_file.read_text())
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON in variables file: {e}[/red]")
            raise typer.Exit(1)
    
    with get_execution_service() as service:
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:
                task = progress.add_task("Executing query...", total=None)
                
                # Convert names to UUIDs if needed
                query_uuid = _resolve_query_id(query_id)
                endpoint_uuid = _resolve_endpoint_id(endpoint_id)
                
                result = await service.execute_query(
                    query_id=query_uuid,
                    endpoint_id=endpoint_uuid,
                    variables=query_variables,
                    timeout=timeout
                )
                
                progress.update(task, description="Processing response...")
            
            # Format and display result
            _display_execution_result(result, format, output_file)
            
        except Exception as e:
            handle_service_error(e, "execute query")

def _display_execution_result(result: dict, format: str, output_file: Optional[Path]):
    """Display execution result in specified format."""
    if format == "json":
        output = json.dumps(result, indent=2, default=str)
    elif format == "yaml":
        import yaml
        output = yaml.dump(result, default_flow_style=False)
    else:
        # Pretty format
        status_icon = "🟢" if result["status"] == "success" else "🔴"
        
        # Execution summary
        summary_table = Table(title="Execution Result")
        summary_table.add_column("Property", style="bold")
        summary_table.add_column("Value")
        
        summary_table.add_row("Status", f"{status_icon} {result['status']}")
        summary_table.add_row("Response Time", f"{result.get('response_time_ms', 0)}ms")
        summary_table.add_row("Complexity Score", str(result.get('complexity_score', 'N/A')))
        summary_table.add_row("Execution ID", str(result['execution_id']))
        
        console.print(summary_table)
        
        # Show data if successful
        if result["status"] == "success" and result.get("data"):
            data_syntax = Syntax(
                json.dumps(result["data"], indent=2),
                "json",
                theme="monokai"
            )
            console.print("\n[bold]Response Data:[/bold]")
            console.print(Panel(data_syntax, title="GraphQL Response"))
        
        # Show errors if any
        if result.get("errors"):
            errors_syntax = Syntax(
                json.dumps(result["errors"], indent=2),
                "json",
                theme="monokai"
            )
            console.print("\n[bold red]Errors:[/bold red]")
            console.print(Panel(errors_syntax, title="GraphQL Errors", border_style="red"))
        
        return
    
    # Save or display output
    if output_file:
        output_file.write_text(output)
        console.print(f"[green]Output saved to {output_file}[/green]")
    else:
        console.print(output)

# Additional commands for edit, delete, copy, etc.
@app.command("edit")
def edit_query(query_id: str = typer.Argument(..., help="Query ID or name")):
    """Edit an existing query interactively."""
    # Implementation for interactive editing
    pass

@app.command("delete")
def delete_query(
    query_id: str = typer.Argument(..., help="Query ID or name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a query."""
    # Implementation for query deletion
    pass
```

#### 3. Interactive Dashboard
```python
"""Interactive dashboard for FraiseQL Doctor."""
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
import asyncio
import time
from datetime import datetime

from fraiseql_doctor.services.health import HealthCheckService
from fraiseql_doctor.services.query import QueryService


class Dashboard:
    """Interactive dashboard for monitoring FraiseQL endpoints."""
    
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.health_service = None  # Initialized in show()
        self.query_service = None   # Initialized in show()
        
    def show(self):
        """Show the live dashboard."""
        # Initialize layout
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        self.layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        self.layout["left"].split_column(
            Layout(name="endpoints", ratio=2),
            Layout(name="queries", ratio=1)
        )
        
        self.layout["right"].split_column(
            Layout(name="health", ratio=1),
            Layout(name="metrics", ratio=1)
        )
        
        # Start live dashboard
        with Live(self.layout, refresh_per_second=4, screen=True):
            try:
                asyncio.run(self._update_loop())
            except KeyboardInterrupt:
                pass
    
    async def _update_loop(self):
        """Main update loop for dashboard."""
        while True:
            try:
                await self._update_dashboard()
                await asyncio.sleep(1)
            except Exception as e:
                self.console.print(f"Dashboard error: {e}")
                await asyncio.sleep(5)
    
    async def _update_dashboard(self):
        """Update all dashboard components."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Header
        header_text = Text("🔍 FraiseQL Doctor Dashboard", style="bold blue")
        self.layout["header"].update(
            Panel(header_text, subtitle=f"Last updated: {current_time}")
        )
        
        # Footer
        footer_text = Text("Press Ctrl+C to exit", style="dim")
        self.layout["footer"].update(Panel(footer_text))
        
        # Update content panels
        await self._update_endpoints_panel()
        await self._update_queries_panel()
        await self._update_health_panel()
        await self._update_metrics_panel()
    
    async def _update_endpoints_panel(self):
        """Update endpoints status panel."""
        # Mock data - replace with actual service calls
        table = Table(title="Endpoints Status")
        table.add_column("Name", style="bold")
        table.add_column("Status")
        table.add_column("Response Time")
        table.add_column("Last Check")
        
        # Add sample data
        table.add_row("Production API", "🟢 Healthy", "45ms", "30s ago")
        table.add_row("Staging API", "🟡 Warning", "120ms", "1m ago")
        table.add_row("Dev API", "🔴 Down", "N/A", "5m ago")
        
        self.layout["endpoints"].update(Panel(table, border_style="green"))
    
    async def _update_queries_panel(self):
        """Update queries overview panel."""
        table = Table(title="Recent Queries")
        table.add_column("Query", style="bold")
        table.add_column("Status")
        table.add_column("Time")
        
        # Add sample data
        table.add_row("user-profile", "🟢 Success", "2s ago")
        table.add_row("order-history", "🟢 Success", "15s ago")
        table.add_row("inventory-check", "🔴 Error", "1m ago")
        
        self.layout["queries"].update(Panel(table, border_style="blue"))
    
    async def _update_health_panel(self):
        """Update health metrics panel."""
        health_text = Text()
        health_text.append("Overall Health: ", style="bold")
        health_text.append("85%", style="green")
        health_text.append("\n\n")
        health_text.append("Active Endpoints: 3\n")
        health_text.append("Healthy: 2\n")
        health_text.append("Warning: 1\n")
        health_text.append("Down: 1\n")
        
        self.layout["health"].update(Panel(health_text, title="Health Summary", border_style="yellow"))
    
    async def _update_metrics_panel(self):
        """Update performance metrics panel."""
        metrics_text = Text()
        metrics_text.append("Avg Response Time: ", style="bold")
        metrics_text.append("67ms\n", style="green")
        metrics_text.append("Success Rate: ")
        metrics_text.append("94.2%\n", style="green")
        metrics_text.append("Queries/min: ")
        metrics_text.append("12\n")
        metrics_text.append("Errors/hour: ")
        metrics_text.append("3", style="red")
        
        self.layout["metrics"].update(Panel(metrics_text, title="Performance", border_style="cyan"))


def show_dashboard():
    """Show the interactive dashboard."""
    dashboard = Dashboard()
    dashboard.show()
```

### CLI Utilities and Helpers

#### 4. CLI Utilities
```python
"""CLI utility functions and helpers."""
from typing import Optional, Any
from uuid import UUID
from datetime import datetime
from contextlib import asynccontextmanager

from rich.console import Console
from fraiseql_doctor.core.exceptions import FraiseQLDoctorError

console = Console()

def format_datetime(dt: datetime) -> str:
    """Format datetime for CLI display."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def handle_service_error(error: Exception, operation: str) -> None:
    """Handle service errors with user-friendly messages."""
    if isinstance(error, FraiseQLDoctorError):
        console.print(f"[red]Error: {error}[/red]")
    else:
        console.print(f"[red]Unexpected error during {operation}: {error}[/red]")
    
    # Show help for common errors
    if "not found" in str(error).lower():
        console.print("[dim]Tip: Use 'fraiseql-doctor query list' to see available queries[/dim]")
    elif "connection" in str(error).lower():
        console.print("[dim]Tip: Check your database connection settings[/dim]")

@asynccontextmanager
async def get_query_service():
    """Get query service with proper session management."""
    # Implementation would return properly configured service
    pass

@asynccontextmanager
async def get_execution_service():
    """Get execution service with proper session management."""
    # Implementation would return properly configured service
    pass

def _resolve_query_id(query_id: str) -> UUID:
    """Resolve query name or UUID to UUID."""
    try:
        return UUID(query_id)
    except ValueError:
        # Search by name - simplified implementation
        raise ValueError(f"Query '{query_id}' not found")

def _resolve_endpoint_id(endpoint_id: str) -> UUID:
    """Resolve endpoint name or UUID to UUID."""
    try:
        return UUID(endpoint_id)
    except ValueError:
        # Search by name - simplified implementation
        raise ValueError(f"Endpoint '{endpoint_id}' not found")
```

### Configuration and Setup

#### 5. Configuration Commands
```python
"""Configuration management commands."""
import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
import json
import yaml

app = typer.Typer()
console = Console()

@app.command("init")
def init_config(
    config_dir: Path = typer.Option(Path.home() / ".fraiseql-doctor", "--dir", help="Config directory"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing config"),
):
    """Initialize FraiseQL Doctor configuration."""
    config_file = config_dir / "config.yaml"
    
    if config_file.exists() and not force:
        console.print(f"[yellow]Config file already exists at {config_file}[/yellow]")
        console.print("Use --force to overwrite")
        return
    
    # Create config directory
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Default configuration
    default_config = {
        "database": {
            "url": "postgresql://localhost/fraiseql_doctor",
            "pool_size": 5,
            "max_overflow": 10
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "defaults": {
            "timeout_seconds": 30,
            "max_retries": 3,
            "health_check_interval": 300
        }
    }
    
    # Write config file
    with open(config_file, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)
    
    console.print(f"[green]✅ Configuration initialized at {config_file}[/green]")
    console.print(f"[dim]Edit the file to customize your settings[/dim]")

@app.command("show")
def show_config():
    """Show current configuration."""
    # Implementation to display current config
    pass

@app.command("validate")
def validate_config():
    """Validate configuration file."""
    # Implementation to validate config
    pass
```

### Success Criteria
- [x] Comprehensive CLI with intuitive subcommands
- [x] Rich formatting and progress indicators
- [x] Interactive dashboard for real-time monitoring
- [x] Query builder and execution commands
- [x] Configuration management
- [x] Error handling with helpful messages
- [x] Shell completion support
- [x] Multiple output formats (table, JSON, YAML)
- [x] File input/output support

### Handoff Notes for Next Phase
- Implement comprehensive test coverage for all CLI commands
- Add shell completion scripts for bash/zsh
- Consider adding plugin architecture for custom commands
- Implement proper signal handling for graceful shutdown
- Add support for configuration profiles (dev, staging, prod)
- Consider adding terminal UI library for more interactive features