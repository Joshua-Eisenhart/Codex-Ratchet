# CB COMPLETE HANDOFF

Generated 20260807T205441Z from disk by `cb_build_handoff.py`. Nothing typed from memory.

## Read in this order

1. **00_OWNER/** — the owner's own prompts and rulings, verbatim. **This section wins over every other file here, including anything a model wrote.**
2. **01_WHAT_CB_IS/** — the definition, the bias, the voice mechanism.
3. **02_WAVES_AND_COUNCILS/** — the nested wave/council model and its enumeration.
4. **03_TOOLS_AND_LIBRARIES/** — the 44-library list and the autoresearch/nanochat feasibility.
5. **04_REPO_AND_PLAN/** — repo lean-out, v9 state, run ledger, and PROJECT_STATE.md.
6. **05_CODE/** — every script, runnable with the interpreter in 08.
7. **06_CONFIG/** — the registries.
8. **07_MEASUREMENTS/** — every receipt produced.
9. **08_EXTERNAL_DEPENDENCIES.json** — agent specs, mini-MMMs, MMM packs, skills and interpreter this work reaches for but does not contain.

## Known defects

See `04_REPO_AND_PLAN/PROJECT_STATE.md` — six verified defects, each with grep-able evidence. In particular: **do not run `cb_loop.py --cycles 20`**, it bills provider calls and its autoresearch leg has never executed.

## Regenerating

```bash
PY=~/.local/share/codex-ratchet/envs/main/bin/python3
$PY constraint_box/scripts/cb_project_state.py    # refresh state
$PY constraint_box/scripts/cb_build_handoff.py    # rebuild this package
```
