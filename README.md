# ANDIO

**Accessible Name and Description Inspector Offline**

A standalone, static accessibility scanner ported from the SSA's [ANDI bookmarklet](https://www.ssa.gov/accessibility/andi/help/). ANDIO runs in CI against HTML templates and CSS files without requiring a live browser or authenticated session.

## What it does

ANDIO is a **shift-left filter** for Section 508 / WCAG compliance. It catches accessibility issues at the PR stage so that UAT testers using the real ANDI bookmarklet can focus on what only a live browser can find.

- **48 checks** across 6 modules (focusable elements, graphics, links, structures, hidden content, global)
- **79 ANDI rules** that axe-core does not cover
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

```yaml
# .github/workflows/ci-accessibility.yml
- run: pip install andio
- run: andio scan path/to/templates/ --format github-summary >> $GITHUB_STEP_SUMMARY
```

Exit code 1 if any **error**-severity findings exist, 0 otherwise.

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

| Level | ANDI equivalent | CI behavior |
|-------|----------------|-------------|
| error | danger | Fails the check (exit code 1) |
| warning | warning | Reported, no failure |
| info | caution | Summary only |

## What ANDIO does not check

Every report includes a "not checked" section:

- Color contrast (requires computed styles)
- Tab order / keyboard navigation (requires live browser)
- Fake heading detection (requires computed font sizes)
- Screen reader name computation (requires full DOM)
- Template variable content (flagged for review, not evaluated)

## Output Formats

- **text** (default) — human-readable grouped by file
- **json** — structured output for tooling integration
- **github-summary** — Markdown for GitHub Step Summary

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Relationship to ANDI

ANDIO complements the SSA's ANDI bookmarklet. It does not replace it. ANDI requires a live browser and tests things ANDIO cannot (contrast, tab order, screen reader output). ANDIO catches the things that don't need a browser, earlier in the development cycle.

See [docs/andio-gap-analysis.md](docs/andio-gap-analysis.md) for the full mapping of ANDI's 114 alerts to ANDIO's coverage.

## License

MIT
