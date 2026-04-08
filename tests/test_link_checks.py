"""Tests for link accessibility checks."""

import os

from andio.checks.base import DocumentContext
from andio.checks.links import LinkChecks
from andio.html_parser import parse_html

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _run(fixture_name):
    parsed = parse_html(os.path.join(FIXTURES, fixture_name))
    context = DocumentContext(parsed)
    return LinkChecks().run(parsed, context, [])


def _ids(findings):
    return [f.check_id for f in findings]


class TestLinkChecks:
    def setup_method(self):
        self.findings = _run("link_violations.html")
        self.ids = _ids(self.findings)

    def test_broken_anchor_target(self):
        assert "ANDI-0069" in self.ids

    def test_valid_anchor_not_flagged(self):
        anchor_findings = [f for f in self.findings if f.check_id == "ANDI-0069"]
        messages = " ".join(f.message for f in anchor_findings)
        assert "section1" not in messages

    def test_deprecated_name(self):
        assert "ANDI-007B" in self.ids

    def test_no_href_no_id_no_tabindex(self):
        assert "ANDI-0128" in self.ids

    def test_no_href_has_id(self):
        assert "ANDI-0168" in self.ids

    def test_no_href_with_role_not_flagged(self):
        # <a id="btn" role="button"> should NOT trigger 0168
        findings_0168 = [f for f in self.findings if f.check_id == "ANDI-0168"]
        for f in findings_0168:
            assert 'role="button"' not in f.element

    def test_ambiguous_links(self):
        assert "ANDI-0161" in self.ids

    def test_same_text_same_href_not_ambiguous(self):
        ambiguous = [f for f in self.findings if f.check_id == "ANDI-0161"]
        messages = " ".join(f.element for f in ambiguous)
        assert "Home" not in messages

    def test_vague_link_text(self):
        assert "ANDI-0163" in self.ids
        vague = [f for f in self.findings if f.check_id == "ANDI-0163"]
        assert len(vague) == 3  # click here, Read More, here

    def test_descriptive_text_not_flagged(self):
        vague = [f for f in self.findings if f.check_id == "ANDI-0163"]
        for f in vague:
            assert "documentation" not in f.element
