---
description: Design test cases from the text of a Monday ticket
---

Act as a senior QA. Read the following Monday.com ticket text
(description + comments + DOD) and design a complete set of test cases.

## Ticket input
$ARGUMENTS

## Instructions

1. **Identify the kind of change:**
   - Is it a bug fix?
   - Is it a new feature?
   - Is it a refactor / improvement with visible impact?

2. **Extract the acceptance criteria** (explicit or implicit).

3. **Produce a Markdown table** of test cases with these columns:

| ID | Title | Type | Priority | Preconditions | Steps | Expected Result |
|----|-------|------|----------|---------------|-------|-----------------|

Rules:
- IDs in `TC-001`, `TC-002`, ... format.
- Types: `Functional`, `UI`, `Negative`, `Edge`, `Regression`.
- Priorities: `High`, `Medium`, `Low`.
- Include **at least 1 negative case** and **1 edge case** per feature.
- Steps must be **actionable and specific** (not "verify it works").
- Expected results must be **observable** (which text, which element,
  which state).

4. **After the table**, add a "**Risks and regression areas**" section
   listing the modules that could be affected by this change.

5. **Close with a "Suggested test data"** section listing the users,
   seed data, or system states needed to execute the cases.

## Output format

Return only the Markdown content, without prefatory phrases like
"here are the cases". The output is meant to be pasted directly into
the ticket's documentation.
