# QA Automation Flow — oneshop

End-to-end UI test automation for **oneshop**, built on Playwright +
pytest with a workflow that pairs QA expertise with AI copilots (Claude
Code, Cursor) to convert manual exploratory testing into reusable,
evidence-rich regression scripts.

> **Status:** working baseline with one smoke and one regression suite.
> Designed so a manual QA can author new tests in ~30 minutes per ticket.

---

## TL;DR for reviewers

- **What it tests:** the oneshop web frontend on the DEV environment.
- **How tests are authored:** QA reads the Monday ticket, designs cases
  with `/qa-design`, records selectors with `playwright codegen`, and
  Claude Code lands the test file following the project's Page Object
  conventions.
- **How tests are executed:** locally via `pytest`. The team chose to
  keep execution under human control — no automatic triggers, no CI yet.
- **What's produced per run:** a Markdown QA report (PASS or FAIL),
  the recorded video as MP4 per test, and a Playwright trace `.zip`.
  The report is ready to paste as a Monday update.
- **Documentation:** every decision and trade-off is captured in
  `SETUP.md` and `QUICKSTART.md`. (An optional local roadmap file
  `HOJA_DE_RUTA_AUTOMATIZACION_QA.md` is gitignored and not on GitHub.)

---

## Quick start

```bash
# 1. Clone and enter the project
git clone <repo-url> "QA Automation Flow"
cd "QA Automation Flow"

# 2. Create venv and install
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 3. Configure
cp .env.example .env
# (fill BASE_URL, optional MONDAY_API_TOKEN)

# 4. Run the smoke suite
pytest tests/smoke/ --headed
```

Full instructions in [`SETUP.md`](SETUP.md). Daily workflow in
[`QUICKSTART.md`](QUICKSTART.md).

---

## Stack

| Layer | Tool | Why |
|---|---|---|
| Language | Python 3.12 | Reads close to English; standard for QA tooling |
| Test runner | pytest | Industry standard; fixtures, marks, paralelization |
| Browser automation | Playwright (Chromium) | Auto-wait, video, trace, accessibility-first locators |
| AI copilots | Claude Code + Cursor | Test scaffolding, refactoring, slash commands |
| Reports | Markdown → HTML | Markdown for review, HTML for Monday updates |
| Optional: Monday integration | GraphQL API v2 | Used manually for now; archived webhook flow available |

---

## Repository layout

```
QA Automation Flow/
├── README.md                      ← you are here
├── SETUP.md                       ← detailed environment setup
├── QUICKSTART.md                  ← daily workflow + demo notes
├── CLAUDE.md                      ← Claude Code project context
│
├── .claude/commands/              ← Claude Code slash commands
│   ├── qa-design.md               ← /qa-design — designs TCs from a ticket
│   └── qa-report.md               ← /qa-report — formats a QA update
│
├── .env.example                   ← config template (commit; never .env)
├── requirements.txt               ← Python dependencies
├── pytest.ini                     ← pytest config + marks
├── conftest.py                    ← global fixtures, video/trace setup
│
├── pages/                         ← Page Object Model
│   ├── base_page.py
│   ├── home_page.py
│   └── search_modal.py
│
├── tests/
│   ├── smoke/                     ← critical-path smoke tests
│   │   └── test_homepage_smoke.py
│   └── regression/                ← ticket-driven regression suites
│       └── test_predictive_search.py
│
├── utils/                         ← helpers
│   ├── monday_client.py           ← optional: read/post to Monday tickets
│   └── report_builder.py          ← generates the QA pass/fail report
│
├── data/                          ← seed data and fixtures (.json / .yaml)
├── reports/                       ← generated QA reports (gitignored)
├── videos/                        ← Playwright video evidence (gitignored)
├── traces/                        ← Playwright trace files (gitignored)
│
└── experimental/                  ← parked code, not in main flow
    └── webhook/                   ← Monday webhook auto-trigger (archived)
```

---

## How a new test gets created (workflow per ticket)

1. **Read the ticket** in Monday and copy its description + DOD.
2. **Design the cases.** In Claude Code:

   ```text
   /qa-design

   <paste the ticket description here>
   ```

   You get a structured Test Case table. Decide which cases worth automating.
3. **Record selectors** with Playwright's codegen:

   ```bash
   playwright codegen --ignore-https-errors <staging-url>
   ```

   Do the user actions manually. Copy the generated Python from the Inspector.
4. **Land the test** following the convention:
   - File goes in `tests/regression/test_<feature>.py`.
   - Reusable UI components live in `pages/` as Page Objects.
   - Docstring includes `Monday`, `Title`, `Feature Area`, `Validation Type`,
     `Overview`, `Checks`, `Summary` (see
     `tests/regression/test_predictive_search.py` as the canonical example).
5. **Run locally:**

   ```bash
   pytest tests/regression/test_<feature>.py --headed
   ```

   The report lands in `reports/qa_PASS_<timestamp>.md`, the MP4 video
   in `videos/` and the trace in `traces/`.
6. **Paste the report as a Monday update** and move the ticket to
   `QA Passed` / `QA Failed`.

---

## Design decisions worth defending

1. **Manual gate kept by design.** The QA stays in control of which
   tickets get executed and when. No auto-trigger from Monday.
2. **Accessibility-first locators** (`get_by_role`, `get_by_test_id`).
   Survive HTML refactors that XPath would not.
3. **Page Object Model.** Each UI component lives in `pages/`. Selector
   changes are fixed in one place.
4. **Video + trace on every run.** Evidence is reproducible and pasteable
   in tickets without extra effort.
5. **Tickets ↔ tests linked by docstring metadata.** No external mapping
   to maintain — the source of truth is the test file itself.
6. **AI copilots for authoring, never for execution.** Claude Code and
   Cursor accelerate writing tests; pytest runs them deterministically.

---

## Reports

After every `pytest` run a Markdown report is written to `reports/`
following this structure:

```
QA Pass Report – <Feature Title>

Overview        ← narrative pulled from the test's docstring
Test Environment   (table)
Test Cases Summary (one row per Checks: bullet)
Evidence        (mp4 videos + trace files)
Verification Summary  (the test's Summary: block, rendered as-is)
Overall QA Result  (PASS ✅ / FAIL ❌ + conclusion)
```

The report is sized and styled to look clean inside Monday's update box
(inline HTML tighten markers; tables with bordered cells).

---

## Roadmap

High-level direction (full phased plan may exist only as a local doc):

- **Phase 6 (next):** API-level testing with `httpx` or
  `playwright.request`. Useful for backend smoke before UI runs.
- **Coverage:** continue adding tests in `tests/regression/` following
  the predictive search pattern. Cursor's tab-complete in test files is
  the fastest tool for this.
- **Future:** reactivate the archived webhook flow from
  `experimental/webhook/` if the team decides to fully automate
  trigger-to-report.

---

## Sending this to GitHub

```bash
# Initial commit
git init -b main
git add .
git commit -m "Initial commit: QA Automation Flow baseline"

# Connect to your repo (create it empty on GitHub first)
git remote add origin git@github.com:<your-user>/qa-automation-flow.git
git push -u origin main
```

`.env` is gitignored and never leaves your machine.

---

## License / Authorship

Internal project — Manuel Villegas, oneshop QA team.
