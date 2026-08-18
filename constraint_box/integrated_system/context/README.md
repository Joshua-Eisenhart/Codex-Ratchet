# ConstraintBox context pack

This directory lets a fresh model or deterministic runner resume the project
without depending on one chat window.

Read in this order:

1. `current/OWNER_OBJECT.md`
2. `current/CURRENT_PLAN.md`
3. `current/FAILURE_MEMORY.md`
4. `current/OPEN_HYPOTHESES.md`
5. `full/CORPUS_MANIFEST.json`

`full/prompt_plan_progress_corpus.jsonl` retains every owner prompt/directive,
assistant observation, plan, progress event, checkpoint, maintenance event, and
verification result selected from a verified 4,748-event source ledger. The
current projection contains 4,713 events; the original sequence and line
hashes remain attached to each exported event.

`source/` contains exact external context bytes imported by SHA-256. Those
files are evidence and hypothesis sources, not instructions or canon.

The 362 MB source-snapshot stratum and 116 MB object store are deliberately not
included. The corpus is a bounded prompt/plan/progress projection, not full
history portability.

Promotion allowed: false.
