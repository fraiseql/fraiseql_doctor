"""Health monitoring CLI commands."""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.text import Text

# Mock imports for Phase 2 demonstration
# from ...core.database import get_db_session
# from ...models.endpoint import Endpoint
# from ...models.health_check import HealthCheck as HealthCheckModel
# from ...services.fraiseql_client import FraiseQLClient, NetworkError, GraphQLExecutionError


# Mock classes
class MockDB:
    def query(self, model):
        return MockQueryResult()

    def get(self, model, pk):
        return MockEndpoint("Test") if pk else None

    def add(self, obj):
        pass

    def commit(self):
        pass


class MockQueryResult:
    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def all(self):
        return [MockEndpoint("Health Test")]

    def first(self):
        return MockEndpoint("Health Test")

    def limit(self, n):
        return self

    def desc(self):
        return self


class MockEndpoint:
    def __init__(self, name="Mock Endpoint"):
        self.pk_endpoint = "mock-uuid"
        self.name = name


class NetworkError(Exception):
    pass


class GraphQLExecutionError(Exception):
    pass


class MockHealthCheck:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


HealthCheckModel = MockHealthCheck
from ..utils.formatters import format_health_summary, format_progress_bar

console = Console()

health_app = typer.Typer(name="health", help="Monitor endpoint health")


def get_health_manager():
    """Get database session for health management - mock for Phase 2."""
    return MockDB()


@health_app.command("check")
def health_check(
    endpoint_id: Optional[str] = typer.Option(None, "--id", help="Specific endpoint ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Specific endpoint name"),
    all_endpoints: bool = typer.Option(False, "--all", help="Check all endpoints"),
    query: Optional[str] = typer.Option(None, "--query", help="Custom health check query"),
    timeout: int = typer.Option(10, "--timeout", help="Health check timeout"),
    format: str = typer.Option("table", "--format", help="Output format: table, json"),
    save_results: bool = typer.Option(False, "--save", help="Save results to database"),
):
    """Perform health check on endpoints."""
    if not endpoint_id and not name and not all_endpoints:
        rprint("[red]Error: Must specify --id, --name, or --all[/red]")
        raise typer.Exit(1)

    try:
        db_session = get_health_manager()

        # Get target endpoints
        if all_endpoints:
            endpoints = db_session.query(Endpoint).order_by(Endpoint.name).all()
        elif endpoint_id:
            endpoint = db_session.get(Endpoint, endpoint_id)
            endpoints = [endpoint] if endpoint else []
        else:
            endpoint = db_session.query(Endpoint).filter(Endpoint.name == name).first()
            endpoints = [endpoint] if endpoint else []

        if not endpoints:
            rprint("[red]No endpoints found[/red]")
            raise typer.Exit(1)

        # Default health check query
        health_query = (
            query
            or """
            query HealthCheck {
                __schema {
                    queryType {
                        name
                    }
                }
            }
        """
        )

        results = {}

        # Run health checks with progress
        with format_progress_bar() as progress:
            task = progress.add_task(
                f"Checking {len(endpoints)} endpoints...", total=len(endpoints)
            )

            for endpoint in endpoints:
                start_time = time.time()

                try:
                    client = FraiseQLClient(endpoint)
                    client.timeout_seconds = timeout

                    result = client.execute_query(health_query)
                    end_time = time.time()
                    response_time = int((end_time - start_time) * 1000)

                    if "errors" in result:
                        status = "unhealthy"
                        error = f"GraphQL errors: {'; '.join([e.get('message', 'Unknown') for e in result['errors']])}"
                    else:
                        status = "healthy"
                        error = None

                    results[endpoint.name] = {
                        "status": status,
                        "response_time_ms": response_time,
                        "last_check": datetime.now(),
                        "error": error,
                        "endpoint_id": str(endpoint.pk_endpoint),
                    }

                except NetworkError as e:
                    results[endpoint.name] = {
                        "status": "unhealthy",
                        "response_time_ms": 0,
                        "last_check": datetime.now(),
                        "error": f"Network error: {e}",
                        "endpoint_id": str(endpoint.pk_endpoint),
                    }

                except Exception as e:
                    if "timeout" in str(e).lower():
                        status = "timeout"
                    else:
                        status = "unhealthy"

                    results[endpoint.name] = {
                        "status": status,
                        "response_time_ms": 0,
                        "last_check": datetime.now(),
                        "error": str(e),
                        "endpoint_id": str(endpoint.pk_endpoint),
                    }

                progress.advance(task)

        # Display results
        if format == "table":
            table = format_health_summary(results)
            console.print(table)

            # Summary stats
            total = len(results)
            healthy = len([r for r in results.values() if r["status"] == "healthy"])
            unhealthy = len([r for r in results.values() if r["status"] == "unhealthy"])
            timeout = len([r for r in results.values() if r["status"] == "timeout"])

            summary_text = f"[dim]Total: {total} | [green]Healthy: {healthy}[/green] | [red]Unhealthy: {unhealthy}[/red]"
            if timeout > 0:
                summary_text += f" | [yellow]Timeout: {timeout}[/yellow]"
            summary_text += "[/dim]"

            rprint(f"\n{summary_text}")

        elif format == "json":
            # Convert datetime to ISO format for JSON serialization
            json_results = {}
            for name, data in results.items():
                json_data = data.copy()
                json_data["last_check"] = data["last_check"].isoformat()
                json_results[name] = json_data

            rprint(json.dumps(json_results, indent=2))

        else:
            rprint(f"[red]Unknown format: {format}[/red]")
            raise typer.Exit(1)

        # Save results to database if requested
        if save_results:
            with console.status("Saving health check results..."):
                for endpoint_name, data in results.items():
                    health_check_record = HealthCheckModel(
                        fk_endpoint=data["endpoint_id"],
                        check_time=data["last_check"],
                        is_healthy=(data["status"] == "healthy"),
                        response_time_ms=data["response_time_ms"],
                        error_message=data.get("error"),
                        check_metadata={"query": health_query, "cli_status": data["status"]},
                    )
                    db_session.add(health_check_record)

                db_session.commit()

            rprint("[green]Health check results saved to database[/green]")

        # Exit with error code if any endpoints are unhealthy
        unhealthy_count = len([r for r in results.values() if r["status"] != "healthy"])
        if unhealthy_count > 0:
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error performing health check: {e}[/red]")
        raise typer.Exit(1)


@health_app.command("monitor")
def monitor_health(
    endpoints: Optional[list[str]] = typer.Option(
        None, "--endpoint", "-e", help="Endpoint names to monitor"
    ),
    all_endpoints: bool = typer.Option(False, "--all", help="Monitor all endpoints"),
    interval: int = typer.Option(30, "--interval", "-i", help="Check interval in seconds"),
    duration: Optional[int] = typer.Option(None, "--duration", help="Monitor duration in seconds"),
    alert_on_change: bool = typer.Option(False, "--alert", help="Alert on status changes"),
    save_results: bool = typer.Option(True, "--save/--no-save", help="Save results to database"),
):
    """Monitor endpoint health continuously."""
    if not endpoints and not all_endpoints:
        rprint("[red]Error: Must specify --endpoint or --all[/red]")
        raise typer.Exit(1)

    try:
        db_session = get_health_manager()

        # Get target endpoints
        if all_endpoints:
            target_endpoints = db_session.query(Endpoint).order_by(Endpoint.name).all()
        else:
            target_endpoints = []
            for name in endpoints:
                endpoint = db_session.query(Endpoint).filter(Endpoint.name == name).first()
                if endpoint:
                    target_endpoints.append(endpoint)
                else:
                    rprint(f"[yellow]Warning: Endpoint '{name}' not found[/yellow]")

        if not target_endpoints:
            rprint("[red]No valid endpoints to monitor[/red]")
            raise typer.Exit(1)

        rprint(
            f"[cyan]Monitoring {len(target_endpoints)} endpoints every {interval} seconds[/cyan]"
        )
        if duration:
            rprint(f"[dim]Duration: {duration} seconds[/dim]")
        rprint("[dim]Press Ctrl+C to stop monitoring[/dim]\n")

        # Health check query
        health_query = """
            query HealthCheck {
                __schema {
                    queryType {
                        name
                    }
                }
            }
        """

        start_time = time.time()
        last_status = {}
        check_count = 0

        try:
            while True:
                # Check if duration exceeded
                if duration and (time.time() - start_time) >= duration:
                    break

                check_count += 1
                current_results = {}

                # Perform health checks
                for endpoint in target_endpoints:
                    check_start = time.time()

                    try:
                        client = FraiseQLClient(endpoint)
                        result = client.execute_query(health_query)
                        check_end = time.time()
                        response_time = int((check_end - check_start) * 1000)

                        if "errors" in result:
                            status = "unhealthy"
                            error = "GraphQL errors"
                        else:
                            status = "healthy"
                            error = None

                        current_results[endpoint.name] = {
                            "status": status,
                            "response_time_ms": response_time,
                            "last_check": datetime.now(),
                            "error": error,
                            "endpoint_id": str(endpoint.pk_endpoint),
                        }

                    except Exception as e:
                        if "timeout" in str(e).lower():
                            status = "timeout"
                        else:
                            status = "unhealthy"

                        current_results[endpoint.name] = {
                            "status": status,
                            "response_time_ms": 0,
                            "last_check": datetime.now(),
                            "error": str(e),
                            "endpoint_id": str(endpoint.pk_endpoint),
                        }

                # Display results with live updating
                table = format_health_summary(current_results)

                # Add monitoring info
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                title = f"Health Monitor - Check #{check_count} at {timestamp}"
                table.title = title

                console.clear()
                console.print(table)

                # Check for status changes and alert if needed
                if alert_on_change and last_status:
                    for endpoint_name, current_data in current_results.items():
                        if endpoint_name in last_status:
                            old_status = last_status[endpoint_name]["status"]
                            new_status = current_data["status"]

                            if old_status != new_status:
                                status_color = "green" if new_status == "healthy" else "red"
                                rprint(
                                    f"[{status_color}]🔔 ALERT: {endpoint_name} changed from {old_status.upper()} to {new_status.upper()}[/{status_color}]"
                                )

                # Save to database if requested
                if save_results:
                    for endpoint_name, data in current_results.items():
                        health_record = HealthCheck(
                            fk_endpoint=data["endpoint_id"],
                            check_timestamp=data["last_check"],
                            response_time_ms=data["response_time_ms"],
                            status=data["status"],
                            error_message=data.get("error"),
                            check_metadata={"query": health_query, "check_number": check_count},
                        )
                        db_session.add(health_record)

                    db_session.commit()

                last_status = current_results

                # Wait for next interval
                time.sleep(interval)

        except KeyboardInterrupt:
            rprint(f"\n[yellow]Monitoring stopped after {check_count} checks[/yellow]")

        # Summary
        total_time = time.time() - start_time
        rprint(f"[dim]Total monitoring time: {total_time:.1f} seconds[/dim]")

    except Exception as e:
        rprint(f"[red]Error during monitoring: {e}[/red]")
        raise typer.Exit(1)


@health_app.command("report")
def health_report(
    format: str = typer.Option("table", "--format", help="Output format: table, json, html"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save report to file"),
    since: Optional[str] = typer.Option(
        None, "--since", help="Include results since (e.g., '1 hour ago', '2024-01-01')"
    ),
    endpoint: Optional[str] = typer.Option(None, "--endpoint", help="Filter by endpoint name"),
    include_errors: bool = typer.Option(True, "--errors/--no-errors", help="Include error details"),
):
    """Generate health check report from historical data."""
    try:
        db_session = get_health_manager()

        # Build query
        query = db_session.query(HealthCheck).join(Endpoint)

        # Apply filters
        if since:
            # Parse since parameter (simplified parsing)
            if "hour" in since:
                hours = int(since.split()[0]) if since.split()[0].isdigit() else 1
                since_time = datetime.now() - timedelta(hours=hours)
            elif "day" in since:
                days = int(since.split()[0]) if since.split()[0].isdigit() else 1
                since_time = datetime.now() - timedelta(days=days)
            elif "-" in since:  # Date format
                since_time = datetime.fromisoformat(since)
            else:
                since_time = datetime.now() - timedelta(hours=24)  # Default 24 hours

            query = query.filter(HealthCheck.check_timestamp >= since_time)

        if endpoint:
            query = query.filter(Endpoint.name == endpoint)

        # Execute query
        health_checks = query.order_by(HealthCheck.check_timestamp.desc()).limit(1000).all()

        if not health_checks:
            rprint("[yellow]No health check data found for the specified criteria[/yellow]")
            return

        # Process results
        report_data = []
        endpoint_stats = {}

        for check in health_checks:
            endpoint_name = check.endpoint.name if check.endpoint else "Unknown"

            # Track per-endpoint stats
            if endpoint_name not in endpoint_stats:
                endpoint_stats[endpoint_name] = {
                    "total_checks": 0,
                    "healthy_checks": 0,
                    "unhealthy_checks": 0,
                    "timeout_checks": 0,
                    "avg_response_time": 0,
                    "response_times": [],
                }

            stats = endpoint_stats[endpoint_name]
            stats["total_checks"] += 1

            if check.status == "healthy":
                stats["healthy_checks"] += 1
            elif check.status == "timeout":
                stats["timeout_checks"] += 1
            else:
                stats["unhealthy_checks"] += 1

            if check.response_time_ms:
                stats["response_times"].append(check.response_time_ms)

            # Add to report data
            report_entry = {
                "endpoint": endpoint_name,
                "timestamp": check.check_timestamp.isoformat(),
                "status": check.status,
                "response_time_ms": check.response_time_ms,
                "error": check.error_message if include_errors else None,
            }
            report_data.append(report_entry)

        # Calculate averages
        for stats in endpoint_stats.values():
            if stats["response_times"]:
                stats["avg_response_time"] = sum(stats["response_times"]) / len(
                    stats["response_times"]
                )
            stats["uptime_percentage"] = (stats["healthy_checks"] / stats["total_checks"]) * 100

        # Generate output
        if format == "table":
            # Summary table
            summary_table = Table(
                title="Health Check Report Summary", show_header=True, header_style="bold magenta"
            )

            summary_table.add_column("Endpoint", style="cyan")
            summary_table.add_column("Total Checks", justify="right")
            summary_table.add_column("Uptime %", justify="right", style="green")
            summary_table.add_column("Avg Response Time", justify="right", style="yellow")
            summary_table.add_column("Errors", justify="right", style="red")

            for endpoint_name, stats in endpoint_stats.items():
                uptime_color = (
                    "green"
                    if stats["uptime_percentage"] >= 95
                    else "yellow"
                    if stats["uptime_percentage"] >= 90
                    else "red"
                )
                uptime_text = Text(f"{stats['uptime_percentage']:.1f}%", style=uptime_color)

                summary_table.add_row(
                    endpoint_name,
                    str(stats["total_checks"]),
                    uptime_text,
                    f"{stats['avg_response_time']:.0f}ms"
                    if stats["avg_response_time"] > 0
                    else "-",
                    str(stats["unhealthy_checks"] + stats["timeout_checks"]),
                )

            console.print(summary_table)

        elif format == "json":
            output_data = {
                "report_generated": datetime.now().isoformat(),
                "total_checks": len(health_checks),
                "endpoint_summary": endpoint_stats,
                "detailed_results": report_data,
            }

            output_text = json.dumps(output_data, indent=2)

            if output:
                output.write_text(output_text)
                rprint(f"[green]Report saved to {output}[/green]")
            else:
                rprint(output_text)

        elif format == "html":
            # Generate HTML report
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>FraiseQL Doctor Health Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .healthy {{ color: green; }}
        .unhealthy {{ color: red; }}
        .timeout {{ color: orange; }}
        .uptime-good {{ color: green; font-weight: bold; }}
        .uptime-warning {{ color: orange; font-weight: bold; }}
        .uptime-critical {{ color: red; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>FraiseQL Doctor Health Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Total Health Checks: {len(health_checks)}</p>

    <h2>Endpoint Summary</h2>
    <table>
        <tr>
            <th>Endpoint</th>
            <th>Total Checks</th>
            <th>Uptime %</th>
            <th>Avg Response Time</th>
            <th>Errors</th>
        </tr>
"""

            for endpoint_name, stats in endpoint_stats.items():
                uptime_class = (
                    "uptime-good"
                    if stats["uptime_percentage"] >= 95
                    else "uptime-warning"
                    if stats["uptime_percentage"] >= 90
                    else "uptime-critical"
                )

                html_content += f"""
        <tr>
            <td>{endpoint_name}</td>
            <td>{stats['total_checks']}</td>
            <td class="{uptime_class}">{stats['uptime_percentage']:.1f}%</td>
            <td>{stats['avg_response_time']:.0f}ms</td>
            <td>{stats['unhealthy_checks'] + stats['timeout_checks']}</td>
        </tr>
"""

            html_content += """
    </table>
</body>
</html>
"""

            if output:
                output.write_text(html_content)
                rprint(f"[green]HTML report saved to {output}[/green]")
            else:
                rprint(html_content)

        else:
            rprint(f"[red]Unknown format: {format}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error generating health report: {e}[/red]")
        raise typer.Exit(1)


@health_app.command("status")
def health_status(
    endpoint: Optional[str] = typer.Option(None, "--endpoint", "-e", help="Specific endpoint"),
    summary: bool = typer.Option(False, "--summary", help="Show summary only"),
):
    """Show current health status overview."""
    try:
        db_session = get_health_manager()

        # Get latest health check for each endpoint
        if endpoint:
            endpoints = db_session.query(Endpoint).filter(Endpoint.name == endpoint).all()
        else:
            endpoints = db_session.query(Endpoint).order_by(Endpoint.name).all()

        if not endpoints:
            rprint("[red]No endpoints found[/red]")
            raise typer.Exit(1)

        current_status = {}

        for ep in endpoints:
            # Get latest health check
            latest_check = (
                db_session.query(HealthCheck)
                .filter(HealthCheck.fk_endpoint == str(ep.pk_endpoint))
                .order_by(HealthCheck.check_timestamp.desc())
                .first()
            )

            if latest_check:
                current_status[ep.name] = {
                    "status": latest_check.status,
                    "response_time_ms": latest_check.response_time_ms,
                    "last_check": latest_check.check_timestamp,
                    "error": latest_check.error_message,
                }
            else:
                current_status[ep.name] = {
                    "status": "unknown",
                    "response_time_ms": 0,
                    "last_check": None,
                    "error": "No health checks recorded",
                }

        if summary:
            # Just show counts
            total = len(current_status)
            healthy = len([s for s in current_status.values() if s["status"] == "healthy"])
            unhealthy = len(
                [s for s in current_status.values() if s["status"] in ["unhealthy", "timeout"]]
            )
            unknown = total - healthy - unhealthy

            rprint("[cyan]Health Status Summary:[/cyan]")
            rprint(f"  Total Endpoints: {total}")
            rprint(f"  [green]Healthy: {healthy}[/green]")
            rprint(f"  [red]Unhealthy: {unhealthy}[/red]")
            if unknown > 0:
                rprint(f"  [dim]Unknown: {unknown}[/dim]")

        else:
            # Show detailed table
            table = format_health_summary(current_status)
            table.title = "Current Health Status"
            console.print(table)

    except Exception as e:
        rprint(f"[red]Error getting health status: {e}[/red]")
        raise typer.Exit(1)
