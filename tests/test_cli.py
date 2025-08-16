"""Basic CLI tests."""

from typer.testing import CliRunner

from fraiseql_doctor.cli.main import app


def test_version_command():
    """Test version command."""
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "FraiseQL Doctor v0.1.0" in result.stdout


def test_help_command():
    """Test help command."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Health monitoring and query execution tool" in result.stdout


def test_hello_command():
    """Test hello command."""
    runner = CliRunner()
    result = runner.invoke(app, ["hello"])

    assert result.exit_code == 0
    assert "Hello from FraiseQL Doctor" in result.stdout
