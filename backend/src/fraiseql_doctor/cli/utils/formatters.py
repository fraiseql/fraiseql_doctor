"""Rich formatting utilities for CLI output."""

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from ...models.endpoint import Endpoint
from ...models.execution import Execution
from ...models.query import Query


def format_query_table(queries: list[Query]) -> Table:
    """Format queries as a rich table."""
    table = Table(title="GraphQL Queries", show_header=True, header_style="bold magenta")

    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Complexity", justify="right", style="yellow")
    table.add_column("Tags", style="blue")
    table.add_column("Created", style="dim")

    for query in queries:
        # Format status with color
        status = getattr(query, "status", "active")
        if status == "active":
            status_text = Text("ACTIVE", style="green")
        elif status == "draft":
            status_text = Text("DRAFT", style="yellow")
        elif status == "deprecated":
            status_text = Text("DEPRECATED", style="red")
        else:
            status_text = Text(status.upper(), style="white")

        # Format complexity score
        complexity = query.expected_complexity_score or 0
        complexity_text = f"{complexity:.1f}" if complexity > 0 else "-"

        # Format tags
        tags_text = ", ".join(query.tags[:3]) if query.tags else "-"
        if len(query.tags) > 3:
            tags_text += "..."

        # Format creation date
        created_text = query.created_at.strftime("%Y-%m-%d") if query.created_at else "-"

        # Truncate description
        desc = query.description or ""
        desc_text = (desc[:50] + "...") if len(desc) > 50 else desc

        table.add_row(query.name, desc_text, status_text, complexity_text, tags_text, created_text)

    return table


def format_query_detail(query: Query) -> Panel:
    """Format query details as a rich panel."""
    # Query metadata
    metadata_lines = [
        f"[cyan]ID:[/cyan] {query.pk_query}",
        f"[cyan]Name:[/cyan] {query.name}",
    ]

    if query.description:
        metadata_lines.append(f"[cyan]Description:[/cyan] {query.description}")

    status = getattr(query, "status", "active")
    status_color = {"active": "green", "draft": "yellow", "deprecated": "red", "error": "red"}.get(
        status, "white"
    )
    metadata_lines.append(f"[cyan]Status:[/cyan] [{status_color}]{status.upper()}[/{status_color}]")

    if query.expected_complexity_score:
        metadata_lines.append(
            f"[cyan]Complexity Score:[/cyan] {query.expected_complexity_score:.2f}"
        )

    if query.tags:
        tags_str = ", ".join(query.tags)
        metadata_lines.append(f"[cyan]Tags:[/cyan] {tags_str}")

    if query.created_by:
        metadata_lines.append(f"[cyan]Created By:[/cyan] {query.created_by}")

    if query.created_at:
        metadata_lines.append(
            f"[cyan]Created:[/cyan] {query.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    if query.updated_at and query.updated_at != query.created_at:
        metadata_lines.append(
            f"[cyan]Updated:[/cyan] {query.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    metadata_text = "\n".join(metadata_lines)

    # Query text with syntax highlighting
    query_syntax = Syntax(
        query.query_text, "graphql", theme="monokai", line_numbers=True, word_wrap=True
    )

    # Variables if present
    variables_text = ""
    if query.variables:
        variables_json = json.dumps(query.variables, indent=2)
        variables_syntax = Syntax(variables_json, "json", theme="monokai", line_numbers=True)
        variables_text = f"\n\n[cyan]Variables:[/cyan]\n{variables_syntax}"

    # Metadata from query_metadata
    metadata_info = ""
    if query.query_metadata:
        interesting_metadata = {
            k: v
            for k, v in query.query_metadata.items()
            if k in ["complexity_score", "field_count", "depth", "estimated_cost", "last_validated"]
        }
        if interesting_metadata:
            metadata_json = json.dumps(interesting_metadata, indent=2, default=str)
            metadata_syntax = Syntax(metadata_json, "json", theme="monokai")
            metadata_info = f"\n\n[cyan]Analysis Metadata:[/cyan]\n{metadata_syntax}"

    content = f"{metadata_text}\n\n[cyan]GraphQL Query:[/cyan]\n{query_syntax}{variables_text}{metadata_info}"

    return Panel(content, title=f"Query: {query.name}", title_align="left", border_style="blue")


def format_endpoint_table(endpoints: list[Endpoint]) -> Table:
    """Format endpoints as a rich table."""
    table = Table(title="GraphQL Endpoints", show_header=True, header_style="bold magenta")

    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("URL", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Auth", style="yellow")
    table.add_column("Timeout", justify="right", style="blue")
    table.add_column("Last Check", style="dim")

    for endpoint in endpoints:
        # Format status with color
        status = getattr(endpoint, "status", "unknown")
        if status == "healthy":
            status_text = Text("HEALTHY", style="green")
        elif status == "unhealthy":
            status_text = Text("UNHEALTHY", style="red")
        elif status == "timeout":
            status_text = Text("TIMEOUT", style="yellow")
        else:
            status_text = Text("UNKNOWN", style="dim")

        # Format auth method
        auth_method = endpoint.auth_config.get("method", "none") if endpoint.auth_config else "none"
        auth_text = auth_method.upper() if auth_method != "none" else "-"

        # Format timeout
        timeout_text = f"{endpoint.timeout_seconds}s" if endpoint.timeout_seconds else "30s"

        # Format last check
        last_check = getattr(endpoint, "last_health_check", None)
        last_check_text = last_check.strftime("%m-%d %H:%M") if last_check else "-"

        # Truncate URL for display
        url = endpoint.url
        url_text = (url[:40] + "...") if len(url) > 40 else url

        table.add_row(
            endpoint.name, url_text, status_text, auth_text, timeout_text, last_check_text
        )

    return table


def format_endpoint_detail(endpoint: Endpoint) -> Panel:
    """Format endpoint details as a rich panel."""
    metadata_lines = [
        f"[cyan]ID:[/cyan] {endpoint.pk_endpoint}",
        f"[cyan]Name:[/cyan] {endpoint.name}",
        f"[cyan]URL:[/cyan] {endpoint.url}",
        f"[cyan]Timeout:[/cyan] {endpoint.timeout_seconds}s",
    ]

    if endpoint.description:
        metadata_lines.append(f"[cyan]Description:[/cyan] {endpoint.description}")

    # Status
    status = getattr(endpoint, "status", "unknown")
    status_color = {
        "healthy": "green",
        "unhealthy": "red",
        "timeout": "yellow",
        "unknown": "dim",
    }.get(status, "white")
    metadata_lines.append(f"[cyan]Status:[/cyan] [{status_color}]{status.upper()}[/{status_color}]")

    # Auth configuration
    if endpoint.auth_config:
        auth_method = endpoint.auth_config.get("method", "none")
        metadata_lines.append(f"[cyan]Auth Method:[/cyan] {auth_method.upper()}")

        if auth_method == "bearer" and endpoint.auth_config.get("token"):
            token_preview = (
                endpoint.auth_config["token"][:10] + "..."
                if len(endpoint.auth_config["token"]) > 10
                else endpoint.auth_config["token"]
            )
            metadata_lines.append(f"[cyan]Token:[/cyan] {token_preview}")
        elif auth_method == "basic" and endpoint.auth_config.get("username"):
            metadata_lines.append(f"[cyan]Username:[/cyan] {endpoint.auth_config['username']}")

    # Custom headers
    if endpoint.custom_headers:
        headers_json = json.dumps(endpoint.custom_headers, indent=2)
        headers_syntax = Syntax(headers_json, "json", theme="monokai", line_numbers=True)
        headers_text = f"\n\n[cyan]Custom Headers:[/cyan]\n{headers_syntax}"
    else:
        headers_text = ""

    # Health check info
    health_info = ""
    last_check = getattr(endpoint, "last_health_check", None)
    if last_check:
        health_info = (
            f"\n[cyan]Last Health Check:[/cyan] {last_check.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    # Additional metadata
    metadata_info = ""
    if endpoint.endpoint_metadata:
        metadata_json = json.dumps(endpoint.endpoint_metadata, indent=2, default=str)
        metadata_syntax = Syntax(metadata_json, "json", theme="monokai")
        metadata_info = f"\n\n[cyan]Metadata:[/cyan]\n{metadata_syntax}"

    metadata_text = "\n".join(metadata_lines)
    content = f"{metadata_text}{health_info}{headers_text}{metadata_info}"

    return Panel(
        content, title=f"Endpoint: {endpoint.name}", title_align="left", border_style="blue"
    )


def format_execution_result(execution: Execution) -> Panel:
    """Format query execution result as a rich panel."""
    # Basic execution info
    info_lines = [
        f"[cyan]Execution ID:[/cyan] {execution.pk_execution}",
        f"[cyan]Query ID:[/cyan] {execution.fk_query}",
        f"[cyan]Status:[/cyan] {execution.status}",
    ]

    if execution.execution_start:
        info_lines.append(
            f"[cyan]Started:[/cyan] {execution.execution_start.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    if execution.execution_end:
        info_lines.append(
            f"[cyan]Completed:[/cyan] {execution.execution_end.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    if execution.response_time_ms:
        info_lines.append(f"[cyan]Response Time:[/cyan] {execution.response_time_ms}ms")

    if execution.response_size_bytes:
        size_mb = execution.response_size_bytes / 1024 / 1024
        size_text = (
            f"{size_mb:.2f}MB" if size_mb >= 1 else f"{execution.response_size_bytes / 1024:.1f}KB"
        )
        info_lines.append(f"[cyan]Response Size:[/cyan] {size_text}")

    if execution.actual_complexity_score:
        info_lines.append(f"[cyan]Complexity Score:[/cyan] {execution.actual_complexity_score:.2f}")

    info_text = "\n".join(info_lines)

    # Error information
    error_text = ""
    if execution.error_message:
        error_text = f"\n\n[red]Error:[/red] {execution.error_message}"
        if execution.error_code:
            error_text += f"\n[red]Error Code:[/red] {execution.error_code}"

    # Variables used
    variables_text = ""
    if execution.variables_used:
        variables_json = json.dumps(execution.variables_used, indent=2)
        variables_syntax = Syntax(variables_json, "json", theme="monokai", line_numbers=True)
        variables_text = f"\n\n[cyan]Variables:[/cyan]\n{variables_syntax}"

    # Response data (truncated if large)
    response_text = ""
    if execution.response_data:
        response_json = json.dumps(execution.response_data, indent=2, default=str)

        # Truncate if too long
        if len(response_json) > 2000:
            response_json = response_json[:2000] + "\n... (truncated)"

        response_syntax = Syntax(response_json, "json", theme="monokai", line_numbers=True)
        response_text = f"\n\n[cyan]Response Data:[/cyan]\n{response_syntax}"

    content = f"{info_text}{error_text}{variables_text}{response_text}"

    # Status-based border color
    border_color = "green" if execution.status == "completed" else "red"

    return Panel(content, title="Execution Result", title_align="left", border_style=border_color)


def format_health_summary(health_data: dict[str, Any]) -> Table:
    """Format health check summary as a table."""
    table = Table(title="Health Check Summary", show_header=True, header_style="bold magenta")

    table.add_column("Endpoint", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Response Time", justify="right", style="yellow")
    table.add_column("Last Check", style="dim")
    table.add_column("Error", style="red")

    for endpoint_name, data in health_data.items():
        status = data.get("status", "unknown")
        if status == "healthy":
            status_text = Text("HEALTHY", style="green")
        elif status == "unhealthy":
            status_text = Text("UNHEALTHY", style="red")
        elif status == "timeout":
            status_text = Text("TIMEOUT", style="yellow")
        else:
            status_text = Text("UNKNOWN", style="dim")

        response_time = data.get("response_time_ms", 0)
        response_text = f"{response_time}ms" if response_time > 0 else "-"

        last_check = data.get("last_check")
        last_check_text = last_check.strftime("%H:%M:%S") if last_check else "-"

        error = data.get("error", "")
        error_text = (error[:30] + "...") if len(error) > 30 else error

        table.add_row(endpoint_name, status_text, response_text, last_check_text, error_text)

    return table


def format_progress_bar(description: str = "Processing") -> "Progress":
    """Create a rich progress bar for long operations."""
    from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=Console(),
        transient=True,
    )
