"""Tests for CSS parser."""

import os

from andio.css_parser import (
    get_background_image_rules,
    get_pseudo_content_rules,
    parse_css,
)

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestParseCSS:
    def test_extracts_pseudo_content(self):
        rules = parse_css(os.path.join(FIXTURES, "pseudo_content.css"))
        pseudo = get_pseudo_content_rules(rules)
        # .status-good::before, .status-bad::after, .divider::before
        assert len(pseudo) == 3

    def test_pseudo_content_values(self):
        rules = parse_css(os.path.join(FIXTURES, "pseudo_content.css"))
        pseudo = get_pseudo_content_rules(rules)
        values = [r.value for r in pseudo]
        assert '"OK"' in values
        assert '"Error: check logs"' in values
        assert '""' in values

    def test_pseudo_selectors(self):
        rules = parse_css(os.path.join(FIXTURES, "pseudo_content.css"))
        pseudo = get_pseudo_content_rules(rules)
        selectors = [r.selector for r in pseudo]
        assert any("::before" in s for s in selectors)
        assert any("::after" in s for s in selectors)

    def test_extracts_background_image(self):
        rules = parse_css(os.path.join(FIXTURES, "pseudo_content.css"))
        bg = get_background_image_rules(rules)
        assert len(bg) == 2  # .hero background-image and .gradient-bg background

    def test_ignores_irrelevant_properties(self):
        rules = parse_css(os.path.join(FIXTURES, "pseudo_content.css"))
        # color, font-size should not appear
        all_props = [r.property for r in rules]
        assert "color" not in all_props
        assert "font-size" not in all_props

    def test_line_numbers(self):
        rules = parse_css(os.path.join(FIXTURES, "pseudo_content.css"))
        pseudo = get_pseudo_content_rules(rules)
        for rule in pseudo:
            assert rule.line > 0

    def test_file_path_set(self):
        rules = parse_css(os.path.join(FIXTURES, "pseudo_content.css"))
        for rule in rules:
            assert rule.file_path.endswith("pseudo_content.css")
