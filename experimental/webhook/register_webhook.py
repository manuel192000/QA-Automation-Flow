"""
Register (or replace) the Monday webhook that triggers the QA Runner.

Usage:
    WEBHOOK_URL=https://<tunnel>.trycloudflare.com/webhook \\
        python -m utils.register_webhook

Reads MONDAY_BOARD_ID from .env. Deletes any existing webhooks of the same
event type on the board before registering, so re-running this script is
idempotent and safe.
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

from utils import monday_client

load_dotenv()


def main():
    url = os.getenv("WEBHOOK_URL", "").strip()
    if not url:
        sys.exit("❌ Set WEBHOOK_URL env var with your tunnel URL ending in /webhook")

    board_id = os.getenv("MONDAY_BOARD_ID", "").strip()
    if not board_id:
        sys.exit("❌ MONDAY_BOARD_ID not set in .env")

    event = "change_column_value"
    print(f"📋 Board: {board_id}")
    print(f"🎯 URL  : {url}")
    print(f"🎟️  Event: {event}\n")

    # Clean previous webhooks of the same event so we don't pile up duplicates
    # (Monday's API does not expose the webhook URL, so we delete by event type.)
    existing = monday_client.list_webhooks(board_id)
    for wh in existing:
        if wh.get("event") == event:
            print(f"🧹 Deleting existing webhook id={wh['id']}")
            monday_client.delete_webhook(wh["id"])

    new_id = monday_client.create_webhook(board_id, url, event=event)
    print(f"\n✅ Webhook registered. id={new_id}")
    print("\nManuel: from now on, every time a column changes on the board,")
    print("Monday will POST to your tunnel and the QA Runner will decide whether")
    print("to dispatch tests for that ticket.")


if __name__ == "__main__":
    main()
