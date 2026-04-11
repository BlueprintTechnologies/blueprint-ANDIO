"""Core scan engine — parses files and runs checks."""

from __future__ import annotations

import glob as globmod
from pathlib import Path
from typing import List, Optional

from andio.checks import get_checks
from andio.checks.base import DocumentContext
from andio.css_parser import CSSRule, parse_css
from andio.html_parser import ParsedHTML, parse_html
from andio.models import CheckSummary, Finding, ScanResult
from andio.not_checked import get_not_checked


HTML_EXTENSIONS = {".html", ".htm", ".jinja", ".jinja2", ".j2"}
CSS_EXTENSIONS = {".css"}
SCANNABLE_EXTENSIONS = HTML_EXTENSIONS | CSS_EXTENSIONS


def scan(
    paths: List[str],
    check_names: Optional[List[str]] = None,
) -> ScanResult:
    """Scan the given file paths and return aggregated findings.

    Args:
        paths: File or directory paths to scan. Directories are searched
               for .html and .css files recursively.
        check_names: If provided, only run checks whose id is in this list.
                     If None, run all v1 checks.

    Returns:
        ScanResult with all findings, scanned files, and not-checked list.
    """
    all_files = _resolve_files(paths)
    html_files = [f for f in all_files if Path(f).suffix in HTML_EXTENSIONS]
    css_files = [f for f in all_files if Path(f).suffix in CSS_EXTENSIONS]

    checks = get_checks(names=check_names, version="v1")

    # Parse all CSS files once — rules are shared across HTML file checks
    css_rules: List[CSSRule] = []
    for css_file in css_files:
        css_rules.extend(parse_css(css_file))

    all_findings: List[Finding] = []
    template_var_count = 0
    per_check_counts: dict[str, int] = {c.id: 0 for c in checks}

    for html_file in html_files:
        parsed = parse_html(html_file)
        context = DocumentContext(parsed)

        # Count template variable attributes for the "not checked" section
        for tag in parsed.all_tags:
            for attr in ("alt", "aria-label", "aria-labelledby", "aria-describedby", "title"):
                if parsed.is_template_variable(tag, attr):
                    template_var_count += 1

        for check in checks:
            findings = check.run(parsed, context, css_rules)
            all_findings.extend(findings)
            per_check_counts[check.id] += len(findings)

    check_summaries = [
        CheckSummary(id=c.id, name=c.name, finding_count=per_check_counts[c.id])
        for c in checks
    ]

    return ScanResult(
        findings=all_findings,
        files_scanned=all_files,
        checks_run=[c.id for c in checks],
        check_summaries=check_summaries,
        not_checked=get_not_checked(template_var_count),
        template_variable_count=template_var_count,
    )


def _resolve_files(paths: List[str]) -> List[str]:
    """Expand paths into a flat list of scannable files."""
    files: List[str] = []
    for p in paths:
        path = Path(p)
        if path.is_file() and path.suffix in SCANNABLE_EXTENSIONS:
            files.append(str(path.resolve()))
        elif path.is_dir():
            for ext in SCANNABLE_EXTENSIONS:
                files.extend(
                    str(Path(f).resolve())
                    for f in globmod.glob(
                        str(path / "**" / f"*{ext}"), recursive=True
                    )
                )
        else:
            # Try as a glob pattern
            matched = globmod.glob(p, recursive=True)
            files.extend(
                str(Path(f).resolve())
                for f in matched
                if Path(f).suffix in SCANNABLE_EXTENSIONS
            )
    return sorted(set(files))
