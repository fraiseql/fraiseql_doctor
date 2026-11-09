"""Batch operations CLI commands."""

import json
from pathlib import Path
from uuid import UUID

import typer
from rich import print as rprint
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

# Mock imports for Phase 2 demonstration
# from ...core.database import get_db_session
# from ...core.execution_manager import QueryExecutionManager, BatchMode, ExecutionConfig
# from ...core.query_collection import QueryCollectionManager, QuerySearchFilter
# from ...models.endpoint import Endpoint
# from ...models.query import Query
# from ...services.complexity import QueryComplexityAnalyzer
# from ...services.fraiseql_client import FraiseQLClient


# Mock classes and enums
class BatchMode:
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PRIORITY = "priority"
    ADAPTIVE = "adaptive"


class ExecutionConfig:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockDB:
    def query(self, model):
        return MockQueryResult()

    def get(self, model, pk):
        return MockEndpoint("Test") if pk else None


class MockQueryResult:
    def order_by(self, *args):
        return self

    def all(self):
        # Return some mock queries for demonstration
        return [
            Query("Sample Query 1", "query { users { id name } }"),
            Query("Sample Query 2", "query { products { id title price } }"),
            Query("Health Check", "query { __schema { types { name } } }"),
        ]


class MockEndpoint:
    def __init__(self, name="Mock"):
        self.pk_endpoint = "mock-uuid"
        self.name = name


class Query:
    """Mock Query class for batch operations with SQLAlchemy-style class attributes."""

    # Class attributes for SQLAlchemy compatibility (order_by usage)
    name = "mock_name_field"
    pk_query = "mock_pk_field"
    created_at = "mock_created_at_field"
    updated_at = "mock_updated_at_field"

    def __init__(self, name="Mock Query", query_text="query { mockField }"):
        self.name = name
        self.query_text = query_text
        self.pk_query = "mock-query-uuid"
        self.description = "Mock query for batch operations"
        self.variables = {}
        self.tags = ["batch", "demo"]
        self.created_at = None
        self.updated_at = None


from ..utils.file_handlers import ExportHandler

console = Console()

# Create a batch command app
batch_app = typer.Typer(name="batch", help="Batch operations for queries and health checks")


def get_managers():
    """Get required managers for batch operations - mock for Phase 2."""
    return MockDB(), "mock-query-manager", "mock-execution-manager"


@batch_app.command("execute")
def batch_execute(
    collection_id: str | None = typer.Option(
        None, "--collection", help="Execute all queries in collection"
    ),
    query_ids: list[str] | None = typer.Option(
        None, "--query", help="Specific query IDs to execute"
    ),
    query_file: Path | None = typer.Option(
        None, "--queries-file", help="File with query IDs (one per line)"
    ),
    endpoint_id: str | None = typer.Option(
        None, "--endpoint-id", help="Endpoint ID to execute against"
    ),
    endpoint_name: str | None = typer.Option(
        None, "--endpoint", "-e", help="Endpoint name to execute against"
    ),
    mode: str = typer.Option(
        "parallel", "--mode", help="Execution mode: parallel, sequential, priority, adaptive"
    ),
    max_concurrent: int = typer.Option(5, "--max-concurrent", help="Maximum concurrent executions"),
    timeout: int = typer.Option(60, "--timeout", help="Query timeout in seconds"),
    output_dir: Path | None = typer.Option(
        None, "--output", "-o", help="Save results to directory"
    ),
    format: str = typer.Option("json", "--format", help="Output format: json, csv"),
    continue_on_error: bool = typer.Option(
        True, "--continue/--stop-on-error", help="Continue on query errors"
    ),
):
    """Execute multiple queries in batch."""
    try:
        db_session, query_manager, execution_manager = get_managers()

        # Get target queries
        target_query_ids = []

        if collection_id:
            # Get all queries in collection (simplified - would need collection query)
            rprint("[yellow]Collection-based execution not fully implemented yet[/yellow]")
            rprint("Use --query to specify individual query IDs")
            raise typer.Exit(1)

        if query_ids:
            target_query_ids = [UUID(qid) for qid in query_ids]

        elif query_file:
            if not query_file.exists():
                rprint(f"[red]Query file not found: {query_file}[/red]")
                raise typer.Exit(1)

            lines = query_file.read_text().strip().split("\n")
            target_query_ids = [UUID(line.strip()) for line in lines if line.strip()]

        else:
            rprint("[red]Error: Must specify --collection, --query, or --queries-file[/red]")
            raise typer.Exit(1)

        if not target_query_ids:
            rprint("[yellow]No queries to execute[/yellow]")
            return

        # Get target endpoint
        if endpoint_id:
            endpoint = db_session.get(Endpoint, UUID(endpoint_id))
        elif endpoint_name:
            endpoint = db_session.query(Endpoint).filter(Endpoint.name == endpoint_name).first()
        else:
            rprint("[red]Error: Must specify --endpoint-id or --endpoint[/red]")
            raise typer.Exit(1)

        if not endpoint:
            rprint("[red]Endpoint not found[/red]")
            raise typer.Exit(1)

        # Validate execution mode
        try:
            batch_mode = BatchMode(mode.lower())
        except ValueError:
            rprint(f"[red]Invalid execution mode: {mode}[/red]")
            rprint("Valid modes: parallel, sequential, priority, adaptive")
            raise typer.Exit(1)

        # Create execution config
        config = ExecutionConfig(
            timeout_seconds=timeout,
            max_concurrent=max_concurrent,
            max_retries=1 if continue_on_error else 0,
        )

        rprint("[cyan]Batch Execution Plan:[/cyan]")
        rprint(f"• Queries: {len(target_query_ids)}")
        rprint(f"• Endpoint: {endpoint.name} ({endpoint.url})")
        rprint(f"• Mode: {batch_mode.value}")
        rprint(f"• Max Concurrent: {max_concurrent}")
        rprint(f"• Timeout: {timeout}s")

        # Confirm execution
        if not typer.confirm("\nProceed with batch execution?"):
            rprint("Cancelled")
            raise typer.Exit(0)

        # Execute batch
        with console.status("[bold green]Starting batch execution..."):
            batch_result = execution_manager.execute_batch(
                target_query_ids, endpoint.pk_endpoint, batch_mode, config_override=config
            )

        # Display results summary
        rprint("\n[cyan]Batch Execution Complete[/cyan]")

        summary_table = Table(title="Execution Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", justify="right")
        summary_table.add_column("Percentage", justify="right", style="dim")

        total = batch_result.total_queries
        summary_table.add_row("Total Queries", str(total), "100.0%")
        summary_table.add_row(
            "Successful",
            str(batch_result.successful),
            f"{(batch_result.successful / total) * 100:.1f}%" if total > 0 else "0%",
        )
        summary_table.add_row(
            "Failed",
            str(batch_result.failed),
            f"{(batch_result.failed / total) * 100:.1f}%" if total > 0 else "0%",
        )
        if batch_result.cancelled > 0:
            summary_table.add_row(
                "Cancelled",
                str(batch_result.cancelled),
                f"{(batch_result.cancelled / total) * 100:.1f}%",
            )

        summary_table.add_row("Total Time", f"{batch_result.total_time:.2f}s", "")

        console.print(summary_table)

        # Show failed queries if any
        failed_results = [r for r in batch_result.results if not r.success]
        if failed_results:
            rprint(f"\n[red]Failed Queries ({len(failed_results)}):[/red]")
            for result in failed_results[:10]:  # Show first 10
                rprint(f"• Query {result.query_id}: {result.error_message}")

            if len(failed_results) > 10:
                rprint(f"... and {len(failed_results) - 10} more")

        # Save results if output directory specified
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save summary
            summary_file = output_dir / f"batch_summary_{batch_result.batch_id}.json"
            summary_data = {
                "batch_id": str(batch_result.batch_id),
                "endpoint": endpoint.name,
                "execution_mode": batch_mode.value,
                "total_queries": batch_result.total_queries,
                "successful": batch_result.successful,
                "failed": batch_result.failed,
                "cancelled": batch_result.cancelled,
                "total_time": batch_result.total_time,
                "timestamp": batch_result.results[0].started_at.isoformat()
                if batch_result.results
                else None,
            }

            summary_file.write_text(json.dumps(summary_data, indent=2))

            # Save detailed results
            if format == "json":
                results_file = output_dir / f"batch_results_{batch_result.batch_id}.json"
                results_data = []

                for result in batch_result.results:
                    result_dict = {
                        "execution_id": str(result.execution_id),
                        "query_id": str(result.query_id),
                        "status": result.status.value,
                        "success": result.success,
                        "execution_time": result.execution_time,
                        "response_size": result.response_size,
                        "error_message": result.error_message,
                        "started_at": result.started_at.isoformat(),
                        "completed_at": result.completed_at.isoformat()
                        if result.completed_at
                        else None,
                    }
                    results_data.append(result_dict)

                results_file.write_text(json.dumps(results_data, indent=2))

            elif format == "csv":
                results_file = output_dir / f"batch_results_{batch_result.batch_id}.csv"

                # Convert results to dict format for CSV export
                results_dicts = []
                for result in batch_result.results:
                    result_dict = {
                        "execution_id": str(result.execution_id),
                        "query_id": str(result.query_id),
                        "status": result.status.value,
                        "success": result.success,
                        "execution_time": result.execution_time or 0,
                        "response_size": result.response_size or 0,
                        "error_message": result.error_message or "",
                        "started_at": result.started_at.isoformat(),
                        "completed_at": result.completed_at.isoformat()
                        if result.completed_at
                        else "",
                    }
                    results_dicts.append(result_dict)

                ExportHandler.export_queries(results_dicts, results_file, "csv")

            rprint(f"\n[green]Results saved to {output_dir}[/green]")

        # Exit with error code if any queries failed and not continuing on error
        if batch_result.failed > 0 and not continue_on_error:
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error in batch execution: {e}[/red]")
        raise typer.Exit(1)


@batch_app.command("import")
def batch_import(
    file: Path = typer.Option(..., "--file", "-f", help="File to import queries from"),
    endpoint_id: str | None = typer.Option(None, "--endpoint-id", help="Default endpoint ID"),
    endpoint_name: str | None = typer.Option(
        None, "--endpoint", "-e", help="Default endpoint name"
    ),
    collection_name: str | None = typer.Option(
        None, "--collection", help="Collection to add queries to"
    ),
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Validate GraphQL syntax"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing queries"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be imported without importing"
    ),
):
    """Import queries from file (JSON/YAML/CSV)."""
    try:
        if not file.exists():
            rprint(f"[red]Import file not found: {file}[/red]")
            raise typer.Exit(1)

        db_session, query_manager, _ = get_managers()

        # Import query data
        with console.status(f"[bold green]Reading queries from {file}..."):
            query_data = ExportHandler.import_queries(file)

        if not query_data:
            rprint("[yellow]No queries found in import file[/yellow]")
            return

        rprint(f"[cyan]Found {len(query_data)} queries in import file[/cyan]\n")

        # Validate required fields
        valid_queries = []
        errors = []

        for i, query_dict in enumerate(query_data):
            if not query_dict.get("name"):
                errors.append(f"Query #{i + 1}: Missing 'name' field")
                continue

            if not query_dict.get("query_text") and not query_dict.get("content"):
                errors.append(
                    f"Query #{i + 1} ({query_dict['name']}): Missing 'query_text' or 'content' field"
                )
                continue

            # Normalize field names
            normalized_query = {
                "name": query_dict["name"],
                "description": query_dict.get("description", ""),
                "query_text": query_dict.get("query_text") or query_dict.get("content", ""),
                "variables": query_dict.get("variables", {}),
                "tags": query_dict.get("tags", []),
            }

            valid_queries.append(normalized_query)

        if errors:
            rprint("[red]Import validation errors:[/red]")
            for error in errors:
                rprint(f"  • {error}")

            if not valid_queries:
                rprint("[red]No valid queries to import[/red]")
                raise typer.Exit(1)

            rprint(f"\n[yellow]Proceeding with {len(valid_queries)} valid queries[/yellow]")

        # Show what will be imported
        preview_table = Table(title="Import Preview")
        preview_table.add_column("Name", style="cyan")
        preview_table.add_column("Description", style="white")
        preview_table.add_column("Variables", justify="right", style="yellow")
        preview_table.add_column("Tags", style="blue")

        for query_dict in valid_queries[:10]:  # Show first 10
            desc = (
                (query_dict["description"][:40] + "...")
                if len(query_dict["description"]) > 40
                else query_dict["description"]
            )
            var_count = len(query_dict["variables"]) if query_dict["variables"] else 0
            tags_str = ", ".join(query_dict["tags"][:3]) if query_dict["tags"] else ""
            if len(query_dict["tags"]) > 3:
                tags_str += "..."

            preview_table.add_row(
                query_dict["name"], desc, str(var_count) if var_count > 0 else "-", tags_str
            )

        if len(valid_queries) > 10:
            preview_table.add_row("...", f"({len(valid_queries) - 10} more)", "", "")

        console.print(preview_table)

        if dry_run:
            rprint("\n[yellow]Dry run - no queries imported[/yellow]")
            return

        # Confirm import
        if not typer.confirm(f"\nImport {len(valid_queries)} queries?"):
            rprint("Import cancelled")
            raise typer.Exit(0)

        # Import queries
        imported_count = 0
        skipped_count = 0
        error_count = 0

        with Progress() as progress:
            task = progress.add_task("Importing queries...", total=len(valid_queries))

            for query_dict in valid_queries:
                try:
                    # Check if query already exists
                    existing_query = (
                        db_session.query(Query).filter(Query.name == query_dict["name"]).first()
                    )

                    if existing_query and not overwrite:
                        skipped_count += 1
                        progress.advance(task)
                        continue

                    if existing_query and overwrite:
                        # Update existing query
                        existing_query.description = query_dict["description"]
                        existing_query.query_text = query_dict["query_text"]
                        existing_query.variables = query_dict["variables"]
                        existing_query.tags = query_dict["tags"]

                        if validate:
                            complexity_analyzer = QueryComplexityAnalyzer()
                            analysis = complexity_analyzer.analyze_query(query_dict["query_text"])
                            existing_query.expected_complexity_score = analysis.complexity_score

                        imported_count += 1

                    else:
                        # Create new query
                        from ...schemas.query import QueryCreate

                        schema = QueryCreate(
                            name=query_dict["name"],
                            description=query_dict["description"],
                            query_text=query_dict["query_text"],
                            variables=query_dict["variables"],
                            tags=query_dict["tags"],
                            created_by="batch-import",
                        )

                        # For now, create without collection (simplified)
                        from uuid import uuid4

                        collection_id = uuid4()  # TODO: Get from config or create default

                        new_query = query_manager.add_query(
                            collection_id, schema, validate=validate
                        )
                        if new_query:
                            imported_count += 1
                        else:
                            error_count += 1

                except Exception as e:
                    error_count += 1
                    rprint(f"[red]Error importing '{query_dict['name']}': {e}[/red]")

                progress.advance(task)

        # Show import summary
        rprint("\n[cyan]Import Summary:[/cyan]")
        rprint(f"• [green]Imported: {imported_count}[/green]")
        if skipped_count > 0:
            rprint(f"• [yellow]Skipped (already exists): {skipped_count}[/yellow]")
        if error_count > 0:
            rprint(f"• [red]Errors: {error_count}[/red]")

    except Exception as e:
        rprint(f"[red]Error importing queries: {e}[/red]")
        raise typer.Exit(1)


@batch_app.command("export")
def batch_export(
    output_file: Path = typer.Option(..., "--output", "-o", help="Output file path"),
    endpoint_id: str | None = typer.Option(
        None, "--endpoint-id", help="Export queries for specific endpoint"
    ),
    endpoint_name: str | None = typer.Option(
        None, "--endpoint", "-e", help="Export queries for specific endpoint"
    ),
    collection_id: str | None = typer.Option(
        None, "--collection", help="Export queries from specific collection"
    ),
    format: str = typer.Option("json", "--format", help="Export format: json, yaml, csv"),
    include_results: bool = typer.Option(
        False, "--include-results", help="Include execution results"
    ),
):
    """Export queries and optionally their execution results."""
    try:
        db_session, query_manager, _ = get_managers()

        # Get queries to export
        if collection_id:
            # Get queries from collection (simplified)
            rprint("[yellow]Collection-based export not fully implemented yet[/yellow]")
            queries = []
        else:
            # Get all queries (simplified query)
            queries = db_session.query(Query).order_by(Query.name).all()

        if not queries:
            rprint("[yellow]No queries found to export[/yellow]")
            return

        rprint(f"[cyan]Exporting {len(queries)} queries...[/cyan]")

        # Convert queries to export format
        export_data = []

        with Progress() as progress:
            task = progress.add_task("Processing queries...", total=len(queries))

            for query in queries:
                query_dict = {
                    "name": query.name,
                    "description": query.description,
                    "query_text": query.query_text,
                    "variables": query.variables,
                    "tags": query.tags,
                    "complexity_score": query.expected_complexity_score,
                    "created_at": query.created_at.isoformat() if query.created_at else None,
                    "metadata": query.query_metadata,
                }

                # Include execution results if requested
                if include_results:
                    # Get recent executions for this query
                    from ...models.execution import Execution

                    recent_executions = (
                        db_session.query(Execution)
                        .filter(Execution.fk_query == str(query.pk_query))
                        .order_by(Execution.execution_start.desc())
                        .limit(10)
                        .all()
                    )

                    query_dict["recent_executions"] = []
                    for exec in recent_executions:
                        exec_dict = {
                            "timestamp": exec.execution_start.isoformat(),
                            "status": exec.status,
                            "response_time_ms": exec.response_time_ms,
                            "success": exec.status == "completed",
                            "error_message": exec.error_message,
                        }
                        query_dict["recent_executions"].append(exec_dict)

                export_data.append(query_dict)
                progress.advance(task)

        # Export to file
        with console.status(f"[bold green]Saving to {output_file}..."):
            ExportHandler.export_queries(export_data, output_file, format)

        rprint(f"[green]✓[/green] Exported {len(queries)} queries to {output_file}")

        # Show file info
        file_size = output_file.stat().st_size
        if file_size > 1024 * 1024:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        elif file_size > 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size} bytes"

        rprint(f"[dim]File size: {size_str}[/dim]")

    except Exception as e:
        rprint(f"[red]Error exporting queries: {e}[/red]")
        raise typer.Exit(1)


# Add the batch_app to the main CLI
# This will be imported in the main CLI file
