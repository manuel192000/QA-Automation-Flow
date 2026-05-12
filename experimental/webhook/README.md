# Webhook trigger (experimental, disabled by default)

This folder contains an **experimental** end-to-end integration that:

1. Listens to Monday.com webhooks on a local Flask server.
2. Filters events: only fires when the ticket is assigned to the QA in the
   `QA/Rel` column **and** the status is `QA In Progress`.
3. Auto-discovers which tests reference the ticket (via the `Monday:` line
   in each test's docstring) and runs only those.
4. Posts the QA report as an update on the Monday ticket and moves the
   status to `QA Passed` / `QA Failed`.

## Why it's archived

The team decided the daily flow is:

- The QA reads the ticket, designs the test cases manually (with help from
  `/qa-design`), records the selectors with `playwright codegen`, and lands
  the test file in `tests/regression/`.
- Test execution is launched **manually** with `pytest`. No automatic
  trigger from Monday.

The webhook flow is kept here in case the team wants to revisit it later —
the code is fully working, just not wired into the main flow.

## How to reactivate (if ever needed)

1. Copy the three files back to `utils/`.
2. Restore the `pytest_sessionfinish` hook in `conftest.py` that imports
   `utils.monday_publisher`.
3. Add `flask>=3.0` back to `requirements.txt`.
4. Set `MONDAY_POST_ENABLED=1` in `.env`.
5. Run the 3 terminals (see `SETUP.md §14` history for the dance —
   server + cloudflared tunnel + register_webhook).

## Files

| File | What it does |
|---|---|
| `qa_runner.py` | Flask server that receives Monday webhooks and dispatches pytest |
| `register_webhook.py` | One-shot script to register the webhook URL with Monday |
| `monday_publisher.py` | Converts the QA report Markdown to HTML and posts it as an update |
