# BOOT PROMPT — Copy-paste into any new thread

---

Follow the boot sequence in `work/A2_BOOT.md` — read it first, then execute each step in order.

Key files to read (in this order):
1. `work/SESSION_STATE.md` — what's working now
2. `work/a2_state/memory.jsonl` — persistent memory (57 entries, last 10 are critical)
3. `work/a2_state/INTENT_SUMMARY.md` — what I want, grouped by topic (READ THIS CAREFULLY)
4. `work/a2_state/doc_index.json` — map of the entire corpus
5. `work/FOLDER_MAP.md` — structure rules

Then verify the machine:
```
cd work/ratchet_core && python3 adversarial_test.py && python3 sim_builder.py --check --out sims/ && python3 spec_ci.py
```

Then report what's working, what's broken, what's next. Ask what to work on.

DO NOT skip the intent summary. DO NOT make me re-explain things that are in memory.jsonl. DO NOT fall back to classical proof thinking. READ BEFORE BUILDING.

---

## If this is a second prompt (context overflow from first):

The boot sequence may take multiple prompts. That's normal.
If the first prompt loaded files 1-4, continue with step 7+ (verify machine, read core docs, report status).

## If this is a different model (not the one that built the code):

Start from step 1. Read everything. The doc_index.json gives you the full corpus map.
The INTENT_SUMMARY.md tells you what the user wants. The memory.jsonl has every decision ever made.
