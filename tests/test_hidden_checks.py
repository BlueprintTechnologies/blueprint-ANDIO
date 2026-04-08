"""Tests for hidden content accessibility checks."""

import os

from andio.checks.base import DocumentContext
from andio.checks.hidden import HiddenChecks
from andio.css_parser import parse_css
from andio.html_parser import parse_html

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestHiddenChecks:
    def test_pseudo_content_flagged(self):
        parsed = parse_html(os.path.join(FIXTURES, "template_jinja.html"))
        context = DocumentContext(parsed)
        css_rules = parse_css(os.path.join(FIXTURES, "pseudo_content.css"))

        findings = HiddenChecks().run(parsed, context, css_rules)
        ids = [f.check_id for f in findings]

        assert "ANDI-0220" in ids
        # "OK" and "Error: check logs" have content — empty "" is skipped
        assert len(findings) == 2

    def test_empty_pseudo_content_not_flagged(self):
        parsed = parse_html(os.path.join(FIXTURES, "template_jinja.html"))
        context = DocumentContext(parsed)
        css_rules = parse_css(os.path.join(FIXTURES, "pseudo_content.css"))

        findings = HiddenChecks().run(parsed, context, css_rules)
        elements = " ".join(f.element for f in findings)
        assert "divider" not in elements
