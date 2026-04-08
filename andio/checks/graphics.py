"""Graphics and image accessibility checks (ANDI gANDI module).

Implements 3 v1 checks:
- ANDI-0174: Redundant phrase in alt text ("image of...")
- ANDI-0175: Alt text contains file name
- ANDI-0176: Alt text is not descriptive ("image", "photo")
"""

from __future__ import annotations

import re
from typing import List

from andio.checks import register
from andio.checks.base import BaseCheck, DocumentContext
from andio.css_parser import CSSRule
from andio.html_parser import ParsedHTML
from andio.models import Finding, Severity, TEMPLATE_SENTINEL

# Redundant phrases in alt text
_REDUNDANT_PHRASES = re.compile(
    r"\b(image of|photo of|picture of|graphic of|screenshot of|icon of|logo of)\b",
    re.IGNORECASE,
)

# File extension patterns in alt text
_FILE_EXTENSIONS = re.compile(
    r"\.(jpg|jpeg|png|gif|bmp|svg|webp|ico|tiff|avif)\b",
    re.IGNORECASE,
)

# Non-descriptive alt text (entire value is just one of these words)
_NON_DESCRIPTIVE = re.compile(
    r"^(image|photo|picture|graphic|icon|logo|banner|spacer|placeholder|untitled)$",
    re.IGNORECASE,
)


@register
class GraphicsChecks(BaseCheck):
    id = "graphics"
    name = "Graphics / Images"
    version = "v1"

    def run(self, parsed: ParsedHTML, context: DocumentContext, css_rules: List[CSSRule]) -> List[Finding]:
        findings: List[Finding] = []

        for tag in parsed.soup.find_all(["img", "input"]):
            if tag.name == "input" and tag.get("type", "").lower() != "image":
                continue

            alt = tag.get("alt")
            if alt is None or TEMPLATE_SENTINEL in str(alt):
                continue

            alt_text = str(alt).strip()
            if not alt_text:
                continue

            # ANDI-0176: Non-descriptive alt (check first — more specific)
            if _NON_DESCRIPTIVE.match(alt_text):
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0176", Severity.ERROR,
                    "Image [alt] text is not descriptive.",
                ))
                continue

            # ANDI-0174: Redundant phrase
            if _REDUNDANT_PHRASES.search(alt_text):
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0174", Severity.INFO,
                    "Redundant phrase in image [alt] text.",
                ))

            # ANDI-0175: File name in alt
            if _FILE_EXTENSIONS.search(alt_text):
                findings.append(self._make_finding(
                    parsed, tag, "ANDI-0175", Severity.WARNING,
                    "Image [alt] text contains file name.",
                ))

        return findings
