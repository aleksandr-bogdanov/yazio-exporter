"""
Tests for CLI interface.
"""

import subprocess
import sys

import pytest

from yazio_exporter import __version__
from yazio_exporter.cli import main


def test_cli_help_exit_code(monkeypatch, capsys):
    """Test that --help exits with code 0."""
    monkeypatch.setattr(sys, "argv", ["yazio-exporter", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0


def test_cli_help_shows_usage(monkeypatch, capsys):
    """Test that --help shows usage information."""
    monkeypatch.setattr(sys, "argv", ["yazio-exporter", "--help"])

    with pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()
    assert "usage: yazio-exporter" in captured.out
    assert "Export your Yazio nutrition data" in captured.out


def test_cli_help_lists_all_subcommands(monkeypatch, capsys):
    """Test that --help lists all 8 subcommands."""
    monkeypatch.setattr(sys, "argv", ["yazio-exporter", "--help"])

    with pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()

    # Verify all 9 subcommands are listed
    expected_subcommands = [
        "login",
        "profile",
        "days",
        "weight",
        "nutrients",
        "products",
        "summary",
        "export-all",
        "report",
    ]

    for subcommand in expected_subcommands:
        assert subcommand in captured.out, f"Subcommand '{subcommand}' not found in help output"


def test_cli_version_flag(monkeypatch, capsys):
    """Test that --version flag works and shows correct version."""
    monkeypatch.setattr(sys, "argv", ["yazio-exporter", "--version"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    captured = capsys.readouterr()
    assert f"yazio-exporter {__version__}" in captured.out
    assert exc_info.value.code == 0


def test_cli_no_args_shows_help(monkeypatch, capsys):
    """Test that running without args shows help and exits 0."""
    monkeypatch.setattr(sys, "argv", ["yazio-exporter"])

    result = main()

    captured = capsys.readouterr()
    assert "usage: yazio-exporter" in captured.out
    assert result == 0


def test_cli_module_execution():
    """Test that the CLI can be executed as a module."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: yazio-exporter" in result.stdout
    assert all(
        cmd in result.stdout
        for cmd in [
            "login",
            "profile",
            "days",
            "weight",
            "nutrients",
            "products",
            "summary",
            "export-all",
            "report",
        ]
    )


# Feature #66: All subcommands have --help
@pytest.mark.parametrize(
    "subcommand",
    [
        "login",
        "profile",
        "days",
        "weight",
        "nutrients",
        "products",
        "summary",
        "export-all",
        "report",
    ],
)
def test_subcommand_help(subcommand):
    """Test that each subcommand has --help and shows usage and options."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", subcommand, "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"{subcommand} --help should exit with code 0"
    assert f"usage: yazio-exporter {subcommand}" in result.stdout, f"{subcommand} should show usage line"
    assert "options:" in result.stdout or "optional arguments:" in result.stdout, f"{subcommand} should show options"
    assert "-h, --help" in result.stdout, f"{subcommand} should show help option"


def test_login_help_shows_options():
    """Test that login --help shows all required options."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", "login", "--help"],
        capture_output=True,
        text=True,
    )

    assert "email" in result.stdout
    assert "password" in result.stdout
    assert "-o" in result.stdout or "--output" in result.stdout


def test_profile_help_shows_options():
    """Test that profile --help shows all required options."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", "profile", "--help"],
        capture_output=True,
        text=True,
    )

    assert "-t" in result.stdout or "--token" in result.stdout
    assert "-o" in result.stdout or "--output" in result.stdout
    assert "--format" in result.stdout


def test_days_help_shows_options():
    """Test that days --help shows all required options."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", "days", "--help"],
        capture_output=True,
        text=True,
    )

    assert "-t" in result.stdout or "--token" in result.stdout
    assert "-f" in result.stdout or "--from-date" in result.stdout
    assert "-e" in result.stdout or "--end-date" in result.stdout
    assert "-o" in result.stdout or "--output" in result.stdout
    assert "--format" in result.stdout


def test_weight_help_shows_options():
    """Test that weight --help shows all required options."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", "weight", "--help"],
        capture_output=True,
        text=True,
    )

    assert "-t" in result.stdout or "--token" in result.stdout
    assert "-f" in result.stdout or "--from-date" in result.stdout
    assert "-e" in result.stdout or "--end-date" in result.stdout
    assert "-o" in result.stdout or "--output" in result.stdout
    assert "--format" in result.stdout


def test_nutrients_help_shows_options():
    """Test that nutrients --help shows all required options."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", "nutrients", "--help"],
        capture_output=True,
        text=True,
    )

    assert "-t" in result.stdout or "--token" in result.stdout
    assert "-n" in result.stdout or "--nutrients" in result.stdout
    assert "-f" in result.stdout or "--from-date" in result.stdout
    assert "-o" in result.stdout or "--output" in result.stdout
    assert "--format" in result.stdout


def test_products_help_shows_options():
    """Test that products --help shows all required options."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", "products", "--help"],
        capture_output=True,
        text=True,
    )

    assert "-t" in result.stdout or "--token" in result.stdout
    assert "-f" in result.stdout or "--from-file" in result.stdout
    assert "-o" in result.stdout or "--output" in result.stdout
    assert "--format" in result.stdout


def test_summary_help_shows_options():
    """Test that summary --help shows all required options."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", "summary", "--help"],
        capture_output=True,
        text=True,
    )

    assert "-f" in result.stdout or "--from-file" in result.stdout
    assert "--period" in result.stdout
    assert "--format" in result.stdout


def test_export_all_help_shows_options():
    """Test that export-all --help shows all required options."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", "export-all", "--help"],
        capture_output=True,
        text=True,
    )

    assert "email" in result.stdout
    assert "password" in result.stdout
    assert "-o" in result.stdout or "--output" in result.stdout
    assert "--format" in result.stdout


# Feature #67: Default values for optional arguments
def test_token_defaults_to_token_txt():
    """Test that -t/--token defaults to token.txt."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", "days", "--help"],
        capture_output=True,
        text=True,
    )

    assert "token.txt" in result.stdout, "Help should show token.txt as default"


def test_output_defaults_to_days_json():
    """Test that -o/--output defaults to days.json for days command."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", "days", "--help"],
        capture_output=True,
        text=True,
    )

    assert "days.json" in result.stdout, "Help should show days.json as default"


def test_missing_positional_args_login():
    """Test that missing positional args (email, password) produces error."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", "login", "-o", "token.txt"],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0, "Missing positional args should exit with non-zero code"
    assert "required" in result.stderr.lower() or "error" in result.stderr.lower(), "Should show error message"
    assert (
        "email" in result.stderr.lower() or "password" in result.stderr.lower() or "argument" in result.stderr.lower()
    ), "Should mention missing positional args"


def test_invalid_format_choice():
    """Test that invalid format choice produces error."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "yazio_exporter",
            "profile",
            "-t",
            "token.txt",
            "-o",
            "out.txt",
            "--format",
            "xml",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0, "Invalid choice should exit with non-zero code"
    assert "invalid choice" in result.stderr.lower() or "error" in result.stderr.lower(), "Should show error message"
    assert "xml" in result.stderr, "Should mention invalid value"


def test_unknown_subcommand():
    """Test that unknown subcommand produces error."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", "invalid-command"],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0, "Unknown subcommand should exit with non-zero code"
    assert "invalid choice" in result.stderr.lower() or "error" in result.stderr.lower(), "Should show error message"


def test_profile_defaults():
    """Test profile command uses defaults for token and output."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", "profile", "--help"],
        capture_output=True,
        text=True,
    )

    assert "token.txt" in result.stdout, "Help should show token.txt as default"
    assert "profile.json" in result.stdout, "Help should show profile.json as default"


def test_report_help_shows_options():
    """Test that report --help shows expected options."""
    result = subprocess.run(
        [sys.executable, "-m", "yazio_exporter", "report", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "-d" in result.stdout or "--dir" in result.stdout
    assert "--start" in result.stdout
    assert "--end" in result.stdout
