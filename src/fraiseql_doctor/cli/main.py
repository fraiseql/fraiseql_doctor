"""FraiseQL Doctor CLI application."""

import typer
from typing import Optional

app = typer.Typer(
    name="fraiseql-doctor",
    help="Health monitoring and query execution tool for FraiseQL/GraphQL endpoints",
)


def version_callback(value: bool):
    if value:
        typer.echo("FraiseQL Doctor v0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True, help="Show version and exit"
    ),
):
    """FraiseQL Doctor main CLI."""
    pass


# Placeholder subcommand groups
query_app = typer.Typer(name="query", help="Manage queries")
endpoint_app = typer.Typer(name="endpoint", help="Manage endpoints")
health_app = typer.Typer(name="health", help="Health monitoring")
config_app = typer.Typer(name="config", help="Configuration")

app.add_typer(query_app, name="query")
app.add_typer(endpoint_app, name="endpoint")
app.add_typer(health_app, name="health")
app.add_typer(config_app, name="config")

if __name__ == "__main__":
    app()
