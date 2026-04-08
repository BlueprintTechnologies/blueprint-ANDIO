"""Base class for all ANDIO accessibility checks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from bs4 import Tag

from andio.css_parser import CSSRule
from andio.html_parser import ParsedHTML
from andio.models import Finding, Severity


class DocumentContext:
    """Pre-computed document-wide data shared across checks.

    Built once per parsed HTML file to avoid redundant traversals.
    """

    def __init__(self, parsed: ParsedHTML):
        self.parsed = parsed
        self._build(parsed)

    def _build(self, parsed: ParsedHTML):
        from collections import Counter, defaultdict

        self.id_map: dict = defaultdict(list)        # id -> [Tag]
        self.label_for_map: dict = defaultdict(list)  # for-value -> [Tag]
        self.element_counts: dict = Counter()         # tag name -> count
        self.accesskeys: dict = defaultdict(list)     # accesskey value -> [Tag]

        for tag in parsed.all_tags:
            # ID map
            tag_id = tag.get("id")
            if tag_id:
                self.id_map[tag_id].append(tag)

            # Label for map
            if tag.name == "label":
                for_val = tag.get("for")
                if for_val:
                    self.label_for_map[for_val].append(tag)

            # Element counts
            self.element_counts[tag.name] += 1

            # AccessKey map
            ak = tag.get("accesskey")
            if ak:
                ak_str = str(ak) if not isinstance(ak, str) else ak
                self.accesskeys[ak_str].append(tag)


class BaseCheck(ABC):
    """Abstract base for all accessibility checks."""

    # Subclasses must define these
    id: str = ""          # e.g., "global", "focusable", "links"
    name: str = ""        # Human-readable name
    version: str = "v1"   # "v1" or "v2"

    @abstractmethod
    def run(
        self,
        parsed: ParsedHTML,
        context: DocumentContext,
        css_rules: List[CSSRule],
    ) -> List[Finding]:
        """Run this check against a parsed document.

        Args:
            parsed: The parsed HTML document.
            context: Pre-computed document-wide data.
            css_rules: CSS rules from associated stylesheets.

        Returns:
            List of findings (may be empty).
        """
        ...

    def _make_finding(
        self,
        parsed: ParsedHTML,
        tag: Tag,
        check_id: str,
        severity: Severity,
        message: str,
    ) -> Finding:
        """Helper to create a Finding with location info from a tag."""
        line, col = parsed.get_location(tag)
        return Finding(
            check_id=check_id,
            severity=severity,
            message=message,
            file_path=parsed.file_path,
            line=line,
            column=col,
            element=parsed.get_element_snippet(tag),
        )
