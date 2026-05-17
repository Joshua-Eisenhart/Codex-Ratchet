# Claude Thread Handoff — QIT Engines Operational, Manifold-Metric Primary (2026-05-15)

This document hands off the comprehensive context from the prior Claude thread to a fresh Claude session. Do not re-discover what is already settled; do not collapse what is divergent.

---

## Bottom line — where we are

Paired QIT engines run operationally. 18+ formal_scouts on disk this session, all `passes local rerun`. Audit chain round 1 closed (zero P1, two P2 + two P3 findings all patched). Engines compose into bipartite entanglement on a shared 4-dim carrier (peak log-negativity 0.41 at J=0.5). The 13-layer constraint manifold actively constrains the dynamics (13/13 layers fire with state diff > 1e-6 per substage; all required by negative controls). The schedule is non-abelian on random walks (92.6%) but the canonical 8-stage cycle is identity-on-2×2 by designed sign cancellation — non-trivial canonical-cycle holonomy needs higher-dim test.

Three load-bearing structural findings emerged this session:

1. **Hysteresis verdict: `irreversible_basin_fall`.** The forward-only loop's "holonomy" h_F ≈ 0.32 is pure attractor-pull; reversed-sign loop A drives the state *deeper* into the basin (h_A/h_F = 1.03), not back toward ρ_0. The previous "linear hysteresis as path geometry" reading is killed.

2. **Late-stage Bloch loses the original label.** Trainable classifier on full trajectory: 96.1%; late-only Bloch: 64%; richer readouts (SVM/RF/GB) cap at 55%. Engines transform the state (mean Bloch displacement 0.90) but the original 4-quadrant label is not recoverable from Bloch alone.

3. **The manifold encodes what Bloch loses.** A 64-dim manifold-metric feature vector (per-layer Frobenius diffs over 32 substages, pooled) recovers quadrant 0.63, octant 0.63, θ R² 0.69 — beats Bloch on every label. **The 13-layer manifold is where the surviving discriminative signal lives, not the carrier.**

---

## Thread arc — what happened in order

The prior session began with an out-of-context handoff (`CLAUDE_THREAD_HANDOFF_FLUX_TERRAIN_AXIS_OPERATOR_DISCIPLINE_20260515.md`) and the owner directive: *"go hard. use max opus. get the qit engines running. run loops of the wizard auto loop auto. grok and gemini exploration, sonnet high subagents."*

The session executed three dispatch waves under wizard /loop dynamic mode:

**Wave 1 (parallel, Opus + 5 sonnet)** — operational engine build, generator-algebra z3 closure, fresh-cycle hysteresis Stage 1, 3-inactive-layers refactor, cross-thread audit, trainable task on engines. All returned receipts; the Opus build produced 5 modules + 1 integration sim totaling ~2700 lines.

**Wave 2 (parallel, 4 sonnet)** — bipartite Type1⊗Type2 coupling, non-abelian schedule commutator, late-stage feature Popper closure, Track A MPS bug fix, persistent homology readout. All passed local rerun.

**Wave 3 (parallel, 4 sonnet patches + 1 new scout + 1 bash exploration)** — canonical-source-drift patches on sims #6 and #9, bipartite caveat surfaced into result JSON, Track A α-sweep validates 0.31 on stable curve, TEBD-native 13-layer composition built (1.1s runtime, MI=4.95 nats), richer-readout scout returned the manifold-metric primacy finding.

Opus audit ran on all 11 wave-1+2 receipts in fresh context. Verdict: 3 CLEAN, 4 NOTE, 2 P2 (source-drift), 2 P3 (caveat + α-origin), 0 P1. All findings patched in wave 3.

---

## Standing facts (what's true now)

| Fact | Status | Evidence file |
|---|---|---|
| Paired engines run as composable objects with Lindblad ODE evolution | `canonical by process` candidate (1 round of audit clean) | `sim_paired_chiral_operational_lindblad_composer_with_terrain_readout_integration_probe.py` (21/21) |
| Engines compose into bipartite entanglement via shared `J·σ_z⊗σ_z` | `passes local rerun` | `sim_paired_engine_bipartite_logarithmic_negativity_coupling_probe.py` (peak E_N=0.41 @ J=0.5, Spearman=0.99) |
| 13-layer constraint manifold actively enforces, every layer load-bearing | `passes local rerun` | `claude_integrated_manifold_modules/active_layer_constraint_enforcers.py`; v3 sim 35/35 |
| 3:1 Fe asymmetry derives from Pauli generator algebra (no spec-table grounding) | `passes local rerun` | `sim_fe_asymmetry_pauli_generator_algebra_z3_derivation_probe.py` (UNSAT on Fe→σ_z swap) |
| Schedule is non-abelian on random walks (92.6% non-commuting) but canonical-cycle cancels in 2D | `passes local rerun` | `sim_non_abelian_schedule_order_commutator_probe.py` |
| Hysteresis is `irreversible_basin_fall`, not path geometry | `passes local rerun` | `sim_fresh_cycle_hysteresis_independence_falsifier_probe.py` (r(20)=0.10); `sim_loop_A_reversibility_attractor_vs_path_geometry_falsifier_probe.py` (h_A/h_F=1.03) |
| Engines preserve total information, destroy the 4-quadrant label on Bloch | `passes local rerun` | `sim_engine_late_stage_feature_only_classification_falsifier_probe.py` (verdict `front_loaded`); `sim_engine_late_stage_mutual_information_encoded_signal_probe.py` (MI ratio 2.84×) |
| Manifold-metric trajectory > Bloch trajectory for label decode | `passes local rerun` | `sim_late_stage_richer_readout_family_information_recovery_probe.py` (manifold-metric quadrant 0.63 vs Bloch 0.55) |
| 4 topology classes (Funnel/Vortex/Pit/Hill) separate via persistence ≥ raw on 32-substage trajectories | `passes local rerun` (Δ=+0.01) | `sim_engine_trajectory_persistent_homology_readout_feature_probe.py` |
| Full 13-layer + G-structure + both-chiral + source-native composition runs in one sim (dense) | `passes local rerun` | `sim_full_thirteen_layer_active_g_structure_both_chiral_source_native_composition_probe.py` |
| TEBD-native 13-layer composition runs (bond_max=16, faster than dense) | `passes local rerun` | `sim_full_thirteen_layer_tebd_native_evolution_strict_composition_probe.py` |
| Track A MPS bug located + fixed (XX+YY annihilates vacuum); α-sweep validates α=0.31 | `passes local rerun` | `claude_integrated_manifold_modules/mps_contraction_and_special_holonomy_comparator.py`; α-sweep 0.305→0.536 |
| Trainable engine-feature classifier achieves 96.1% (vs 27.6% random-engine baseline) | `passes local rerun` | `sim_qit_engines_perform_classification_task_with_trainable_readout_probe.py` |

---

## Canonical source-of-truth (read before any QIT-engine work)

All engine specs are in `system_v5/ops/formal_scouts/canonical_qit_engine_specs.py`. Any new sim that defines its own `TYPE_ONE_TOPOLOGIES` or `OPERATOR_GENERATORS` is source-drift — the audit found this pattern in two sims (now patched). Always import:

```python
from canonical_qit_engine_specs import (
    PERCEPTION_L_MATRICES,
    OPERATOR_GENERATORS,
    TYPE_ONE_TOPOLOGIES,
    TYPE_TWO_TOPOLOGIES,
    H_TYPE_ONE,
    H_TYPE_TWO,
    MANIFOLD_LAYERS,
    ENGINE_SCHEDULE_TYPE_ONE,
    ENGINE_SCHEDULE_TYPE_TWO,
    get_engine_spec,
    get_topology_spec,
    get_lindblad_params,
    get_loop_class_op_sign,
    get_schedule,
)
```

Schema: topology dicts use `outer`/`inner` field names (NOT `major`/`minor` — that was the drift schema). Each `outer`/`inner` carries `op`, `sign`, `result`. Engine type maps to chirality sign: type 1 → +1, type 2 → −1. Field naming convention enforced by lint and by audit.

---

## Operating modules

Under `system_v5/ops/formal_scouts/`:

- `engine_core.py` — `EngineCore` class with Lindblad ODE evolution per substage (operator unitary → ODE → 13-layer manifold → terrain dephase + loop placement).
- `engine_schedule.py` — `Schedule` class composing `Φ_engine,N ∘ … ∘ Φ_engine,1` and `run_paired_engines` for joint Type 1 + Type 2 runs.
- `engine_readouts.py` — `terrain_of_arrival`, `pattern_resolution`, `entropy_signature`, `persistence_class`, `holonomy_phase`.
- `claude_integrated_manifold_modules/` — 10+ modules including `active_layer_constraint_enforcers.py` (all 13 layers active post-refactor), `mps_contraction_and_special_holonomy_comparator.py` (Track A vacuum-breaking patch), `special_holonomy_dynamic_projectors.py` (G-structure reduction chain), etc.

These names contain the token `engine` which is allowed in non-`sim_*.py` modules. The lint forbids `engine`, `type1`, `type2`, `mbti`, `jung` in sim filenames; helper modules are exempt.

---

## Surviving Popper opens (do not skip past these)

| Open | Decisive check | Receipt link |
|---|---|---|
| Manifold-metric advantage: genuine encoding or feature-dimensionality artifact? | Run manifold-metric on bond-dim-1 baseline; if accuracy stays ≈ 0.63 it's artifact, if collapses to chance it's genuine | `sim_late_stage_richer_readout_family_information_recovery_probe.py` |
| Canonical-cycle non-abelianism at higher dim | Lift canonical 8-stage to 4-qubit tensor product; measure commutator at 16-dim | `sim_non_abelian_schedule_order_commutator_probe.py` |
| Late-stage decode threshold (0.75 cross): can per-layer (separated) manifold-metric features cross it? | Run per-layer features (each layer's trajectory as separate 32-dim) vs pooled 64-dim | `sim_late_stage_richer_readout_family_information_recovery_probe.py` |
| Late-stage via sequence-aware readout (transformer) | Train small transformer on substage-indexed feature sequence | `sim_engine_late_stage_mutual_information_encoded_signal_probe.py` |
| Round-2 audit (audit-chain fixed-point closure) | Run opus audit on the post-patch receipt set; need zero findings to close fixed point | `system_v5/docs/AUDIT_REPORT_ELEVEN_WORKER_RECEIPTS_20260515.md` |
| Bipartite initial-state generality | Sweep |ψ_0⟩ over 5+ initial states; show peak E_N curve is not specific to |+⟩⟨+|⊗|+⟩⟨+| | `sim_paired_engine_bipartite_logarithmic_negativity_coupling_probe.py` |

---

## Live divergent readings (do not collapse)

Three readings remain admitted by current evidence; bounded work has not yet excluded any:

- **R1: engines as information-preserving channels** that rearrange labels into the manifold state (consistent with MI ratio 2.84× and manifold-metric primacy).
- **R2: engines as basin-fall machines** whose "geometry" is irreversible Lindblad dissipation (consistent with hysteresis verdict and h_A/h_F=1.03).
- **R3: engines as non-abelian-on-random-walks-only**; canonical cycle is trivial in 2D (consistent with non-abelian scout's canonical-cycle cancellation note).

R1, R2, R3 are not mutually exclusive — they may be co-true at different probes. The harness rule is: hold them all open until bounded work decides.

---

## Doctrinal flag for the owner

The doctrine "geometry stack = constraint ratchet iff non-commutative ordering" needs sharpening. Non-commutativity exists (92.6% on random walks, max ‖C-I‖=1.98) but the canonical 8-stage schedule cancels in 2D (designed). The ratchet that operates in the canonical cycle is the irreversible basin-fall ratchet, not a reversible path-holonomy ratchet. The owner may want to:

1. Promote the basin-fall reading to canonical and demote the path-holonomy reading; OR
2. Lift the canonical schedule to higher dim and test if path-holonomy survives; OR
3. Keep both readings open with the explicit recognition that "ratchet" means different things at different probes.

This is the kind of question the harness expects the owner to decide, not the agent. The agent has presented the divergence; flagging for owner attention.

---

## Status labels (binding, never collapse)

| Label | Meaning | Current canonical-by-process count |
|---|---|---|
| `exists` | file present | 18+ |
| `runs` | exit 0 | 18+ |
| `passes local rerun` | fresh run all_pass=True | 18+ |
| `canonical by process` | passes local rerun + SIM_TEMPLATE + tool manifest + non-empty reasons + classification field + round-2 audit clean | **0** (round-1 audit done, round-2 pending) |

Round-2 audit is the next gate for any sim to advance to `canonical by process`.

---

## Tool stack (load-bearing tools used in current scouts)

- `numpy`, `scipy.integrate`, `scipy.linalg` — density matrix algebra, ODE, expm
- `sympy` — commutator verification, partial-transpose identity check
- `z3` — UNSAT proofs (admissibility counts, generator-algebra, layer-replacement)
- `pytorch` — MLP readouts, training loops
- `quimb`, `cotengra`, `opt_einsum` — tensor networks, MPS, TEBD
- `sklearn` — k-NN, SVM, RandomForest, GradientBoosting, mutual_info
- `gudhi` — persistent homology (giotto-tda not installed; gudhi is the alternative)
- `e3nn`, `torch_geometric` — equivariant features, GNN message passing (covered by prior sims)
- `toponetx`, `xgi` — simplicial complexes, hypergraphs (covered by prior sims)

All sims declare TOOL_MANIFEST with `tried`, `used`, non-empty `reason`. At least one tool must be `load_bearing` outside the numeric baseline.

---

## Interpreter, not optional

Run all sims with: `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3`. The repo Makefile defines `PYTHON` to this path; do not use system python3 or `.venv/bin/python` (does not exist in this worktree).

---

## Sim contract (every formal_scout must)

- Start from `system_v4/probes/SIM_TEMPLATE.py` (or follow its structure if not literally copy-pasted).
- `classification = "formal_scout"` (or `"canonical"` for canonical sims, but `formal_scout` is the safe default this session).
- `promotion_allowed = False`.
- `TOOL_MANIFEST` with `tried`, `used`, `reason` non-empty for every tool.
- `TOOL_INTEGRATION_DEPTH` declares which tools are `load_bearing`, `supportive`, or `None`.
- Positive predicates + negative predicates + boundary tests.
- Result JSON written to `system_v5/ops/formal_scouts/results/{stem}_results.json` with `all_pass` boolean, the per-predicate verdicts, and structured surviving alternatives.

---

## What the fresh thread should NOT do (no-go zones)

- Do NOT git commit without explicit owner directive.
- Do NOT rebase under any circumstances.
- Do NOT add `engine`, `type1`, `type2`, `mbti`, `jung` to `sim_*.py` filenames. Helper modules (not starting with `sim_`) are exempt — the lint checks sim filenames.
- Do NOT promote any sim to `canonical` without round-2 audit clean.
- Do NOT edit READ ONLY-labeled files or directories.
- Do NOT collapse the three live readings (R1/R2/R3) into one "winner" without bounded work that excludes the others.
- Do NOT report "ALL PASS" without specifying which sims, which run, and citing the result JSON path from the current session.
- Do NOT introduce new doctrinal labels (IGT, I-Ching, Jungian, win/lose semantics) into sim code or JSON — owner has been explicit that Rosetta mapping is a separate post-hoc pass.

---

## Recommended first 5 minutes of the fresh thread

1. Read this doc.
2. Read `system_v5/docs/CROSS_THREAD_AUDIT_CODEX_VS_CLAUDE_SIM_ESTATE_20260515.md` (cross-thread context).
3. Read `system_v5/docs/AUDIT_REPORT_ELEVEN_WORKER_RECEIPTS_20260515.md` (last audit + patch resolution).
4. Read `system_v5/ops/formal_scouts/canonical_qit_engine_specs.py` (single source of truth).
5. Read `system_v5/ops/formal_scouts/engine_core.py` (operational Lindblad evolution).
6. Read `system_v5/ops/formal_scouts/results/paired_chiral_operational_lindblad_composer_with_terrain_readout_integration_probe_results.json` (the 21/21 anchor receipt).

Then dispatch the next work — see Recommended next moves below.

---

## Recommended next moves (in priority order)

1. **Round-2 audit** on the post-patch receipt set (opus, fresh context). Need zero findings to close the audit-chain fixed point per owner doctrine. This unblocks every sim's promotion to `canonical by process`.

2. **Bond-dim-1 manifold-metric control** — the decisive Popper check on the manifold-metric primacy finding. If manifold-metric accuracy stays at 0.63 under bond-dim-1, it is a feature-dimensionality artifact. If it collapses to chance, the manifold-encoding claim is genuine.

3. **Per-layer manifold-metric feature variant** — separate each of the 13 layers' Frobenius-diff trajectories into its own feature column (13 × 32 = 416-dim, or per-layer 32-dim chunks). Test if the decode threshold of 0.75 is crossed.

4. **Higher-dim canonical-cycle non-abelianism** — lift the canonical 8-stage schedule to a 4-qubit tensor product representation (16-dim). Measure commutator norm. If designed-cancellation breaks at higher dim, the canonical schedule IS non-trivially path-dependent at the right Hilbert dimension.

5. **Transformer sequence-aware readout** on late-stage features — wildcard; sklearn family caps at 0.55, sequence-aware may unlock decode.

6. **Owner-directed doctrinal sharpening** — present the basin-fall vs path-holonomy choice to the owner; do not resolve it in the agent.

---

## File inventory for this session

### New sims (`system_v5/ops/formal_scouts/`)
- `sim_paired_chiral_operational_lindblad_composer_with_terrain_readout_integration_probe.py`
- `sim_paired_engine_bipartite_logarithmic_negativity_coupling_probe.py`
- `sim_non_abelian_schedule_order_commutator_probe.py`
- `sim_engine_late_stage_feature_only_classification_falsifier_probe.py`
- `sim_engine_late_stage_mutual_information_encoded_signal_probe.py`
- `sim_late_stage_richer_readout_family_information_recovery_probe.py`
- `sim_fresh_cycle_hysteresis_independence_falsifier_probe.py`
- `sim_loop_A_reversibility_attractor_vs_path_geometry_falsifier_probe.py`
- `sim_fe_asymmetry_pauli_generator_algebra_z3_derivation_probe.py`
- `sim_engine_trajectory_persistent_homology_readout_feature_probe.py`
- `sim_qit_engines_perform_classification_task_with_trainable_readout_probe.py`
- `sim_full_thirteen_layer_active_g_structure_both_chiral_source_native_composition_probe.py`
- `sim_full_thirteen_layer_tebd_native_evolution_strict_composition_probe.py`

### New modules (`system_v5/ops/formal_scouts/`)
- `canonical_qit_engine_specs.py`
- `engine_core.py`
- `engine_schedule.py`
- `engine_readouts.py`

### Patched modules
- `claude_integrated_manifold_modules/active_layer_constraint_enforcers.py` (3 inactive layers now active)
- `claude_integrated_manifold_modules/mps_contraction_and_special_holonomy_comparator.py` (Track A vacuum-breaking)

### Patched sims (audit response)
- `sim_qit_engines_perform_classification_task_with_trainable_readout_probe.py` (canonical-source import)
- `sim_engine_late_stage_feature_only_classification_falsifier_probe.py` (canonical-source import)
- `sim_thirteen_layer_active_nested_manifold_mps_special_holonomy_deep_graveyard_dynamic_tensor_network_probe.py` (α-sweep predicate added)
- `sim_paired_engine_bipartite_logarithmic_negativity_coupling_probe.py` (initial-state caveat surfaced)

### New docs (`system_v5/docs/`)
- `CLAUDE_THREAD_HANDOFF_QIT_ENGINES_OPERATIONAL_MANIFOLD_PRIMARY_20260515.md` — this file
- `AUDIT_REPORT_ELEVEN_WORKER_RECEIPTS_20260515.md` — audit chain round 1 findings + patch resolution
- `CROSS_THREAD_AUDIT_CODEX_VS_CLAUDE_SIM_ESTATE_20260515.md` — Codex+Claude sim composition audit

### Provider receipts (`system_v5/ops/formal_scouts/provider_receipts/`)
- `20260515T205043Z_grok_xai_qit_engines_operational_wide_exploration.json`
- `20260515T205043Z_gemini_qit_engines_operational_wide_exploration.json`
- `20260515T213536Z_grok_xai_topology_entropy_tensor_network_provider_review.json`
- `20260515T213536Z_gemini_topology_entropy_tensor_network_provider_review.json`

---

## Worktree info

This thread ran in worktree `/Users/joshuaeisenhart/Desktop/Codex Ratchet/.claude/worktrees/flamboyant-jackson-4d7f5f`. Branch `claude/flamboyant-jackson-4d7f5f`. All file paths in this doc are absolute against `/Users/joshuaeisenhart/Desktop/Codex Ratchet/` and apply equally in the worktree and the main repo (worktree shares the same file tree mounted under the worktree path; canonical paths use the main repo root).

---

## Closing note to the fresh thread

The math is locked. The engines run. The audit has caught what it catches in round 1. The owner doctrine "audit must come back clean twice" puts round 2 as the next gate, not new exploration. Do not skip past audit closure to chase new findings — every new scout dispatched without audit closure widens the receipt set faster than it can be verified.

Hold the divergence between R1, R2, R3 readings. The owner has been explicit: do not collapse surviving readings; do not promote agent-side decisions on doctrinal questions; do not "improve" adjacent code while debugging. Surgical changes only.

Wizard mode is on. The /loop autonomous mode was active in the prior thread. Whether to keep auto-looping in the fresh thread is the owner's call — the fresh thread should ask, not assume.
