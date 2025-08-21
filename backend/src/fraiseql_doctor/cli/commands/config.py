"""Configuration management CLI commands."""

import json
import time
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# Mock imports for Phase 2 demonstration
# from ...core.config import DatabaseConfig, get_config
# from ...core.database import init_database, get_db_session


# Mock classes
class DatabaseConfig:
    def __init__(self, url, **kwargs):
        self.url = url
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockConfig:
    def __init__(self):
        self.database = DatabaseConfig("postgresql://localhost:5432/fraiseql_doctor")


def get_config():
    return MockConfig()


def init_database():
    print("Mock database initialization")


console = Console()

config_app = typer.Typer(name="config", help="Configuration management")


@config_app.command("init")
def init_config(
    database_url: Optional[str] = typer.Option(
        None, "--database-url", help="PostgreSQL database URL"
    ),
    config_file: Optional[Path] = typer.Option(None, "--config", help="Config file to create"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing config"),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", help="Interactive configuration"
    ),
):
    """Initialize FraiseQL Doctor configuration."""
    try:
        # Determine config file location
        if config_file:
            config_path = config_file
        else:
            config_dir = Path.home() / ".config" / "fraiseql-doctor"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / "config.yaml"

        # Check if config already exists
        if config_path.exists() and not force:
            rprint(f"[yellow]Configuration file already exists at {config_path}[/yellow]")
            rprint("Use --force to overwrite or specify a different path with --config")
            raise typer.Exit(1)

        config_data = {}

        if interactive:
            rprint("[cyan]🚀 FraiseQL Doctor Configuration Setup[/cyan]\n")

            # Database configuration
            rprint("[bold]Database Configuration[/bold]")

            if not database_url:
                default_url = "postgresql://localhost:5432/fraiseql_doctor"
                database_url = typer.prompt("Database URL", default=default_url, show_default=True)

            config_data["database"] = {
                "url": database_url,
                "pool_size": 10,
                "max_overflow": 20,
                "pool_timeout": 30,
                "pool_recycle": 3600,
            }

            # Default timeout settings
            default_timeout = typer.prompt("Default query timeout (seconds)", default=30, type=int)
            max_retries = typer.prompt("Default max retries", default=3, type=int)

            config_data["execution"] = {
                "default_timeout_seconds": default_timeout,
                "default_max_retries": max_retries,
                "default_max_concurrent": 10,
                "default_batch_size": 50,
            }

            # Logging configuration
            log_level = typer.prompt(
                "Log level",
                default="INFO",
                type=typer.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
            )

            config_data["logging"] = {
                "level": log_level,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": None,  # Console only by default
            }

            # Health monitoring defaults
            config_data["health_monitoring"] = {
                "default_check_interval": 30,
                "default_timeout": 10,
                "save_results_by_default": True,
                "alert_on_status_change": False,
            }

        else:
            # Non-interactive mode - use defaults
            config_data = {
                "database": {
                    "url": database_url or "postgresql://localhost:5432/fraiseql_doctor",
                    "pool_size": 10,
                    "max_overflow": 20,
                    "pool_timeout": 30,
                    "pool_recycle": 3600,
                },
                "execution": {
                    "default_timeout_seconds": 30,
                    "default_max_retries": 3,
                    "default_max_concurrent": 10,
                    "default_batch_size": 50,
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "file": None,
                },
                "health_monitoring": {
                    "default_check_interval": 30,
                    "default_timeout": 10,
                    "save_results_by_default": True,
                    "alert_on_status_change": False,
                },
            }

        # Save configuration
        with console.status(f"[bold green]Saving configuration to {config_path}..."):
            with open(config_path, "w") as f:
                yaml.safe_dump(config_data, f, default_flow_style=False, indent=2)

        rprint(f"[green]✓[/green] Configuration saved to {config_path}")

        # Test database connection if URL provided
        if database_url:
            rprint("\n[yellow]Testing database connection...[/yellow]")
            try:
                # Create temporary config for testing
                test_config = DatabaseConfig(**config_data["database"])

                with console.status("Connecting to database..."):
                    # Test connection
                    from sqlalchemy import create_engine, text

                    engine = create_engine(test_config.url)
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))

                rprint("[green]✓[/green] Database connection successful")

                # Ask about database initialization
                if interactive and typer.confirm("\nInitialize database schema?"):
                    init_database()
                    rprint("[green]✓[/green] Database schema initialized")

            except Exception as e:
                rprint(f"[red]✗[/red] Database connection failed: {e}")
                rprint("You can update the database configuration later with:")
                rprint("  fraiseql-doctor config update --database-url <new-url>")

        # Show next steps
        rprint("\n[cyan]Configuration complete![/cyan]")
        rprint(f"Config file: {config_path}")
        rprint("\n[bold]Next steps:[/bold]")
        rprint("• Add GraphQL endpoints: [cyan]fraiseql-doctor endpoint add[/cyan]")
        rprint("• Create queries: [cyan]fraiseql-doctor query create[/cyan]")
        rprint("• Check health: [cyan]fraiseql-doctor health check --all[/cyan]")

    except Exception as e:
        rprint(f"[red]Error initializing configuration: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("show")
def show_config(
    section: Optional[str] = typer.Option(None, "--section", help="Show specific section only"),
    format: str = typer.Option("yaml", "--format", help="Output format: yaml, json"),
    show_sensitive: bool = typer.Option(False, "--show-sensitive", help="Show sensitive values"),
):
    """Show current configuration."""
    try:
        config = get_config()

        # Convert config to dictionary
        config_dict = {}

        if hasattr(config, "database"):
            config_dict["database"] = {
                "url": config.database.url if show_sensitive else _mask_url(config.database.url),
                "pool_size": config.database.pool_size,
                "max_overflow": config.database.max_overflow,
                "pool_timeout": config.database.pool_timeout,
                "pool_recycle": config.database.pool_recycle,
            }

        # Add other config sections as they're implemented
        config_dict["execution"] = {
            "default_timeout_seconds": 30,
            "default_max_retries": 3,
            "default_max_concurrent": 10,
            "default_batch_size": 50,
        }

        config_dict["logging"] = {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        }

        # Filter to specific section if requested
        if section:
            if section in config_dict:
                config_dict = {section: config_dict[section]}
            else:
                rprint(f"[red]Unknown configuration section: {section}[/red]")
                rprint(f"Available sections: {', '.join(config_dict.keys())}")
                raise typer.Exit(1)

        # Output in requested format
        if format == "yaml":
            yaml_content = yaml.safe_dump(config_dict, default_flow_style=False, indent=2)
            syntax = Syntax(yaml_content, "yaml", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="Configuration", border_style="blue"))

        elif format == "json":
            json_content = json.dumps(config_dict, indent=2)
            syntax = Syntax(json_content, "json", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="Configuration", border_style="blue"))

        else:
            rprint(f"[red]Unknown format: {format}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error showing configuration: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("validate")
def validate_config(
    config_file: Optional[Path] = typer.Option(None, "--config", help="Config file to validate"),
    fix_permissions: bool = typer.Option(False, "--fix-permissions", help="Fix file permissions"),
):
    """Validate configuration file and settings."""
    try:
        # Load configuration
        if config_file:
            if not config_file.exists():
                rprint(f"[red]Configuration file not found: {config_file}[/red]")
                raise typer.Exit(1)

            with open(config_file) as f:
                config_data = yaml.safe_load(f)
        else:
            config = get_config()
            config_file = Path.home() / ".config" / "fraiseql-doctor" / "config.yaml"
            config_data = {"database": {"url": config.database.url}}

        rprint(f"[cyan]Validating configuration: {config_file}[/cyan]\n")

        errors = []
        warnings = []

        # Check database configuration
        if "database" in config_data:
            db_config = config_data["database"]

            if "url" not in db_config:
                errors.append("Database URL is required")
            else:
                # Test database connection
                try:
                    from sqlalchemy import create_engine, text

                    engine = create_engine(db_config["url"])
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    rprint("[green]✓[/green] Database connection successful")
                except Exception as e:
                    errors.append(f"Database connection failed: {e}")
        else:
            errors.append("Database configuration is missing")

        # Check file permissions
        if config_file.exists():
            file_mode = oct(config_file.stat().st_mode)[-3:]

            if file_mode not in ["600", "644"]:
                warning_msg = f"Config file permissions ({file_mode}) may be too permissive"
                warnings.append(warning_msg)

                if fix_permissions:
                    config_file.chmod(0o600)
                    rprint("[green]✓[/green] Fixed file permissions (set to 600)")
                else:
                    rprint(f"[yellow]⚠[/yellow] {warning_msg}")
                    rprint("  Use --fix-permissions to correct this")

        # Check for required directories
        config_dir = config_file.parent
        if not config_dir.exists():
            warnings.append(f"Configuration directory does not exist: {config_dir}")

        # Validate execution settings
        if "execution" in config_data:
            exec_config = config_data["execution"]

            if exec_config.get("default_timeout_seconds", 30) < 1:
                errors.append("Default timeout must be at least 1 second")

            if exec_config.get("default_max_concurrent", 10) < 1:
                errors.append("Max concurrent executions must be at least 1")

        # Show results
        if errors:
            rprint(f"\n[red]Configuration Errors ({len(errors)}):[/red]")
            for error in errors:
                rprint(f"  • {error}")

        if warnings:
            rprint(f"\n[yellow]Configuration Warnings ({len(warnings)}):[/yellow]")
            for warning in warnings:
                rprint(f"  • {warning}")

        if not errors and not warnings:
            rprint("\n[green]✓[/green] Configuration is valid")
        elif not errors:
            rprint("\n[yellow]Configuration is valid with warnings[/yellow]")
        else:
            rprint(f"\n[red]Configuration validation failed with {len(errors)} errors[/red]")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error validating configuration: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("update")
def update_config(
    database_url: Optional[str] = typer.Option(None, "--database-url", help="Update database URL"),
    timeout: Optional[int] = typer.Option(None, "--default-timeout", help="Update default timeout"),
    log_level: Optional[str] = typer.Option(None, "--log-level", help="Update log level"),
    config_file: Optional[Path] = typer.Option(None, "--config", help="Config file to update"),
):
    """Update configuration settings."""
    if not any([database_url, timeout, log_level]):
        rprint("[red]No configuration updates specified[/red]")
        rprint("Available options: --database-url, --default-timeout, --log-level")
        raise typer.Exit(1)

    try:
        # Determine config file
        if config_file:
            if not config_file.exists():
                rprint(f"[red]Configuration file not found: {config_file}[/red]")
                raise typer.Exit(1)
        else:
            config_file = Path.home() / ".config" / "fraiseql-doctor" / "config.yaml"
            if not config_file.exists():
                rprint(
                    "[red]No configuration file found. Run 'fraiseql-doctor config init' first[/red]"
                )
                raise typer.Exit(1)

        # Load existing config
        with open(config_file) as f:
            config_data = yaml.safe_load(f) or {}

        updates = []

        # Update database URL
        if database_url:
            if "database" not in config_data:
                config_data["database"] = {}
            config_data["database"]["url"] = database_url
            updates.append("database URL")

            # Test new database connection
            try:
                from sqlalchemy import create_engine, text

                engine = create_engine(database_url)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                rprint("[green]✓[/green] New database connection tested successfully")
            except Exception as e:
                rprint(f"[yellow]⚠[/yellow] Warning: Could not test new database URL: {e}")

        # Update default timeout
        if timeout:
            if "execution" not in config_data:
                config_data["execution"] = {}
            config_data["execution"]["default_timeout_seconds"] = timeout
            updates.append(f"default timeout to {timeout}s")

        # Update log level
        if log_level:
            if log_level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
                rprint(f"[red]Invalid log level: {log_level}[/red]")
                rprint("Valid levels: DEBUG, INFO, WARNING, ERROR")
                raise typer.Exit(1)

            if "logging" not in config_data:
                config_data["logging"] = {}
            config_data["logging"]["level"] = log_level.upper()
            updates.append(f"log level to {log_level.upper()}")

        # Save updated config
        with console.status("[bold green]Saving configuration updates..."):
            with open(config_file, "w") as f:
                yaml.safe_dump(config_data, f, default_flow_style=False, indent=2)

        rprint(f"[green]✓[/green] Configuration updated: {', '.join(updates)}")

    except Exception as e:
        rprint(f"[red]Error updating configuration: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("reset")
def reset_config(
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup before reset"),
):
    """Reset configuration to defaults."""
    if not confirm:
        rprint("[red]⚠ This will reset all configuration to defaults![/red]")
        if not typer.confirm("Are you sure you want to continue?"):
            rprint("Cancelled")
            raise typer.Exit(0)

    try:
        config_dir = Path.home() / ".config" / "fraiseql-doctor"
        config_file = config_dir / "config.yaml"

        if not config_file.exists():
            rprint("[yellow]No configuration file found to reset[/yellow]")
            return

        # Create backup if requested
        if backup:
            backup_file = config_file.with_suffix(f".backup.{int(time.time())}.yaml")
            import shutil

            shutil.copy2(config_file, backup_file)
            rprint(f"[green]✓[/green] Backup created: {backup_file}")

        # Remove existing config
        config_file.unlink()

        rprint("[green]✓[/green] Configuration reset")
        rprint("Run [cyan]fraiseql-doctor config init[/cyan] to create a new configuration")

    except Exception as e:
        rprint(f"[red]Error resetting configuration: {e}[/red]")
        raise typer.Exit(1)


def _mask_url(url: str) -> str:
    """Mask sensitive parts of database URL."""
    import re

    # Pattern to match postgresql://user:password@host:port/database
    pattern = r"(postgresql://[^:]+:)([^@]+)(@.*)"

    def replace_password(match):
        return f"{match.group(1)}***{match.group(3)}"

    return re.sub(pattern, replace_password, url)
