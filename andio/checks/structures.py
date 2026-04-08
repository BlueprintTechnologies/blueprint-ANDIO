"""Structure and heading accessibility checks (ANDI sANDI module).

Implements 7 v1 checks:
- ANDI-0005: Figure has no accessible name / figcaption
- ANDI-0133: Live region has no inner text
- ANDI-0182: Live region contains form element
- ANDI-0184: Live region on non-container element
- ANDI-0191: Heading level conflicts with aria-level
- ANDI-0192: role=heading without aria-level
- ANDI-0194: List item container has invalid role
"""

from __future__ import annotations

from typing import List

from bs4 import Tag

from andio.checks import register
from andio.checks.base import BaseCheck, DocumentContext
from andio.css_parser import CSSRule
from andio.html_parser import ParsedHTML
from andio.models import Finding, Severity, TEMPLATE_SENTINEL

# Elements that can be live region containers
_CONTAINER_ELEMENTS = {
    "div", "span", "section", "article", "aside", "main", "header", "footer",
    "nav", "p", "ul", "ol", "dl", "table", "output", "form", "fieldset",
}

# Form elements that should not be inside live regions
_FORM_ELEMENTS = {"input", "select", "textarea", "button"}

# Heading elements and their inherent levels
_HEADING_LEVELS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}


@register
class StructureChecks(BaseCheck):
    id = "structures"
    name = "Structures / Headings"
    version = "v1"

    def run(self, parsed: ParsedHTML, context: DocumentContext, css_rules: List[CSSRule]) -> List[Finding]:
        findings: List[Finding] = []

        findings.extend(self._check_figures(parsed))
        findings.extend(self._check_live_regions(parsed))
        findings.extend(self._check_headings(parsed))
        findings.extend(self._check_list_container_roles(parsed))

        return findings

    # ANDI-0005: Figure has no accessible name or figcaption
    def _check_figures(self, parsed: ParsedHTML) -> List[Finding]:
        findings = []
        for fig in parsed.soup.find_all("figure"):
            has_caption = fig.find("figcaption") is not None
            has_name = _has_figure_name(fig)
            if not has_caption and not has_name:
                findings.append(self._make_finding(
                    parsed, fig, "ANDI-0005", Severity.WARNING,
                    "Figure has no accessible name, <figcaption>, or [title].",
                ))
        return findings

    # ANDI-0133 / 0182 / 0184: Live region checks
    def _check_live_regions(self, parsed: ParsedHTML) -> List[Finding]:
        findings = []
        for tag in parsed.all_tags:
            if not _is_live_region(tag):
                continue

            # ANDI-0184: Live region on non-container element
            if tag.name not in _CONTAINER_ELEMENTS:
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0184", Severity.ERROR,
                    "A live region can only be a container element.",
                ))
                continue

            # ANDI-0133: Empty live region
            text = tag.get_text(strip=True)
            if not text or TEMPLATE_SENTINEL in text:
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0133", Severity.WARNING,
                    "Live region has no innerText content.",
                ))

            # ANDI-0182: Live region contains form element
            for _ in tag.find_all(_FORM_ELEMENTS):
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0182", Severity.ERROR,
                    "Live Region contains a form element.",
                ))
                break  # One finding per live region

        return findings

    # ANDI-0191 / 0192: Heading checks
    def _check_headings(self, parsed: ParsedHTML) -> List[Finding]:
        findings = []
        for tag in parsed.all_tags:
            aria_level = tag.get("aria-level")
            native_level = _HEADING_LEVELS.get(tag.name)
            has_heading_role = (tag.get("role") or "").strip() == "heading"

            # ANDI-0191: Native heading level conflicts with aria-level
            if native_level and aria_level:
                try:
                    al = int(aria_level)
                    if al != native_level:
                        findings.append(self._make_finding(
                            parsed, tag, "ANDI-0191", Severity.ERROR,
                            f"Heading element level <{tag.name}> conflicts with [aria-level={aria_level}].",
                        ))
                except (ValueError, TypeError):
                    pass

            # ANDI-0192: role=heading without aria-level
            if has_heading_role and not aria_level and not native_level:
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0192", Severity.ERROR,
                    "[role=heading] used without [aria-level]; level 2 will be assumed.",
                ))

        return findings

    # ANDI-0194: List item container has invalid role
    def _check_list_container_roles(self, parsed: ParsedHTML) -> List[Finding]:
        findings = []
        for tag in parsed.soup.find_all(["li", "dd", "dt"]):
            parent = tag.parent
            if parent is None:
                continue
            parent_role = (parent.get("role") or "").strip()
            if not parent_role:
                continue
            valid_roles = {"list", "listbox", "menu", "menubar", "tablist",
                           "tree", "group", "none", "presentation"}
            if parent_role not in valid_roles:
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0194", Severity.WARNING,
                    f"List item's container is not recognized as a list because it has [role={parent_role}].",
                ))
        return findings


def _has_figure_name(tag: Tag) -> bool:
    """Check if a figure has an accessible name."""
    if tag.get("aria-label") and TEMPLATE_SENTINEL not in str(tag.get("aria-label")):
        return True
    if tag.get("aria-labelledby"):
        return True
    if tag.get("title") and TEMPLATE_SENTINEL not in str(tag.get("title")):
        return True
    return False


def _is_live_region(tag: Tag) -> bool:
    """Check if an element is a live region."""
    if tag.get("aria-live") and tag["aria-live"] != "off":
        return True
    role = (tag.get("role") or "").strip()
    return role in ("alert", "log", "marquee", "status", "timer")
