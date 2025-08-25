"""Test basic CLI functionality."""

from typer.testing import CliRunner

from fraiseql_doctor.cli.main import app


def test_cli_app_exists():
    """Test that CLI app can be imported and instantiated."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "fraiseql-doctor" in result.stdout.lower()


def test_version_command():
    """Test version command works."""
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


def test_subcommands_exist():
    """Test that required subcommands exist."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    required_commands = ["query", "endpoint", "health", "config"]
    for command in required_commands:
        assert command in result.stdout
