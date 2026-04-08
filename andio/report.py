"""Output formatters for ANDIO scan results."""

from __future__ import annotations

import json

from andio.models import Finding, ScanResult, Severity
from andio.wcag import format_508_ref, format_wcag_short


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
    lines.append(f"ANDIO scan complete: {len(result.files_scanned)} file(s) scanned")
    lines.append(
        f"  {result.error_count} error(s), "
        f"{result.warning_count} warning(s), "
        f"{result.info_count} info"
    )
    lines.append("")

    if result.findings:
        # Group by file
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
    else:
        lines.append("No findings.")
        lines.append("")

    lines.append("=== Not checked by ANDIO (requires live browser) ===")
    for item in result.not_checked:
        lines.append(f"  - {item}")

    return "\n".join(lines)


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
                "section_508": _format_508(f.check_id),
            }
            for f in result.findings
        ],
        "summary": {
            "files_scanned": len(result.files_scanned),
            "errors": result.error_count,
            "warnings": result.warning_count,
            "info": result.info_count,
        },
        "checks_run": result.checks_run,
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
        f"**{result.info_count}** info"
    )
    lines.append("")

    if result.findings:
        # Group by file
        by_file: dict[str, list[Finding]] = {}
        for f in result.findings:
            by_file.setdefault(f.file_path, []).append(f)

        for file_path, findings in sorted(by_file.items()):
            lines.append(f"<details><summary><code>{file_path}</code> ({len(findings)} finding(s))</summary>")
            lines.append("")
            lines.append("| Line | Severity | Check | Section 508 / WCAG | Message |")
            lines.append("|------|----------|-------|-------------------|---------|")
            for f in sorted(findings, key=lambda x: x.line):
                sev = _severity_emoji(f.severity)
                wcag = format_wcag_short(f.check_id)
                lines.append(f"| {f.line} | {sev} | `{f.check_id}` | {wcag} | {f.message} |")
            lines.append("")
            lines.append("</details>")
            lines.append("")
    else:
        lines.append("No findings.")
        lines.append("")

    lines.append("<details><summary>Not checked by ANDIO (requires live browser)</summary>")
    lines.append("")
    for item in result.not_checked:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("</details>")

    return "\n".join(lines)


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
