"""FraiseQL Doctor CLI application."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from fraiseql_doctor import __version__

app = typer.Typer(
    name="fraiseql-doctor",
    help="🔍 Health monitoring and query execution tool for FraiseQL/GraphQL endpoints",
    rich_markup_mode="rich",
    no_args_is_help=True,
    add_completion=True,
)

console = Console()


def version_callback(value: bool) -> None:
    """Handle version callback."""
    if value:
        console.print(f"🔍 FraiseQL Doctor v{__version__}")
        raise typer.Exit


@app.callback()
def main(
    ctx: typer.Context,
    version: bool | None = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True, help="Show version"
    ),
    config_file: Path | None = typer.Option(None, "--config", "-c", help="Config file path"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
) -> None:
    """FraiseQL Doctor - Monitor and execute GraphQL queries."""
    # Store global options in context
    ctx.ensure_object(dict)
    ctx.obj["config_file"] = config_file
    ctx.obj["verbose"] = verbose

    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")


@app.command()
def hello() -> None:
    """Test command to verify CLI is working."""
    text = Text("Hello from FraiseQL Doctor! 🔍", style="bold green")
    panel = Panel(text, title="Welcome", border_style="green")
    console.print(panel)
    console.print("CLI is working correctly!")


if __name__ == "__main__":
    app()
