"""Output formatters for ANDIO scan results."""

from __future__ import annotations

import json

from andio.models import Finding, ScanResult, Severity
from andio.wcag import format_508_ref, format_wcag_linked, format_wcag_short

_DETAILS_CLOSE = "</details>"


def format_output(result: ScanResult, fmt: str) -> str:
    """Dispatch to the appropriate formatter."""
    formatters = {
        "text": format_text,
        "json": format_json,
        "github-summary": format_github_summary,
    }
    return formatters[fmt](result)


def format_text(result: ScanResult) -> str:
    """Human-readable plain text output."""
    lines: list[str] = []
    lines.extend(_text_header(result))
    lines.extend(_text_findings(result))
    lines.append("=== Not checked by ANDIO (requires live browser) ===")
    for item in result.not_checked:
        lines.append(f"  - {item}")
    return "\n".join(lines)


def _text_header(result: ScanResult) -> list[str]:
    lines = [
        f"ANDIO scan complete: {len(result.files_scanned)} file(s) scanned",
        (
            f"  {result.error_count} error(s), "
            f"{result.warning_count} warning(s), "
            f"{result.info_count} info"
        ),
    ]
    if result.check_summaries:
        lines.append(
            f"  {result.passed_check_count}/{result.total_check_count} check module(s) passed, "
            f"{result.passed_rule_count}/{result.total_rule_count} ANDI rule(s) passed"
        )
        for c in result.check_summaries:
            status = "PASS" if c.passed else f"FAIL ({c.finding_count})"
            lines.append(
                f"    [{status}] {c.name} "
                f"({c.passed_rule_count}/{c.total_rule_count} rules)"
            )
    lines.append("")
    return lines


def _text_findings(result: ScanResult) -> list[str]:
    if not result.findings:
        return ["No findings.", ""]

    lines: list[str] = []
    by_file: dict[str, list[Finding]] = {}
    for f in result.findings:
        by_file.setdefault(f.file_path, []).append(f)

    for file_path, findings in sorted(by_file.items()):
        lines.append(f"--- {file_path} ---")
        for f in sorted(findings, key=lambda x: x.line):
            marker = _severity_marker(f.severity)
            wcag = format_wcag_short(f.check_id)
            wcag_suffix = f" [{wcag}]" if wcag else ""
            lines.append(f"  {marker} line {f.line}: [{f.check_id}] {f.message}{wcag_suffix}")
        lines.append("")
    return lines


def format_json(result: ScanResult) -> str:
    """JSON output for tooling integration."""
    data = {
        "findings": [
            {
                "check_id": f.check_id,
                "severity": f.severity.value,
                "message": f.message,
                "file_path": f.file_path,
                "line": f.line,
                "column": f.column,
                "element": f.element,
                "wcag": format_wcag_short(f.check_id),
                "wcag_linked": format_wcag_linked(f.check_id),
                "section_508": _format_508(f.check_id),
            }
            for f in result.findings
        ],
        "summary": {
            "files_scanned": len(result.files_scanned),
            "errors": result.error_count,
            "warnings": result.warning_count,
            "info": result.info_count,
            "checks_passed": result.passed_check_count,
            "checks_total": result.total_check_count,
            "rules_passed": result.passed_rule_count,
            "rules_total": result.total_rule_count,
        },
        "checks_run": result.checks_run,
        "check_summaries": [
            {
                "id": c.id,
                "name": c.name,
                "finding_count": c.finding_count,
                "passed": c.passed,
                "rules_passed": c.passed_rule_count,
                "rules_total": c.total_rule_count,
                "rules": [
                    {
                        "id": r.id,
                        "finding_count": r.finding_count,
                        "passed": r.passed,
                        "wcag": format_wcag_short(r.id),
                        "wcag_linked": format_wcag_linked(r.id),
                        "section_508": _format_508(r.id),
                    }
                    for r in c.rules
                ],
            }
            for c in result.check_summaries
        ],
        "not_checked": result.not_checked,
    }
    return json.dumps(data, indent=2)


def format_github_summary(result: ScanResult) -> str:
    """GitHub-flavored Markdown for $GITHUB_STEP_SUMMARY."""
    lines: list[str] = []
    lines.append("## ANDIO Accessibility Scan")
    lines.append("")

    lines.append(
        f"**{len(result.files_scanned)}** file(s) scanned | "
        f"**{result.error_count}** error(s) | "
        f"**{result.warning_count}** warning(s) | "
        f"**{result.info_count}** info | "
        f"**{result.passed_check_count}/{result.total_check_count}** modules passed | "
        f"**{result.passed_rule_count}/{result.total_rule_count}** ANDI rules passed"
    )
    lines.append("")

    lines.extend(_summary_checks_table(result))
    lines.extend(_summary_rules_table(result))
    lines.extend(_summary_findings(result))

    lines.append("<details><summary>Not checked by ANDIO (requires live browser)</summary>")
    lines.append("")
    for item in result.not_checked:
        lines.append(f"- {item}")
    lines.append("")
    lines.append(_DETAILS_CLOSE)

    return "\n".join(lines)


def _summary_checks_table(result: ScanResult) -> list[str]:
    if not result.check_summaries:
        return []
    lines = [
        "<details open><summary>Check modules</summary>",
        "",
        "| Module | Status | Rules passed | Findings |",
        "|--------|--------|--------------|----------|",
    ]
    for c in result.check_summaries:
        status = "passed" if c.passed else "failed"
        rule_progress = f"{c.passed_rule_count}/{c.total_rule_count}"
        lines.append(f"| {c.name} | {status} | {rule_progress} | {c.finding_count} |")
    lines.append("")
    lines.append(_DETAILS_CLOSE)
    lines.append("")
    return lines


def _summary_rules_table(result: ScanResult) -> list[str]:
    """Per-rule pass/fail drill-down, collapsed by default."""
    if not result.check_summaries:
        return []
    lines = [
        "<details><summary>ANDI rules (per-rule pass/fail)</summary>",
        "",
        "| Module | Rule | Status | Section 508 / WCAG | Findings |",
        "|--------|------|--------|-------------------|----------|",
    ]
    for c in result.check_summaries:
        for r in c.rules:
            status = "passed" if r.passed else "failed"
            wcag = format_wcag_linked(r.id)
            lines.append(f"| {c.name} | `{r.id}` | {status} | {wcag} | {r.finding_count} |")
    lines.append("")
    lines.append(_DETAILS_CLOSE)
    lines.append("")
    return lines


def _summary_findings(result: ScanResult) -> list[str]:
    if not result.findings:
        return ["No findings.", ""]

    by_file: dict[str, list[Finding]] = {}
    for f in result.findings:
        by_file.setdefault(f.file_path, []).append(f)

    lines: list[str] = []
    for file_path, findings in sorted(by_file.items()):
        lines.append(
            f"<details><summary><code>{file_path}</code> ({len(findings)} finding(s))</summary>"
        )
        lines.append("")
        lines.append("| Line | Severity | Check | Section 508 / WCAG | Message |")
        lines.append("|------|----------|-------|-------------------|---------|")
        for f in sorted(findings, key=lambda x: x.line):
            sev = _severity_emoji(f.severity)
            wcag = format_wcag_linked(f.check_id)
            lines.append(f"| {f.line} | {sev} | `{f.check_id}` | {wcag} | {f.message} |")
        lines.append("")
        lines.append(_DETAILS_CLOSE)
        lines.append("")
    return lines


def _format_508(check_id: str) -> str:
    """Format Section 508 reference for JSON output."""
    return format_508_ref(check_id)


def _severity_marker(severity: Severity) -> str:
    return {
        Severity.ERROR: "ERROR",
        Severity.WARNING: "WARN ",
        Severity.INFO: "INFO ",
    }[severity]


def _severity_emoji(severity: Severity) -> str:
    return {
        Severity.ERROR: "error",
        Severity.WARNING: "warning",
        Severity.INFO: "info",
    }[severity]
