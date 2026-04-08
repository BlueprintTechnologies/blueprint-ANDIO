"""Tests for HTML parser with template stripping."""

import os

import pytest

from andio.html_parser import parse_html, strip_template_syntax
from andio.models import TEMPLATE_SENTINEL

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestTemplateStripping:
    def test_jinja2_expressions_stripped(self):
        source = '<h1>{{ heading }}</h1>'
        result, _ = strip_template_syntax(source)
        assert "{{" not in result
        assert "}}" not in result

    def test_jinja2_blocks_stripped(self):
        source = '{% for item in items %}<li>x</li>{% endfor %}'
        result, _ = strip_template_syntax(source)
        assert "{%" not in result
        assert "<li>x</li>" in result

    def test_jinja2_comments_stripped(self):
        source = '{# this is a comment #}<p>text</p>'
        result, _ = strip_template_syntax(source)
        assert "{#" not in result
        assert "<p>text</p>" in result

    def test_erb_expressions_stripped(self):
        source = '<h1><%= @title %></h1>'
        result, _ = strip_template_syntax(source)
        assert "<%=" not in result
        assert "%>" not in result

    def test_erb_blocks_stripped(self):
        source = '<% if true %><p>yes</p><% end %>'
        result, _ = strip_template_syntax(source)
        assert "<%" not in result

    def test_line_numbers_preserved(self):
        source = "line1\n{{ var }}\nline3\n{% block %}\nline5"
        result, _ = strip_template_syntax(source)
        assert result.count("\n") == source.count("\n")

    def test_multiline_template_preserves_lines(self):
        source = '{# this\nis\nmultiline #}\n<p>text</p>'
        result, _ = strip_template_syntax(source)
        assert result.count("\n") == source.count("\n")

    def test_sentinel_injected_for_template_alt(self):
        source = '<img alt="{{ dynamic }}" src="x.png">'
        result, count = strip_template_syntax(source)
        assert TEMPLATE_SENTINEL in result
        assert count == 1

    def test_sentinel_injected_for_aria_label(self):
        source = '<button aria-label="{{ label }}">X</button>'
        result, count = strip_template_syntax(source)
        assert TEMPLATE_SENTINEL in result
        assert count == 1

    def test_static_alt_not_sentinel(self):
        source = '<img alt="A real description" src="x.png">'
        result, count = strip_template_syntax(source)
        assert TEMPLATE_SENTINEL not in result
        assert count == 0

    def test_non_name_attribute_not_sentinel(self):
        source = '<a href="{{ url }}">Link</a>'
        result, count = strip_template_syntax(source)
        assert TEMPLATE_SENTINEL not in result
        assert count == 0


class TestParseHTML:
    def test_parse_jinja_fixture(self):
        parsed = parse_html(os.path.join(FIXTURES, "template_jinja.html"))
        assert parsed.soup is not None
        assert parsed.file_path.endswith("template_jinja.html")

        # Template syntax should be gone
        raw = str(parsed.soup)
        assert "{{" not in raw
        assert "{%" not in raw
        assert "{#" not in raw

    def test_parse_erb_fixture(self):
        parsed = parse_html(os.path.join(FIXTURES, "template_erb.html"))
        raw = str(parsed.soup)
        assert "<%=" not in raw
        assert "<%" not in raw

    def test_static_alt_preserved(self):
        parsed = parse_html(os.path.join(FIXTURES, "template_jinja.html"))
        imgs = parsed.soup.find_all("img")
        # Second img has static alt
        static_img = [i for i in imgs if "Static alt text" in str(i.get("alt", ""))]
        assert len(static_img) == 1

    def test_template_alt_has_sentinel(self):
        parsed = parse_html(os.path.join(FIXTURES, "template_jinja.html"))
        imgs = parsed.soup.find_all("img")
        template_imgs = [i for i in imgs if parsed.is_template_variable(i, "alt")]
        assert len(template_imgs) == 1

    def test_get_location_returns_line(self):
        parsed = parse_html(os.path.join(FIXTURES, "template_jinja.html"))
        h1 = parsed.soup.find("h1")
        line, col = parsed.get_location(h1)
        assert line > 0

    def test_all_tags(self):
        parsed = parse_html(os.path.join(FIXTURES, "template_jinja.html"))
        tags = parsed.all_tags
        assert len(tags) > 0
        tag_names = [t.name for t in tags]
        assert "html" in tag_names
        assert "img" in tag_names

    def test_get_element_snippet(self):
        parsed = parse_html(os.path.join(FIXTURES, "template_jinja.html"))
        img = parsed.soup.find("img")
        snippet = parsed.get_element_snippet(img)
        assert snippet.startswith("<img")
        assert snippet.endswith(">")
