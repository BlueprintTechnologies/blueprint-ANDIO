"""Tests for graphics / image accessibility checks."""

import os

from andio.checks.base import DocumentContext
from andio.checks.graphics import GraphicsChecks
from andio.html_parser import parse_html

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _run(fixture_name):
    parsed = parse_html(os.path.join(FIXTURES, fixture_name))
    context = DocumentContext(parsed)
    return GraphicsChecks().run(parsed, context, [])


def _ids(findings):
    return [f.check_id for f in findings]


class TestGraphicsChecks:
    def setup_method(self):
        self.findings = _run("graphics_violations.html")
        self.ids = _ids(self.findings)

    def test_redundant_phrase(self):
        assert "ANDI-0174" in self.ids
        redundant = [f for f in self.findings if f.check_id == "ANDI-0174"]
        assert len(redundant) == 2  # "image of" and "Photo of"

    def test_file_name_in_alt(self):
        assert "ANDI-0175" in self.ids

    def test_non_descriptive_alt(self):
        assert "ANDI-0176" in self.ids
        non_desc = [f for f in self.findings if f.check_id == "ANDI-0176"]
        assert len(non_desc) == 3  # "image", "Photo", "icon"

    def test_valid_alt_not_flagged(self):
        # Good descriptions should produce no findings
        all_elements = " ".join(f.element for f in self.findings)
        assert "blue mountain" not in all_elements
        assert "deployment metrics" not in all_elements

    def test_empty_alt_not_flagged(self):
        # alt="" is decorative, not a violation
        all_elements = " ".join(f.element for f in self.findings)
        assert "spacer" not in all_elements
