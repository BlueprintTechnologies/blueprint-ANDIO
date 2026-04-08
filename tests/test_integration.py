"""Integration tests — end-to-end scan behavior."""

import json
import os

from click.testing import CliRunner

from andio.cli import main
from andio.scanner import scan

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestEndToEndScan:
    def test_scan_directory(self):
        result = scan([FIXTURES])
        assert len(result.files_scanned) > 0
        assert len(result.checks_run) == 6  # all 6 v1 check modules

    def test_scan_single_html(self):
        result = scan([os.path.join(FIXTURES, "global_violations.html")])
        assert len(result.files_scanned) == 1
        assert result.has_errors is True

    def test_scan_clean_template(self):
        result = scan([os.path.join(FIXTURES, "clean.html")])
        assert result.has_errors is False

    def test_scan_with_check_filter(self):
        result = scan(
            [os.path.join(FIXTURES, "global_violations.html")],
            check_names=["links"],
        )
        assert len(result.checks_run) == 1
        assert result.checks_run[0] == "links"

    def test_not_checked_section(self):
        result = scan([FIXTURES])
        assert len(result.not_checked) == 5
        assert any("Color contrast" in item for item in result.not_checked)

    def test_template_variable_count(self):
        result = scan([os.path.join(FIXTURES, "template_jinja.html")])
        assert result.template_variable_count > 0
        assert any("template variables" in item for item in result.not_checked)

    def test_scan_nonexistent_path(self):
        result = scan(["/nonexistent/path"])
        assert len(result.files_scanned) == 0
        assert len(result.findings) == 0


class TestCLIIntegration:
    def test_exit_code_1_on_errors(self):
        runner = CliRunner()
        result = runner.invoke(main, [
            "scan", os.path.join(FIXTURES, "global_violations.html"),
        ])
        assert result.exit_code == 1

    def test_exit_code_0_on_clean(self):
        runner = CliRunner()
        result = runner.invoke(main, [
            "scan", os.path.join(FIXTURES, "clean.html"),
        ])
        assert result.exit_code == 0

    def test_json_output_format(self):
        runner = CliRunner()
        result = runner.invoke(main, [
            "scan", os.path.join(FIXTURES, "global_violations.html"),
            "--format", "json",
        ])
        data = json.loads(result.output)
        assert "findings" in data
        assert "summary" in data
        assert "not_checked" in data
        assert data["summary"]["errors"] > 0

    def test_github_summary_format(self):
        runner = CliRunner()
        result = runner.invoke(main, [
            "scan", os.path.join(FIXTURES, "global_violations.html"),
            "--format", "github-summary",
        ])
        assert "## ANDIO Accessibility Scan" in result.output
        assert "<details>" in result.output

    def test_checks_filter_flag(self):
        runner = CliRunner()
        result = runner.invoke(main, [
            "scan", os.path.join(FIXTURES, "global_violations.html"),
            "--checks", "graphics",
        ])
        # graphics checks on global_violations.html should find the long alt
        # but no structural errors, so exit 0
        assert result.exit_code == 0

    def test_malformed_html_does_not_crash(self):
        runner = CliRunner()
        # Create a temp malformed file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
            f.write("<div><p>Unclosed tags <img <broken attr")
            f.flush()
            result = runner.invoke(main, ["scan", f.name])
            os.unlink(f.name)
        assert result.exit_code in (0, 1)  # Doesn't crash
