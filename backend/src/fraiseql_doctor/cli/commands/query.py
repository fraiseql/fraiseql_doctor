"""Query management CLI commands."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import typer
import yaml
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

# Temporarily commented out to avoid circular imports during Phase 2 implementation
# from ...core.database import get_db_session
# from ...core.query_collection import QueryCollectionManager, QuerySearchFilter, QueryStatus, QueryPriority
# from ...services.complexity import QueryComplexityAnalyzer
# from ...schemas.query import QueryCreate, QueryUpdate
# from ...models.query import Query

# Mock classes for Phase 2 demonstration
class MockQuerySearchFilter:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class QueryStatus:
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"

class QueryPriority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

QuerySearchFilter = MockQuerySearchFilter

# Mock schema classes
class QueryCreate:
    def __init__(self, name, description=None, query_text="", variables=None, tags=None, created_by=None):
        self.name = name
        self.description = description
        self.query_text = query_text
        self.variables = variables or {}
        self.tags = tags or []
        self.created_by = created_by

class QueryUpdate:
    def __init__(self, name=None, description=None, query_text=None):
        self.name = name
        self.description = description
        self.query_text = query_text

from ..utils.file_handlers import GraphQLFileHandler, VariableFileHandler
from ..utils.formatters import format_query_table, format_query_detail, format_execution_result

console = Console()

query_app = typer.Typer(name="query", help="Manage GraphQL queries")


def get_query_manager():
    """Get configured query collection manager - mock for Phase 2."""
    class MockQuery:
        def __init__(self, name="Mock Query", pk_query="mock-uuid"):
            self.name = name
            self.pk_query = pk_query
            self.description = "Mock query for CLI demonstration"
            self.query_text = "query { mockField }"
            self.variables = {}
            self.tags = ["demo"]
            self.created_at = None
            self.updated_at = None
            self.created_by = "cli-user"
            self.query_metadata = {"complexity_score": 5.0}
            self.expected_complexity_score = 5
        
        def to_dict(self):
            return {
                "pk_query": self.pk_query,
                "name": self.name,
                "description": self.description,
                "query_text": self.query_text,
                "variables": self.variables,
                "tags": self.tags,
                "created_at": self.created_at,
                "query_metadata": self.query_metadata
            }
    
    class MockQueryManager:
        def search_queries(self, filter_params):
            # Return mock queries for demonstration
            return [
                MockQuery("Sample Query 1"),
                MockQuery("Sample Query 2", "mock-uuid-2")
            ]
        
        def get_query(self, query_id):
            return MockQuery("Retrieved Query", str(query_id))
        
        def add_query(self, collection_id, schema, validate=True):
            return MockQuery(getattr(schema, 'name', 'New Query'))
        
        def update_query(self, query_id, schema, validate=True):
            return MockQuery("Updated Query", str(query_id))
        
        def delete_query(self, query_id):
            return True
    
    return MockQueryManager()


@query_app.command("create")
def create_query(
    name: str = typer.Option(..., "--name", "-n", help="Query name"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="GraphQL file path"),
    endpoint: Optional[str] = typer.Option(None, "--endpoint", "-e", help="Target endpoint"),
    description: Optional[str] = typer.Option(None, "--description", help="Query description"),
    variables_file: Optional[Path] = typer.Option(None, "--variables", "-v", help="Variables JSON/YAML file"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", help="Query tags"),
    priority: str = typer.Option("medium", "--priority", help="Priority: low, medium, high, critical"),
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Validate GraphQL syntax"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive query input"),
):
    """Create a new GraphQL query."""
    try:
        # Get query text
        if file:
            if not file.exists():
                rprint(f"[red]Error: File {file} not found[/red]")
                raise typer.Exit(1)
            query_text = GraphQLFileHandler.parse_graphql_file(file)
        elif interactive:
            query_text = _interactive_query_input()
        else:
            rprint("[yellow]No query provided. Use --file or --interactive[/yellow]")
            raise typer.Exit(1)

        # Load variables if provided
        variables = {}
        if variables_file:
            if not variables_file.exists():
                rprint(f"[red]Error: Variables file {variables_file} not found[/red]")
                raise typer.Exit(1)
            variables = VariableFileHandler.load_variables(variables_file)

        # Create query schema
        schema = QueryCreate(
            name=name,
            description=description,
            query_text=query_text,
            variables=variables,
            tags=tags or [],
            created_by="cli-user"  # TODO: Get from config/auth
        )

        # Create query
        manager = get_query_manager()
        
        with console.status(f"[bold green]Creating query '{name}'..."):
            # For now, create without collection (simplified)
            collection_id = uuid4()  # TODO: Get from config or create default
            query = manager.add_query(collection_id, schema, validate=validate)
            
        if query:
            rprint(f"[green]✓[/green] Query '{name}' created successfully")
            rprint(f"Query ID: {query.pk_query}")
            
            if validate and query.query_metadata.get("complexity_score"):
                score = query.query_metadata["complexity_score"]
                rprint(f"Complexity Score: {score:.2f}")
        else:
            rprint("[red]Failed to create query[/red]")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error creating query: {e}[/red]")
        raise typer.Exit(1)


@query_app.command("list")
def list_queries(
    endpoint: Optional[str] = typer.Option(None, "--endpoint", "-e", help="Filter by endpoint"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    priority: Optional[str] = typer.Option(None, "--priority", help="Filter by priority"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", help="Filter by tags"),
    limit: int = typer.Option(50, "--limit", help="Limit results"),
    offset: int = typer.Option(0, "--offset", help="Offset results"),
    format: str = typer.Option("table", "--format", help="Output format: table, json, csv"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search query text"),
):
    """List all queries with optional filtering."""
    try:
        manager = get_query_manager()
        
        # Build search filter
        filter_params = QuerySearchFilter(
            text=search,
            status=QueryStatus(status) if status else None,
            priority=QueryPriority(priority) if priority else None,
            tags=set(tags) if tags else None,
            limit=limit,
            offset=offset
        )
        
        with console.status("[bold green]Loading queries..."):
            queries = manager.search_queries(filter_params)
        
        if not queries:
            rprint("[yellow]No queries found matching criteria[/yellow]")
            return
        
        if format == "table":
            table = format_query_table(queries)
            console.print(table)
        elif format == "json":
            output = [q.to_dict() for q in queries]
            rprint(json.dumps(output, indent=2, default=str))
        elif format == "csv":
            _output_csv(queries)
        else:
            rprint(f"[red]Unknown format: {format}[/red]")
            raise typer.Exit(1)
            
        rprint(f"\n[dim]Showing {len(queries)} queries[/dim]")

    except Exception as e:
        rprint(f"[red]Error listing queries: {e}[/red]")
        raise typer.Exit(1)


@query_app.command("show")
def show_query(
    query_id: Optional[str] = typer.Option(None, "--id", help="Query ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Query name"),
    format: str = typer.Option("pretty", "--format", help="Output format: pretty, json, raw"),
):
    """Show detailed information about a query."""
    if not query_id and not name:
        rprint("[red]Error: Must specify either --id or --name[/red]")
        raise typer.Exit(1)
    
    try:
        manager = get_query_manager()
        
        if query_id:
            query = manager.get_query(UUID(query_id))
        else:
            # Search by name
            filter_params = QuerySearchFilter(text=name, limit=1)
            queries = manager.search_queries(filter_params)
            query = queries[0] if queries else None
        
        if not query:
            rprint("[red]Query not found[/red]")
            raise typer.Exit(1)
        
        if format == "pretty":
            panel = format_query_detail(query)
            console.print(panel)
        elif format == "json":
            rprint(json.dumps(query.to_dict(), indent=2, default=str))
        elif format == "raw":
            rprint(query.query_text)
        else:
            rprint(f"[red]Unknown format: {format}[/red]")
            raise typer.Exit(1)

    except ValueError as e:
        rprint(f"[red]Invalid query ID: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error showing query: {e}[/red]")
        raise typer.Exit(1)


@query_app.command("execute")
def execute_query(
    query_id: Optional[str] = typer.Option(None, "--id", help="Query ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Query name"),
    endpoint: Optional[str] = typer.Option(None, "--endpoint", "-e", help="Endpoint name or URL"),
    variables_file: Optional[Path] = typer.Option(None, "--variables", "-v", help="Variables file"),
    variables_json: Optional[str] = typer.Option(None, "--var-json", help="Variables as JSON string"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to file"),
    format: str = typer.Option("json", "--format", help="Output format: json, table, raw"),
    timeout: int = typer.Option(30, "--timeout", help="Timeout in seconds"),
):
    """Execute a GraphQL query."""
    if not query_id and not name:
        rprint("[red]Error: Must specify either --id or --name[/red]")
        raise typer.Exit(1)
    
    try:
        manager = get_query_manager()
        
        # Get query
        if query_id:
            query = manager.get_query(UUID(query_id))
        else:
            filter_params = QuerySearchFilter(text=name, limit=1)
            queries = manager.search_queries(filter_params)
            query = queries[0] if queries else None
        
        if not query:
            rprint("[red]Query not found[/red]")
            raise typer.Exit(1)
        
        # Load variables
        variables = {}
        if variables_file:
            variables = VariableFileHandler.load_variables(variables_file)
        elif variables_json:
            variables = json.loads(variables_json)
        else:
            variables = query.variables or {}
        
        # Execute query (simplified for now - would use execution manager)
        rprint(f"[yellow]Note: Query execution not fully implemented yet[/yellow]")
        rprint(f"Would execute query: {query.name}")
        rprint(f"Variables: {variables}")
        
        # TODO: Use execution manager to actually execute
        # execution_manager = get_execution_manager()
        # result = execution_manager.execute_query(query.pk_query, endpoint_id, variables)

    except ValueError as e:
        rprint(f"[red]Invalid query ID: {e}[/red]")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        rprint(f"[red]Invalid JSON in variables: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error executing query: {e}[/red]")
        raise typer.Exit(1)


@query_app.command("update")
def update_query(
    query_id: Optional[str] = typer.Option(None, "--id", help="Query ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Query name to update"),
    new_name: Optional[str] = typer.Option(None, "--new-name", help="New query name"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="New GraphQL file"),
    description: Optional[str] = typer.Option(None, "--description", help="New description"),
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Validate GraphQL syntax"),
):
    """Update an existing query."""
    if not query_id and not name:
        rprint("[red]Error: Must specify either --id or --name[/red]")
        raise typer.Exit(1)
    
    try:
        manager = get_query_manager()
        
        # Get query
        if query_id:
            target_id = UUID(query_id)
        else:
            filter_params = QuerySearchFilter(text=name, limit=1)
            queries = manager.search_queries(filter_params)
            if not queries:
                rprint("[red]Query not found[/red]")
                raise typer.Exit(1)
            target_id = queries[0].pk_query
        
        # Build update schema
        query_text = None
        if file:
            if not file.exists():
                rprint(f"[red]Error: File {file} not found[/red]")
                raise typer.Exit(1)
            query_text = GraphQLFileHandler.parse_graphql_file(file)
        
        schema = QueryUpdate(
            name=new_name,
            description=description,
            query_text=query_text,
        )
        
        with console.status(f"[bold green]Updating query..."):
            updated_query = manager.update_query(target_id, schema, validate=validate)
        
        if updated_query:
            rprint(f"[green]✓[/green] Query updated successfully")
            if validate and query_text and updated_query.query_metadata.get("complexity_score"):
                score = updated_query.query_metadata["complexity_score"]
                rprint(f"New complexity score: {score:.2f}")
        else:
            rprint("[red]Query not found or update failed[/red]")
            raise typer.Exit(1)

    except ValueError as e:
        rprint(f"[red]Invalid query ID: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error updating query: {e}[/red]")
        raise typer.Exit(1)


@query_app.command("delete")
def delete_query(
    query_id: Optional[str] = typer.Option(None, "--id", help="Query ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Query name"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
):
    """Delete a query."""
    if not query_id and not name:
        rprint("[red]Error: Must specify either --id or --name[/red]")
        raise typer.Exit(1)
    
    try:
        manager = get_query_manager()
        
        # Get query first to confirm
        if query_id:
            target_id = UUID(query_id)
            query = manager.get_query(target_id)
        else:
            filter_params = QuerySearchFilter(text=name, limit=1)
            queries = manager.search_queries(filter_params)
            if not queries:
                rprint("[red]Query not found[/red]")
                raise typer.Exit(1)
            query = queries[0]
            target_id = query.pk_query
        
        if not query:
            rprint("[red]Query not found[/red]")
            raise typer.Exit(1)
        
        # Confirm deletion
        if not confirm:
            rprint(f"[yellow]Are you sure you want to delete query '{query.name}'?[/yellow]")
            if not typer.confirm("Continue?"):
                rprint("Cancelled")
                raise typer.Exit(0)
        
        with console.status(f"[bold red]Deleting query '{query.name}'..."):
            success = manager.delete_query(target_id)
        
        if success:
            rprint(f"[green]✓[/green] Query '{query.name}' deleted successfully")
        else:
            rprint("[red]Failed to delete query[/red]")
            raise typer.Exit(1)

    except ValueError as e:
        rprint(f"[red]Invalid query ID: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error deleting query: {e}[/red]")
        raise typer.Exit(1)


@query_app.command("validate")
def validate_queries(
    query_id: Optional[str] = typer.Option(None, "--id", help="Validate specific query"),
    collection_id: Optional[str] = typer.Option(None, "--collection", help="Validate collection"),
    fix_issues: bool = typer.Option(False, "--fix", help="Attempt to fix validation issues"),
):
    """Validate GraphQL query syntax."""
    try:
        manager = get_query_manager()
        
        if query_id:
            # Validate single query
            query = manager.get_query(UUID(query_id))
            if not query:
                rprint("[red]Query not found[/red]")
                raise typer.Exit(1)
            
            with console.status(f"[bold green]Validating query '{query.name}'..."):
                # Re-analyze the query
                complexity_analyzer = QueryComplexityAnalyzer()
                try:
                    analysis = complexity_analyzer.analyze_query(query.query_text)
                    rprint(f"[green]✓[/green] Query '{query.name}' is valid")
                    rprint(f"Complexity: {analysis.complexity_score:.2f}")
                    rprint(f"Depth: {analysis.depth}")
                    rprint(f"Field count: {analysis.field_count}")
                except Exception as e:
                    rprint(f"[red]✗[/red] Query '{query.name}' validation failed: {e}")
        
        elif collection_id:
            # Validate all queries in collection
            with console.status(f"[bold green]Validating collection queries..."):
                results = manager.validate_all_queries(UUID(collection_id))
            
            rprint(f"[green]Validation Results:[/green]")
            rprint(f"Total queries: {results['total']}")
            rprint(f"Valid: {results['valid']}")
            rprint(f"Invalid: {results['invalid']}")
            
            if results['errors']:
                rprint(f"\n[red]Errors found:[/red]")
                for error in results['errors']:
                    rprint(f"- {error['query_name']}: {error['error']}")
        
        else:
            # Validate all queries (simplified)
            rprint("[yellow]Validating all queries not implemented yet[/yellow]")

    except ValueError as e:
        rprint(f"[red]Invalid ID: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error validating queries: {e}[/red]")
        raise typer.Exit(1)


def _interactive_query_input() -> str:
    """Interactive query input using editor."""
    rprint("[yellow]Enter your GraphQL query (Ctrl+D to finish):[/yellow]")
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    return "\n".join(lines)


def _output_csv(queries):
    """Output queries in CSV format."""
    import csv
    
    writer = csv.writer(sys.stdout)
    writer.writerow(["ID", "Name", "Description", "Status", "Created", "Tags"])
    
    for query in queries:
        writer.writerow([
            str(query.pk_query),
            query.name,
            query.description or "",
            getattr(query, 'status', 'active'),
            query.created_at.isoformat() if query.created_at else "",
            ",".join(query.tags) if query.tags else ""
        ])