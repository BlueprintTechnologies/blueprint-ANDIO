"""Hidden content accessibility checks (ANDI hANDI module).

Implements 1 v1 check:
- ANDI-0220: CSS pseudo-element content (::before/::after)
"""

from __future__ import annotations

from typing import List

from andio.checks import register
from andio.checks.base import BaseCheck, DocumentContext
from andio.css_parser import CSSRule, get_pseudo_content_rules
from andio.html_parser import ParsedHTML
from andio.models import Finding, Severity


@register
class HiddenChecks(BaseCheck):
    id = "hidden"
    name = "Hidden Content"
    version = "v1"

    def run(self, parsed: ParsedHTML, context: DocumentContext, css_rules: List[CSSRule]) -> List[Finding]:
        findings: List[Finding] = []

        pseudo_rules = get_pseudo_content_rules(css_rules)
        for rule in pseudo_rules:
            # Empty content ("" or '') is decorative — skip
            if _is_empty_content(rule.value):
                continue
            findings.append(Finding(
                check_id="ANDI-0220",
                severity=Severity.WARNING,
                message=f'Content has been injected using CSS pseudo-element on "{rule.selector}".',
                file_path=rule.file_path,
                line=rule.line,
                column=0,
                element=f"{rule.selector} {{ content: {rule.value}; }}",
            ))

        return findings


def _is_empty_content(value: str) -> bool:
    """Check if a CSS content value is empty/decorative."""
    stripped = value.strip()
    return stripped in ('""', "''", "none", "normal")
