# ANDIO Gap Analysis

**ANDIO** — Accessible Name and Description Inspector Offline

A standalone, static accessibility scanner ported from the SSA's [ANDI bookmarklet](https://www.ssa.gov/accessibility/andi/help/), designed to run in CI (GitHub Actions, pre-commit hooks) against HTML templates and CSS source files without requiring a live browser or authenticated session.

## Design philosophy

- **Shift-left filter, not a replacement for ANDI.** ANDIO catches what it can at the PR stage so that UAT testers using the real ANDI bookmarklet spend their time on things only a live browser can find — not missing alt text or misspelled ARIA attributes.
- **No false confidence.** If ANDIO cannot definitively check something (computed contrast, inherited styles, tab order), it either flags it for manual review or omits it entirely. ANDIO never reports "accessible" when it means "I couldn't tell."
- **Explicit coverage boundaries.** Every ANDIO report includes a "not checked" section listing the categories that require live-browser testing, so UAT testers know exactly what still needs manual attention.
- **Standalone tool.** Configurable inputs (file paths, file types, check selection). Any team with HTML templates can use it — not hardwired to a specific project.

## Design decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Color contrast | **Out of v1** | Static CSS analysis produces too many false negatives — can't resolve inheritance, cascade, or runtime styles. Contrast stays in ANDI-in-browser territory. |
| Jinja2 template variables | **Flag for review** | When an element's accessible name is entirely `{{ variable }}`, ANDIO emits a warning: "accessible name is a template variable — verify at runtime." Not an error, not a pass. |
| SAT dashboard JSON | **Out of v1** | Lakeview dashboard definitions are a JSON spec, not HTML. Scanning them for 508 compliance is a different problem — defer to a future version. |
| Standalone vs coupled | **Standalone** | ANDIO lives in its own repo (blueprint-ANDIO) and is consumed as a dependency or CLI tool, not embedded in any single project. |
| Relationship to ANDI | **Complement** | ANDIO shortens UAT by catching static issues early. It does not replace the need for ANDI bookmarklet testing during user acceptance. |

## v1 vs v2 check allocation

Checks are tiered based on what shows up most in real-world Flask/Jinja2 templates:

| Version | Categories | Rationale |
|---------|-----------|-----------|
| **v1** | Accessible names, ARIA validity, link quality, reference integrity, structural orphans, deprecated HTML | Common in any HTML template |
| **v2** | Deep table analysis, font icon detection, image map validation, ARIA grid roles | Deferred until a consumer has these elements |

## Methodology

ANDI defines **114 alerts** across 8 modules. Each alert is classified below by:

1. **Static feasibility** — can it be checked against source HTML/CSS without rendering?
2. **axe-core coverage** — does axe-core already check this?
3. **ANDIO priority** — should we port it?

### Classification key

| Tag | Meaning |
|-----|---------|
| **STATIC** | Can be checked against raw HTML/Jinja2 templates |
| **CSS-STATIC** | Can be checked by parsing CSS source (custom properties, declared values) |
| **NEEDS-DOM** | Requires rendered DOM / computed styles — out of scope for ANDIO |
| **AXE-COVERED** | axe-core has an equivalent rule |
| **ANDI-UNIQUE** | No axe-core equivalent — candidate for ANDIO porting |
| **PORT** | Recommended for ANDIO implementation |

---

## Module-by-module analysis

### 1. Focusable Elements (fANDI) — 12 alerts

| Alert | Description | Static? | axe-core? | ANDIO? |
|-------|-------------|---------|-----------|--------|
| 0001 | Form element has no accessible name, label, or title | STATIC | `label`, `aria-input-field-name` — AXE-COVERED | Skip |
| 0002 | Generic element has no accessible name, innerText, or title | STATIC | `button-name`, `link-name` — partial | **PORT** |
| 0008 | Focusable element has no accessible name | STATIC | partial coverage | **PORT** |
| 0052 | accessKey value has more than one character | STATIC | — ANDI-UNIQUE | **PORT** |
| 0054 | Duplicate accessKey on button | STATIC | — ANDI-UNIQUE | **PORT** |
| 0055 | Duplicate accessKey (generic) | STATIC | — ANDI-UNIQUE | **PORT** |
| 0056 | Duplicate accessKey on link | STATIC | — ANDI-UNIQUE | **PORT** |
| 0121 | Focusable element not in tab order (negative tabindex) | STATIC | — ANDI-UNIQUE | **PORT** |
| 0122 | Focusable element not in tab order and no accessible name | STATIC | — ANDI-UNIQUE | **PORT** |
| 0123 | Iframe not in tab order (negative tabindex) | STATIC | — ANDI-UNIQUE | **PORT** |
| 0124 | Canvas with no focusable fallback | STATIC | — ANDI-UNIQUE | **PORT** |
| 0127 | Canvas has focusable fallback — test keyboard equivalency | STATIC | — ANDI-UNIQUE | Skip (manual) |

### 2. Graphics / Images (gANDI) — 14 alerts

| Alert | Description | Static? | axe-core? | ANDIO? |
|-------|-------------|---------|-----------|--------|
| 0003 | Image has no accessible name, alt, or title | STATIC | `image-alt` — AXE-COVERED | Skip |
| 006A | Image map references missing img | STATIC | — ANDI-UNIQUE | **PORT** |
| 0126 | Decorative image in tab order | STATIC | — ANDI-UNIQUE | **PORT** |
| 0134 | `role=image` invalid, should be `role=img` | STATIC | `aria-roles` — AXE-COVERED | Skip |
| 0171 | `<marquee>` element found | STATIC | `marquee` — AXE-COVERED | Skip |
| 0172 | `<blink>` element found | STATIC | `blink` — AXE-COVERED | Skip |
| 0173 | Server-side image map (ismap) | STATIC | `server-side-image-map` — AXE-COVERED | Skip |
| 0174 | Redundant phrase in alt text ("image of...") | STATIC | — ANDI-UNIQUE | **PORT** |
| 0175 | Alt text contains file name | STATIC | — ANDI-UNIQUE | **PORT** |
| 0176 | Alt text is not descriptive ("image", "photo") | STATIC | — ANDI-UNIQUE | **PORT** |
| 0177 | Background images — ensure decorative | CSS-STATIC | — ANDI-UNIQUE | **PORT** |
| 0178 | `<area>` not in `<map>` | STATIC | `area-alt` — partial | **PORT** |
| 0179 | Font icon without `role=img` | STATIC | — ANDI-UNIQUE | **PORT** |
| 017A | Font icon — is this meaningful? | STATIC | — ANDI-UNIQUE | **PORT** |

### 3. Links / Buttons (lANDI) — 11 alerts

| Alert | Description | Static? | axe-core? | ANDIO? |
|-------|-------------|---------|-----------|--------|
| 0069 | In-page anchor target not found | STATIC | — ANDI-UNIQUE | **PORT** |
| 007B | Deprecated `<a name="">` attribute | STATIC | — ANDI-UNIQUE | **PORT** |
| 0125 | Interactive role not in tab order | STATIC | — ANDI-UNIQUE | **PORT** |
| 0128 | `<a>` without href, id, or tabindex | STATIC | — ANDI-UNIQUE | **PORT** |
| 0129 | `<a>` without href or tabindex (caution) | STATIC | — ANDI-UNIQUE | Skip (0128 covers) |
| 012A | Anchor target may not receive focus indication | NEEDS-DOM | — | Skip |
| 0161 | Ambiguous link: same text, different href | STATIC | `identical-links-same-purpose` — partial | **PORT** |
| 0162 | Ambiguous internal link | STATIC | — partial | Skip (0161 covers) |
| 0163 | Vague link text ("click here", "more") | STATIC | `link-name` — partial | **PORT** |
| 0164 | Link has click event but no keyboard access | STATIC | — ANDI-UNIQUE | **PORT** |
| 0168 | `<a>` without href may not be recognized as link | STATIC | — ANDI-UNIQUE | **PORT** |

### 4. Tables (tANDI) — 27 alerts

| Alert | Description | Static? | axe-core? | ANDIO? |
|-------|-------------|---------|-----------|--------|
| 0004 | Table has no accessible name, caption, or title | STATIC | `table-fake-caption` — partial | **PORT** |
| 0005 | Figure has no accessible name or figcaption | STATIC | — ANDI-UNIQUE | **PORT** |
| 0011 | Duplicate element IDs | STATIC | `duplicate-id` — AXE-COVERED | Skip |
| 0041 | Presentation table has data table markup | STATIC | — ANDI-UNIQUE | **PORT** |
| 0043 | Too many scope nesting levels | STATIC | — ANDI-UNIQUE | **PORT** |
| 0045 | `[headers]` on non-th/td element | STATIC | `td-headers-attr` — AXE-COVERED | Skip |
| 0046 | Data table has no `<th>` cells | STATIC | `th-has-data-cells` — AXE-COVERED | Skip |
| 0047 | Scope needed at th intersection | STATIC | — ANDI-UNIQUE | **PORT** |
| 0048 | Table has no scope associations | STATIC | — ANDI-UNIQUE | **PORT** |
| 0049 | Mixed scope and headers — screen reader issues | STATIC | — ANDI-UNIQUE | **PORT** |
| 004A | Table has no headers/id associations | STATIC | `td-has-header` — partial | Skip |
| 004B | Table mode recommendation (scope) | STATIC | — ANDI-UNIQUE | Skip (informational) |
| 004C | Table mode recommendation (headers) | STATIC | — ANDI-UNIQUE | Skip (informational) |
| 004E | Table has no th or td cells | STATIC | — ANDI-UNIQUE | **PORT** |
| 004F | ARIA table/grid missing cell roles | STATIC | `aria-required-children` — partial | **PORT** |
| 004G | ARIA grid missing header roles | STATIC | — ANDI-UNIQUE | **PORT** |
| 004H | ARIA grid missing row role | STATIC | — ANDI-UNIQUE | **PORT** |
| 004I | Table with non-standard role | STATIC | — ANDI-UNIQUE | **PORT** |
| 004J | ARIA table header cells missing roles | STATIC | — ANDI-UNIQUE | **PORT** |
| 004K | ARIA table cells not in role=row | STATIC | — ANDI-UNIQUE | **PORT** |
| 0062 | Headers references element outside table | STATIC | — ANDI-UNIQUE | **PORT** |
| 0066 | Headers references non-th element | STATIC | `td-headers-attr` — partial | **PORT** |
| 0067 | Headers references td instead of th | STATIC | — ANDI-UNIQUE | **PORT** |
| 0068 | Headers references provide no text | STATIC | — ANDI-UNIQUE | **PORT** |
| 007C | Invalid scope value | STATIC | — ANDI-UNIQUE | **PORT** |
| 0132 | Empty header cell | STATIC | `empty-table-header` — AXE-COVERED | Skip |
| 0233 | ARIA grid — test navigation | STATIC | — ANDI-UNIQUE | Skip (manual) |

### 5. Structures / Headings (sANDI) — 10 alerts

| Alert | Description | Static? | axe-core? | ANDIO? |
|-------|-------------|---------|-----------|--------|
| 0079 | List item not in list container | STATIC | `listitem` — AXE-COVERED | Skip |
| 007A | Description list item not in `<dl>` | STATIC | `dlitem` — AXE-COVERED | Skip |
| 0133 | Live region has no innerText | STATIC | — ANDI-UNIQUE | **PORT** |
| 0182 | Live region contains form element | STATIC | — ANDI-UNIQUE | **PORT** |
| 0184 | Live region on non-container element | STATIC | — ANDI-UNIQUE | **PORT** |
| 0190 | Fake heading (styled div, not semantic) | NEEDS-DOM | — ANDI-UNIQUE | Skip |
| 0191 | Heading level conflicts with aria-level | STATIC | — ANDI-UNIQUE | **PORT** |
| 0192 | `role=heading` without aria-level | STATIC | — ANDI-UNIQUE | **PORT** |
| 0193 | Invalid aria-level value | STATIC | `aria-valid-attr-value` — AXE-COVERED | Skip |
| 0194 | List item container has invalid role | STATIC | — ANDI-UNIQUE | **PORT** |

### 6. Color Contrast (cANDI) — 5 alerts

| Alert | Description | Static? | axe-core? | ANDIO? |
|-------|-------------|---------|-----------|--------|
| 0230 | Element has background-image — manual contrast test | CSS-STATIC | — ANDI-UNIQUE | Skip (v1 — contrast out of scope) |
| 0231 | Page has images with possible text | STATIC | — ANDI-UNIQUE | Skip (manual) |
| 0232 | Opacity < 100% — manual contrast test | CSS-STATIC | — ANDI-UNIQUE | Skip (v1 — contrast out of scope) |
| 0240 | Insufficient contrast ratio | CSS-STATIC | `color-contrast` — partial | Skip (v1 — contrast out of scope) |
| 0251 | Disabled elements — contrast exempt | CSS-STATIC | — ANDI-UNIQUE | Skip (informational) |

> **Contrast is out of v1 scope.** Static CSS analysis cannot reliably resolve color inheritance, cascade, or runtime styles. The false-negative rate would give users false confidence that their colors are compliant. Contrast testing stays in ANDI-in-browser territory during UAT.

### 7. Hidden Content (hANDI) — 1 alert

| Alert | Description | Static? | axe-core? | ANDIO? |
|-------|-------------|---------|-----------|--------|
| 0220 | CSS pseudo-element content (::before/::after) | CSS-STATIC | — ANDI-UNIQUE | **PORT** |

### 8. iFrames (iANDI) — 2 alerts

| Alert | Description | Static? | axe-core? | ANDIO? |
|-------|-------------|---------|-----------|--------|
| 0007 | Iframe has no accessible name or title (danger) | STATIC | `frame-title` — AXE-COVERED | Skip |
| 0009 | Iframe has no accessible name or title (warning) | STATIC | `frame-title` — AXE-COVERED | Skip |

### 9. Global / Cross-module (Main) — 30 alerts

| Alert | Description | Static? | axe-core? | ANDIO? |
|-------|-------------|---------|-----------|--------|
| 0012 | Multiple labels with same `for` attribute | STATIC | — ANDI-UNIQUE | **PORT** |
| 0021 | aria-describedby used alone | STATIC | — ANDI-UNIQUE | **PORT** |
| 0022 | legend used alone | STATIC | — ANDI-UNIQUE | **PORT** |
| 0031 | `aria-labeledby` misspelled | STATIC | — ANDI-UNIQUE | **PORT** |
| 0032 | Unsupported role value | STATIC | `aria-roles` — AXE-COVERED | Skip |
| 0033 | Multiple roles on element | STATIC | — ANDI-UNIQUE | **PORT** |
| 0063 | Referenced ID not found | STATIC | `aria-valid-attr-value` — partial | **PORT** |
| 0065 | Referenced IDs not found (danger) | STATIC | — ANDI-UNIQUE | **PORT** |
| 006B | Reference points to legend (verbosity) | STATIC | — ANDI-UNIQUE | **PORT** |
| 006C | Nested references | STATIC | — ANDI-UNIQUE | **PORT** |
| 006D | Duplicate reference to same ID | STATIC | — ANDI-UNIQUE | **PORT** |
| 006E | Direct and indirect reference to same ID | STATIC | — ANDI-UNIQUE | **PORT** |
| 006F | Nested label mismatch | STATIC | — ANDI-UNIQUE | **PORT** |
| 0071 | Empty page title | STATIC | `document-title` — AXE-COVERED | Skip |
| 0072 | No page title | STATIC | `document-title` — AXE-COVERED | Skip |
| 0073 | Multiple title tags | STATIC | — ANDI-UNIQUE | **PORT** |
| 0074 | More legends than fieldsets | STATIC | — ANDI-UNIQUE | **PORT** |
| 0075 | More figcaptions than figures | STATIC | — ANDI-UNIQUE | **PORT** |
| 0076 | More captions than tables | STATIC | — ANDI-UNIQUE | **PORT** |
| 0077 | Tabindex is not a number | STATIC | `tabindex` — AXE-COVERED | Skip |
| 0078 | Deprecated HTML5 attributes | STATIC | — ANDI-UNIQUE | **PORT** |
| 0081 | Alt attribute on non-image element | STATIC | — ANDI-UNIQUE | **PORT** |
| 0091 | Label `for` on non-form element | STATIC | — ANDI-UNIQUE | **PORT** |
| 0101 | Unreliable component combinations | STATIC | — ANDI-UNIQUE | **PORT** |
| 0112 | JS event may cause keyboard issues | STATIC | — ANDI-UNIQUE | **PORT** |
| 0142 | Presentational image alt not used | STATIC | — ANDI-UNIQUE | Skip (informational) |
| 0151 | Attribute text too long (>250 chars) | STATIC | — ANDI-UNIQUE | **PORT** |
| 0200 | Non-unique button text | STATIC | — ANDI-UNIQUE | **PORT** |
| 0210 | Small clickable area — add label | STATIC | — ANDI-UNIQUE | **PORT** |
| 0260 | Focusable element in aria-hidden=true | STATIC | `aria-hidden-focus` — AXE-COVERED | Skip |
| 0261 | Non-focusable element has aria-hidden=true | STATIC | — ANDI-UNIQUE | Skip (informational) |

---

## Summary

| Category | Count |
|----------|-------|
| Total ANDI alerts | 114 |
| Skipped (axe-core covers) | 24 |
| Skipped (needs live DOM) | 2 |
| Skipped (contrast — out of v1) | 3 |
| Skipped (manual/informational only) | 9 |
| **Ported to ANDIO (total)** | **76** |
| v1 checks | 48 |
| v2 checks (deferred) | 28 |

### v1 checks — 48 ANDI-unique rules

| Category | Count | Highlights |
|----------|-------|------------|
| Accessible names | 2 | Generic/focusable elements missing names |
| AccessKey validation | 4 | Duplicate detection, multi-char values |
| Alt text quality | 3 | Filename detection, redundant phrases, non-descriptive text |
| Link quality | 5 | Vague text, ambiguous links, missing href |
| Reference integrity | 7 | Nested refs, legend verbosity, label mismatches |
| ARIA edge cases | 5 | Misspellings, multiple roles, unreliable combos |
| Live region validation | 3 | Forms in live regions, empty content, non-container |
| Structural orphans | 3 | Orphaned legends, figcaptions, captions |
| Heading conflicts | 2 | aria-level mismatches, role=heading without level |
| Deprecated HTML | 2 | HTML5 deprecated attrs, anchor name attr |
| Component quality | 4 | Long attributes, non-unique buttons, small click areas, JS events |
| CSS content injection | 1 | Pseudo-element content detection |
| Negative tabindex | 3 | Focusable elements/iframes removed from tab order |
| Label misuse | 2 | Label for non-form elements, multiple labels same for |
| List container roles | 1 | List items in containers with invalid role |
| Figure naming | 1 | Figures without figcaption or accessible name |

### v2 checks — 28 rules (deferred)

| Category | Count | Rationale for deferral |
|----------|-------|----------------------|
| Table deep analysis | 14 | Scope/headers validation, ARIA grid roles — deferred until consumer has tables |
| Font icon detection | 2 | Missing role=img on icon fonts — niche |
| Image map validation | 3 | area/map associations, decorative image in tab order — niche |
| Table accessible names | 1 | Table without caption/title |
| Presentation table conflicts | 1 | Presentation role with data markup |
| Table scope nesting | 1 | Excessive scope levels |
| Canvas fallback | 1 | Canvas without focusable fallback |
| Interactive role tab order | 1 | role=button/link not keyboard accessible |
| Background image flags | 1 | CSS background-image on elements |
| Table naming | 1 | Tables with non-standard roles |
| Table empty structure | 1 | Tables with no th/td cells |
| Link click-only access | 1 | Links with onclick but no keyboard handler |

### What ANDIO does not check (deferred to ANDI UAT)

These categories are listed in every ANDIO report so UAT testers know what still needs manual attention:

- **Color contrast** — requires CSS cascade resolution and computed styles
- **Tab order / keyboard navigation** — requires live focus traversal
- **Fake heading detection** — requires computed font-size comparison against surrounding text
- **Screen reader output simulation** — requires accessible name computation with full DOM
- **Dynamic content** — Jinja2 template variables flagged for review but not evaluated

This is by design. ANDIO is a shift-left filter that shortens UAT — it does not replace ANDI.

---

## Implementation approach

### Language: Python

Widely used in web development CI pipelines. Minimal dependencies.

### Architecture

```
andio/
├── __init__.py
├── cli.py              # CLI entry point — andio scan <paths> [--format] [--checks]
├── scanner.py          # Core engine — accepts file paths, returns findings
├── html_parser.py      # BeautifulSoup-based HTML parser with Jinja2 stripping
├── css_parser.py       # CSS rule parser (pseudo-elements, background-image detection)
├── checks/
│   ├── __init__.py
│   ├── focusable.py    # Accessible names, accesskey, negative tabindex
│   ├── graphics.py     # Alt text quality, font icons, image maps (v2)
│   ├── links.py        # Vague text, ambiguous links, missing href
│   ├── structures.py   # Live regions, heading conflicts, list containers
│   ├── tables.py       # Scope/headers deep analysis (v2)
│   ├── hidden.py       # Pseudo-element content detection
│   └── global_checks.py # Refs, orphans, deprecated HTML, ARIA, labels
├── report.py           # Output formatter (text, JSON, SARIF, GitHub annotations)
├── not_checked.py      # Generates "not checked" section for reports
tests/
├── fixtures/           # HTML test files with known violations
└── ...                 # pytest
pyproject.toml
```

### CLI usage

```bash
# Scan HTML templates
andio scan templates/ --format text

# Scan with specific check modules only
andio scan templates/ --checks focusable,links,global

# Output for CI (GitHub Step Summary)
andio scan templates/ --format github-summary >> $GITHUB_STEP_SUMMARY

# JSON output for tooling integration
andio scan templates/ --format json > andio-results.json
```

### CI integration (consumer example)

```yaml
# In any repo that consumes ANDIO
- run: pip install andio
- run: andio scan path/to/templates/ --format github-summary >> $GITHUB_STEP_SUMMARY
```

### Severity mapping

| ANDI level | ANDIO level | CI behavior |
|------------|-------------|-------------|
| danger | error | Fail the check (exit code 1) |
| warning | warning | GitHub annotation, no failure |
| caution | info | Summary only |

### Template engine handling

ANDIO strips template syntax before parsing to avoid false positives on dynamic content. Supported engines:

| Engine | Syntax stripped | Example |
|--------|----------------|---------|
| Jinja2 | `{{ }}`, `{% %}`, `{# #}` | Flask, Django |
| ERB | `<%= %>`, `<% %>` | Rails |
| Handlebars | `{{ }}`, `{{# }}` | Express |

When an element's accessible name is *entirely* a template variable (e.g., `<img alt="{{ img.alt }}">`), ANDIO emits a warning: **"accessible name is a template variable — verify at runtime."** Not an error, not a pass.

### Report "not checked" section

Every ANDIO report ends with a section listing what was NOT checked, so downstream testers know exactly what manual ANDI testing must still cover:

```
=== Not checked by ANDIO (requires live browser) ===
- Color contrast (WCAG 1.4.3, 1.4.11)
- Tab order and keyboard navigation (WCAG 2.1.1, 2.4.3)
- Fake heading detection (WCAG 1.3.1)
- Screen reader accessible name computation
- Dynamic/runtime content from template variables (N elements flagged for review)
```
