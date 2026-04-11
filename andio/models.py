"""Core data models for ANDIO findings and scan results."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    """Finding severity levels, mapped from ANDI alert levels."""

    ERROR = "error"      # ANDI "danger" — fails the CI check
    WARNING = "warning"  # ANDI "warning" — GitHub annotation, no failure
    INFO = "info"        # ANDI "caution" — summary only


# Sentinel value used to mark template variable placeholders after stripping.
TEMPLATE_SENTINEL = "__ANDIO_TMPL__"


@dataclass
class Finding:
    """A single accessibility issue detected by a check."""

    check_id: str        # ANDI alert ID, e.g. "ANDI-0031"
    severity: Severity
    message: str
    file_path: str
    line: int
    column: int = 0
    element: str = ""    # HTML snippet of the offending element

    @property
    def is_error(self) -> bool:
        return self.severity is Severity.ERROR


@dataclass
class CheckSummary:
    """Per-check-module rollup: how many findings a given module produced."""

    id: str           # module id, e.g. "links"
    name: str         # human-readable, e.g. "Links / Buttons"
    finding_count: int

    @property
    def passed(self) -> bool:
        return self.finding_count == 0


@dataclass
class ScanResult:
    """Aggregated results from a full scan."""

    findings: list[Finding] = field(default_factory=list)
    files_scanned: list[str] = field(default_factory=list)
    checks_run: list[str] = field(default_factory=list)
    check_summaries: list[CheckSummary] = field(default_factory=list)
    not_checked: list[str] = field(default_factory=list)
    template_variable_count: int = 0

    @property
    def passed_check_count(self) -> int:
        return sum(1 for c in self.check_summaries if c.passed)

    @property
    def total_check_count(self) -> int:
        return len(self.check_summaries)

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity is Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity is Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity is Severity.INFO)

    @property
    def has_errors(self) -> bool:
        return self.error_count > 0
