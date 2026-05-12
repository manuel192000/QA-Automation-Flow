# QUICKSTART — Daily workflow

What you need to start working every day. If you need to install from
scratch (new machine, first time), read `SETUP.md` first.

> The team flow is **manual**: you run `npm test` (or `npx playwright
> test`) when you want. The original Monday auto-trigger lives archived
> in `experimental/webhook/` in case it ever gets revisited.

---

## 1. Pre-flight (10 seconds)

```bash
cd "/Users/user/Documents/Claude/Projects/QA Automation Flow"
```

Sanity-check the staging:

```bash
curl -I https://oneshopqa.com.dev.nmg-platform.com
```

Must answer `HTTP/2 200`. If not, contact the DEV admin before going on.

---

## 2. Working on a new ticket

1. **Read the ticket** in Monday and copy description + DOD.
2. **Design the cases.** Start Claude Code (`claude`) in the project
   root, then:

   ```text
   /qa-design

   <ticket description + DOD>
   ```

3. **Record selectors with codegen** (Playwright Test JS output —
   matches the official repo):

   ```bash
   npm run codegen:ts -- https://oneshopqa.com.dev.nmg-platform.com/
   ```

   Drive the UI manually. The Inspector keeps writing TypeScript code
   you can copy as-is.

4. **Ask Claude Code to lay down the spec:**

   ```text
   Create a new spec in tests/regression/<feature>.spec.ts for the ticket
   <Monday-URL>. Selectors recorded with codegen:

   <paste the code from the Inspector>

   Follow the pattern of tests/regression/predictive-search.spec.ts.
   ```

5. **Run it:**

   ```bash
   npx playwright test tests/regression/<feature>.spec.ts --headed
   npm run show-report
   ```

6. **Promote to the official repo.** Once green, copy the new
   `<feature>.spec.ts` and any new Page Object into the official
   automation repository. Then paste the run summary as an update on
   the Monday ticket and move the status manually.

---

## 3. Re-running the suite (any time)

```bash
npm test                                  # full suite
npm run test:smoke                        # smoke only
npm run test:regression                   # regression only
npx playwright test --headed              # visible browser
npx playwright test --ui                  # Playwright UI runner
npx playwright test -g "AMANA"            # filter by test title
```

---

## 4. Quick troubleshooting

| Symptom | Check | Fix |
|---|---|---|
| `403 Forbidden` from the staging | `curl -I <BASE_URL>` | Your IP is not authorized. Talk to the DEV admin. |
| `Error: browserType.launch` | `npx playwright install --dry-run` | `npm run install:browsers`. |
| Codegen opens but stays blank | DEV env unreachable | Same as `403` above. |
| Spec fails on a locator | DOM probably changed | Re-record with codegen, update the Page Object. |
| Random video filenames | Playwright nests evidence by test | Look under `test-results/<test-name>/` — Playwright Test names the folder after the test. |

---

## 5. Tech notes for the demo / questions from the lead

### What does the project do?

It takes the manual QA flow on oneshop and turns it into reusable
Playwright Test specs. The QA stays in control of which tickets get
executed; AI copilots (Claude Code, Cursor) accelerate the writing of
the specs themselves. Specs land here, get validated, then are copied
into the official automation repository.

### Stack

| Layer | Tool | Why |
|---|---|---|
| Language | TypeScript | Same language and conventions as the official automation repo |
| Test runner | Playwright Test | First-class auto-wait, video, trace, codegen, fixtures |
| Browser | Chromium (Playwright build) | Deterministic; no system browser version drift |
| AI copilots | Claude Code (CLI) + Cursor | Spec scaffolding, refactors, slash commands |

### Design decisions worth defending

1. **Manual gate by design.** Tests run when the QA says they run. Keeps
   human review in the loop.
2. **Accessibility-first locators** (`getByRole`, `getByTestId`). Survive
   HTML refactors that CSS / XPath would not.
3. **Page Object Model.** UI changes are absorbed in one file.
4. **Video + trace per run.** Evidence is reproducible without extra
   tooling.
5. **Ticket ↔ spec linked by JSDoc metadata.** No external mapping to
   keep in sync.
6. **AI copilots for authoring, never for execution.** They write the
   specs; Playwright Test runs them deterministically.

### Coverage today

- `tests/smoke/homepage.spec.ts` — home smoke (loads + no console errors).
- `tests/regression/predictive-search.spec.ts` — AMANA as pill in the
  Brands section of the predictive search panel (Monday: NGSCH Follow-Up).
- `tests/regression/predictive-search-trademark.spec.ts` — Trademark
  symbols rendering correctly in Featured Products.

Add new specs by copying the pattern from the predictive search file.

### Typical timings

- Smoke (2 tests): ~10 seconds.
- A single regression spec: ~5–15 seconds depending on the flow.
- New spec authoring per ticket: ~30 minutes (read → design → codegen →
  write → run green).

### Security / secrets

- `.env` is gitignored and never leaves the machine.
- Sensitive vars: `TEST_USER_PASSWORD`, optional `MONDAY_API_TOKEN`.
- The DEV environment uses a self-signed-ish cert (host mismatch);
  `ignoreHTTPSErrors: true` in `playwright.config.ts` handles that on
  purpose.

### Known limits / next steps

- **Single browser (Chromium)** for now. Multi-browser is one config
  change away when needed.
- **No CI yet.** Adding GitHub Actions to run smoke on every PR is the
  natural next step once specs land in the official repo.
- **API-level tests** are out of scope here; the official repo is the
  right place to add them with `request` fixtures.
