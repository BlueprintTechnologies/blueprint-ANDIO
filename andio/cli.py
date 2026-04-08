"""CLI entry point for ANDIO."""

from __future__ import annotations

import sys

import click

from andio import __version__
from andio.scanner import scan


@click.group()
@click.version_option(version=__version__, prog_name="andio")
def main():
    """ANDIO — Accessible Name and Description Inspector Offline.

    Static 508/WCAG accessibility scanner for HTML templates and CSS files.
    """


@main.command("scan")
@click.argument("paths", nargs=-1, required=True)
@click.option(
    "--format", "output_format",
    type=click.Choice(["text", "json", "github-summary"]),
    default="text",
    help="Output format.",
)
@click.option(
    "--checks",
    default=None,
    help="Comma-separated list of check modules to run (e.g. focusable,links,global).",
)
def scan_cmd(paths, output_format, checks):
    """Scan HTML/CSS files for accessibility issues.

    PATHS can be files, directories, or glob patterns.
    """
    check_names = [c.strip() for c in checks.split(",")] if checks else None
    result = scan(list(paths), check_names=check_names)

    # Phase 3 will wire up formatters. Stub output for now.
    from andio.report import format_output
    output = format_output(result, output_format)
    click.echo(output)

    sys.exit(1 if result.has_errors else 0)
