"""Lightweight CSS parser for pseudo-element content and background-image detection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class CSSRule:
    """A single CSS declaration extracted from a stylesheet."""

    selector: str
    property: str
    value: str
    file_path: str
    line: int


# Regex to match CSS rule blocks: selector { ... }
_RULE_BLOCK = re.compile(
    r"([^{}]+?)\s*\{([^{}]*)\}",
    re.DOTALL,
)

# Regex to match individual property: value declarations
_DECLARATION = re.compile(
    r"([\w-]+)\s*:\s*([^;]+);",
)

# Properties we care about extracting
_RELEVANT_PROPERTIES = {"content", "background-image", "background"}

# Pseudo-element selectors
_PSEUDO_ELEMENT = re.compile(r"::(?:before|after)")


def parse_css(file_path: str) -> List[CSSRule]:
    """Parse a CSS file and extract relevant rules.

    Currently extracts:
    - ::before/::after rules with content: declarations
    - background-image declarations (for v2 flagging)
    """
    path = Path(file_path)
    source = path.read_text(encoding="utf-8", errors="replace")

    # Strip CSS comments
    source_no_comments = re.sub(r"/\*.*?\*/", _whitespace_replacer, source, flags=re.DOTALL)

    rules: List[CSSRule] = []

    for block_match in _RULE_BLOCK.finditer(source_no_comments):
        selector = block_match.group(1).strip()
        body = block_match.group(2)
        block_start = block_match.start()

        # Calculate line number of the selector
        line_num = source_no_comments[:block_start].count("\n") + 1

        for decl_match in _DECLARATION.finditer(body):
            prop = decl_match.group(1).strip().lower()
            value = decl_match.group(2).strip()

            if prop not in _RELEVANT_PROPERTIES:
                continue

            # Calculate line number of the declaration
            decl_offset = block_start + block_match.group(0).index(decl_match.group(0))
            decl_line = source_no_comments[:decl_offset].count("\n") + 1

            rules.append(CSSRule(
                selector=selector,
                property=prop,
                value=value,
                file_path=str(path.resolve()),
                line=decl_line,
            ))

    return rules


def get_pseudo_content_rules(rules: List[CSSRule]) -> List[CSSRule]:
    """Filter to only ::before/::after rules with content declarations."""
    return [
        r for r in rules
        if _PSEUDO_ELEMENT.search(r.selector) and r.property == "content"
    ]


def get_background_image_rules(rules: List[CSSRule]) -> List[CSSRule]:
    """Filter to rules with background-image declarations."""
    return [
        r for r in rules
        if r.property in ("background-image", "background")
        and ("url(" in r.value or "gradient" in r.value)
    ]


def _whitespace_replacer(match):
    """Replace match with same-length whitespace preserving newlines."""
    return "".join("\n" if ch == "\n" else " " for ch in match.group(0))
