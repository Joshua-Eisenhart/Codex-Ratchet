# ChatUI Claw (Playwright) Protocol (v1)
Status: DRAFT / NONCANON
Date: 2026-03-04

## Purpose
Define a local, repeatable “ZIP-in / ZIP-out” browser automation loop for ChatGPT (Web UI) using Playwright, so:
- A2/A1 reasoning can run in the Web UI (Pro threads),
- Codex remains the orchestrator and file-based state manager,
- the deterministic kernel (A0/B/SIM) consumes returned artifacts.

This is an operational protocol, not an ontology spec.

## Scope
Automates the simple loop:
1) attach a `ZIP_JOB` bundle + one source document
2) send minimal command text
3) download the returned `.zip`

## Implementation (repo-local)
- Script: `system_v3/tools/chatgpt_pro_claw_playwright/run_one_job.mjs`
- Notes: `system_v3/tools/chatgpt_pro_claw_playwright/README.md`

## Security / operator requirements
- Runs locally (not in a remote sandbox).
- Uses a persistent browser profile directory for manual login bootstrap.
- No credentials are stored in code; user logs in once interactively.

## Inputs (per job)
- `--zip`: path to a `ZIP_JOB__*.zip`
- `--doc`: path to a source document to attach with the job
- `--send-text-file`: path to a minimal copy/paste send-text file
- `--download-dir`: directory to save downloaded `.zip` outputs
- `--profile-dir`: persistent browser profile directory
- `--headed` (optional): show the browser (recommended for first run / UI drift)

## Outputs
- One or more `.zip` files saved under `--download-dir`.
- The script prints `DOWNLOADED: <path>` for each download event.

## Failure handling (expected)
- UI selectors may drift. If auto-attach or auto-send fails:
  - the script prompts the operator to attach/send manually,
  - it still captures browser download events.

## Determinism boundary
- Browser reasoning is nondeterministic.
- The automation step must be deterministic in ordering and artifact capture:
  - do not mix multiple jobs in one chat unless the job contract explicitly allows it,
  - one job = one ZIP bundle + one doc + one send-text payload.

