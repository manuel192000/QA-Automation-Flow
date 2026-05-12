"""
QA Report builder — Markdown output for Monday.com updates.

Templates follow the "QA Pass / Fail Report" convention:

    QA Pass Report – <Feature Title>
    Overview
    Test Environment (table)
    Test Cases Summary (table)
    Evidence – <files>
    Overall QA Result – PASS ✅ / FAIL ❌
    Conclusion

Outcome-driven:
- All tests passed   → QA Pass Report
- Any test failed    → QA Fail Report (adds Findings section)

Metadata is parsed from each test's docstring. Supported keys:
    Monday:           ticket ID or full URL
    Feature Area:     area under test (e.g. "Predictive Search / Header")
    Validation Type:  e.g. "UI Regression", "Functional Pricing Validation"
    Title:            optional override for the report headline

Example docstring:
    \"\"\"
    Monday: https://retailerwebservices.monday.com/boards/.../pulses/...
    Title: Predictive Search — Featured Brands as Pills
    Feature Area: Predictive Search / Header
    Validation Type: UI Regression
    Verifies that ...
    \"\"\"
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
VIDEOS_DIR = PROJECT_ROOT / "videos"
TRACES_DIR = PROJECT_ROOT / "traces"

# Keys supported in test docstrings
META_KEYS = ("monday", "title", "feature area", "validation type", "site")

# Keys that introduce multi-line blocks of free-form text
BLOCK_KEYS = ("overview", "summary")

# All known keys (used as block terminators when parsing one block)
ALL_KEYS = META_KEYS + BLOCK_KEYS + ("checks", "preconditions")


# ============================================================
# Helpers
# ============================================================

def _parse_meta(docstring: str) -> Dict[str, str]:
    """Parse 'Key: value' lines from a docstring into a dict (lowercase keys)."""
    out: Dict[str, str] = {}
    if not docstring:
        return out
    for line in docstring.splitlines():
        m = re.match(r"\s*([A-Za-z][A-Za-z ]*?):\s*(.+)\s*$", line)
        if not m:
            continue
        key = m.group(1).strip().lower()
        if key in META_KEYS:
            out[key] = m.group(2).strip()
    return out


def _description_from_doc(docstring: str) -> str:
    """First non-meta, non-empty line of the docstring (a one-line summary)."""
    if not docstring:
        return ""
    for line in docstring.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Skip bullet items (belong to Checks/Preconditions blocks)
        if re.match(r"^[-*•]\s+", stripped):
            continue
        # Skip meta lines like "Monday: ...", "Feature Area: ...", "Checks:"
        if re.match(r"[A-Za-z][A-Za-z ]*?:\s*", stripped):
            head = stripped.split(":", 1)[0].strip().lower()
            if head in META_KEYS or head in ("preconditions", "precondiciones", "checks"):
                continue
        return stripped
    return ""


def _parse_text_block(docstring: str, key: str) -> str:
    """
    Parse a multi-line text block from the docstring, like:

        Overview:
          The QA cycle validates ...
          Previously, ...

    Reads content from `Key:` until another known meta/block key starts a
    new section, then strips common leading indentation.
    """
    if not docstring:
        return ""
    lines = docstring.splitlines()
    in_block = False
    collected: List[str] = []
    for line in lines:
        if not in_block:
            m = re.match(rf"^\s*{re.escape(key)}:\s*(.*)$", line, flags=re.IGNORECASE)
            if m:
                in_block = True
                rest = m.group(1).rstrip()
                if rest.strip():
                    collected.append(rest)
            continue
        # in_block — check if another known key starts here. We match a key
        # whether it is followed by text on the same line ("Title: foo") or
        # introduces a multi-line block alone ("Checks:" then bullets below).
        stripped = line.strip()
        if stripped:
            head_match = re.match(r"^([A-Za-z][A-Za-z ]*?):(\s|$)", stripped)
            if head_match:
                head = head_match.group(1).strip().lower()
                if head in ALL_KEYS:
                    break
        collected.append(line)

    # Remove a trailing run of blank lines
    while collected and not collected[-1].strip():
        collected.pop()

    # Strip the smallest common leading indentation among non-blank lines
    non_blank = [l for l in collected if l.strip()]
    if non_blank:
        min_indent = min(len(l) - len(l.lstrip(" ")) for l in non_blank)
        collected = [l[min_indent:] if len(l) >= min_indent else l for l in collected]

    return "\n".join(collected).strip()


def _parse_checks(docstring: str) -> List[str]:
    """
    Extract the list of validation checks from a 'Checks:' block in the
    docstring. Each test can declare its individual validations so the
    report's Test Cases Summary expands into one row per check.

    Example block (4-space indented bullets work too):
        Checks:
          - AMANA brand is visible in the predictive panel
          - AMANA brand is rendered inside the "Brands" section
          - AMANA brand is rendered as a pill (rounded border-radius)
    """
    if not docstring:
        return []
    out: List[str] = []
    in_block = False
    for line in docstring.splitlines():
        stripped = line.strip()
        if not in_block:
            if stripped.lower().startswith("checks:"):
                in_block = True
                rest = stripped.split(":", 1)[1].strip()
                if rest:
                    out.append(rest)
            continue
        # in_block == True
        if not stripped:
            # Blank line ends the block only if we already collected items
            if out:
                break
            continue
        m = re.match(r"^[-*•]\s+(.+)$", stripped)
        if m:
            out.append(m.group(1).strip())
            continue
        # Another meta key (e.g. "Preconditions:") ends the block
        if re.match(r"^[A-Za-z][A-Za-z ]*?:\s*", stripped):
            break
    return out


def _humanize_test_name(name: str) -> str:
    """test_predictive_search_shows_amana → 'Predictive search shows amana'."""
    base = name.replace("test_", "", 1).replace("_", " ").strip()
    return base[:1].upper() + base[1:] if base else name


def _aggregate_meta(results: List[Dict]) -> Dict[str, str]:
    """Merge meta from all tests, first non-empty value wins per key."""
    merged: Dict[str, str] = {}
    for r in results:
        meta = _parse_meta(r.get("docstring", ""))
        for k, v in meta.items():
            merged.setdefault(k, v)
    return merged


# ============================================================
# Sections
# ============================================================

def _build_title(overall: str, meta: Dict[str, str], results: List[Dict]) -> str:
    label = "QA Pass Report" if overall == "PASS" else "QA Fail Report"
    title = meta.get("title")
    if not title:
        # Fallback: derive from the first test's first doc line, or its name
        if results:
            title = (
                _description_from_doc(results[0].get("docstring", ""))
                or _humanize_test_name(results[0]["name"])
            )
        else:
            title = "Automated Test Run"
    return f"# {label} – {title}\n"


def _build_overview(overall: str, results: List[Dict], meta: Dict[str, str], custom_overview: str) -> str:
    """
    If the test docstring includes an `Overview:` block, use it verbatim —
    that's the QA's own narrative and should win over any generated text.
    Otherwise fall back to a short generic paragraph (no mention of how
    the validation was carried out).
    """
    if custom_overview:
        return "## Overview\n\n" + custom_overview + "\n"

    total = len(results)
    passed = sum(1 for r in results if r["outcome"] == "passed")
    failed = sum(1 for r in results if r["outcome"] == "failed")
    feature = meta.get("feature area", "the feature under test")

    if overall == "PASS":
        body = (
            f"This QA cycle validates {feature}. "
            f"All **{total}** scenarios behaved according to the acceptance "
            "criteria, including boundary and negative cases where applicable."
        )
    else:
        body = (
            f"This QA cycle validates {feature}. "
            f"**{passed} of {total}** scenarios passed and **{failed}** failed. "
            "Defects were identified that block acceptance — see **Findings** "
            "for details, reproduction steps and captured evidence."
        )
    return "## Overview\n\n" + body + "\n"


def _build_environment(meta: Dict[str, str], results: List[Dict]) -> str:
    base_url = os.getenv("BASE_URL", "—")
    browsers = sorted({r.get("browser") for r in results if r.get("browser")})
    browser_line = ", ".join(b.capitalize() for b in browsers) if browsers else "Chrome"
    site = meta.get("site", "oneshop")
    feature = meta.get("feature area", "—")
    val_type = meta.get("validation type", "Functional Validation")

    lines = [
        "## Test Environment",
        "",
        "| Field | Details |",
        "|---|---|",
        f"| Environment | DEV - {base_url} |",
        f"| Site | {site} |",
        f"| Browser | {browser_line} |",
        f"| Feature Area | {feature} |",
        f"| Validation Type | {val_type} |",
    ]
    monday = meta.get("monday")
    if monday:
        display = f"[{monday}]({monday})" if monday.startswith("http") else monday
        lines.append(f"| Monday Ticket | {display} |")
    lines.append("")
    return "\n".join(lines)


def _build_cases_summary(results: List[Dict]) -> str:
    """
    Build the Test Cases Summary table.

    If a test declares a `Checks:` block in its docstring, each check is
    expanded as a separate row (one per validation point), all sharing the
    test's outcome. Otherwise we fall back to one row using the first
    descriptive line of the docstring.
    """
    lines = ["## Test Cases Summary", "", "| Test Case | Result |", "|---|---|"]
    for r in results:
        result_label = {
            "passed": "Passed ✅",
            "failed": "Failed ❌",
            "skipped": "Skipped ⏭️",
        }.get(r["outcome"], r["outcome"].capitalize())

        checks = _parse_checks(r.get("docstring", ""))
        if checks:
            for check in checks:
                lines.append(f"| {check} | {result_label} |")
        else:
            desc = _description_from_doc(r.get("docstring", "")) or _humanize_test_name(r["name"])
            lines.append(f"| {desc} | {result_label} |")
    lines.append("")
    return "\n".join(lines)


def _build_findings(results: List[Dict]) -> str:
    failures = [r for r in results if r["outcome"] == "failed"]
    if not failures:
        return ""
    lines = ["## Findings", ""]
    for i, r in enumerate(failures, 1):
        desc = _description_from_doc(r.get("docstring", "")) or _humanize_test_name(r["name"])
        lines.append(f"### F-{i:02d} – {desc}")
        lines.append("")
        lines.append(f"- **Test:** `{r['nodeid']}`")
        lines.append(f"- **Browser:** {r.get('browser', '—')}")
        lines.append(f"- **Severity:** [to be reviewed — Critical / High / Medium / Low]")
        lines.append("")
        lines.append("**Actual result (stack trace):**")
        lines.append("")
        lines.append("```")
        err = (r.get("error") or "").strip() or "(no error detail)"
        # Cap to last 30 lines to keep the report focused
        if len(err.splitlines()) > 30:
            err = "...\n" + "\n".join(err.splitlines()[-30:])
        lines.append(err)
        lines.append("```")
        lines.append("")
        lines.append("**Expected result:**")
        lines.append("")
        doc_block = (r.get("docstring") or "").strip() or "See the test source."
        lines.append("> " + doc_block.replace("\n", "\n> "))
        lines.append("")
        # Per-test evidence
        trace_for_test = TRACES_DIR / f"{r['name']}.zip"
        if trace_for_test.exists():
            lines.append(f"- 🧪 Trace: `{trace_for_test.relative_to(PROJECT_ROOT)}`")
        lines.append("")
    return "\n".join(lines)


def _build_evidence() -> str:
    """
    List evidence files. Prefer .mp4 over .webm (Monday previews mp4 natively),
    but if conversion didn't run we fall back to webm.
    """
    if not VIDEOS_DIR.exists():
        return ""
    mp4s = sorted(VIDEOS_DIR.rglob("*.mp4"))
    if mp4s:
        videos = mp4s
    else:
        videos = sorted(VIDEOS_DIR.rglob("*.webm"))
    if not videos:
        return ""
    lines = ["## Evidence", ""]
    for v in videos:
        lines.append(f"- `{v.relative_to(PROJECT_ROOT)}`")
    lines.append("")
    return "\n".join(lines)


def _build_verification_summary(custom_summary: str) -> str:
    """Optional narrative summary block. Rendered verbatim if provided."""
    if not custom_summary:
        return ""
    return "## Verification Summary\n\n" + custom_summary + "\n"


def _build_overall_result(overall: str, meta: Dict[str, str], results: List[Dict]) -> str:
    feature = meta.get("feature area") or meta.get("title") or "the change"
    if overall == "PASS":
        return (
            "## Overall QA Result\n\n"
            "**PASS ✅**\n\n"
            f"{feature} is functioning as expected. All validated scenarios "
            "behave according to the acceptance criteria. The ticket is ready "
            "to be moved to `QA Passed`.\n"
        )
    failed = sum(1 for r in results if r["outcome"] == "failed")
    return (
        "## Overall QA Result\n\n"
        "**FAIL ❌**\n\n"
        f"{feature} is **not** behaving as expected. **{failed}** scenario(s) "
        "failed during validation. The ticket must remain in `QA Failed` and "
        "be returned to development for fixes. Re-test once the issues listed "
        "in **Findings** are resolved.\n"
    )


# ============================================================
# Public API
# ============================================================

def build_markdown_report(results: List[Dict], base_url: Optional[str] = None) -> str:
    """Build the full Markdown QA report from a list of test results."""
    if not results:
        return "# QA Report – No tests executed\n"

    if base_url:
        os.environ["BASE_URL"] = base_url  # for _build_environment

    failed = sum(1 for r in results if r["outcome"] == "failed")
    overall = "PASS" if failed == 0 else "FAIL"
    meta = _aggregate_meta(results)

    # Free-text blocks that the QA can write in the test docstring
    custom_overview = ""
    custom_summary = ""
    for r in results:
        doc = r.get("docstring", "")
        if not custom_overview:
            custom_overview = _parse_text_block(doc, "Overview")
        if not custom_summary:
            custom_summary = _parse_text_block(doc, "Summary")
        if custom_overview and custom_summary:
            break

    sections = [
        _build_title(overall, meta, results),
        _build_overview(overall, results, meta, custom_overview),
        _build_environment(meta, results),
        _build_cases_summary(results),
    ]
    if overall == "FAIL":
        sections.append(_build_findings(results))
    sections.append(_build_evidence())
    sections.append(_build_verification_summary(custom_summary))
    sections.append(_build_overall_result(overall, meta, results))
    return "\n".join(s for s in sections if s)


def write_report(results: List[Dict], base_url: Optional[str] = None) -> Path:
    """
    Write the report to `reports/` and return the path.
    File naming: `qa_<PASS|FAIL>_YYYY-MM-DD_HH-MM.md`
    """
    REPORTS_DIR.mkdir(exist_ok=True)
    failed = sum(1 for r in results if r["outcome"] == "failed")
    overall = "PASS" if failed == 0 else "FAIL"
    now = datetime.now()
    out_path = REPORTS_DIR / f"qa_{overall}_{now.strftime('%Y-%m-%d_%H-%M')}.md"
    out_path.write_text(build_markdown_report(results, base_url), encoding="utf-8")
    return out_path
