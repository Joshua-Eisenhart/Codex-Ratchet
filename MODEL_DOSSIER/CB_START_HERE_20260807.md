# CB — what we're doing and where everything is

Plain orientation. No authority markers, no doctrine framing.

## The goal

Build a deterministic gate that constrains LLMs.

Many diverse models run in nested councils, arranged in waves. They
propose, critique, and diverge. Code — not a model — decides what gets
admitted. The gate never says what's true; it says whether a claim
arrived in a shape that can be checked, and refuses what can't be.

Why: the earlier CR versions had deterministic gates and no exploration
at them. Models absorbed the gate's vocabulary and stopped proposing
anything new. Diverse models under different prompts can't collapse that
way, so the swarm is the exploration and CB is the wall it runs into.

CB light = lean, mostly Python libraries, starts in under a second.
CB heavy = the same thing plus the sim engines (jax, torch, julia,
qutip and friends), ~1.2 GB and ~10 seconds to import.

## Where things are

**The work**
```
~/Codex-Ratchet/constraint_box/
    scripts/     30 .py   the code
    docs/        51 .md   designs and notes
    config/       8 .json registries and tuned params
    receipts/   169 .json every run's output
    handoff/              packaged bundle + zip
    PROJECT_STATE.md      generated from disk, regenerable
```

**Your prompts and rulings**
```
~/Codex-Ratchet/constraint_box/docs/OWNER_RULINGS_VERBATIM_20260806.md
```

**The bundle**
```
~/Desktop/CB_COMPLETE_HANDOFF.zip
~/Codex-Ratchet/constraint_box/handoff/CB_COMPLETE_20260807T205441Z/
```

**What the code reaches for but doesn't contain**
```
~/Codex-Ratchet/.claude/agents/           23 agent specs, incl. 9 voices
~/wiki/wizard/packet-v4-3-current/        the Wizard packet
    mmm/mini/full/voices/md/              9 mini-MMMs the voices require
~/Codex-Ratchet/constraint_box/mmm/packs/ 6 MMM packs
~/.codex/skills/                          44 skills
~/.agents/skills/                         codex-autoresearch and others
~/.claude/skills/                         7 skills
~/.local/share/codex-ratchet/envs/main/bin/python3   the interpreter (3.8 GB env)
```

Run everything with that interpreter. The system python at
`/opt/homebrew/bin/python3` does not have the libraries and will give
wrong answers — I made that mistake and reported "11 of 15 lanes absent"
when all 18 were installed.

## What works

Verified by rerunning, in your environment:

- 28 of 33 Python libraries wired into CB, each with a passing and a
  refusing test — `cb_light_integrations.py` 19/19,
  `cb_light_tier2.py` 21/21
- 23 tools voting as council members. **13 discriminate on library
  behaviour; 10 discriminate only on one dict field.** The good/bad
  twins differ on nine fields at once, so ten members rode on
  `promotion_allowed` and never exercised their library: pygit2,
  blake3, xxhash, rfc8785, zstandard, lmdb, msgspec, beartype, maude,
  deepdiff. Every member of L0_CUSTODY is in that list, so the
  minimal-council pass can only pick a hollow member for that layer
- multi-provider dispatch: Haiku plus OpenRouter free models (7 NVIDIA
  Nemotron variants available), real per-lane costs and latencies
- the premortem skill run to its own contract: 10 failure reasons,
  10 parallel subagents, 5 declared sections, gated against the skill's
  own output shape
- a falsification wave: 4 children x 5 members answering the same
  question, debate round fired. The divergence numbers are real
  (difflib similarity 0.16-0.41) but the receipt also carries
  `"could_disagree": True` hardcoded at `cb_wave_falsifier_v2.py:88` —
  the receipt asserts the property the test exists to measure
- lateral spread measured: ~2.8x on both cheap and heavy tiers, then
  negative past the knee

## What's broken

Six things, each checkable by grep. Full evidence in `PROJECT_STATE.md`.

1. The falsifier can't return SURVIVED — `councils_run: 0` is hardcoded
2. `--resume` is a no-op — both branches of the ternary are identical
3. `cb_loop.py --cycles 20` bills provider calls. Don't run it
4. Autoresearch has never executed — schema mismatch on `ladder`
5. `never_run` counts text mentions, not execution. Real execution
   coverage is 21 of 43 role units
6. Three receipts hold text where a regex dropped a negation, so two
   claims read as the opposite of their source. Files named in
   `PROJECT_STATE.md`
7. **The regeneration recipe below deepens defect 5.**
   `cb_integrated_run.py:38` scans `REPO.rglob("*")`, and
   `cb_build_handoff.py` copies receipts into
   `constraint_box/handoff/` — inside that scan. The three poisoned
   receipts now exist twice, and every rebuild adds another copy.
   Fix order: exclude `constraint_box/handoff/` AND
   `constraint_box/receipts/` from the corpus first, then quarantine
   both trees, then the rest
8. Ten of the 23 council members are hollow (see above). The
   good/bad twins must differ on ONE field at a time, or a member can
   pass without touching its library

None of it is committed. All 66 paths under `constraint_box/` are
untracked — on disk, not in git history.

## What hasn't been built

- Decision and Follow-Up waves (only the Failure wave exists, and only
  one of its three councils has run)
- The five managers and the collapse auditor — specced, never run
- Skills: 1 of ~110 has been run as a skill

## Regenerating any of this

```bash
PY=~/.local/share/codex-ratchet/envs/main/bin/python3
cd ~/Codex-Ratchet
$PY constraint_box/scripts/cb_project_state.py    # refresh state from disk
$PY constraint_box/scripts/cb_build_handoff.py    # rebuild the bundle
```

**Do not run the second command until defect 7 is fixed.** It writes
receipt copies into the tree that `cb_integrated_run.py` scans, so each
rebuild adds another copy of the poisoned receipts to the corpus.
