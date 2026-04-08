"""Tests for structure and heading accessibility checks."""

import os

from andio.checks.base import DocumentContext
from andio.checks.structures import StructureChecks
from andio.html_parser import parse_html

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _run(fixture_name):
    parsed = parse_html(os.path.join(FIXTURES, fixture_name))
    context = DocumentContext(parsed)
    return StructureChecks().run(parsed, context, [])


def _ids(findings):
    return [f.check_id for f in findings]


class TestStructureChecks:
    def setup_method(self):
        self.findings = _run("structure_violations.html")
        self.ids = _ids(self.findings)

    def test_figure_no_name(self):
        assert "ANDI-0005" in self.ids
        fig_findings = [f for f in self.findings if f.check_id == "ANDI-0005"]
        assert len(fig_findings) == 1  # Only the unnamed figure

    def test_empty_live_region(self):
        assert "ANDI-0133" in self.ids

    def test_live_region_with_form(self):
        assert "ANDI-0182" in self.ids

    def test_live_region_non_container(self):
        assert "ANDI-0184" in self.ids

    def test_heading_level_conflict(self):
        assert "ANDI-0191" in self.ids

    def test_heading_role_no_level(self):
        assert "ANDI-0192" in self.ids
        role_findings = [f for f in self.findings if f.check_id == "ANDI-0192"]
        assert len(role_findings) == 1  # Only the one without aria-level

    def test_list_container_invalid_role(self):
        assert "ANDI-0194" in self.ids
