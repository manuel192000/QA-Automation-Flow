"""
Minimal Monday.com GraphQL v2 client.

Provides three operations needed by the QA automation flow:
- get_item(item_id):     read title + description + updates of a ticket
- create_update(...):    post the QA report as an update on the ticket
- set_status(...):       move the ticket to "QA passed" / "QA failed"

Reads credentials from env vars:
    MONDAY_API_TOKEN          (required)
    MONDAY_BOARD_ID           (required for set_status)
    MONDAY_STATUS_COLUMN_ID   (default: "status")

The token is created in Monday → avatar → Developers → My Access Tokens.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

# Cargar .env aunque este módulo se use desde scripts CLI sueltos
# (cuando se usa desde pytest, conftest.py ya lo cargó).
load_dotenv()

MONDAY_API_URL = "https://api.monday.com/v2"


class MondayError(RuntimeError):
    """Raised when Monday's API returns an error or unexpected payload."""


def _token() -> str:
    token = os.getenv("MONDAY_API_TOKEN", "").strip()
    if not token:
        raise MondayError(
            "MONDAY_API_TOKEN is not set. Add it to your .env file."
        )
    return token


def _request(query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Send a GraphQL request and return the `data` block. Raises on errors."""
    payload: Dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    resp = requests.post(
        MONDAY_API_URL,
        headers={
            "Authorization": _token(),
            "Content-Type": "application/json",
            "API-Version": "2024-10",
        },
        json=payload,
        timeout=30,
    )
    try:
        body = resp.json()
    except ValueError as e:
        raise MondayError(f"Non-JSON response from Monday: {resp.text[:200]}") from e

    if "errors" in body and body["errors"]:
        raise MondayError(f"Monday API errors: {body['errors']}")
    if "data" not in body:
        raise MondayError(f"Unexpected Monday payload: {body}")
    return body["data"]


# ============================================================
# Public API
# ============================================================

def get_me() -> Dict[str, Any]:
    """Return basic info about the authenticated user: {id, name, email}."""
    data = _request("query { me { id name email } }")
    return data.get("me") or {}


def create_webhook(board_id: int | str, url: str, event: str = "change_column_value") -> str:
    """
    Register a webhook on a board. Returns the webhook id.
    Common events: change_column_value, change_status, create_item, change_specific_column_value.
    """
    query = """
    mutation ($board_id: ID!, $url: String!, $event: WebhookEventType!) {
      create_webhook(board_id: $board_id, url: $url, event: $event) { id board_id }
    }
    """
    data = _request(query, {"board_id": str(board_id), "url": url, "event": event})
    wid = (data.get("create_webhook") or {}).get("id")
    if not wid:
        raise MondayError(f"create_webhook returned no id: {data}")
    return wid


def list_webhooks(board_id: int | str) -> list:
    """
    List webhooks currently registered on a board.
    NOTE: Monday's Webhook type does not expose the URL via the API (privacy);
    only id, event and config are available.
    """
    query = "query ($board_id: ID!) { webhooks(board_id: $board_id) { id event config } }"
    data = _request(query, {"board_id": str(board_id)})
    return data.get("webhooks") or []


def delete_webhook(webhook_id: int | str) -> bool:
    """Delete a webhook by id."""
    query = "mutation ($id: ID!) { delete_webhook(id: $id) { id } }"
    _request(query, {"id": str(webhook_id)})
    return True


def get_item(item_id: int | str) -> Dict[str, Any]:
    """
    Fetch a Monday item by ID.
    Returns: {id, name, column_values: [...], updates: [{id, body}]}
    """
    query = """
    query ($ids: [ID!]) {
      items(ids: $ids) {
        id
        name
        column_values { id type text value }
        updates(limit: 50) { id body created_at }
      }
    }
    """
    data = _request(query, {"ids": [str(item_id)]})
    items = data.get("items") or []
    if not items:
        raise MondayError(f"Item {item_id} not found.")
    return items[0]


def create_update(item_id: int | str, body_markdown: str) -> str:
    """
    Post a new update (comment) on the ticket. Monday accepts Markdown and
    a subset of HTML inside the body. Returns the update ID.
    """
    query = """
    mutation ($item_id: ID!, $body: String!) {
      create_update(item_id: $item_id, body: $body) { id }
    }
    """
    data = _request(query, {"item_id": str(item_id), "body": body_markdown})
    upd = (data.get("create_update") or {}).get("id")
    if not upd:
        raise MondayError(f"create_update returned no id: {data}")
    return upd


def set_status(
    item_id: int | str,
    label: str,
    board_id: Optional[int | str] = None,
    column_id: Optional[str] = None,
) -> bool:
    """
    Set the status column of a Monday item to the given label
    (e.g. "QA passed", "QA failed"). Returns True on success.

    board_id and column_id default to env vars MONDAY_BOARD_ID and
    MONDAY_STATUS_COLUMN_ID ("status" if unset).
    """
    board_id = board_id or os.getenv("MONDAY_BOARD_ID", "").strip()
    column_id = column_id or os.getenv("MONDAY_STATUS_COLUMN_ID", "status").strip()
    if not board_id:
        raise MondayError(
            "MONDAY_BOARD_ID is required to change status. Set it in .env."
        )

    # Monday expects the status value as a JSON string with the label
    value_json = json.dumps({"label": label})

    query = """
    mutation ($board_id: ID!, $item_id: ID!, $column_id: String!, $value: JSON!) {
      change_column_value(
        board_id: $board_id,
        item_id: $item_id,
        column_id: $column_id,
        value: $value
      ) { id }
    }
    """
    _request(query, {
        "board_id": str(board_id),
        "item_id": str(item_id),
        "column_id": column_id,
        "value": value_json,
    })
    return True
