"""Categories not checked by ANDIO — included in every report."""

from __future__ import annotations

NOT_CHECKED = [
    "Color contrast (WCAG 1.4.3, 1.4.11) — requires CSS cascade resolution and computed styles",
    "Tab order and keyboard navigation (WCAG 2.1.1, 2.4.3) — requires live focus traversal",
    "Fake heading detection (WCAG 1.3.1) — requires computed font-size comparison",
    "Screen reader accessible name computation — requires full DOM traversal",
    "Dynamic/runtime content from template variables — flagged for review, not evaluated",
]


def get_not_checked(template_variable_count: int = 0) -> list[str]:
    """Return the not-checked list, with template variable count appended."""
    items = list(NOT_CHECKED)
    if template_variable_count > 0:
        items[-1] = (
            f"Dynamic/runtime content from template variables "
            f"({template_variable_count} elements flagged for review)"
        )
    return items
