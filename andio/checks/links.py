"""Link and button accessibility checks (ANDI lANDI module).

Implements 6 v1 checks:
- ANDI-0069: In-page anchor target not found
- ANDI-007B: Deprecated <a name=""> attribute
- ANDI-0128: <a> without href, id, or tabindex
- ANDI-0161: Ambiguous link (same text, different href)
- ANDI-0163: Vague link text
- ANDI-0168: <a> without href may not be recognized as link
"""

from __future__ import annotations

import re
from typing import List

from bs4 import Tag

from andio.checks import register
from andio.checks.base import BaseCheck, DocumentContext
from andio.css_parser import CSSRule
from andio.html_parser import ParsedHTML
from andio.models import Finding, Severity, TEMPLATE_SENTINEL

_VAGUE_LINK_TEXT = re.compile(
    r"^(click here|here|more|read more|learn more|link|this|info|details)$",
    re.IGNORECASE,
)


@register
class LinkChecks(BaseCheck):
    id = "links"
    name = "Links / Buttons"
    version = "v1"

    def run(self, parsed: ParsedHTML, context: DocumentContext, css_rules: List[CSSRule]) -> List[Finding]:
        findings: List[Finding] = []
        anchors = parsed.soup.find_all("a")

        findings.extend(self._check_anchor_targets(parsed, context, anchors))
        findings.extend(self._check_deprecated_name(parsed, anchors))
        findings.extend(self._check_missing_href(parsed, anchors))
        findings.extend(self._check_ambiguous_links(parsed, anchors))
        findings.extend(self._check_vague_text(parsed, anchors))

        return findings

    # ANDI-0069: In-page anchor target not found
    def _check_anchor_targets(self, parsed: ParsedHTML, context: DocumentContext, anchors: list) -> List[Finding]:
        findings = []
        for tag in anchors:
            href = tag.get("href", "")
            if not isinstance(href, str) or not href.startswith("#") or len(href) < 2:
                continue
            target_id = href[1:]
            if TEMPLATE_SENTINEL in target_id:
                continue
            if target_id not in context.id_map:
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0069", Severity.WARNING,
                    f'In-page anchor target with [id={target_id}] not found.',
                ))
        return findings

    # ANDI-007B: Deprecated <a name="">
    def _check_deprecated_name(self, parsed: ParsedHTML, anchors: list) -> List[Finding]:
        findings = []
        for tag in anchors:
            if tag.get("name"):
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-007B", Severity.WARNING,
                    f'This <a> element has [name={tag["name"]}] which is a deprecated way of making an anchor target; use [id].',
                ))
        return findings

    # ANDI-0128 / ANDI-0168: <a> without href
    def _check_missing_href(self, parsed: ParsedHTML, anchors: list) -> List[Finding]:
        findings = []
        for tag in anchors:
            if tag.get("href"):
                continue
            has_id = bool(tag.get("id"))
            has_tabindex = tag.get("tabindex") is not None
            has_role = bool(tag.get("role"))

            if not has_id and not has_tabindex:
                # ANDI-0128: no href, no id, no tabindex
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0128", Severity.WARNING,
                    "<a> element has no [href], [id], or [tabindex]; this might be a link that only works with a mouse.",
                ))
            elif not has_role:
                # ANDI-0168: no href, may not be recognized as link
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0168", Severity.WARNING,
                    "<a> without [href] may not be recognized as a link; add [role=link] or [href].",
                ))
        return findings

    # ANDI-0161: Ambiguous links (same text, different href)
    def _check_ambiguous_links(self, parsed: ParsedHTML, anchors: list) -> List[Finding]:
        link_map = _build_link_text_map(anchors)
        findings = []
        for text, entries in link_map.items():
            hrefs_seen: dict = {}
            for href, tag in entries:
                if href not in hrefs_seen and hrefs_seen:
                    findings.append(self._make_finding(
                        parsed, tag, "ANDI-0161", Severity.WARNING,
                        "Ambiguous Link: same name/description as another link but different href.",
                    ))
                hrefs_seen.setdefault(href, tag)
        return findings

    # ANDI-0163: Vague link text
    def _check_vague_text(self, parsed: ParsedHTML, anchors: list) -> List[Finding]:
        findings = []
        for tag in anchors:
            if not tag.get("href"):
                continue
            text = _get_link_text(tag)
            if not text or TEMPLATE_SENTINEL in text:
                continue
            if _VAGUE_LINK_TEXT.match(text.strip()):
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0163", Severity.WARNING,
                    "Link text is vague and does not identify its purpose.",
                ))
        return findings


def _build_link_text_map(anchors: list) -> dict:
    """Group anchors by their accessible text: text -> [(href, tag)]."""
    link_map: dict = {}
    for tag in anchors:
        href = tag.get("href", "")
        if not href or TEMPLATE_SENTINEL in str(href):
            continue
        text = _get_link_text(tag)
        if not text or TEMPLATE_SENTINEL in text:
            continue
        link_map.setdefault(text.lower().strip(), []).append((str(href), tag))
    return link_map


def _get_link_text(tag: Tag) -> str:
    """Get the accessible text of a link element."""
    # aria-label takes precedence
    label = tag.get("aria-label")
    if label:
        return str(label)
    return tag.get_text(strip=True)
