# CB work order

Do these in order. Verify each yourself — don't trust anything here.
Nothing under `constraint_box/` is tracked, so every step reverses.

Interpreter for everything:
`~/.local/share/codex-ratchet/envs/main/bin/python3`

---

1. **Stop the corpus from eating its own output.**
   `cb_integrated_run.py:38` scans `REPO.rglob("*")`. Exclude
   `constraint_box/receipts/` and `constraint_box/handoff/`.
   Verify: rerun it, `never_run` should come back at 21.

2. **Quarantine the poisoned receipts, both copies.**
   `constraint_box/receipts/integrated_run_*.json` and
   `constraint_box/handoff/*/07_MEASUREMENTS/integrated_run_*.json`
   Move to `constraint_box/_quarantine/`. Three files, twice over.
   Verify: `grep -r "evaluated on a single isolated spinor" constraint_box/`
   returns nothing outside `_quarantine/`.

3. **Stop the handoff builder writing into the scanned tree.**
   `cb_build_handoff.py` writes to `constraint_box/handoff/`. Point it
   outside the repo, or exclude it permanently in step 1.

4. **Fix the autoresearch schema mismatch.**
   `cb_autoresearch_loop.py` reads `params["ladder"]`;
   `cb_tuned_params.json` doesn't have it. Also
   `cb_loop.py` discards the return code, so the traceback reads as a
   clean "nothing to write".
   Verify: run `cb_autoresearch_loop.py` alone, expect rc=0.

5. **Give the falsifier a SURVIVED path.**
   `cb_wave_falsifier_v3.py` hardcodes `councils_run: 0` in `TARGETS`,
   so celpy's rule fails every time.
   Verify: set a target to conformant numbers, confirm it returns
   something other than KILLED.

6. **Fix `--resume`.**
   `cb_loop.py:75` is `load_state() if a.resume else load_state()`.
   Also the dead-cycle counter is process-local, so every resume grants
   a fresh budget.

7. **Fix the hollow council members.**
   `cb_all_tools_council.py` twins differ on nine fields at once, so ten
   members pass on `promotion_allowed` alone without touching their
   library: pygit2, blake3, xxhash, rfc8785, zstandard, lmdb, msgspec,
   beartype, maude, deepdiff.
   Fix: one field difference per twin pair.
   Verify: repair `promotion_allowed` in the bad twin, confirm all 23
   still discriminate.

8. **Remove `"could_disagree": True`** from
   `cb_wave_falsifier_v2.py:88` — it asserts the thing the test measures.

9. **Commit.** All 66 paths under `constraint_box/` are untracked. Put
   them on a clean branch. Don't merge into the dirty one.

---

## Don't run

`cb_loop.py --cycles 20` — it bills OpenRouter and `claude` calls
through `cb_wave_falsifier_v3` → `cb_multi_provider`, and its
autoresearch leg has never executed.

## After these

The Failure wave has three councils; only `failure.falsifier` has run.
Decision and Follow-Up waves don't exist. Five managers and the collapse
auditor are specced and never run. One skill of about 110 has been run
as a skill.

## Context

`~/Desktop/CB_COMPLETE_HANDOFF.zip` — the whole estate.
`00_OWNER/` in it is the owner's own prompts; read that before any
model-written file, including this one.
