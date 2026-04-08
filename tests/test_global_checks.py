"""Tests for global / cross-module accessibility checks."""

import os

from andio.checks.base import DocumentContext
from andio.css_parser import CSSRule
from andio.html_parser import parse_html

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _run_global_checks(fixture_name):
    """Parse a fixture and run only global checks."""
    from andio.checks.global_checks import GlobalChecks
    parsed = parse_html(os.path.join(FIXTURES, fixture_name))
    context = DocumentContext(parsed)
    check = GlobalChecks()
    return check.run(parsed, context, [])


def _finding_ids(findings):
    return [f.check_id for f in findings]


class TestGlobalChecks:
    def setup_method(self):
        self.findings = _run_global_checks("global_violations.html")
        self.ids = _finding_ids(self.findings)

    def test_duplicate_label_for(self):
        assert "ANDI-0012" in self.ids

    def test_aria_describedby_alone(self):
        assert "ANDI-0021" in self.ids

    def test_legend_without_fieldset(self):
        assert "ANDI-0022" in self.ids

    def test_misspelled_aria_labeledby(self):
        assert "ANDI-0031" in self.ids

    def test_multiple_roles(self):
        assert "ANDI-0033" in self.ids

    def test_missing_aria_ref_error(self):
        # aria-labelledby pointing to nonexistent ID is an error
        assert "ANDI-0065" in self.ids

    def test_missing_aria_ref_warning(self):
        # aria-controls pointing to nonexistent ID is a warning
        assert "ANDI-0063" in self.ids

    def test_reference_to_legend(self):
        assert "ANDI-006B" in self.ids

    def test_duplicate_reference(self):
        assert "ANDI-006D" in self.ids

    def test_label_mismatch(self):
        assert "ANDI-006F" in self.ids

    def test_multiple_titles(self):
        assert "ANDI-0073" in self.ids

    def test_deprecated_html(self):
        assert "ANDI-0078" in self.ids
        # Should flag both summary and border
        deprecated_findings = [f for f in self.findings if f.check_id == "ANDI-0078"]
        deprecated_messages = " ".join(f.message for f in deprecated_findings)
        assert "summary" in deprecated_messages
        assert "border" in deprecated_messages

    def test_alt_on_non_image(self):
        assert "ANDI-0081" in self.ids

    def test_label_for_non_form(self):
        assert "ANDI-0091" in self.ids

    def test_unreliable_combo(self):
        assert "ANDI-0101" in self.ids

    def test_js_event(self):
        assert "ANDI-0112" in self.ids

    def test_long_attribute(self):
        assert "ANDI-0151" in self.ids

    def test_non_unique_buttons(self):
        assert "ANDI-0200" in self.ids

    def test_small_clickable_area(self):
        assert "ANDI-0210" in self.ids
        # Should flag both checkbox and radio
        area_findings = [f for f in self.findings if f.check_id == "ANDI-0210"]
        assert len(area_findings) == 2


class TestGlobalChecksCleanFile:
    """Verify no false positives on a clean file."""

    def test_clean_jinja_template(self):
        findings = _run_global_checks("template_jinja.html")
        # The Jinja template should produce no global check findings
        # (template variables are stripped, not flagged as errors)
        assert len(findings) == 0
