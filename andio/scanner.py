"""Core scan engine — parses files and runs checks."""

from __future__ import annotations

import glob as globmod
from pathlib import Path
from typing import List, Optional

from andio.checks import get_checks
from andio.checks.base import BaseCheck, DocumentContext
from andio.css_parser import CSSRule, parse_css
from andio.html_parser import ParsedHTML, parse_html
from andio.models import CheckSummary, Finding, RuleSummary, ScanResult
from andio.not_checked import get_not_checked


HTML_EXTENSIONS = {".html", ".htm", ".jinja", ".jinja2", ".j2"}
CSS_EXTENSIONS = {".css"}
SCANNABLE_EXTENSIONS = HTML_EXTENSIONS | CSS_EXTENSIONS

_TEMPLATE_VAR_ATTRS = ("alt", "aria-label", "aria-labelledby", "aria-describedby", "title")


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
    css_rules = _parse_css_files(css_files)

    all_findings: List[Finding] = []
    template_var_count = 0
    per_check_counts: dict[str, int] = {c.id: 0 for c in checks}
    per_rule_counts: dict[str, int] = {
        rule_id: 0 for c in checks for rule_id in c.rule_ids
    }

    for html_file in html_files:
        parsed = parse_html(html_file)
        context = DocumentContext(parsed)
        template_var_count += _count_template_vars(parsed)
        _run_checks_for_file(
            checks, parsed, context, css_rules,
            all_findings, per_check_counts, per_rule_counts,
        )

    check_summaries = _build_check_summaries(checks, per_check_counts, per_rule_counts)

    return ScanResult(
        findings=all_findings,
        files_scanned=all_files,
        checks_run=[c.id for c in checks],
        check_summaries=check_summaries,
        not_checked=get_not_checked(template_var_count),
        template_variable_count=template_var_count,
    )


def _parse_css_files(css_files: List[str]) -> List[CSSRule]:
    """Parse all CSS files once — rules are shared across HTML file checks."""
    rules: List[CSSRule] = []
    for css_file in css_files:
        rules.extend(parse_css(css_file))
    return rules


def _count_template_vars(parsed: ParsedHTML) -> int:
    """Count attributes whose values were stripped as template variables."""
    count = 0
    for tag in parsed.all_tags:
        for attr in _TEMPLATE_VAR_ATTRS:
            if parsed.is_template_variable(tag, attr):
                count += 1
    return count


def _run_checks_for_file(
    checks: List[BaseCheck],
    parsed: ParsedHTML,
    context: DocumentContext,
    css_rules: List[CSSRule],
    all_findings: List[Finding],
    per_check_counts: dict,
    per_rule_counts: dict,
) -> None:
    """Run every check against a parsed file and update aggregate counters."""
    for check in checks:
        findings = check.run(parsed, context, css_rules)
        all_findings.extend(findings)
        per_check_counts[check.id] += len(findings)
        for f in findings:
            if f.check_id in per_rule_counts:
                per_rule_counts[f.check_id] += 1


def _build_check_summaries(
    checks: List[BaseCheck],
    per_check_counts: dict,
    per_rule_counts: dict,
) -> List[CheckSummary]:
    """Compose CheckSummary objects (with nested RuleSummary) from counters."""
    return [
        CheckSummary(
            id=c.id,
            name=c.name,
            finding_count=per_check_counts[c.id],
            rules=[
                RuleSummary(id=rid, finding_count=per_rule_counts[rid])
                for rid in c.rule_ids
            ],
        )
        for c in checks
    ]


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
