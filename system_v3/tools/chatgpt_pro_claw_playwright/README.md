# ChatGPT Pro ZIP-in/ZIP-out Claw (Playwright)

Goal: automate the simple loop:
1) upload a `ZIP_JOB` bundle + a high-entropy doc
2) send the minimal command text
3) download the returned ZIP

This runs **locally** and uses a **persistent browser profile** so you can log in once manually (no password in code).

## Install (already done in this repo)
- Node `playwright` is a dev dependency.
- Chromium binaries installed via `npx playwright install chromium`.

Verify:
- `npx playwright --version`

## First run (login bootstrap)
Run the script with `--headed` so a browser opens.
If you are not logged in, log in manually, then return to the terminal and press Enter when prompted.

## One-off run
Example (paths must exist):
```bash
node work/chatgpt_pro_claw_playwright/run_one_job.mjs \
  --zip "/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/zip_dropins/ZIP_JOB__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__DEFAULT_ANY_DOCUMENT__CHATUI_DROPIN__v1.zip" \
  --doc "/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a2_feed_high entropy doc/Leviathan v3.2 word.txt" \
  --send-text-file "/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/zip_dropins/ZIP_JOB__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__DEFAULT_ANY_DOCUMENT__CHATUI_DROPIN__v1/meta/CHATUI_MINIMAL_SEND_TEXT__COPY_PASTE.md" \
  --download-dir "/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/chatgpt_pro_claw_playwright/downloads" \
  --profile-dir "/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/chatgpt_pro_claw_playwright/profile" \
  --headed
```

## Ingest + validate downloads (fail-closed)
After downloads land in `--download-dir`, run the deterministic validators to reject common drift failures (e.g. empty topic slugs, too few topics in discovery mode):

```bash
python3 system_v3/tools/chatgpt_pro_claw_playwright/ingest_downloads.py \
  --download-dir "/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/chatgpt_pro_claw_playwright/downloads" \
  --mode discovery \
  --min-topic-slugs 10 \
  --move
```

Notes:
- This script makes a best-effort attempt to attach both files and click Send.
- It then watches for downloads and tries to click a “download” UI for any returned `.zip`.
- If the UI changes, you may need to click the returned ZIP manually; the script will still capture the download event.

## Security
- Do not run this in a remote sandbox.
- Keep `--profile-dir` local and private; it contains session cookies.
