"""WCAG 2.1 success criteria and Section 508 mappings for ANDI checks.

Section 508 (Revised 2017) incorporates WCAG 2.0 Level A and AA by reference.
Each ANDI check maps to one or more WCAG success criteria, which establishes
the Section 508 compliance basis.

Reference: https://www.section508.gov/manage/laws-and-policies/quick-reference-guide/
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class WCAGCriterion:
    """A single WCAG success criterion."""
    id: str          # e.g. "1.1.1"
    name: str        # e.g. "Non-text Content"
    level: str       # "A", "AA", or "AAA"

    @property
    def ref(self) -> str:
        """Short reference string for reports."""
        return f"WCAG {self.id} ({self.level})"

    @property
    def section_508(self) -> str:
        """Section 508 reference."""
        return f"Section 508 / WCAG {self.id} {self.name} (Level {self.level})"


# WCAG 2.1 criteria referenced by ANDIO checks
_CRITERIA = {
    "1.1.1": WCAGCriterion("1.1.1", "Non-text Content", "A"),
    "1.3.1": WCAGCriterion("1.3.1", "Info and Relationships", "A"),
    "2.1.1": WCAGCriterion("2.1.1", "Keyboard", "A"),
    "2.4.1": WCAGCriterion("2.4.1", "Bypass Blocks", "A"),
    "2.4.2": WCAGCriterion("2.4.2", "Page Titled", "A"),
    "2.4.4": WCAGCriterion("2.4.4", "Link Purpose (In Context)", "A"),
    "2.4.6": WCAGCriterion("2.4.6", "Headings and Labels", "AA"),
    "2.5.3": WCAGCriterion("2.5.3", "Label in Name", "A"),
    "3.3.2": WCAGCriterion("3.3.2", "Labels or Instructions", "A"),
    "4.1.1": WCAGCriterion("4.1.1", "Parsing", "A"),
    "4.1.2": WCAGCriterion("4.1.2", "Name, Role, Value", "A"),
}


# Mapping: ANDI check ID -> list of WCAG criterion IDs
CHECK_TO_WCAG: Dict[str, List[str]] = {
    # Global checks
    "ANDI-0012": ["4.1.1", "3.3.2"],        # Duplicate label for
    "ANDI-0021": ["4.1.2"],                  # aria-describedby alone
    "ANDI-0022": ["1.3.1"],                  # Legend without fieldset
    "ANDI-0031": ["4.1.2"],                  # Misspelled aria-labelledby
    "ANDI-0033": ["4.1.2"],                  # Multiple roles
    "ANDI-0063": ["4.1.2"],                  # Referenced ID not found
    "ANDI-0065": ["4.1.2"],                  # Referenced IDs not found (danger)
    "ANDI-006B": ["4.1.2"],                  # Reference to legend
    "ANDI-006C": ["4.1.2"],                  # Nested references
    "ANDI-006D": ["4.1.2"],                  # Duplicate reference
    "ANDI-006E": ["4.1.2"],                  # Direct+indirect reference
    "ANDI-006F": ["3.3.2", "4.1.2"],         # Label mismatch
    "ANDI-0073": ["2.4.2"],                  # Multiple titles
    "ANDI-0074": ["1.3.1"],                  # More legends than fieldsets
    "ANDI-0075": ["1.3.1"],                  # More figcaptions than figures
    "ANDI-0076": ["1.3.1"],                  # More captions than tables
    "ANDI-0078": ["4.1.1"],                  # Deprecated HTML5
    "ANDI-0081": ["1.1.1"],                  # Alt on non-image
    "ANDI-0091": ["3.3.2", "4.1.2"],         # Label for non-form element
    "ANDI-0101": ["4.1.2"],                  # Unreliable combos
    "ANDI-0112": ["2.1.1"],                  # JS event keyboard issues
    "ANDI-0151": ["4.1.2"],                  # Long attribute text
    "ANDI-0200": ["4.1.2", "2.4.6"],         # Non-unique buttons
    "ANDI-0210": ["3.3.2"],                  # Small clickable area

    # Focusable checks
    "ANDI-0002": ["4.1.2", "3.3.2"],         # Form element no name
    "ANDI-0008": ["4.1.2"],                  # Focusable element no name
    "ANDI-0052": ["4.1.2"],                  # Multi-char accesskey
    "ANDI-0054": ["4.1.1"],                  # Duplicate accesskey button
    "ANDI-0055": ["4.1.1"],                  # Duplicate accesskey generic
    "ANDI-0056": ["4.1.1"],                  # Duplicate accesskey link
    "ANDI-0121": ["2.1.1"],                  # Negative tabindex with name
    "ANDI-0122": ["2.1.1", "4.1.2"],         # Negative tabindex no name
    "ANDI-0123": ["2.1.1"],                  # Iframe negative tabindex

    # Link checks
    "ANDI-0069": ["2.4.1"],                  # Broken anchor target
    "ANDI-007B": ["4.1.1"],                  # Deprecated <a name>
    "ANDI-0128": ["2.1.1", "4.1.2"],         # <a> no href/id/tabindex
    "ANDI-0161": ["2.4.4"],                  # Ambiguous link
    "ANDI-0163": ["2.4.4"],                  # Vague link text
    "ANDI-0168": ["4.1.2"],                  # <a> no href not recognized

    # Structure checks
    "ANDI-0005": ["1.1.1"],                  # Figure no name
    "ANDI-0133": ["4.1.2"],                  # Empty live region
    "ANDI-0182": ["4.1.2"],                  # Live region with form
    "ANDI-0184": ["4.1.2"],                  # Live region non-container
    "ANDI-0191": ["1.3.1", "2.4.6"],         # Heading level conflict
    "ANDI-0192": ["1.3.1", "2.4.6"],         # role=heading no aria-level
    "ANDI-0194": ["1.3.1"],                  # List container invalid role

    # Graphics checks
    "ANDI-0174": ["1.1.1"],                  # Redundant alt phrase
    "ANDI-0175": ["1.1.1"],                  # File name in alt
    "ANDI-0176": ["1.1.1"],                  # Non-descriptive alt

    # Hidden checks
    "ANDI-0220": ["1.3.1"],                  # CSS pseudo content
}


def get_wcag_refs(check_id: str) -> List[WCAGCriterion]:
    """Return WCAG criteria for a given ANDI check ID."""
    criterion_ids = CHECK_TO_WCAG.get(check_id, [])
    return [_CRITERIA[cid] for cid in criterion_ids if cid in _CRITERIA]


def format_wcag_short(check_id: str) -> str:
    """Format WCAG references as a compact string for report output.

    Example: "WCAG 4.1.2 (A), 3.3.2 (A)"
    """
    refs = get_wcag_refs(check_id)
    if not refs:
        return ""
    return ", ".join(r.ref for r in refs)


def format_508_ref(check_id: str) -> str:
    """Format as Section 508 reference string.

    Example: "Section 508 / WCAG 4.1.2 Name, Role, Value (Level A)"
    """
    refs = get_wcag_refs(check_id)
    if not refs:
        return ""
    return "; ".join(r.section_508 for r in refs)
