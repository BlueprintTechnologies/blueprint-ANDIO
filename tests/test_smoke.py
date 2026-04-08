"""Smoke tests — verify the package is importable and CLI responds."""

from click.testing import CliRunner

from andio import __version__
from andio.cli import main
from andio.models import Finding, ScanResult, Severity


def test_version():
    assert __version__ == "0.1.0"


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "ANDIO" in result.output


def test_cli_scan_help():
    runner = CliRunner()
    result = runner.invoke(main, ["scan", "--help"])
    assert result.exit_code == 0
    assert "PATHS" in result.output


def test_finding_is_error():
    f = Finding(
        check_id="ANDI-0031",
        severity=Severity.ERROR,
        message="test",
        file_path="test.html",
        line=1,
    )
    assert f.is_error is True


def test_finding_not_error():
    f = Finding(
        check_id="ANDI-0031",
        severity=Severity.WARNING,
        message="test",
        file_path="test.html",
        line=1,
    )
    assert f.is_error is False


def test_scan_result_counts():
    result = ScanResult(findings=[
        Finding("A", Severity.ERROR, "e", "f", 1),
        Finding("B", Severity.WARNING, "w", "f", 2),
        Finding("C", Severity.WARNING, "w", "f", 3),
        Finding("D", Severity.INFO, "i", "f", 4),
    ])
    assert result.error_count == 1
    assert result.warning_count == 2
    assert result.info_count == 1
    assert result.has_errors is True


def test_scan_result_no_errors():
    result = ScanResult(findings=[
        Finding("B", Severity.WARNING, "w", "f", 2),
    ])
    assert result.has_errors is False
