# ANDIO

**Accessible Name and Description Inspector Offline**

A standalone, static accessibility scanner ported from the SSA's [ANDI bookmarklet](https://www.ssa.gov/accessibility/andi/help/). ANDIO runs in CI against HTML templates and CSS files without requiring a live browser or authenticated session.

## What it does

ANDIO is a **shift-left filter** for Section 508 / WCAG compliance. It catches accessibility issues at the PR stage so that UAT testers using the real ANDI bookmarklet can focus on what only a live browser can find.

- **48 checks** across 6 modules (focusable elements, graphics, links, structures, hidden content, global)
- **79 ANDI rules** that axe-core does not cover
- **WCAG traceability** — every finding maps to specific WCAG success criteria with links to W3C docs
- **508 Compliance gate** — PR comments with pass/fail status, inline annotations, and step summaries
- **Template-aware** — strips Jinja2, ERB, and Handlebars syntax before parsing
- **No false confidence** — explicitly lists what it cannot check

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Scan HTML templates
andio scan templates/

# Scan with specific output format
andio scan templates/ --format json
andio scan templates/ --format github-summary >> $GITHUB_STEP_SUMMARY

# Scan specific check modules only
andio scan templates/ --checks focusable,links,global

# Scan files directly
andio scan index.html styles.css
```

## CI Integration

### GitHub Action (recommended)

Add ANDIO as a step in your workflow. It posts a 508 Compliance status comment on the PR with findings detail, adds inline annotations on changed files, and writes a step summary.

```yaml
# .github/workflows/ci-accessibility.yml
name: CI — Accessibility (ANDIO)
on:
  pull_request:
    paths:
      - 'app/templates/**'

permissions:
  contents: read
  pull-requests: write

jobs:
  andio:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: BlueprintTechnologies/blueprint-ANDIO@main
        with:
          paths: app/templates/
```

**Action inputs:**

| Input | Default | Description |
|-------|---------|-------------|
| `paths` | *(required)* | Space-separated files or directories to scan |
| `checks` | all | Comma-separated check modules to run |
| `fail-on-error` | `false` | Set to `true` to fail the workflow on errors |
| `python-version` | `3.11` | Python version to use |

By default ANDIO is **visibility-only** — it reports findings but does not block the PR.

### pip install (alternative)

```bash
pip install git+https://github.com/BlueprintTechnologies/blueprint-ANDIO.git
andio scan path/to/templates/ --format github-summary >> $GITHUB_STEP_SUMMARY
```

## Check Modules

| Module | Checks | What it catches |
|--------|--------|----------------|
| `global` | 24 | ARIA refs, label misuse, deprecated HTML, orphan elements, JS events |
| `focusable` | 9 | Missing accessible names, duplicate accesskeys, negative tabindex |
| `links` | 6 | Vague link text, ambiguous links, broken anchors, missing href |
| `structures` | 7 | Live region issues, heading conflicts, figure names, list containers |
| `graphics` | 3 | Alt text quality (redundant phrases, file names, non-descriptive) |
| `hidden` | 1 | CSS pseudo-element content injection (::before/::after) |

## Severity Levels

| Level | ANDI equivalent | CI behavior | Example |
|-------|----------------|-------------|---------|
| error | danger | Reported (fails if `fail-on-error: true`) | Missing accessible name, misspelled ARIA |
| warning | warning | Reported, no failure | Vague link text, deprecated HTML |
| info | caution | Summary only | Small clickable area, legend verbosity |

## What ANDIO does not check

Every report includes a "not checked" section:

- Color contrast (requires computed styles)
- Tab order / keyboard navigation (requires live browser)
- Fake heading detection (requires computed font sizes)
- Screen reader name computation (requires full DOM)
- Template variable content (flagged for review, not evaluated)

## Output Formats

- **text** (default) — human-readable, grouped by file, with WCAG references
- **json** — structured output with `wcag`, `wcag_linked`, and `section_508` fields per finding
- **github-summary** — Markdown with clickable WCAG links for GitHub Step Summary

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Relationship to ANDI

ANDIO complements the SSA's ANDI bookmarklet. It does not replace it. ANDI requires a live browser and tests things ANDIO cannot (contrast, tab order, screen reader output). ANDIO catches the things that don't need a browser, earlier in the development cycle.

See [docs/andio-gap-analysis.md](docs/andio-gap-analysis.md) for the full mapping of ANDI's 114 alerts to ANDIO's coverage.

## License

Apache 2.0 — derivative work based on [SSA's ANDI](https://github.com/SSAgov/ANDI), also Apache 2.0. See [NOTICE](NOTICE) for attribution.
