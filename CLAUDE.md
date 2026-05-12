# Project: QA Automation Flow — oneshop

This file is automatically loaded by Claude Code whenever it is started
in this folder. It defines context, conventions and commands.

---

## Project context

- **Role:** Manual QA accelerating their workflow with AI copilots and
  Playwright Test (TypeScript).
- **App under test:** oneshop (web frontend).
  - **DEV environment:** `https://oneshopqa.com.dev.nmg-platform.com/`
- **Ticket tracker:** monday.com, board "Enterprise 2026".
- **Ticket states:** `QA Ready` → `QA In Progress` → `QA Passed` / `QA Failed`.
- **Repo purpose:** local sandbox to author Playwright specs. Once a spec
  is stable, it is copied into the official automation repository.

---

## Tech stack

- Node.js 18+
- Playwright Test (`@playwright/test`)
- TypeScript
- Chromium (downloaded by `npm run install:browsers`)

---

## Project conventions

- **Tests:** in `tests/`, split between `smoke/` and `regression/`. One
  file per ticket / feature, named `<feature>.spec.ts`.
- **Page Objects:** in `pages/`, one class per page or UI component.
- **Test data:** in `data/` (JSON).
- **Utilities:** in `utils/` (TypeScript helpers).
- **Reports:** Playwright HTML report in `playwright-report/`. Custom
  Markdown summaries (if needed) go in `reports/`.

### Code style

- Test names in **English**, lower-kebab in filenames (`predictive-search.spec.ts`).
- JSDoc-style comments in English above `test.describe`.
- Locators via `getByRole` and `getByTestId`. **Avoid XPath and brittle
  CSS selectors.**
- Never use raw `setTimeout` / `page.waitForTimeout`. Rely on Playwright's
  auto-wait and `expect()` assertions.

### Test docstring template

Every regression spec ships a header comment with this metadata so the
ticket linkage stays in the source of truth:

```ts
/**
 * Monday: <full ticket URL>
 * Title: <human-readable title>
 * Feature Area: <area under test>
 * Validation Type: <e.g. UI Regression, Functional, Smoke>
 * Site: oneshop
 *
 * Overview:
 *   <narrative of what is being validated and why>
 *
 * Checks:
 *   - <validation 1>
 *   - <validation 2>
 *
 * Preconditions:
 *   - <required setup>
 */
```

---

## Common commands

| Command | What it does |
|---|---|
| `npm test` | Run the full suite, headless |
| `npm run test:smoke` | Smoke specs only |
| `npm run test:regression` | Regression specs only |
| `npm run test:headed` | All specs with visible browser |
| `npm run test:ui` | Playwright UI runner (interactive) |
| `npm run codegen:ts` | Codegen with Playwright Test output |
| `npm run codegen` | Codegen with plain JavaScript output |
| `npm run show-report` | Open the last HTML report |

---

## Slash commands available

Defined in `.claude/commands/`:

- `/qa-design` — Designs test cases from a Monday ticket description.
- `/qa-report` — Produces a QA pass/fail update ready to paste in Monday.

---

## Team workflow

Manual: the QA picks up a ticket, designs cases with `/qa-design`,
records selectors with `npm run codegen:ts`, writes the spec, runs it
with `npx playwright test`, and pastes the summary back into Monday.
**No auto-trigger from Monday** — that option was prototyped and lives
archived in `experimental/webhook/`.

---

## Environment variables (`.env`)

```
BASE_URL=https://oneshopqa.com.dev.nmg-platform.com/
TEST_USER_EMAIL=
TEST_USER_PASSWORD=
MONDAY_API_TOKEN=   # optional, not required for the standard flow
```

`.env` is gitignored. New contributors copy `.env.example` and fill in.

---

## Rules for Claude Code in this project

1. **Never commit** `.env` or credentials.
2. **Before writing a new spec**, check whether a reusable Page Object
   already exists in `pages/`.
3. **Before inventing a locator**, suggest the frontend team add a
   `data-testid` if the element is not accessibility-reachable.
4. **Every spec must be runnable in isolation** (no implicit state from
   previous tests).
5. **Language:** answer Manuel in Spanish when chatting; keep all code,
   comments and docs in English.
