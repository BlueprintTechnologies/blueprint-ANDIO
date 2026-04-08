"""Global / cross-module accessibility checks (ANDI Main module).

Implements 24 v1 checks covering:
- Reference integrity (ARIA refs, label mismatches)
- Structural orphans (legends, figcaptions, captions, titles)
- ARIA edge cases (misspellings, multiple roles, unreliable combos)
- Deprecated HTML
- Component quality (long attrs, non-unique buttons, small clickable areas, JS events)
- Label misuse
"""

from __future__ import annotations

import re
from typing import List, Set

from bs4 import Tag

from andio.checks import register
from andio.checks.base import BaseCheck, DocumentContext
from andio.css_parser import CSSRule
from andio.html_parser import ParsedHTML
from andio.models import Finding, Severity, TEMPLATE_SENTINEL

# Form elements that <label for> can legitimately target
_FORM_ELEMENTS = {"input", "select", "textarea", "button", "meter", "output", "progress"}

# Elements with natively focusable behavior
_FOCUSABLE_ELEMENTS = {"input", "select", "textarea", "button", "a", "area"}

# JavaScript events that may cause keyboard accessibility issues
_PROBLEMATIC_EVENTS = {"ondblclick", "onmouseover", "onmouseout", "onmousedown", "onmouseup", "onmousemove"}

# ARIA reference attributes that point to IDs
_ARIA_REF_ATTRS = {"aria-labelledby", "aria-describedby", "aria-controls", "aria-owns", "aria-flowto"}

# Deprecated HTML5 attributes (element, attribute)
_DEPRECATED_ATTRS = {
    ("table", "summary"),
    ("a", "name"),
    ("td", "scope"),
    ("img", "longdesc"),
    ("table", "cellpadding"),
    ("table", "cellspacing"),
    ("table", "border"),
    ("table", "align"),
    ("table", "bgcolor"),
    ("table", "width"),
    ("td", "width"),
    ("td", "height"),
    ("td", "bgcolor"),
    ("td", "align"),
    ("td", "valign"),
    ("th", "width"),
    ("th", "height"),
    ("th", "bgcolor"),
    ("th", "align"),
    ("th", "valign"),
    ("tr", "bgcolor"),
    ("tr", "align"),
    ("tr", "valign"),
    ("body", "bgcolor"),
    ("body", "text"),
    ("body", "link"),
    ("body", "vlink"),
    ("body", "alink"),
}

# ARIA attribute combinations that produce unreliable screen reader results
_UNRELIABLE_COMBOS = [
    ({"aria-label", "aria-labelledby"}, "aria-label with aria-labelledby"),
]

# Vague link text patterns (used by links module too, but 0200 checks buttons)
_VAGUE_PATTERNS = re.compile(
    r"^(click here|here|more|read more|learn more|link|this|info|details)$",
    re.IGNORECASE,
)

# Max attribute text length before warning
_MAX_ATTR_LENGTH = 250


@register
class GlobalChecks(BaseCheck):
    id = "global"
    name = "Global / Cross-module"
    version = "v1"

    def run(self, parsed: ParsedHTML, context: DocumentContext, css_rules: List[CSSRule]) -> List[Finding]:
        findings: List[Finding] = []

        findings.extend(self._check_duplicate_label_for(parsed, context))
        findings.extend(self._check_aria_describedby_alone(parsed, context))
        findings.extend(self._check_legend_alone(parsed, context))
        findings.extend(self._check_aria_labeledby_misspelled(parsed, context))
        findings.extend(self._check_multiple_roles(parsed, context))
        findings.extend(self._check_referenced_ids(parsed, context))
        findings.extend(self._check_legend_reference(parsed, context))
        findings.extend(self._check_nested_references(parsed, context))
        findings.extend(self._check_duplicate_id_references(parsed, context))
        findings.extend(self._check_label_mismatch(parsed, context))
        findings.extend(self._check_multiple_titles(parsed, context))
        findings.extend(self._check_orphan_counts(parsed, context))
        findings.extend(self._check_deprecated_html(parsed, context))
        findings.extend(self._check_alt_on_non_image(parsed, context))
        findings.extend(self._check_label_for_non_form(parsed, context))
        findings.extend(self._check_unreliable_combos(parsed, context))
        findings.extend(self._check_js_events(parsed, context))
        findings.extend(self._check_long_attributes(parsed, context))
        findings.extend(self._check_non_unique_buttons(parsed, context))
        findings.extend(self._check_small_clickable_area(parsed, context))

        return findings

    # ANDI-0012: Multiple labels with same for attribute
    def _check_duplicate_label_for(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for for_val, labels in context.label_for_map.items():
            if len(labels) > 1:
                for label in labels[1:]:
                    findings.append(self._make_finding(
                        parsed, label, "ANDI-0012", Severity.ERROR,
                        f'More than one <label for="{for_val}"> associates with element [id={for_val}].',
                    ))
        return findings

    # ANDI-0021: aria-describedby used alone (no accessible name)
    def _check_aria_describedby_alone(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for tag in parsed.all_tags:
            if tag.get("aria-describedby") and not _has_accessible_name(tag, context):
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0021", Severity.WARNING,
                    "[aria-describedby] should be used in combination with a component that provides an accessible name.",
                ))
        return findings

    # ANDI-0022: legend used alone (no accessible name on parent fieldset)
    def _check_legend_alone(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for tag in parsed.soup.find_all("legend"):
            parent = tag.find_parent("fieldset")
            if parent is None:
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0022", Severity.ERROR,
                    "<legend> should be contained within a <fieldset>.",
                ))
        return findings

    # ANDI-0031: aria-labeledby misspelled
    def _check_aria_labeledby_misspelled(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for tag in parsed.all_tags:
            if tag.get("aria-labeledby"):
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0031", Severity.ERROR,
                    '[aria-labeledby] is misspelled, use [aria-labelledby].',
                ))
        return findings

    # ANDI-0033: Multiple roles on element
    def _check_multiple_roles(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for tag in parsed.all_tags:
            role = tag.get("role", "")
            if isinstance(role, str) and len(role.split()) > 1:
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0033", Severity.WARNING,
                    "Element has multiple roles. Determine if sequence is acceptable.",
                ))
        return findings

    # ANDI-0063 / ANDI-0065: Referenced IDs not found
    def _check_referenced_ids(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for tag, attr, ref_ids in _iter_aria_refs(parsed):
            missing = [rid for rid in ref_ids if rid not in context.id_map]
            if missing:
                is_name_attr = attr in ("aria-labelledby", "aria-describedby")
                severity = Severity.ERROR if is_name_attr else Severity.WARNING
                check_id = "ANDI-0065" if is_name_attr else "ANDI-0063"
                findings.append(self._make_finding(
                    parsed, tag, check_id, severity,
                    f'[{attr}] references id(s) "{" ".join(missing)}" not found.',
                ))
        return findings

    # ANDI-006B: Reference points to legend
    def _check_legend_reference(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for tag, attr, ref_ids in _iter_aria_refs(parsed):
            for target in _resolve_ref_targets(ref_ids, context):
                if target.name == "legend":
                    findings.append(self._make_finding(
                        parsed, tag, "ANDI-006B", Severity.INFO,
                        f'[{attr}] is referencing a legend which may cause speech verbosity.',
                    ))
        return findings

    # ANDI-006C: Nested references
    def _check_nested_references(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for tag, attr, ref_ids in _iter_aria_refs(parsed):
            for target in _resolve_ref_targets(ref_ids, context):
                for inner_attr in _ARIA_REF_ATTRS:
                    if target.get(inner_attr):
                        findings.append(self._make_finding(
                            parsed, tag, "ANDI-006C", Severity.WARNING,
                            f'[{attr}] reference contains another [{inner_attr}] reference which won\'t be used for this Output.',
                        ))
        return findings

    # ANDI-006D / ANDI-006E: Duplicate references to same ID
    def _check_duplicate_id_references(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for tag, attr, ref_ids in _iter_aria_refs(parsed):
            seen: Set[str] = set()
            for rid in ref_ids:
                if rid in seen:
                    findings.append(self._make_finding(
                        parsed, tag, "ANDI-006D", Severity.WARNING,
                        f'[{attr}] is directly referencing [id={rid}] multiple times which may cause speech verbosity.',
                    ))
                seen.add(rid)
        return findings

    # ANDI-006F: Nested label mismatch
    def _check_label_mismatch(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for label in parsed.soup.find_all("label"):
            for_val = label.get("for")
            if not for_val:
                continue
            # Find form elements nested inside this label
            for child in label.find_all(_FORM_ELEMENTS):
                child_id = child.get("id")
                if child_id and child_id != for_val:
                    findings.append(self._make_finding(
                        parsed, label, "ANDI-006F", Severity.WARNING,
                        f'Element nested in <label> but label[for={for_val}] does not match element [id={child_id}].',
                    ))
        return findings

    # ANDI-0073: Multiple title tags
    def _check_multiple_titles(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        titles = parsed.soup.find_all("title")
        if len(titles) > 1:
            for title in titles[1:]:
                findings.append(self._make_finding(
                    parsed, title, "ANDI-0073", Severity.WARNING,
                    "Page has more than one <title> tag.",
                ))
        return findings

    # ANDI-0074 / 0075 / 0076: Orphan counts
    def _check_orphan_counts(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        counts = context.element_counts

        legends = counts.get("legend", 0)
        fieldsets = counts.get("fieldset", 0)
        if legends > fieldsets:
            # Report on the first legend
            tag = parsed.soup.find("legend")
            if tag:
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0074", Severity.WARNING,
                    f"There are more legends ({legends}) than fieldsets ({fieldsets}).",
                ))

        figcaptions = counts.get("figcaption", 0)
        figures = counts.get("figure", 0)
        if figcaptions > figures:
            tag = parsed.soup.find("figcaption")
            if tag:
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0075", Severity.WARNING,
                    f"There are more figcaptions ({figcaptions}) than figures ({figures}).",
                ))

        captions = counts.get("caption", 0)
        tables = counts.get("table", 0)
        if captions > tables:
            tag = parsed.soup.find("caption")
            if tag:
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0076", Severity.WARNING,
                    f"There are more captions ({captions}) than tables ({tables}).",
                ))

        return findings

    # ANDI-0078: Deprecated HTML5 attributes
    def _check_deprecated_html(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for tag in parsed.all_tags:
            for elem, attr in _DEPRECATED_ATTRS:
                if tag.name == elem and tag.get(attr) is not None:
                    findings.append(self._make_finding(
                        parsed, tag, "ANDI-0078", Severity.WARNING,
                        f'Using HTML5, found deprecated [{attr}] on <{elem}>.',
                    ))
        return findings

    # ANDI-0081: Alt attribute on non-image element
    def _check_alt_on_non_image(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        _alt_allowed = {"img", "input", "area", "applet"}
        for tag in parsed.all_tags:
            if tag.get("alt") is not None and tag.name not in _alt_allowed:
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0081", Severity.WARNING,
                    f'[alt] attribute is meant for <img> elements, found on <{tag.name}>.',
                ))
        return findings

    # ANDI-0091: Label for on non-form element
    def _check_label_for_non_form(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for for_val, labels in context.label_for_map.items():
            targets = context.id_map.get(for_val, [])
            for target in targets:
                if target.name not in _FORM_ELEMENTS:
                    for label in labels:
                        findings.append(self._make_finding(
                            parsed, label, "ANDI-0091", Severity.ERROR,
                            f'Explicit <label for="{for_val}"> only works with form elements, targets <{target.name}>.',
                        ))
        return findings

    # ANDI-0101: Unreliable component combinations
    def _check_unreliable_combos(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for tag in parsed.all_tags:
            for combo_attrs, desc in _UNRELIABLE_COMBOS:
                if all(tag.get(a) for a in combo_attrs):
                    findings.append(self._make_finding(
                        parsed, tag, "ANDI-0101", Severity.WARNING,
                        f"Combining {desc} may produce inconsistent screen reader results.",
                    ))
        return findings

    # ANDI-0112: JS event may cause keyboard issues
    def _check_js_events(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for tag in parsed.all_tags:
            for event in _PROBLEMATIC_EVENTS:
                if tag.get(event):
                    findings.append(self._make_finding(
                        parsed, tag, "ANDI-0112", Severity.WARNING,
                        f"JavaScript event [{event}] may cause keyboard accessibility issues; investigate.",
                    ))
        return findings

    # ANDI-0151: Attribute text too long
    def _check_long_attributes(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        _check_attrs = {"alt", "aria-label", "title", "aria-describedby"}
        for tag in parsed.all_tags:
            for attr in _check_attrs:
                val = tag.get(attr, "")
                if isinstance(val, list):
                    val = " ".join(val)
                if TEMPLATE_SENTINEL in val:
                    continue
                if len(val) > _MAX_ATTR_LENGTH:
                    findings.append(self._make_finding(
                        parsed, tag, "ANDI-0151", Severity.WARNING,
                        f'[{attr}] attribute length ({len(val)}) exceeds {_MAX_ATTR_LENGTH} characters; consider condensing.',
                    ))
        return findings

    # ANDI-0200: Non-unique button text
    def _check_non_unique_buttons(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        buttons = parsed.soup.find_all(["button", "input"])
        button_names: dict = {}  # name -> [Tag]

        for btn in buttons:
            if btn.name == "input" and btn.get("type") not in ("button", "submit", "reset"):
                continue
            name = _get_button_name(btn)
            if name and TEMPLATE_SENTINEL not in name:
                button_names.setdefault(name.lower().strip(), []).append(btn)

        for name, btns in button_names.items():
            if len(btns) > 1:
                for btn in btns[1:]:
                    findings.append(self._make_finding(
                        parsed, btn, "ANDI-0200", Severity.WARNING,
                        "Non-unique button: same name/description as another button.",
                    ))
        return findings

    # ANDI-0210: Small clickable area
    def _check_small_clickable_area(self, parsed: ParsedHTML, context: DocumentContext) -> List[Finding]:
        findings = []
        for tag in parsed.soup.find_all("input"):
            input_type = (tag.get("type") or "").lower()
            if input_type in ("radio", "checkbox") and not _has_label(tag, context):
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0210", Severity.INFO,
                    f"An associated <label> containing text would increase the clickable area of this {input_type}.",
                ))
        return findings


def _iter_aria_refs(parsed: ParsedHTML):
    """Yield (tag, attr_name, ref_id_list) for every ARIA reference attribute on every tag."""
    for tag in parsed.all_tags:
        for attr in _ARIA_REF_ATTRS:
            ref_val = tag.get(attr)
            if not ref_val or TEMPLATE_SENTINEL in str(ref_val):
                continue
            yield tag, attr, str(ref_val).split()


def _resolve_ref_targets(ref_ids: List[str], context: DocumentContext):
    """Yield all Tag elements referenced by a list of IDs."""
    for rid in ref_ids:
        for target in context.id_map.get(rid, []):
            yield target


def _has_label(tag: Tag, context: DocumentContext) -> bool:
    """Check if an input element has an associated label with text."""
    tag_id = tag.get("id")
    if tag_id:
        for label in context.label_for_map.get(tag_id, []):
            if label.get_text(strip=True):
                return True
    parent_label = tag.find_parent("label")
    if parent_label and parent_label.get_text(strip=True):
        return True
    return False


def _has_accessible_name(tag: Tag, context: DocumentContext) -> bool:
    """Check if an element has any form of accessible name (simplified static check)."""
    if tag.get("aria-label"):
        return True
    if tag.get("aria-labelledby"):
        return True
    if tag.get("title"):
        return True
    if tag.get("alt"):
        return True
    # Check for associated label
    tag_id = tag.get("id")
    if tag_id and tag_id in context.label_for_map:
        return True
    # Check inner text
    text = tag.get_text(strip=True)
    if text and TEMPLATE_SENTINEL not in text:
        return True
    return False


def _get_button_name(tag: Tag) -> str:
    """Get the accessible name of a button element."""
    if tag.get("aria-label"):
        return str(tag["aria-label"])
    if tag.name == "input":
        return str(tag.get("value", ""))
    return tag.get_text(strip=True)
