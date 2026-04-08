"""Focusable element accessibility checks (ANDI fANDI module).

Implements 9 v1 checks:
- ANDI-0002: Generic element has no accessible name
- ANDI-0008: Focusable element has no accessible name
- ANDI-0052: accessKey value > 1 character
- ANDI-0054: Duplicate accessKey on button
- ANDI-0055: Duplicate accessKey (generic)
- ANDI-0056: Duplicate accessKey on link
- ANDI-0121: Focusable element negative tabindex
- ANDI-0122: Focusable + negative tabindex + no name
- ANDI-0123: Iframe negative tabindex
"""

from __future__ import annotations

from typing import List

from bs4 import Tag

from andio.checks import register
from andio.checks.base import BaseCheck, DocumentContext
from andio.css_parser import CSSRule
from andio.html_parser import ParsedHTML
from andio.models import Finding, Severity, TEMPLATE_SENTINEL

# Natively focusable elements (when conditions met)
_NATIVELY_FOCUSABLE = {"input", "select", "textarea", "button"}

# Elements that are focusable when they have href
_FOCUSABLE_WITH_HREF = {"a", "area"}


def _is_focusable(tag: Tag) -> bool:
    """Check if an element is focusable (static approximation)."""
    if tag.name in _NATIVELY_FOCUSABLE:
        return tag.get("type", "").lower() != "hidden"
    if tag.name in _FOCUSABLE_WITH_HREF and tag.get("href"):
        return True
    if tag.get("tabindex") is not None:
        return True
    if tag.get("contenteditable") in ("true", ""):
        return True
    return False


def _has_accessible_name(tag: Tag, context: DocumentContext) -> bool:
    """Simplified static check for accessible name."""
    if _has_aria_name(tag):
        return True
    if tag.name == "img" and _has_non_template_attr(tag, "alt"):
        return True
    tag_id = tag.get("id")
    if tag_id and context.label_for_map.get(tag_id):
        return True
    text = tag.get_text(strip=True)
    if text and TEMPLATE_SENTINEL not in text:
        return True
    if tag.name == "input" and _input_has_implicit_name(tag):
        return True
    return False


def _has_aria_name(tag: Tag) -> bool:
    """Check ARIA naming attributes (non-template)."""
    if _has_non_template_attr(tag, "aria-label"):
        return True
    if tag.get("aria-labelledby"):
        return True
    if _has_non_template_attr(tag, "title"):
        return True
    return False


def _has_non_template_attr(tag: Tag, attr: str) -> bool:
    """Check if an attribute exists and is not a template sentinel."""
    val = tag.get(attr)
    return bool(val) and TEMPLATE_SENTINEL not in str(val)


def _input_has_implicit_name(tag: Tag) -> bool:
    """Check if an input has an implicit name (submit/reset have defaults)."""
    input_type = (tag.get("type") or "").lower()
    if input_type in ("submit", "reset"):
        return True
    if input_type == "button" and tag.get("value"):
        return True
    return False


def _get_tabindex(tag: Tag) -> int | None:
    """Parse tabindex attribute, returning None if not present or invalid."""
    val = tag.get("tabindex")
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


@register
class FocusableChecks(BaseCheck):
    id = "focusable"
    name = "Focusable Elements"
    version = "v1"

    def run(self, parsed: ParsedHTML, context: DocumentContext, css_rules: List[CSSRule]) -> List[Finding]:
        findings: List[Finding] = []

        findings.extend(self._check_accessible_names(parsed, context))
        findings.extend(self._check_accesskeys(parsed, context))
        findings.extend(self._check_negative_tabindex(parsed, context))

        return findings

    # ANDI-0002 / ANDI-0008: Elements with no accessible name
    def _check_accessible_names(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for tag in parsed.all_tags:
            if not _is_focusable(tag):
                continue
            if _has_accessible_name(tag, context):
                continue
            # Skip elements with template sentinel (flagged separately)
            if _has_template_name(tag):
                continue

            if tag.name in _NATIVELY_FOCUSABLE:
                # ANDI-0002 is for form elements specifically
                elem_desc = f"<{tag.name}>"
                if tag.name == "input":
                    elem_desc = f'<input type="{tag.get("type", "text")}">'
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0002", Severity.ERROR,
                    f'{elem_desc} has no accessible name, associated <label>, or [title].',
                ))
            else:
                # ANDI-0008 for other focusable elements
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0008", Severity.ERROR,
                    f'<{tag.name}> has no accessible name.',
                ))
        return findings

    # ANDI-0052 / 0054 / 0055 / 0056: accessKey issues
    def _check_accesskeys(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []

        for tag in parsed.all_tags:
            ak = tag.get("accesskey")
            if not ak:
                continue
            # ANDI-0052: Multi-character accessKey
            if len(str(ak)) > 1:
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0052", Severity.ERROR,
                    f'[accesskey] value "{ak}" has more than one character.',
                ))

        # Duplicate accessKey checks
        for ak_val, tags in context.accesskeys.items():
            if len(tags) <= 1:
                continue
            for tag in tags[1:]:
                check_id = _accesskey_check_id(tag)
                findings.append(self._make_finding(
                    parsed, tag, check_id, Severity.ERROR,
                    f'Duplicate [accesskey={ak_val}] found on <{tag.name}>.',
                ))

        return findings

    # ANDI-0121 / 0122 / 0123: Negative tabindex
    def _check_negative_tabindex(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for tag in parsed.all_tags:
            tabindex = _get_tabindex(tag)
            if tabindex is None or tabindex >= 0:
                continue

            if tag.name == "iframe":
                # ANDI-0123
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0123", Severity.WARNING,
                    "Iframe contents are not in keyboard tab order because iframe has negative tabindex.",
                ))
            elif _has_accessible_name(tag, context):
                # ANDI-0121
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0121", Severity.INFO,
                    "Focusable element is not in keyboard tab order; should it be tabbable?",
                ))
            else:
                # ANDI-0122
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0122", Severity.ERROR,
                    "Focusable element is not in keyboard tab order and has no accessible name; should it be tabbable?",
                ))
        return findings


def _accesskey_check_id(tag: Tag) -> str:
    """Return the appropriate ANDI check ID for duplicate accessKey."""
    if tag.name == "button" or (tag.name == "input" and tag.get("type") in ("button", "submit", "reset")):
        return "ANDI-0054"
    if tag.name == "a":
        return "ANDI-0056"
    return "ANDI-0055"


def _has_template_name(tag: Tag) -> bool:
    """Check if any name attribute contains the template sentinel."""
    for attr in ("alt", "aria-label", "title"):
        val = tag.get(attr, "")
        if TEMPLATE_SENTINEL in str(val):
            return True
    return False
