# Python prototype (archived)

This folder contains the original Python + pytest + Playwright prototype
of the QA Automation Flow project. It was the first working version of
the flow and has been **superseded** by the TypeScript + Playwright Test
implementation at the repo root.

## Why it's archived

The official automation repository at oneshop uses JavaScript /
TypeScript. To make the specs authored here directly portable, the main
project was migrated to Playwright Test (TypeScript). The Python code
stays here as reference — useful if someone wants to compare patterns
or revive a piece of it.

## What's inside

- `conftest.py`, `pytest.ini`, `requirements.txt`: pytest configuration.
- `pages/`: Page Objects in Python (BasePage, HomePage, SearchModal).
- `tests/`: smoke and regression suites in pytest format.
- `utils/`: Monday GraphQL client and Markdown report builder.
- `ROADMAP_OLD_PYTHON.md`: original phased roadmap that drove the
  prototype.

## How it ran (historical)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
pytest tests/smoke/ --headed
```

The companion auto-trigger flow (Flask webhook + cloudflared tunnel)
lives next door at `../webhook/` and was archived together.
