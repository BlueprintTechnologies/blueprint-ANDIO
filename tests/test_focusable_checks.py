"""Tests for focusable element accessibility checks."""

import os

from andio.checks.base import DocumentContext
from andio.checks.focusable import FocusableChecks
from andio.html_parser import parse_html

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _run(fixture_name):
    parsed = parse_html(os.path.join(FIXTURES, fixture_name))
    context = DocumentContext(parsed)
    return FocusableChecks().run(parsed, context, [])


def _ids(findings):
    return [f.check_id for f in findings]


class TestFocusableChecks:
    def setup_method(self):
        self.findings = _run("focusable_violations.html")
        self.ids = _ids(self.findings)

    def test_form_element_no_name(self):
        assert "ANDI-0002" in self.ids
        name_findings = [f for f in self.findings if f.check_id == "ANDI-0002"]
        # input, textarea (select has inner text from <option> so it has a name)
        assert len(name_findings) == 2

    def test_non_form_focusable_no_name(self):
        assert "ANDI-0008" in self.ids

    def test_multi_char_accesskey(self):
        assert "ANDI-0052" in self.ids

    def test_duplicate_accesskey_button(self):
        assert "ANDI-0054" in self.ids

    def test_duplicate_accesskey_link(self):
        assert "ANDI-0056" in self.ids

    def test_duplicate_accesskey_generic(self):
        assert "ANDI-0055" in self.ids

    def test_negative_tabindex_with_name(self):
        assert "ANDI-0121" in self.ids

    def test_negative_tabindex_no_name(self):
        assert "ANDI-0122" in self.ids

    def test_iframe_negative_tabindex(self):
        assert "ANDI-0123" in self.ids

    def test_no_false_positives_on_labeled_elements(self):
        # Elements with labels, aria-label, text, or implicit names
        # should NOT produce ANDI-0002 or ANDI-0008
        name_findings = [
            f for f in self.findings
            if f.check_id in ("ANDI-0002", "ANDI-0008")
        ]
        for f in name_findings:
            assert "has-label" not in f.element
            assert "Click Me" not in f.element
            assert "submit" not in f.element.lower() or "type" not in f.element
            assert "Search" not in f.element
