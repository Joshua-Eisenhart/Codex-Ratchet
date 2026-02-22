# A2 BOOT SEQUENCE

Run these steps IN ORDER at the start of every new chat thread.
Booting may take multiple prompts. That's normal. Don't rush it.

## STEP 1: Read session state
Read `work/SESSION_STATE.md` — current status, what works, what doesn't.

## STEP 2: Read persistent memory
Read `work/a2_state/memory.jsonl` — all past decisions, intents, failures. Append-only.
PAY SPECIAL ATTENTION to the last 10 entries — they contain critical architectural decisions.
Do not skim. These are the user's intentions. They must not need to re-explain them.

## STEP 3: Read intent summary
Read `work/a2_state/INTENT_SUMMARY.md` — the user's intentions grouped by topic.
This is the most important file for understanding what they want. Do not make them re-explain.

## STEP 4: Read doc index
Read `work/a2_state/doc_index.json` — layered index of what every doc is and what it contains.
This lets you know the corpus without re-reading everything from scratch.

## STEP 5: Read intent manifest (original)
Read `core_docs/a2 hand assembled docs/A2_UPDATED_MEMORY/A2_INTENT_MANIFEST_v1.md` — user's core principles.

## STEP 6: Read folder map
Read `work/FOLDER_MAP.md` — what goes where, size limits.

## STEP 7: Verify the machine
Run:
```
cd work/ratchet_core
python3 adversarial_test.py
python3 sim_builder.py --check --out sims/
python3 spec_ci.py
```
Report pass/fail counts. If anything fails, fix before proceeding.

## STEP 8: Read key core docs (skim, not full read — use doc_index for guidance)
- `A2_EPISODE_01_WORKING_LOG.md` — failure modes, L0/L1 graveyard, core realizations
- `AXES_MASTER_SPEC_v0.2.md` — axis definitions and build order
- `CANON_GEOMETRY_CONSTRAINT_MANIFOLD_SPEC_v1.0.md` — geometry = constraint manifold

If deeper reading is needed for the task, read the full docs. The doc_index tells you what's where.

## STEP 9: Report status
Print one paragraph: what's working, what's broken, what's next. Ask user what to work on.

## RULES
- Do not create files without being asked.
- Do not delete files without archiving first.
- Do not skip steps.
- If a file doesn't exist, say so and continue.
- The constraint ladder is FUEL for A1, not code to dump into the ratchet.
- A1 is NOT conservative. Do not fall back to classical proof thinking.
- Each graveyard item must be structurally tied to a specific term. No random padding.
- The user's intentions are the most important content. Preserve them. Don't make them re-explain.

## SEAL DISCIPLINE (CRITICAL)
A2 seals OFTEN throughout a thread, not just at the end. Saving = mining the thread's high-entropy context into low-entropy artifacts. The same process as mining a doc.

**Seal every ~10-15 substantive exchanges:**
- Append new decisions/intents/learnings to `memory.jsonl`
- Update `SESSION_STATE.md` if status changed significantly
- Update `doc_index.json` if new docs were read
- Update `INTENT_SUMMARY.md` if new intent was expressed

**Seal before thread degradation (~60-70% context):**
- Threads get weaker past a certain point. Don't exhaust context before saving.
- Start the final seal pass early. Leave headroom.
- A thread that runs to exhaustion produces weak saves.

**Remind the user:** If you haven't sealed in a while, say so. "We should seal — it's been a while since the last save." Don't wait for the user to ask.

**Model check at seal time:** When reminding to seal, also ask: "Are you still on the right model for what's next?" Different work needs different models. Building = fast/non-thinking. Deep reasoning about constraints = thinking. The user uses the model dropdown in the chat input (NOT the selector that opens new windows). Remind them of this if relevant.
