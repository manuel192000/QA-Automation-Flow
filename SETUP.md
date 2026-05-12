# Setup from scratch — QA Automation Flow

Step-by-step guide for cloning this repo and getting it running on a new
machine. Aimed at QAs of any level: follow the steps in order and in
~15 minutes you'll have everything working.

---

## 1. Prerequisites by OS

### macOS

```bash
# Homebrew (package manager)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Base tools
brew install node git
```

### Windows

1. Install [Node.js LTS (18+)](https://nodejs.org/en/download).
2. Install [Git for Windows](https://git-scm.com/download/win).

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y nodejs npm git
```

Check the Node version:

```bash
node --version    # must be 18 or higher
```

---

## 2. Editor and AI agent

### Cursor

Download from https://cursor.com and install like any app.

### Claude Code (CLI)

```bash
npm install -g @anthropic-ai/claude-code --foreground-scripts
claude --version
claude login
```

> If installation fails with `Cannot find module 'install.cjs'`, reinstall
> with `--foreground-scripts` as above, or use the native installer:
> `curl -fsSL https://claude.ai/install.sh | bash`.

You need an Anthropic account with a plan that includes Claude Code
(Pro or Max).

---

## 3. Clone the project

```bash
git clone <repo-url> "QA Automation Flow"
cd "QA Automation Flow"
```

---

## 4. Install dependencies

```bash
npm install
npm run install:browsers   # downloads Chromium (~150 MB)
```

`npm install` reads `package.json` and pulls Playwright Test +
TypeScript + Node types into `node_modules/`.

---

## 5. Configure environment

```bash
cp .env.example .env
```

Edit `.env` if you need to change the defaults:

| Variable | Default | When to change |
|---|---|---|
| `BASE_URL` | `https://oneshopqa.com.dev.nmg-platform.com/` | If you target a different environment |
| `TEST_USER_EMAIL` / `TEST_USER_PASSWORD` | empty | Only if a spec logs in |
| `MONDAY_API_TOKEN` | empty | Only if you script Monday access manually |

`.env` is gitignored. **Never commit it.**

---

## 6. Confirm staging is reachable

```bash
curl -I https://oneshopqa.com.dev.nmg-platform.com
```

Must return `HTTP/2 200`. If you get `403` or no response, contact the
DEV environment admin before continuing.

---

## 7. Run the first test

```bash
npm run test:smoke -- --headed
```

Expected output:

```
Running 2 tests using 1 worker
  ✓  tests/smoke/homepage.spec.ts:13:3 › Homepage smoke › home loads
  ✓  tests/smoke/homepage.spec.ts:19:3 › Homepage smoke › home has no console errors
  2 passed (Xs)
```

After every run:

- HTML report → `playwright-report/index.html` (`npm run show-report`)
- Videos → `test-results/<test>/video.webm`
- Traces → `test-results/<test>/trace.zip` (`npx playwright show-trace`)

---

## 8. Slash commands in Claude Code

The repo ships two slash commands in `.claude/commands/`:

- `/qa-design` — designs Test Cases from a ticket description.
- `/qa-report` — formats a QA pass/fail update for Monday.

Use them inside `claude` from the project root:

```text
/qa-design

<paste the Monday ticket description here>
```

---

## 9. Daily commands

| Command | What it does |
|---|---|
| `npm test` | Run the full suite, headless |
| `npm run test:smoke` | Smoke specs only |
| `npm run test:regression` | Regression specs only |
| `npm run test:headed` | All specs with visible browser |
| `npm run test:ui` | Playwright UI mode (interactive runner) |
| `npm run codegen:ts` | Codegen with Playwright Test output (preferred) |
| `npm run codegen` | Codegen with plain JavaScript output |
| `npm run show-report` | Open the last HTML report |
| `claude` | Start Claude Code in the current folder |

---

## 10. Troubleshooting

### `npm: command not found`
Node is not installed or not on PATH. Reinstall from
https://nodejs.org/en/download.

### `Error: browserType.launch: Executable doesn't exist`
You skipped `npm run install:browsers`. Run it once.

### Pytest / Python errors (legacy)
The previous Python prototype lives under `experimental/python-prototype/`.
Tests in TypeScript run with `npm test`, never with `pytest`.

### `playwright codegen` opens an empty browser
The DEV environment did not respond. Verify with `curl -I <BASE_URL>` and
check the network / VPN policy of the host.

### My spec fails with `TimeoutError` waiting for a locator
The selector probably changed. Re-run codegen on the same flow and update
the Page Object accordingly. Prefer `getByRole` and `getByTestId` over
brittle CSS or XPath.

### `Cannot find module 'install.cjs'` installing Claude Code CLI
Node 26+ + npm sometimes skips the post-install script. Reinstall with
`--foreground-scripts`, or use the native installer:
`curl -fsSL https://claude.ai/install.sh | bash`.

---

## 11. Project structure

```
QA Automation Flow/
├── README.md                ← project home
├── SETUP.md                 ← this file
├── QUICKSTART.md            ← daily flow + demo notes
├── CLAUDE.md                ← Claude Code context
├── package.json             ← npm scripts and dependencies
├── playwright.config.ts     ← Playwright Test config
├── tsconfig.json
├── .env.example
│
├── .claude/commands/        ← slash commands
├── pages/                   ← Page Objects (TypeScript)
├── tests/
│   ├── smoke/
│   └── regression/
├── utils/                   ← reserved for TS helpers
├── data/                    ← seed data / fixtures
├── reports/                 ← generated reports (gitignored)
│
└── experimental/            ← parked code, not in main flow
    ├── webhook/             ← Monday auto-trigger (Python)
    └── python-prototype/    ← original Python + pytest prototype
```

---

## 12. Next steps

- Author new specs by following the convention in
  `tests/regression/predictive-search.spec.ts`. The JSDoc header (Monday,
  Title, Feature Area, Validation Type, Overview, Checks, Preconditions)
  is the canonical pattern.
- When a spec is stable, copy it (and any new Page Object) into the
  official automation repository — paths and conventions are aligned so
  the move is a plain `cp`.
