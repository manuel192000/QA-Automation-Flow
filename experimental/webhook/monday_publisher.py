"""
Glue layer between the QA report and Monday.com.

Given the list of test results (the same shape used by report_builder), this
module:
  1. Extracts the Monday ticket IDs referenced in each test's docstring
     (`Monday: <ID-or-URL>` line).
  2. Posts the QA report (Markdown) as an update on each ticket.
  3. Updates the status column to "QA passed" / "QA failed" based on the
     overall outcome.

Disabled by default. Enable by exporting MONDAY_POST_ENABLED=1 before pytest.
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Tuple

import markdown as md_lib

from utils import monday_client


def _markdown_to_html(md_text: str) -> str:
    """
    Convert Markdown to HTML for Monday updates and tighten the spacing.

    Monday's update body accepts a subset of HTML (p, h1-h6, ul/ol/li, table,
    a, strong/b, em/i, code, pre, br) but NOT raw Markdown — without this
    step headings, tables and bold all render as literal ``##`` / ``|`` /
    ``**`` characters. We also inject inline styles so headings and tables
    don't get Monday's default oversized vertical margin.
    """
    html = md_lib.markdown(
        md_text,
        extensions=["tables", "fenced_code"],
        output_format="html5",
    )
    return _tighten_html_spacing(html)


def _tighten_html_spacing(html: str) -> str:
    """
    Inject inline CSS into the generated HTML so the update looks compact
    inside Monday's update card. Monday strips <style> blocks but respects
    `style="..."` attributes per element.
    """
    rules = [
        (r"<h1(\s|>)", r'<h1 style="margin:0.6em 0 0.2em;font-size:1.4em;"\1'),
        (r"<h2(\s|>)", r'<h2 style="margin:0.6em 0 0.2em;font-size:1.2em;"\1'),
        (r"<h3(\s|>)", r'<h3 style="margin:0.5em 0 0.15em;font-size:1.05em;"\1'),
        (r"<p(\s|>)", r'<p style="margin:0.25em 0;"\1'),
        (r"<table(\s|>)", r'<table style="margin:0.3em 0;border-collapse:collapse;"\1'),
        (r"<thead(\s|>)", r'<thead style="background:#f4f5f7;"\1'),
        (r"<th(\s|>)", r'<th style="padding:4px 10px;border:1px solid #e1e3e6;text-align:left;"\1'),
        (r"<td(\s|>)", r'<td style="padding:4px 10px;border:1px solid #e1e3e6;"\1'),
        (r"<ul(\s|>)", r'<ul style="margin:0.2em 0;padding-left:1.3em;"\1'),
        (r"<ol(\s|>)", r'<ol style="margin:0.2em 0;padding-left:1.3em;"\1'),
        (r"<li(\s|>)", r'<li style="margin:0.05em 0;"\1'),
        (r"<pre(\s|>)", r'<pre style="margin:0.3em 0;padding:8px;background:#f4f5f7;border-radius:4px;"\1'),
    ]
    for pattern, sub in rules:
        html = re.sub(pattern, sub, html)
    return html

MONDAY_URL_RE = re.compile(r"/pulses/(\d+)")
MONDAY_LINE_RE = re.compile(r"^\s*Monday:\s*(.+)\s*$", re.IGNORECASE | re.MULTILINE)


def _extract_item_ids(results: List[Dict]) -> List[str]:
    """Collect unique Monday item IDs from the tests' docstrings."""
    ids: List[str] = []
    seen = set()
    for r in results:
        doc = r.get("docstring") or ""
        m = MONDAY_LINE_RE.search(doc)
        if not m:
            continue
        raw = m.group(1).strip()
        if raw.upper() == "N/A" or not raw:
            continue
        # Either a full URL (.../pulses/<id>) or a bare numeric ID
        url_match = MONDAY_URL_RE.search(raw)
        item_id = url_match.group(1) if url_match else raw
        if item_id.isdigit() and item_id not in seen:
            ids.append(item_id)
            seen.add(item_id)
    return ids


def publish(results: List[Dict], report_markdown: str) -> Tuple[List[str], List[str]]:
    """
    Post the report and update status on every ticket referenced by the run.

    Returns (posted_ids, errors). `errors` contains human-readable messages
    for tickets that failed to update.
    """
    posted: List[str] = []
    errors: List[str] = []

    failed_count = sum(1 for r in results if r["outcome"] == "failed")
    # Defaults match the OS Enterprise Sprints 2026 board labels exactly
    # (case-sensitive — Monday rejects unknown labels).
    passed_label = os.getenv("MONDAY_QA_PASSED_LABEL", "QA Passed")
    failed_label = os.getenv("MONDAY_QA_FAILED_LABEL", "QA Failed")
    target_label = passed_label if failed_count == 0 else failed_label

    report_html = _markdown_to_html(report_markdown)

    for item_id in _extract_item_ids(results):
        try:
            monday_client.create_update(item_id, report_html)
            monday_client.set_status(item_id, target_label)
            posted.append(item_id)
        except Exception as e:  # noqa: BLE001 — surface anything from Monday
            errors.append(f"{item_id}: {e}")
    return posted, errors


def is_enabled() -> bool:
    return os.getenv("MONDAY_POST_ENABLED", "").strip() in ("1", "true", "yes", "on")
