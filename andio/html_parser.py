"""HTML parser with template syntax stripping and line-number tracking."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from bs4 import BeautifulSoup, Tag

from andio.models import TEMPLATE_SENTINEL

# Template syntax patterns — each replaced with same-length whitespace
# to preserve source line/column numbers.
_TEMPLATE_PATTERNS = [
    # Jinja2 / Django: comments first, then blocks, then expressions
    re.compile(r"\{#.*?#\}", re.DOTALL),
    re.compile(r"\{%.*?%\}", re.DOTALL),
    re.compile(r"\{\{.*?\}\}", re.DOTALL),
    # ERB
    re.compile(r"<%=?.*?%>", re.DOTALL),
    # Handlebars: block helpers, then expressions
    re.compile(r"\{\{#.*?\}\}", re.DOTALL),
    re.compile(r"\{\{/.*?\}\}", re.DOTALL),
]

# Attributes that contribute to an element's accessible name.
_NAME_ATTRIBUTES = {"alt", "aria-label", "aria-labelledby", "aria-describedby", "title"}


@dataclass
class TemplateMarker:
    """Tracks which (element_index, attribute) pairs had template variables."""
    template_attrs: Set[Tuple[int, str]] = field(default_factory=set)


@dataclass
class ParsedHTML:
    """Wrapper around BeautifulSoup with template-variable tracking."""

    soup: BeautifulSoup
    file_path: str
    template_markers: TemplateMarker = field(default_factory=TemplateMarker)
    _original_source: str = ""

    def get_location(self, tag: Tag) -> Tuple[int, int]:
        """Return (line, column) for a tag. Falls back to (0, 0)."""
        line = getattr(tag, "sourceline", 0) or 0
        col = getattr(tag, "sourcepos", 0) or 0
        return (line, col)

    def is_template_variable(self, tag: Tag, attr: str) -> bool:
        """Check if this attribute's value was entirely a template variable."""
        val = tag.get(attr, "")
        if isinstance(val, list):
            val = " ".join(val)
        return TEMPLATE_SENTINEL in str(val)

    def get_element_snippet(self, tag: Tag, max_len: int = 120) -> str:
        """Return a short string representation of the tag for reporting."""
        if not isinstance(tag, Tag):
            return ""
        # Build opening tag only
        attrs = []
        for k, v in (tag.attrs or {}).items():
            if isinstance(v, list):
                v = " ".join(v)
            attrs.append(f'{k}="{v}"')
        attr_str = " " + " ".join(attrs) if attrs else ""
        snippet = f"<{tag.name}{attr_str}>"
        if len(snippet) > max_len:
            snippet = snippet[:max_len - 3] + "..."
        return snippet

    @property
    def all_tags(self) -> List[Tag]:
        """All Tag elements in the document."""
        return [t for t in self.soup.descendants if isinstance(t, Tag)]


def _replace_preserving_lines(source: str, pattern: re.Pattern) -> Tuple[str, int]:
    """Replace pattern matches with same-length whitespace, preserving newlines.

    Returns the modified source and count of replacements made.
    """
    count = 0

    def _replacer(match):
        nonlocal count
        count += 1
        text = match.group(0)
        # Preserve newlines, replace everything else with spaces
        return "".join("\n" if ch == "\n" else " " for ch in text)

    result = pattern.sub(_replacer, source)
    return result, count


def _inject_sentinels(source: str) -> Tuple[str, int]:
    """After stripping template syntax, detect attributes that are now empty
    or whitespace-only and inject the sentinel value.

    Returns modified source and count of template-variable attributes found.
    """
    # Find attribute values that are entirely whitespace (were template vars).
    # Pattern: attr="   " where the spaces came from template stripping.
    sentinel_count = 0

    def _replace_empty_attr(match):
        nonlocal sentinel_count
        attr_name = match.group(1)
        if attr_name.lower() in _NAME_ATTRIBUTES:
            sentinel_count += 1
            return f'{attr_name}="{TEMPLATE_SENTINEL}"'
        return match.group(0)

    # Match attr="<only whitespace>"
    result = re.sub(
        r'([\w-]+)="(\s+)"',
        _replace_empty_attr,
        source,
    )
    return result, sentinel_count


def strip_template_syntax(source: str) -> Tuple[str, int]:
    """Strip all template engine syntax from HTML source.

    Template expressions are replaced with same-length whitespace to preserve
    line numbers. Attributes whose values were entirely template variables
    get the TEMPLATE_SENTINEL value injected.

    Returns:
        Tuple of (stripped source, count of template-variable attributes).
    """
    for pattern in _TEMPLATE_PATTERNS:
        source, _ = _replace_preserving_lines(source, pattern)

    source, sentinel_count = _inject_sentinels(source)
    return source, sentinel_count


def parse_html(file_path: str) -> ParsedHTML:
    """Parse an HTML file, stripping template syntax first.

    Uses Python's built-in html.parser backend for BeautifulSoup to get
    sourceline/sourcepos attributes on tags.
    """
    path = Path(file_path)
    original_source = path.read_text(encoding="utf-8", errors="replace")

    stripped, template_count = strip_template_syntax(original_source)

    soup = BeautifulSoup(stripped, "html.parser")

    return ParsedHTML(
        soup=soup,
        file_path=str(path.resolve()),
        _original_source=original_source,
        template_markers=TemplateMarker(),
    )
