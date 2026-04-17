# Tier B status — 2026-04-16

Status: blocker

Read / bootstrap completed:
- `CLAUDE.md`
- `system_v5/new docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- `system_v5/new docs/LLM_CONTROLLER_CONTRACT.md`
- `system_v4/probes/SIM_TEMPLATE.py`
- wiki `current/` spine via harness-bootstrap order
- session recall on `g_tower_math_backlog` + `constraint_manifold_simultaneous`

Requested read targets not found in this checkout:
- `system_v5/new docs/HERMES_OPERATING_CONTRACT.md`
- `wiki/harness/00_READ_FIRST.md`

Repo state audit:
- repo root: `/Users/joshuaeisenhart/Desktop/Codex Ratchet`
- branch: `main`
- worktree is already dirty in the exact Tier B families, including direct overlap in the requested scopes:
  - B1 dirty examples: `_gstack_shell_local_common.py`, `sim_gstack_associated_bundle_shell_local.py`, `sim_gstack_floer_complex_shell_local.py`, `sim_gstack_gerbe_shell_local.py`, `sim_gstack_spectral_triple_shell_local.py`, `sim_gstack_stable_bundle_shell_local.py`, `sim_gstack_twistor_line_shell_local.py`
  - B2 dirty count: 41 matching `hopf_` paths
  - B3 dirty count: 38 matching `weyl_` paths
  - B4 dirty count: 1 matching `flux_/u1_` path
  - B5 dirty count: 32 matching `clifford_/pauli_` paths
- because the exact target families are already being edited, a safe bounded controller pass cannot honestly separate my Tier B deltas from pre-existing/concurrent edits without first creating fresh isolated worktrees or receiving an explicit overlap waiver

Coverage reconnaissance from the current checkout:

B1 — G-stack / G-tower shell-local coverage
- existing canonical shell-local-like gstack probes found:
  - `sim_gstack_associated_bundle_shell_local.py`
  - `sim_gstack_floer_complex_shell_local.py`
  - `sim_gstack_gerbe_shell_local.py`
  - `sim_gstack_spectral_triple_shell_local.py`
  - `sim_gstack_stable_bundle_shell_local.py`
  - `sim_gstack_twistor_line_shell_local.py`
- existing gtower shell-local-like probes found, but all currently classify as `classical_baseline` rather than `canonical`:
  - `sim_gtower_gl3_shell_local.py`
  - `sim_gtower_o3_shell_local.py`
  - `sim_gtower_so3_shell_local.py`
  - `sim_gtower_sp6_shell_local.py`
  - `sim_gtower_sp6_weyl_shell_local.py`
  - `sim_gtower_su3_shell_local.py`
  - `sim_gtower_u3_shell_local.py`
- current gap relative to brief: I do not yet have ≥10 new canonical sims landed from this session; existing surface suggests B1 is mid-stream and not safely attributable in the dirty tree

B2 — Hopf shell-local coverage check
- filename audit inside `system_v4/probes/` found many Hopf-related files, but no clearly named current `*_shell_local.py` Hopf family in the direct `sim_hopf_*` scope
- notable current shell-local-adjacent Hopf files include:
  - `sim_hopf_torch_foundation.py`
  - `sim_hopf_torus_lego.py`
  - `sim_pure_lego_hopf_tori_base.py`
  - `sim_hopf_connection_curvature_operators.py`
  - `sim_hopf_deep_u1_holonomy_equivariance.py`
  - `sim_hopf_deep_fiber_winding_number_bound.py`
- current gap relative to brief: shell-local naming / catalog coverage is not yet cleanly documented and I have not yet produced a fresh conformant gap-fill set in an isolated Tier B worktree

B3 — Weyl shell-local coverage check
- only one direct `weyl_*` shell-local-like file was found by this pass:
  - `sim_weyl_group_g2_shell_local.py` (`classification = canonical`)
- other Weyl shell-local-adjacent files exist but are not a clean shell-local catalog in the direct scope, e.g.:
  - `sim_weyl_nested_shell.py`
  - `sim_weyl_spinor_hopf.py`
  - `sim_lego_weyl_hopf_spinor_bridge.py`
  - `sim_lego_weyl_pauli_transport.py`
- current gap relative to brief: Weyl shell-local coverage is still sparse as a clean catalog and I have not yet landed isolated gap-fill sims from this session

B4 — Flux / U(1) shell-local legos
- this is still the biggest visible gap in the current checkout
- direct scope findings are thin:
  - `sim_lego_flux_candidates.py`
  - `sim_symplectic_berry_flux_axis0.py`
  - `sim_cvc5_flux_compactification_constraint.py`
  - `sim_pure_lego_berry_phase_u1_abelian.py`
  - `classical_baseline_u1_phase_loop.py`
  - `sim_hopf_deep_u1_holonomy_equivariance.py`
- current gap relative to brief: I did not find an existing clean `flux_*/u1_*` shell-local canonical catalog, and I have not yet added the requested ≥6 new canonical sims in an isolated Tier B worktree

B5 — Pauli / Clifford baseline-tag audit
- direct Pauli/Clifford scope is nontrivial and already dirty
- current direct baseline examples present in repo:
  - `classical_baseline_cl6_kron_pauli_rep.py`
  - `classical_baseline_cl3_rotor_pauli_rep.py`
- additional direct Pauli/Clifford probes needing bounded audit before any retag claim:
  - `sim_lego_pauli_algebra.py`
  - `sim_pauli_generator_basis.py`
  - `sim_pauli_algebra_relations.py`
  - `sim_pure_lego_clifford_algebra.py`
  - `sim_clifford_generator_basis.py`
  - `sim_clifford_capability.py`
- current gap relative to brief: I have not yet completed the per-file tag-confirmation pass in an isolated worktree, so I cannot honestly claim B5 closed

Why this is a blocker right now:
1. two required read targets named in the brief are absent in this checkout
2. the requested Tier B file families are already dirty, so a safe bounded controller patch cannot yet separate fresh Tier B edits from concurrent/pre-existing work without fresh disjoint worktrees or an explicit overlap waiver
3. the brief’s gate requires all new results to be conformant and documented, but this session has not yet landed isolated conformant sims/results for B1–B5
4. B4 remains visibly under-covered even before new work starts; closing it safely requires a clean worktree plus a bounded per-file generation/rerun loop, not in-place edits on the live dirty tree

Recommended unblock conditions:
- provide the authoritative replacement locations for the missing contract/read-first files, or confirm the current substitutes
- provide or authorize fresh disjoint git worktrees for B1–B5 starting from clean `HEAD`
- confirm whether I should ignore pre-existing dirty edits in the Tier B scopes and proceed from fresh worktrees only
- if an external L3 transport/target is expected, provide the exact Hermes delivery target; otherwise this file is the blocker report artifact

Artifacts from this controller pass:
- this status note: `wiki/projects/2026-04-16/tier_b.md`
