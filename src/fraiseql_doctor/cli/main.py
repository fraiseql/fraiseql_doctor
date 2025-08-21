"""FraiseQL Doctor CLI application."""

import typer
from typing import Optional
from rich import print as rprint

from .commands.query import query_app
from .commands.endpoint import endpoint_app  
from .commands.health import health_app
from .commands.config import config_app
from .commands.batch import batch_app

app = typer.Typer(
    name="fraiseql-doctor",
    help="Health monitoring and query execution tool for FraiseQL/GraphQL endpoints",
    rich_markup_mode="rich",
    no_args_is_help=True,
)


def version_callback(value: bool):
    if value:
        rprint("[bold cyan]FraiseQL Doctor v0.1.0[/bold cyan]")
        rprint("Test-driven health monitoring and query execution tool for FraiseQL/GraphQL endpoints")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True, help="Show version and exit"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
):
    """
    [bold cyan]FraiseQL Doctor[/bold cyan] - Advanced GraphQL endpoint monitoring and query management.
    
    🚀 [bold green]Key Features:[/bold green]
    • Query management with validation and complexity analysis
    • Endpoint health monitoring with detailed reporting
    • Batch operations for efficient testing
    • Rich terminal output with syntax highlighting
    
    📚 [bold yellow]Quick Start:[/bold yellow]
    • [cyan]fraiseql-doctor query list[/cyan] - List all stored queries
    • [cyan]fraiseql-doctor endpoint add[/cyan] - Add a GraphQL endpoint
    • [cyan]fraiseql-doctor health check[/cyan] - Check endpoint health
    
    Use [cyan]--help[/cyan] with any command for detailed usage information.
    """
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)


# Register command groups
app.add_typer(query_app, name="query", help="📝 Manage GraphQL queries")
app.add_typer(endpoint_app, name="endpoint", help="🌐 Manage GraphQL endpoints")
app.add_typer(health_app, name="health", help="💚 Monitor endpoint health")
app.add_typer(batch_app, name="batch", help="🔄 Batch operations for queries")
app.add_typer(config_app, name="config", help="⚙️ Configuration management")

if __name__ == "__main__":
    app()
