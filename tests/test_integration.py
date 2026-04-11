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

    def test_check_summaries_populated(self):
        result = scan([FIXTURES])
        assert len(result.check_summaries) == 6
        module_ids = {c.id for c in result.check_summaries}
        assert module_ids == {"global", "focusable", "links", "structures", "graphics", "hidden"}
        # Every finding must be reflected in exactly one module's count
        assert sum(c.finding_count for c in result.check_summaries) == len(result.findings)
        # Each summary must have a human-readable name
        assert all(c.name for c in result.check_summaries)

    def test_rule_summaries_populated(self):
        result = scan([FIXTURES])
        # 49 ANDI rules across 6 modules
        assert result.total_rule_count == 49
        assert 0 <= result.passed_rule_count <= result.total_rule_count
        # Per-module rule counts add up to the global total
        assert sum(c.total_rule_count for c in result.check_summaries) == 49
        # Every rule that fired in findings must be marked as failed
        fired_ids = {f.check_id for f in result.findings}
        for c in result.check_summaries:
            for r in c.rules:
                if r.id in fired_ids:
                    assert not r.passed
                    assert r.finding_count > 0

    def test_clean_scan_all_checks_pass(self):
        result = scan([os.path.join(FIXTURES, "clean.html")])
        assert result.passed_check_count == result.total_check_count
        assert all(c.passed for c in result.check_summaries)
        # Clean scan = every rule passed
        assert result.passed_rule_count == result.total_rule_count
        assert all(r.passed for c in result.check_summaries for r in c.rules)

    def test_rule_ids_match_wcag_registry(self):
        """Every rule_id declared by a check must have a WCAG mapping."""
        from andio.checks import get_checks
        from andio.wcag import CHECK_TO_WCAG
        for check in get_checks():
            for rule_id in check.rule_ids:
                assert rule_id in CHECK_TO_WCAG, (
                    f"{check.id} declares {rule_id} but it has no WCAG mapping"
                )

    def test_no_orphan_rules_in_wcag_registry(self):
        """Every WCAG registry entry must be owned by some check module."""
        from andio.checks import get_checks
        from andio.wcag import CHECK_TO_WCAG
        owned = {rid for c in get_checks() for rid in c.rule_ids}
        orphans = set(CHECK_TO_WCAG.keys()) - owned
        assert orphans == set(), f"Orphan rules in WCAG registry: {orphans}"

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
        # Pass counts and per-module rollup are exposed for the PR comment
        assert "checks_passed" in data["summary"]
        assert data["summary"]["checks_total"] == 6
        assert data["summary"]["rules_total"] == 49
        assert "rules_passed" in data["summary"]
        assert len(data["check_summaries"]) == 6
        sample = data["check_summaries"][0]
        assert {"id", "name", "finding_count", "passed", "rules_passed", "rules_total", "rules"} <= set(sample.keys())
        rule = sample["rules"][0]
        assert {"id", "finding_count", "passed", "wcag", "wcag_linked"} <= set(rule.keys())

    def test_github_summary_format(self):
        runner = CliRunner()
        result = runner.invoke(main, [
            "scan", os.path.join(FIXTURES, "global_violations.html"),
            "--format", "github-summary",
        ])
        assert "## ANDIO Accessibility Scan" in result.output
        assert "<details>" in result.output
        # Headline pass counts and rollup tables are present
        assert "modules passed" in result.output
        assert "ANDI rules passed" in result.output
        assert "Check modules" in result.output
        assert "| Module | Status | Rules passed | Findings |" in result.output
        assert "ANDI rules (per-rule pass/fail)" in result.output

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
