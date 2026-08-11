# SESSION SAVE — CB / Wizard / swarm work, 2026-08-06/07

Everything below is in the repo. Nothing here depends on a chat context
remaining open.

## What was RUN (not designed) — with results

| Run | Result |
|---|---|
| Wave-0 census on the real repo | 131 declared members; JSON-only scan said 56 seen / 75 never |
| Nine-voice flat council (Haiku, 9/9, $0.31, 38.6 s) | pushback/hume/zhuangzi independently caught that the census was JSON-only; zhuangzi gave the testable exclusion condition |
| Full-stack rescan (18,540 files) | SEEN 110 / NEVER 21 — voices 9/9 not 0/9. The council corrected the gate-holder. |
| Nested 3-level council (9 leaves + 3 member-councils + 1 top, $0.17) | local convergence worked; `L2-evidence` REFUSED to converge and the top propagated the refusal instead of blending — PARKED with a named blocker, arrived at structurally |
| 3x3x(2 voices + 2 tools), 31 LLM calls, 133 s | structure held; two failures found: deterministic members contaminated by my own registry, and context evaporated upward (no strategy_memory wired) |
| Deterministic exhaustive nest | negative controls PASS; contamination council caught the self-reference |
| Autoresearch sweep, 218 council compositions | full 8-member council scored 9/13; a single member scored 11/13 — **more members made it worse** |
| Digger council rounds 1-3 | 165 cross-version survivors; 7 at >=3 versions; control 0 hits |
| Lost-canon test vs 2.76M chars of current canon | 3 survived, **4 LOST** |
| Resemblance engine | 4 laws measured, then encoded and self-tested 5/5 in-repo |
| Harvest sweep over lev-os/agents | 45 skills classified; minimum full-wave coverage = 1,418 of 11,794 lines (88% less) |

## The four LOST canon items (recovered, with sources)

1. **"Axis 0 cannot be evaluated on a single isolated spinor"** — v4 through v8, five versions. A constraint on what a probe can measure. Bears directly on the psi-level spinor and Hopf-tori runs, which are single-object computations.
2. **"every piece must earn its way through B" (anti-teleology)** — v5, v6, v7. Carried an OWNER-QUOTE: *"i am not asking for this to be validated. i am building the system to prove it instead."*
3. **"Axis-2 (frame) is a gauge choice"** — legacy, v5, v7 — with the v7 qualifier that Axis 3 selecting a Weyl Hamiltonian is NOT a gauge choice because it changes the topological class of evolution.
4. **The `OWNER-QUOTE: "…" Source: /path/file.md:21` provenance convention** — used in system_v7, absent now. Everything this week rebuilt weaker versions of it.

Also recovered, still in canon: non-commutation defines the ratchet
("if you can freely swap order, it is not a ratchet — just independent
filters"); information cannot be destroyed; time IS entropy increase.

## Files written to the repo this session

```
constraint_box/config/council_member_registry_v1.json          131 members, 5 kinds
constraint_box/config/council_member_registry_skills_v1.json   skills + 9 MMM slices
constraint_box/scripts/cb_control_laws.py                      8 laws, self-test 5/5
constraint_box/docs/OWNER_RULINGS_VERBATIM_20260806.md         authoritative layer
constraint_box/docs/CB_DEFINITION_OWNER_CANON_20260806.md
constraint_box/docs/WIZARD_V4_3_ACTUAL_STRUCTURE_20260806.md
constraint_box/docs/WIZARD_NESTED_COUNCIL_WAVE_MODEL_20260806.md
constraint_box/docs/WIZARD_WAVE_MODEL_OWNER_CANON_20260806.md
constraint_box/docs/WIZARD_WAVES_COUNCILS_AND_SKILLS_20260806.md
constraint_box/docs/NESTED_COUNCILS_FULL_ENUMERATION_20260806.md
constraint_box/docs/VOICES_AND_MMM_DIVERGENCE_MECHANISM_20260806.md
constraint_box/docs/COUNCIL_MEMBER_CATALOG_20260806.md
constraint_box/docs/CB_SWARM_DRIVER_RECOVERED_DESIGN_20260806.md
constraint_box/docs/CB_EXEMPLAR_PROGRAM_20260806.md
constraint_box/docs/INTEGRATION_WAVE_PROGRAM_20260806.md
constraint_box/docs/WAVE_TAXONOMY_ROLES_AND_HARVEST_20260806.md
constraint_box/docs/CB_BIAS_AND_DIVERSITY_MEASURE_20260806.md
constraint_box/docs/AUTORESEARCH_AND_NANOCHAT_FEASIBILITY_20260806.md
constraint_box/docs/CR_LEANOUT_INVENTORY_AND_PLAN_20260806.md
constraint_box/docs/V9_STATE_AND_PLAN_20260806.md
constraint_box/docs/SESSION_SAVE_20260807.md                   this file
```

Staged in the container, **not yet in the repo** — needs placing:
`input_diversity_gate.py`, `member_coverage_auditor.py`,
`repo_state_gate.py`, `semantic_drift_gate.py` (with the commitment
ledger), `cb_receipt_index.py`, `cb_release_gate.py`,
`cb_layer_purity_and_canaries.py`, `cb_independence_gate.py`,
`strict_receipt_consumer.py`, the MMM pack `constraint-box.md`, and the
digger. Also shipped as `CB_CONTROL_PACK_20260806_v4.zip`.

## Verified capability from a chat session

- read/write the repo and the wiki
- run commands on the machine (`git`, `python3`, the CLIs)
- dispatch real LLM swarms via `claude_child_fanout.py` with receipts,
  budgets, timeouts, concurrency, `stop-after-completed`
- clone and harvest public repos

Not available from here: being a Codex parent with the installed Wizard
skills loaded, and surviving a long looping wave program in one context.
Split stands: deterministic waves and bounded fanouts here; LLM councils
in Codex where the skills live.

## Open, named

- W-PROMPT has **no council-capable candidate** in the entire harvest —
  the one wave where diversity is the product has only single-model
  skills. Build target, not import target.
- `manager.strategy_memory` is not wired; its absence caused the
  context evaporation in the 3-layer run.
- Registry needs a second table: **member x role x wave**, because
  coverage of a member is weaker than coverage of its roles.
- The 21 unreferenced registry ids are a naming defect (my `lane.*` and
  `packet.*` conventions), not missing tools.
- Sim lanes 0/10 by identifier; the tools are used under other names.
- 165 cross-version survivors remain unreviewed below the >=3 cut.
