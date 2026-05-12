---
description: Produce a QA pass/fail report ready to paste as a Monday update
---

Produce a QA report in Markdown following the template below.

## Input
$ARGUMENTS

The input must include (ask for it if missing):
- Monday ticket ID and title
- Environment (DEV / Staging / Prod)
- Browser(s) used
- List of executed cases with outcomes (passed / failed)
- For failures: defect description and steps to reproduce
- Links or file names for evidence (video, screenshots)

## Output template

# QA Pass Report - <Feature Title>

## Overview
<2-3 lines summarizing what was validated and the global result>

## Test Environment

| Field | Details |
|-------|---------|
| Environment | DEV - <URL> |
| Site | oneshop |
| Browser | <Chromium / Chrome / Firefox / WebKit> |
| Feature Area | <area> |
| Validation Type | <UI Regression / Functional / Smoke / etc.> |
| Monday Ticket | <URL> |

## Test Cases Summary

| Test Case | Result |
|-----------|--------|
| <case 1>  | Passed |
| <case 2>  | Passed |

## Evidence

- <evidence file 1>
- <evidence file 2>

## Verification Summary

<Topic 1>
- <observation>
- <observation>

<Topic 2>
- <observation>

## Overall QA Result

**PASS**

<1-2 lines: the ticket is ready for production / requires fixes>

## Rules

- If all cases passed: status `PASS`, omit any "Findings" section.
- If at least one failed: title becomes `QA Fail Report - ...`, status
  `FAIL`, and add a "## Findings" section per defect with severity,
  steps to reproduce, actual vs expected, and associated evidence.
- Never invent information. If a datum is missing, leave a placeholder
  like `[to complete]`.
- The output is meant to be pasted into a Monday update - keep the
  Markdown clean.
