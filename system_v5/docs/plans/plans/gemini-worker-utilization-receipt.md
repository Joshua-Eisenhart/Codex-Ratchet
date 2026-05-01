# Gemini Worker Utilization Receipt

Status: checked live receipt
Date: 2026-04-20
Purpose: record what is actually proved about Google/Gemini CLI worker usage on this machine and in this repo.

## Checked machine/runtime facts
- `gemini` present: `/usr/local/bin/gemini`
- Gemini CLI version: `0.35.3`
- headless non-interactive mode works via:
  - `gemini -p ...`
- read-only approval mode available via:
  - `--approval-mode plan`
- structured output available via:
  - `--output-format json`

## Checked Gemini CLI runtime fact
- a headless prompt returned a normal usable-response prelude
- so Gemini CLI is not merely installed; it is currently usable in this environment

## Proved Gemini path now

### Direct Gemini headless worker path — PROVED
One simple headless smoke passed with:
- `gemini -p "Reply with exactly OK." --approval-mode plan --output-format json < /dev/null`

Observed model:
- `gemini-3.1-pro-preview`

### Parallel Gemini read-only worker smoke — PROVED
A 3-worker direct Gemini headless read-only probe succeeded with:
- provider: `gemini`
- mode: `-p`
- approval mode: `plan`
- output format: `json`

All three workers exited successfully.

Observed task family:
- lane row extraction
- worker-model extraction
- smoke-test extraction

Observed model usage:
- `gemini-3.1-pro-preview`

Observed evidence files:
- `/tmp/gemini_probe_3_summary.json`
- `/tmp/gemini_probe_3/gemini_lanes-status.json`
- `/tmp/gemini_probe_3/gemini_worker-model.json`
- `/tmp/gemini_probe_3/gemini_smoke-tests-1-3.json`

## Current role recommendation
Gemini CLI is usable now.
But under the current user preference and current receipts, it should be treated as:
- supportive / overflow worker capacity
- useful for secondary audits, extraction, summarization, or comparative reads
- not the primary worker family while Claude capacity is still available and working

## One-sentence summary
Google/Gemini CLI is installed, usable in headless mode, and proved for a 3-worker read-only smoke, but it should currently sit behind Claude in the worker priority order.
