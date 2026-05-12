# QA Automation Flow — oneshop

Local sandbox for designing **oneshop** end-to-end tests with **Playwright
+ TypeScript**. The tests written here are meant to be copy-pasted into
the official automation repository — this project is the experimentation
space where the QA, with help from `playwright codegen` and Claude Code,
authors and validates new specs before promoting them.

> **Status:** working baseline with one smoke and two regression specs.
> Aimed at letting a manual QA produce a clean Playwright Test spec
> per ticket in ~30 minutes.

---

## TL;DR for reviewers

- **What is tested:** the oneshop web frontend on the DEV environment.
- **Language / framework:** TypeScript + Playwright Test (matches the
  official automation repo).
- **How a new test is authored:** read the Monday ticket, design cases
  with `/qa-design` in Claude Code, record selectors with `playwright
  codegen --target=javascript`, land the file in `tests/regression/`
  following the Page Object pattern.
- **How tests run:** locally with `npm test` (or `npx playwright test`).
  Execution is fully under human control — no auto-triggers, no CI yet.
- **Per-run output:** Playwright HTML report + video + trace per test,
  all ready to be linked from a Monday update.

---

## Quick start

```bash
# 1. Clone and enter
git clone <repo-url> "QA Automation Flow"
cd "QA Automation Flow"

# 2. Install dependencies
npm install
npm run install:browsers     # downloads Chromium

# 3. Configure environment
cp .env.example .env
# fill BASE_URL if it differs from the default

# 4. Run the smoke suite (visible browser)
npm run test:smoke -- --headed
```

Full setup in [`SETUP.md`](SETUP.md). Daily workflow in
[`QUICKSTART.md`](QUICKSTART.md).

---

## Stack

| Layer | Tool | Why |
|---|---|---|
| Language | TypeScript | Matches the official automation repo |
| Runtime | Node 18+ | Playwright Test requirement |
| Test runner | Playwright Test | Built-in fixtures, parallelism, trace, video, codegen |
| Browser automation | Playwright (Chromium) | Auto-wait, accessibility-first locators |
| AI copilots | Claude Code + Cursor | Test scaffolding, refactors, slash commands |

---

## Repository layout

```
QA Automation Flow/
├── README.md                ← you are here
├── SETUP.md                 ← environment setup from scratch
├── QUICKSTART.md            ← daily workflow + demo notes
├── CLAUDE.md                ← Claude Code project context
│
├── package.json             ← npm scripts and dependencies
├── playwright.config.ts     ← Playwright Test config (baseURL, reporters, etc.)
├── tsconfig.json            ← TypeScript config
│
├── .env.example             ← env template (commit; never .env)
├── .gitignore
│
├── .claude/commands/        ← Claude Code slash commands
│   ├── qa-design.md         ← /qa-design — designs TCs from a Monday ticket
│   └── qa-report.md         ← /qa-report — formats a QA pass/fail update
│
├── pages/                   ← Page Object Model (TypeScript)
│   ├── base-page.ts
│   ├── home-page.ts
│   └── search-modal.ts
│
├── tests/
│   ├── smoke/               ← critical-path smoke specs
│   │   └── homepage.spec.ts
│   └── regression/          ← ticket-driven regression specs
│       ├── predictive-search.spec.ts
│       └── predictive-search-trademark.spec.ts
│
├── utils/                   ← reserved for TS helpers (empty for now)
├── data/                    ← seed data / fixtures (.json)
├── reports/                 ← generated reports (gitignored)
│
└── experimental/            ← parked code, not part of the main flow
    ├── webhook/             ← Monday auto-trigger (Python)
    └── python-prototype/    ← original Python + pytest prototype
```

---

## Authoring a new test (workflow per ticket)

1. **Read the ticket** in Monday and copy its description + DOD.
2. **Design the cases.** In Claude Code:

   ```text
   /qa-design

   <paste the ticket description here>
   ```

   You get a structured Test Case table. Decide which cases are worth
   automating.

3. **Record selectors** with Playwright's codegen — JavaScript output
   targeted at Playwright Test (the same flavor the official repo uses):

   ```bash
   npm run codegen:ts -- https://oneshopqa.com.dev.nmg-platform.com/
   ```

   Drive the UI manually in the browser that opens. Copy the spec code
   the Inspector generates.

4. **Land the test** following the project conventions:
   - File goes in `tests/regression/<feature>.spec.ts`.
   - Reusable UI components live in `pages/` as Page Objects.
   - Test docstring (JSDoc-style comment above `test.describe`) includes
     `Monday`, `Title`, `Feature Area`, `Validation Type`, `Overview`
     and `Checks` (see `tests/regression/predictive-search.spec.ts`
     as the canonical example).

5. **Run locally:**

   ```bash
   npx playwright test tests/regression/<feature>.spec.ts --headed
   npm run show-report          # open the HTML report
   ```

6. **Promote to the official repo:** copy the new spec (and any new Page
   Object) into the official automation repo. Paths follow the same
   layout — no path rewriting needed.

---

## Design decisions worth defending

1. **Manual gate kept by design.** Execution is launched by the QA, not
   by Monday changes. Keeps human review in the loop.
2. **Accessibility-first locators** (`getByRole`, `getByTestId`).
   Survive HTML refactors that XPath would not.
3. **Page Object Model.** Each UI component lives in `pages/`. Selector
   changes are fixed in one place.
4. **Video + trace on every run.** Evidence is reproducible and pasteable
   in tickets without extra effort.
5. **Ticket ↔ spec linked via JSDoc metadata.** No external mapping to
   maintain — the source of truth is the spec file itself.
6. **AI copilots for authoring, never for execution.** Claude Code and
   Cursor accelerate writing tests; Playwright Test runs them
   deterministically.

---

## NPM scripts cheat sheet

```bash
npm test                         # run the full suite, headless
npm run test:smoke               # only smoke specs
npm run test:regression          # only regression specs
npm run test:headed              # all specs with visible browser
npm run test:ui                  # open Playwright UI (interactive runner)
npm run codegen                  # codegen, JavaScript output
npm run codegen:ts               # codegen, Playwright Test output (preferred)
npm run show-report              # open the last HTML report
npm run install:browsers         # install Chromium (once per machine)
```

---

## Sending this to GitHub

```bash
git init -b main
git add .
git commit -m "Initial commit: QA Automation Flow (TypeScript baseline)"
git remote add origin git@github.com:<your-user>/qa-automation-flow.git
git push -u origin main
```

`.env` is gitignored and never leaves the machine.

---

## License / Authorship

Internal project — Manuel Villegas, oneshop QA team.
