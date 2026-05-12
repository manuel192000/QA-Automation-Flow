"""
QA Runner — webhook server that triggers automated tests.

Workflow:
1. Monday sends a webhook to /webhook whenever a column changes on the board.
2. The server filters events: only fire when the ticket meets BOTH conditions:
       - Manuel is assigned in the QA/Rel column.
       - Status column equals MONDAY_QA_TRIGGER_LABEL (default "QA In Progress").
3. It scans `tests/` for any test whose docstring contains `Monday: <ticket_id>`
   (full URL or numeric id).
4. If matches are found, it runs `pytest` on exactly those tests. The existing
   pytest hooks will generate the QA report and post it back to the ticket
   (when MONDAY_POST_ENABLED=1).

Usage:
    # 1) Activate venv
    source .venv/bin/activate

    # 2) Start the server
    python -m utils.qa_runner

    # 3) Expose port 8765 with a tunnel (cloudflared / ngrok)
    cloudflared tunnel --url http://localhost:8765
    # or:
    ngrok http 8765

    # 4) Register the webhook on Monday (once)
    WEBHOOK_URL=https://<your-tunnel>.trycloudflare.com/webhook \\
        python -m utils.register_webhook
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from flask import Flask, request, jsonify

from utils import monday_client

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"

app = Flask(__name__)

# In-memory deduplication: Monday may resend; we ignore the same item within N seconds.
_recent_runs: dict[str, float] = {}
_RUNS_LOCK = threading.Lock()
_DEDUP_WINDOW_SECONDS = 60


# ============================================================
# Helpers
# ============================================================

def _my_user_id() -> str:
    """Return Manuel's Monday user id, fetched once and cached."""
    cached = os.getenv("MONDAY_MY_USER_ID", "").strip()
    if cached:
        return cached
    me = monday_client.get_me()
    uid = str(me.get("id", "")).strip()
    if uid:
        os.environ["MONDAY_MY_USER_ID"] = uid  # cache for the lifetime of this process
    return uid


def _find_tests_for_ticket(ticket_id: str) -> list[str]:
    """Return test files that reference this ticket id in their docstrings."""
    matches: list[str] = []
    for path in TESTS_DIR.rglob("test_*.py"):
        try:
            source = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if re.search(rf"Monday:[^\n]*{re.escape(ticket_id)}", source):
            matches.append(str(path.relative_to(PROJECT_ROOT)))
    return matches


def _ticket_qualifies(item_id: str) -> tuple[bool, str]:
    """
    Check whether the ticket meets the trigger conditions:
      - Manuel is in the QA/Rel column.
      - Status equals MONDAY_QA_TRIGGER_LABEL.
    Returns (qualifies, reason).

    Defaults baked in from the OS Enterprise Sprints 2026 board (mayo 2026).
    Override via .env if your board layout changes.
    """
    qa_rel_col = os.getenv("MONDAY_QA_REL_COLUMN_ID", "multiple_person_mkxkt529").strip()
    status_col = os.getenv("MONDAY_STATUS_COLUMN_ID", "status").strip()
    trigger_label = os.getenv("MONDAY_QA_TRIGGER_LABEL", "QA In Progress").strip()
    my_id = _my_user_id()

    if not qa_rel_col:
        return False, "MONDAY_QA_REL_COLUMN_ID is empty (check .env)"
    if not my_id:
        return False, "MONDAY_MY_USER_ID is empty and auto-fetch via get_me() failed"

    try:
        item = monday_client.get_item(item_id)
    except Exception as e:
        return False, f"failed to fetch item: {e}"

    cols = {c["id"]: c for c in item.get("column_values", [])}

    # Check assignment
    qa_rel = cols.get(qa_rel_col, {})
    raw_value = qa_rel.get("value") or ""
    try:
        parsed = json.loads(raw_value) if raw_value else {}
    except Exception:
        parsed = {}
    persons = (parsed.get("personsAndTeams") or []) if isinstance(parsed, dict) else []
    if not any(str(p.get("id")) == my_id for p in persons):
        return False, f"not assigned to user {my_id} in QA/Rel"

    # Check status label
    status_cell = cols.get(status_col, {})
    current_label = (status_cell.get("text") or "").strip()
    if current_label != trigger_label:
        return False, f"status is '{current_label}', expected '{trigger_label}'"

    return True, "OK"


def _run_pytest(test_files: list[str]) -> int:
    """Run pytest on the given files. Returns the exit code."""
    cmd = [sys.executable, "-m", "pytest", *test_files]
    print(f"\n🚀 Running: {' '.join(cmd)}\n", flush=True)
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return proc.returncode


def _dispatch(item_id: str):
    """Background dispatch: validate ticket, find tests, run pytest.

    Dedup only applies once the ticket qualified — we don't burn the dedup
    window on tickets that were skipped, because the next webhook (right
    after the user finishes configuring the ticket) is the real one.
    """
    import time
    print(f"\n🔔 Webhook received for item {item_id}", flush=True)
    ok, reason = _ticket_qualifies(item_id)
    if not ok:
        print(f"   ⏭️  Skipped: {reason}", flush=True)
        return

    # The ticket qualified. Check dedup so we don't run pytest twice if
    # another webhook arrives within the window.
    now = time.time()
    with _RUNS_LOCK:
        last = _recent_runs.get(item_id, 0)
        if now - last < _DEDUP_WINDOW_SECONDS:
            print(f"   ⏭️  Skipped (dedup): ran for this ticket {int(now-last)}s ago", flush=True)
            return
        _recent_runs[item_id] = now

    tests = _find_tests_for_ticket(item_id)
    if not tests:
        print(f"   ⚠️  No automated tests reference ticket {item_id}", flush=True)
        return

    print(f"   ▶️  Tests for ticket {item_id}: {tests}", flush=True)
    _run_pytest(tests)


# ============================================================
# Routes
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok")


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Receive Monday webhooks. Monday requires the challenge handshake on first
    registration: we echo the `challenge` field back as JSON.

    Note on dedupe: we DO NOT dedupe here — a single ticket change can produce
    multiple webhooks while the user is still configuring the ticket (assign,
    then status). The dedupe lives inside `_dispatch`, only kicking in for
    tickets that actually qualified for execution.
    """
    payload = request.get_json(silent=True) or {}

    # Handshake on webhook registration
    if "challenge" in payload:
        return jsonify(challenge=payload["challenge"])

    event = payload.get("event") or {}
    item_id = str(event.get("pulseId") or event.get("itemId") or "").strip()
    if not item_id:
        return jsonify(ok=False, error="no item id in payload"), 200

    # Dispatch in background — Monday expects a quick 200
    threading.Thread(target=_dispatch, args=(item_id,), daemon=True).start()
    return jsonify(ok=True, dispatched=item_id)


# ============================================================
# Entry point
# ============================================================

def main():
    port = int(os.getenv("QA_RUNNER_PORT", "8765"))
    print(f"📡 QA Runner listening on http://localhost:{port}/webhook")
    print("   Expose with: cloudflared tunnel --url http://localhost:{port}")
    print("   (or: ngrok http {port})\n")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
