# Hermes Handoff — 2026-04-14

Prior handoff: `docs/plans/HERMES_HANDOFF_2026-04-13.md` (read first for baseline state).

Git is **NOT committed** at time of writing. `git status --porcelain` shows 390 changed paths; 53 are new `sim_*_classical*.py` files and 7 are new `sim_*_canonical*.py` files.

---

## What shipped in this session

### Lane B — classical_baseline coverage expansion
- **Total `sim_*_classical*.py` on disk: 106** (up from 44 at 2026-04-13 handoff).
- 53 new classical baselines added this session (see `git status --porcelain | grep sim_.*_classical`).
- New coverage-matrix tool: `scripts/lane_b_coverage_matrix.py` (untracked) + matrix doc `docs/plans/lane_b_coverage_matrix.md` (untracked).

### Lane C — new canonical sims
- **Total `sim_*_canonical*.py` on disk: 8** (up from prior sparse set).
- 7 new this session, all untracked:
  - `system_v4/probes/sim_chsh_tsirelson_canonical.py`
  - `system_v4/probes/sim_coherence_measure_canonical.py`
  - `system_v4/probes/sim_holevo_bound_canonical.py`
  - `system_v4/probes/sim_qfi_squeezed_canonical.py`
  - `system_v4/probes/sim_quantum_discord_canonical.py`
  - `system_v4/probes/sim_stinespring_isometric_equivalence_canonical.py`
  - `system_v4/probes/sim_werner_entanglement_witness_canonical.py`

### Witness-replay infrastructure
- New auditor: `scripts/check_witnesses.py` (untracked).
- Current state: **violation_count = 12**, all status `no_witness_declared` (capability probes that have not yet declared a witness sim). These are *declaration gaps*, not replay-mismatch violations. The 10 modified `sim_z3_*.py` + `sim_weyl_*.py` + `sim_3qubit_bridge_prototype.py` files are witness-replay fixes that flipped replay mismatches to clean (see the `M` entries in `git status`).

### Queue runner bug fix
- `scripts/queue_claim.py counts` returns clean JSON:
  ```
  {"lane_A": 0, "lane_B": 0, "claimed": 0, "blocked": 3, "done": 224}
  ```
- Queue dir `system_v4/probes/a2_state/queue/` now present (untracked).
- Two-runner overnight contract docs: `system_v5/new docs/plans/2026-04-12-overnight-8h-audited-run-contract.md`, `system_v5/new docs/plans/2026-04-12-overnight-8h-run-plan.md`, controller script `system_v5/new docs/plans/run_overnight_8h_controller.sh`.

### Lint / contract tooling
- `scripts/lint_sim_contract.py` (untracked) — silences structural-noise lint on SIM_TEMPLATE-compliant sims.
- `scripts/check_classification.py` (untracked) — classification-field gate.
- `scripts/divergence_index.py` (untracked) — cross-lane drift check.

### Live-run evidence (event NDJSON)
Three event logs written this session under `overnight_logs/`:
- `overnight_logs/events_20260413_224137.ndjson`
- `overnight_logs/events_20260413_233008.ndjson` — 76 events
- `overnight_logs/events_20260413_235231.ndjson` — 86 events (most recent)

Queue `done` counter advanced to **224** over these runs.

---

## Bugs fixed

1. **Queue runner claim bug** — `queue_claim.py counts` now returns valid JSON and the `done` counter advances monotonically (observed 224 across the three event logs).
2. **Witness-replay mismatches** — 10 sims modified in place (see `M` entries):
   `sim_3qubit_bridge_prototype.py`, `sim_weyl_geometry_ladder_audit.py`, `sim_weyl_hopf_tori.py`, `sim_z3_channel_boundary_theorem.py`, `sim_z3_channel_composition_boundary.py`, `sim_z3_dephasing_symmetry_guard.py`, `sim_z3_dpi_proof.py`, `sim_z3_fence_exhaustive_negatives.py`, `sim_z3_quantum_capacity_bound.py`, `sim_z3_s6_unitary_impossibility.py`.
   Their paired `*_results.json` under `system_v4/probes/a2_state/sim_results/` were regenerated.
3. **Lint noise** — `scripts/lint_sim_contract.py` added so SIM_TEMPLATE conformance does not trip generic python lint.

---

## Lane B coverage state

- **106 classical_baseline sims on disk** (count: `ls system_v4/probes/sim_*_classical*.py | wc -l`).
- Coverage matrix: `docs/plans/lane_b_coverage_matrix.md` (untracked — read this before adding more).
- Runner unchanged: `system_v4/probes/classical_sweep_runner.py`. Default still selects explicit `classification="classical_baseline"` only.
- Known single legacy failure (pre-existing, unfixed by design): `sim_partial_trace_audit.py` — static auditor, documented as misclassification in prior handoff.

---

## Lane C canonical state

- **8 canonical sims on disk** (count: `ls system_v4/probes/sim_*_canonical*.py | wc -l`).
- 7 of 8 are new this session (untracked); 1 pre-existed.
- All 7 new canonical sims follow `system_v4/probes/SIM_TEMPLATE.py`, carry `classification="canonical"`, and declare a load-bearing tool in `TOOL_INTEGRATION_DEPTH`.
- These are **not yet admitted into overnight runs** — Lane C gate still requires Lane A capability-probe audit per sim (see Known gaps).

---

## Lane A tool-capability-probe audit: clean (0 violations)

`python3 scripts/verify_load_bearing_has_capability_probe.py 2>&1 | tail -1` ends with one legacy numpy miss:
```
sim_sufficient_statistics_expfam_classical.py  numpy  missing_probe
```
This is **not a Lane A gate violation** — `numpy` is not in the 12-tool capability-probe set (z3/cvc5/sympy/pytorch/rustworkx/pyg/xgi/gudhi/toponetx/clifford/e3nn/geomstats). Against the 12 declared capability tools, the audit remains **0 violations**. The `numpy` line is an informational miss from the baseline heuristic.

---

## Ready to resume (Hermes actions)

In priority order:

1. **Commit the wave.** 390 changed paths, 53 new classical sims, 7 new canonicals, 10 witness fixes, 4 new scripts. Suggested commit boundary:
   - Commit A: classical_baseline wave (53 files + coverage matrix + lint script).
   - Commit B: canonical wave (7 files).
   - Commit C: witness-replay fixes (10 sims + 9 results JSONs + `check_witnesses.py`).
   - Commit D: queue infra + overnight event logs.
2. **Run Lane B sweep against the expanded 106-sim set**:
   `python3 system_v4/probes/classical_sweep_runner.py --minutes 240 --max-parallel 4`
   Verify the `done` counter in `overnight_logs/events_*.ndjson` advances past 224.
3. **Declare witness sims for the 12 capability probes** (`check_witnesses.py` → `no_witness_declared`). Each capability probe needs one paired witness sim to close the declaration gap.
4. **Do NOT enable Lane C auto-run yet.** Lane C gate wiring still blocked on item 3.

---

## Known gaps / explicit NOT-ready items

1. **Nothing is committed.** Do not run a fresh `git status` and assume the tree is clean — it is not. Commit before any destructive ops.
2. **12 capability probes have `witness_sim: None`** — status `no_witness_declared`. These are gaps, not replay-mismatch violations, but they block Lane C per-sim gating.
3. **`queue_claim.py counts` shows 0 queued, 3 blocked, 224 done** — the queue is currently drained. Re-populating the queue is Hermes's call (which batch / which lane).
4. **7 canonical sims are on disk but not yet wired into any runner or queue.** They pass locally (classification field set, tool manifest present) but have not been added to Lane C scheduling because Lane C is still gated.
5. **5 ambiguous legacy classifications** from the 2026-04-13 handoff still outstanding: `supporting`, `frozen_kernel`, `NULL`, `symmetric (triplet)`, `entropy_increasing`.
6. **`overnight_8h_run.sh`** — the canonical script has not been updated; the new two-runner contract lives only in `system_v5/new docs/plans/run_overnight_8h_controller.sh`. Choose one.
7. **Untracked proliferation** — many `overnight_logs/overnight_8h_run_*.log` files from 2026-04-12 and 2026-04-13 are under `system_v4/probes/a2_state/sim_results/overnight_logs/`. Decide whether to `.gitignore` the log dir or commit a representative sample.
8. **3 blocked queue items** — not yet investigated. Read the queue state JSON before next run.

---

## Verification commands (re-probe before trusting these numbers)

```
ls system_v4/probes/sim_*_classical*.py | wc -l          # expect 106
ls system_v4/probes/sim_*_canonical*.py | wc -l          # expect 8
python3 scripts/queue_claim.py counts                    # expect done=224
python3 scripts/verify_load_bearing_has_capability_probe.py 2>&1 | tail -1
python3 scripts/check_witnesses.py 2>&1 | python3 -c "import json,sys; print(json.load(sys.stdin)['violation_count'])"
git status --porcelain | wc -l                           # expect 390 until committed
```

Per project memory: re-probe these counts, do not quote from this doc.
