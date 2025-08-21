"""Endpoint management CLI commands."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Mock imports for Phase 2 demonstration - avoiding circular imports
# from ...core.database import get_db_session
# from ...models.endpoint import Endpoint
# from ...schemas.endpoint import EndpointCreate, EndpointUpdate
# from ...services.fraiseql_client import FraiseQLClient, NetworkError, GraphQLExecutionError

# Mock classes for Phase 2
class MockEndpoint:
    # Class attributes for SQLAlchemy-style access
    name = "name_field"
    
    def __init__(self, name="Mock Endpoint", url="https://api.example.com/graphql"):
        self.pk_endpoint = "mock-endpoint-uuid"
        self.name = name
        self.url = url
        self.description = "Mock endpoint for CLI demonstration"
        self.timeout_seconds = 30
        self.auth_config = {"method": "none"}
        self.custom_headers = {}
        self.endpoint_metadata = {}
        self.created_at = None

class NetworkError(Exception):
    pass

class GraphQLExecutionError(Exception):
    pass

class MockFraiseQLClient:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.timeout_seconds = 30
    
    def execute_query(self, query, variables=None):
        return {"data": {"__schema": {"queryType": {"name": "Query"}}}}

FraiseQLClient = MockFraiseQLClient
Endpoint = MockEndpoint

from ..utils.formatters import format_endpoint_table, format_endpoint_detail, format_progress_bar

console = Console()

endpoint_app = typer.Typer(name="endpoint", help="Manage GraphQL endpoints")


def get_endpoint_manager():
    """Get database session for endpoint management - mock for Phase 2."""
    class MockDB:
        def query(self, model):
            return MockQueryResult()
        
        def get(self, model, pk):
            return MockEndpoint("Retrieved Endpoint") if pk else None
        
        def add(self, obj): pass
        def delete(self, obj): pass
        def commit(self): pass
    
    class MockQueryResult:
        def filter(self, *args): return self
        def order_by(self, *args): return self
        def all(self): 
            return [
                MockEndpoint("Sample Endpoint 1", "https://api.example.com/graphql"),
                MockEndpoint("Sample Endpoint 2", "https://api2.example.com/graphql")
            ]
        def first(self): return MockEndpoint("Found Endpoint")
    
    return MockDB()


@endpoint_app.command("add")
def add_endpoint(
    name: str = typer.Option(..., "--name", "-n", help="Endpoint name"),
    url: str = typer.Option(..., "--url", "-u", help="GraphQL endpoint URL"),
    description: Optional[str] = typer.Option(None, "--description", help="Endpoint description"),
    auth_method: Optional[str] = typer.Option(None, "--auth", help="Auth method: bearer, apikey, basic, none"),
    token: Optional[str] = typer.Option(None, "--token", help="Bearer token or API key"),
    username: Optional[str] = typer.Option(None, "--username", help="Basic auth username"),
    password: Optional[str] = typer.Option(None, "--password", help="Basic auth password"),
    timeout: int = typer.Option(30, "--timeout", help="Request timeout in seconds"),
    headers_file: Optional[Path] = typer.Option(None, "--headers", help="JSON file with custom headers"),
    headers_json: Optional[str] = typer.Option(None, "--header-json", help="Custom headers as JSON string"),
    test_connection: bool = typer.Option(True, "--test/--no-test", help="Test connection after adding"),
):
    """Add a new GraphQL endpoint."""
    try:
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            rprint("[red]Error: URL must start with http:// or https://[/red]")
            raise typer.Exit(1)
        
        # Build auth configuration
        auth_config = {}
        if auth_method:
            auth_method = auth_method.lower()
            if auth_method == "bearer":
                if not token:
                    token = typer.prompt("Bearer token", hide_input=True)
                auth_config = {"method": "bearer", "token": token}
            
            elif auth_method == "apikey":
                if not token:
                    token = typer.prompt("API key", hide_input=True)
                auth_config = {"method": "apikey", "key": token}
            
            elif auth_method == "basic":
                if not username:
                    username = typer.prompt("Username")
                if not password:
                    password = typer.prompt("Password", hide_input=True)
                auth_config = {"method": "basic", "username": username, "password": password}
            
            elif auth_method not in ["none"]:
                rprint(f"[red]Error: Unknown auth method '{auth_method}'. Use: bearer, apikey, basic, none[/red]")
                raise typer.Exit(1)
        
        # Load custom headers
        custom_headers = {}
        if headers_file:
            if not headers_file.exists():
                rprint(f"[red]Error: Headers file {headers_file} not found[/red]")
                raise typer.Exit(1)
            try:
                custom_headers = json.loads(headers_file.read_text())
            except json.JSONDecodeError as e:
                rprint(f"[red]Error parsing headers file: {e}[/red]")
                raise typer.Exit(1)
        elif headers_json:
            try:
                custom_headers = json.loads(headers_json)
            except json.JSONDecodeError as e:
                rprint(f"[red]Error parsing headers JSON: {e}[/red]")
                raise typer.Exit(1)
        
        # Create endpoint
        db_session = get_endpoint_manager()
        
        # Check for existing endpoint with same name
        existing = db_session.query(Endpoint).filter(Endpoint.name == name).first()
        if existing:
            rprint(f"[red]Error: Endpoint with name '{name}' already exists[/red]")
            raise typer.Exit(1)
        
        endpoint = Endpoint(
            pk_endpoint=uuid4(),
            name=name,
            description=description,
            url=url,
            timeout_seconds=timeout,
            auth_config=auth_config,
            custom_headers=custom_headers,
            endpoint_metadata={}
        )
        
        with console.status(f"[bold green]Adding endpoint '{name}'..."):
            db_session.add(endpoint)
            db_session.commit()
        
        rprint(f"[green]✓[/green] Endpoint '{name}' added successfully")
        rprint(f"Endpoint ID: {endpoint.pk_endpoint}")
        
        # Test connection if requested
        if test_connection:
            rprint("\n[yellow]Testing connection...[/yellow]")
            try:
                client = FraiseQLClient(endpoint)
                with console.status("Testing endpoint connectivity..."):
                    # Try a simple introspection query
                    introspection_query = """
                        query IntrospectionQuery {
                            __schema {
                                types {
                                    name
                                }
                            }
                        }
                    """
                    result = client.execute_query(introspection_query)
                    
                if "errors" not in result:
                    rprint("[green]✓[/green] Connection test successful")
                else:
                    rprint(f"[yellow]⚠[/yellow] Connection established but GraphQL errors: {result['errors']}")
            
            except NetworkError as e:
                rprint(f"[red]✗[/red] Connection test failed: {e}")
            except Exception as e:
                rprint(f"[red]✗[/red] Connection test error: {e}")

    except Exception as e:
        rprint(f"[red]Error adding endpoint: {e}[/red]")
        raise typer.Exit(1)


@endpoint_app.command("list")
def list_endpoints(
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status: healthy, unhealthy, unknown"),
    format: str = typer.Option("table", "--format", help="Output format: table, json"),
    show_urls: bool = typer.Option(False, "--show-urls", help="Show full URLs in table"),
):
    """List all configured endpoints."""
    try:
        db_session = get_endpoint_manager()
        
        with console.status("[bold green]Loading endpoints..."):
            query = db_session.query(Endpoint)
            
            # Apply status filter if provided
            if status:
                # Note: This would require a status field or join with health checks
                # For now, we'll just load all and filter in memory
                pass
            
            endpoints = query.order_by(Endpoint.name).all()
        
        if not endpoints:
            rprint("[yellow]No endpoints configured[/yellow]")
            rprint("Use [cyan]fraiseql-doctor endpoint add[/cyan] to add your first endpoint.")
            return
        
        if format == "table":
            if show_urls:
                # Custom table with full URLs
                table = Table(
                    title="GraphQL Endpoints",
                    show_header=True,
                    header_style="bold magenta"
                )
                table.add_column("Name", style="cyan")
                table.add_column("URL", style="white")
                table.add_column("Auth", style="yellow")
                table.add_column("Timeout", style="blue")
                
                for endpoint in endpoints:
                    auth_method = endpoint.auth_config.get('method', 'none') if endpoint.auth_config else 'none'
                    auth_text = auth_method.upper() if auth_method != 'none' else "-"
                    timeout_text = f"{endpoint.timeout_seconds}s"
                    
                    table.add_row(
                        endpoint.name,
                        endpoint.url,
                        auth_text,
                        timeout_text
                    )
                
                console.print(table)
            else:
                table = format_endpoint_table(endpoints)
                console.print(table)
        
        elif format == "json":
            output = []
            for endpoint in endpoints:
                endpoint_dict = {
                    "pk_endpoint": str(endpoint.pk_endpoint),
                    "name": endpoint.name,
                    "url": endpoint.url,
                    "description": endpoint.description,
                    "timeout_seconds": endpoint.timeout_seconds,
                    "auth_method": endpoint.auth_config.get('method', 'none') if endpoint.auth_config else 'none',
                    "has_custom_headers": bool(endpoint.custom_headers),
                    "created_at": endpoint.created_at.isoformat() if endpoint.created_at else None
                }
                output.append(endpoint_dict)
            
            rprint(json.dumps(output, indent=2))
        
        else:
            rprint(f"[red]Unknown format: {format}[/red]")
            raise typer.Exit(1)
        
        rprint(f"\n[dim]Showing {len(endpoints)} endpoints[/dim]")

    except Exception as e:
        rprint(f"[red]Error listing endpoints: {e}[/red]")
        raise typer.Exit(1)


@endpoint_app.command("show")
def show_endpoint(
    endpoint_id: Optional[str] = typer.Option(None, "--id", help="Endpoint ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Endpoint name"),
    format: str = typer.Option("pretty", "--format", help="Output format: pretty, json"),
    show_sensitive: bool = typer.Option(False, "--show-auth", help="Show authentication details"),
):
    """Show detailed information about an endpoint."""
    if not endpoint_id and not name:
        rprint("[red]Error: Must specify either --id or --name[/red]")
        raise typer.Exit(1)
    
    try:
        db_session = get_endpoint_manager()
        
        if endpoint_id:
            endpoint = db_session.get(Endpoint, UUID(endpoint_id))
        else:
            endpoint = db_session.query(Endpoint).filter(Endpoint.name == name).first()
        
        if not endpoint:
            rprint("[red]Endpoint not found[/red]")
            raise typer.Exit(1)
        
        if format == "pretty":
            # Mask sensitive information unless explicitly requested
            if not show_sensitive and endpoint.auth_config:
                auth_config = endpoint.auth_config.copy()
                if 'token' in auth_config:
                    auth_config['token'] = auth_config['token'][:8] + "..." if len(auth_config['token']) > 8 else "***"
                if 'password' in auth_config:
                    auth_config['password'] = "***"
                endpoint_copy = endpoint
                endpoint_copy.auth_config = auth_config
                panel = format_endpoint_detail(endpoint_copy)
            else:
                panel = format_endpoint_detail(endpoint)
            console.print(panel)
        
        elif format == "json":
            endpoint_dict = {
                "pk_endpoint": str(endpoint.pk_endpoint),
                "name": endpoint.name,
                "url": endpoint.url,
                "description": endpoint.description,
                "timeout_seconds": endpoint.timeout_seconds,
                "auth_config": endpoint.auth_config if show_sensitive else {
                    k: ("***" if k in ["token", "password", "key"] else v)
                    for k, v in (endpoint.auth_config or {}).items()
                },
                "custom_headers": endpoint.custom_headers,
                "endpoint_metadata": endpoint.endpoint_metadata,
                "created_at": endpoint.created_at.isoformat() if endpoint.created_at else None,
                "updated_at": endpoint.updated_at.isoformat() if endpoint.updated_at else None
            }
            rprint(json.dumps(endpoint_dict, indent=2))
        
        else:
            rprint(f"[red]Unknown format: {format}[/red]")
            raise typer.Exit(1)

    except ValueError as e:
        rprint(f"[red]Invalid endpoint ID: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error showing endpoint: {e}[/red]")
        raise typer.Exit(1)


@endpoint_app.command("test")
def test_endpoint(
    endpoint_id: Optional[str] = typer.Option(None, "--id", help="Endpoint ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Endpoint name"),
    query: Optional[str] = typer.Option(None, "--query", help="Custom test query"),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="Override timeout"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Test endpoint connectivity and GraphQL capabilities."""
    if not endpoint_id and not name:
        rprint("[red]Error: Must specify either --id or --name[/red]")
        raise typer.Exit(1)
    
    try:
        db_session = get_endpoint_manager()
        
        if endpoint_id:
            endpoint = db_session.get(Endpoint, UUID(endpoint_id))
        else:
            endpoint = db_session.query(Endpoint).filter(Endpoint.name == name).first()
        
        if not endpoint:
            rprint("[red]Endpoint not found[/red]")
            raise typer.Exit(1)
        
        rprint(f"[cyan]Testing endpoint:[/cyan] {endpoint.name}")
        rprint(f"[cyan]URL:[/cyan] {endpoint.url}")
        
        # Create client
        client = FraiseQLClient(endpoint)
        if timeout:
            client.timeout_seconds = timeout
        
        # Use custom query or default introspection
        test_query = query or """
            query TestConnection {
                __schema {
                    queryType {
                        name
                    }
                    mutationType {
                        name
                    }
                    subscriptionType {
                        name
                    }
                }
            }
        """
        
        # Run tests with progress indicator
        with format_progress_bar() as progress:
            task = progress.add_task("Testing connection...", total=None)
            
            try:
                result = client.execute_query(test_query)
                progress.stop()
                
                if "errors" in result:
                    rprint("[red]✗[/red] GraphQL errors in response:")
                    for error in result["errors"]:
                        rprint(f"  • {error.get('message', 'Unknown error')}")
                    
                    if verbose:
                        rprint("\n[dim]Full response:[/dim]")
                        rprint(json.dumps(result, indent=2))
                    
                    raise typer.Exit(1)
                
                else:
                    rprint("[green]✓[/green] Connection test successful")
                    
                    # Show schema info if using default query
                    if not query and "data" in result and "__schema" in result["data"]:
                        schema = result["data"]["__schema"]
                        rprint(f"[green]Query Type:[/green] {schema.get('queryType', {}).get('name', 'Not available')}")
                        
                        if schema.get('mutationType'):
                            rprint(f"[green]Mutation Type:[/green] {schema['mutationType']['name']}")
                        
                        if schema.get('subscriptionType'):
                            rprint(f"[green]Subscription Type:[/green] {schema['subscriptionType']['name']}")
                    
                    if verbose:
                        rprint("\n[dim]Full response:[/dim]")
                        rprint(json.dumps(result, indent=2))

            except NetworkError as e:
                progress.stop()
                rprint(f"[red]✗[/red] Network error: {e}")
                raise typer.Exit(1)
            
            except GraphQLExecutionError as e:
                progress.stop()
                rprint(f"[red]✗[/red] GraphQL execution error: {e}")
                raise typer.Exit(1)
            
            except Exception as e:
                progress.stop()
                rprint(f"[red]✗[/red] Unexpected error: {e}")
                if verbose:
                    import traceback
                    rprint(traceback.format_exc())
                raise typer.Exit(1)

    except ValueError as e:
        rprint(f"[red]Invalid endpoint ID: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error testing endpoint: {e}[/red]")
        raise typer.Exit(1)


@endpoint_app.command("update")
def update_endpoint(
    endpoint_id: Optional[str] = typer.Option(None, "--id", help="Endpoint ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Endpoint name to update"),
    new_name: Optional[str] = typer.Option(None, "--new-name", help="New endpoint name"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="New endpoint URL"),
    description: Optional[str] = typer.Option(None, "--description", help="New description"),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="New timeout in seconds"),
    clear_auth: bool = typer.Option(False, "--clear-auth", help="Remove authentication"),
):
    """Update an existing endpoint."""
    if not endpoint_id and not name:
        rprint("[red]Error: Must specify either --id or --name[/red]")
        raise typer.Exit(1)
    
    try:
        db_session = get_endpoint_manager()
        
        if endpoint_id:
            endpoint = db_session.get(Endpoint, UUID(endpoint_id))
        else:
            endpoint = db_session.query(Endpoint).filter(Endpoint.name == name).first()
        
        if not endpoint:
            rprint("[red]Endpoint not found[/red]")
            raise typer.Exit(1)
        
        # Track what's being updated
        updates = []
        
        if new_name:
            # Check for name conflicts
            existing = db_session.query(Endpoint).filter(
                Endpoint.name == new_name,
                Endpoint.pk_endpoint != endpoint.pk_endpoint
            ).first()
            if existing:
                rprint(f"[red]Error: Endpoint with name '{new_name}' already exists[/red]")
                raise typer.Exit(1)
            endpoint.name = new_name
            updates.append(f"name → {new_name}")
        
        if url:
            if not url.startswith(('http://', 'https://')):
                rprint("[red]Error: URL must start with http:// or https://[/red]")
                raise typer.Exit(1)
            endpoint.url = url
            updates.append(f"url → {url}")
        
        if description is not None:  # Allow empty string to clear description
            endpoint.description = description or None
            updates.append(f"description → {description or 'cleared'}")
        
        if timeout:
            endpoint.timeout_seconds = timeout
            updates.append(f"timeout → {timeout}s")
        
        if clear_auth:
            endpoint.auth_config = {}
            updates.append("authentication cleared")
        
        if not updates:
            rprint("[yellow]No changes specified[/yellow]")
            return
        
        with console.status(f"[bold green]Updating endpoint..."):
            db_session.commit()
        
        rprint(f"[green]✓[/green] Endpoint '{endpoint.name}' updated successfully")
        rprint("Changes made:")
        for update in updates:
            rprint(f"  • {update}")

    except ValueError as e:
        rprint(f"[red]Invalid endpoint ID: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error updating endpoint: {e}[/red]")
        raise typer.Exit(1)


@endpoint_app.command("remove")
def remove_endpoint(
    endpoint_id: Optional[str] = typer.Option(None, "--id", help="Endpoint ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Endpoint name"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
):
    """Remove an endpoint."""
    if not endpoint_id and not name:
        rprint("[red]Error: Must specify either --id or --name[/red]")
        raise typer.Exit(1)
    
    try:
        db_session = get_endpoint_manager()
        
        if endpoint_id:
            endpoint = db_session.get(Endpoint, UUID(endpoint_id))
        else:
            endpoint = db_session.query(Endpoint).filter(Endpoint.name == name).first()
        
        if not endpoint:
            rprint("[red]Endpoint not found[/red]")
            raise typer.Exit(1)
        
        # Show what will be deleted
        rprint(f"[yellow]About to delete endpoint:[/yellow]")
        rprint(f"  Name: {endpoint.name}")
        rprint(f"  URL: {endpoint.url}")
        
        # Confirm deletion
        if not confirm:
            rprint(f"\n[red]This action cannot be undone![/red]")
            if not typer.confirm("Are you sure you want to delete this endpoint?"):
                rprint("Cancelled")
                raise typer.Exit(0)
        
        with console.status(f"[bold red]Deleting endpoint '{endpoint.name}'..."):
            db_session.delete(endpoint)
            db_session.commit()
        
        rprint(f"[green]✓[/green] Endpoint '{endpoint.name}' deleted successfully")

    except ValueError as e:
        rprint(f"[red]Invalid endpoint ID: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error deleting endpoint: {e}[/red]")
        raise typer.Exit(1)