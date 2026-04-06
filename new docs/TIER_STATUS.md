# Tier Status (Resolution Levels on M(C))

Date: 2026-04-05
Supersedes framing of: CURRENT_PRE_AXIS_SIM_STATUS__KEEP_OPEN_DIAGNOSTIC_BROKEN.md,
                        CURRENT_PREAXIS_STATUS_AND_ORDERING_NOTE.md,
                        WAVE2_AXES_NEXT_SIMS_AUDIT.md,
                        CURRENT_PRE_AXIS_SIM_STATUS__WAVE1_REFRESH.md,
                        CURRENT_PRE_AXIS_WAVE2_VALIDATION_NOTE.md
                        (factual content from those docs remains valid)

Vocabulary: survived / killed / open / not_yet_tested
            (NOT pass/fail — this system does not verify correctness,
            it falsifies what it can and reports what remains)

Note: "tiers" are resolution levels for finite exploration of the
simultaneous constraint surface M(C), not floors in a building.

---

## Resolution 0-2: Root Constraints and Charter (Analytical)

### Resolution 0: F01 (Finitude) + N01 (Noncommutation)

Status: DOCTRINAL — not mechanically executed
Artifacts: ROOT_CONSTRAINT_EXTENDED_FOUNDATIONS.md, constraint_manifold.yaml
Sims: NONE
What exists: z3 predicates in constraint_manifold.yaml (C1-C8, X1-X8) but never run

What "explored" means here: work out what F01 and N01 forbid. Small targeted
probes. z3/pySMT guards. Not a full sim campaign — reasonable exploration of
the allowed math. The constraints kill analytically, not by brute-force sim.

### Resolution 1: Admissibility Charter (24 constraints)

Status: DOCTRINAL — charter written, no executable validator
Artifacts: ROOT_CONSTRAINT_EXTENDED_FOUNDATIONS.md, Formal constraints and geometry.md
Sims: NONE

### Resolution 2: Constraint Manifold M(C) Characterization

Status: DOCTRINAL — defined in prose, no computational characterization
Artifacts: CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md

---

## Resolution 3+: Sims Begin (Concrete Objects Exist)

### Resolution 3: Geometry / Operator Basis

Status: OPEN (Type1 survived, Type2 open)

Sim: sim_operator_basis_search.py
Artifact: operator_basis_search_results.json

Results:
- B3.1 (basis remap): remap_breaks_grammar = true — survived
- B3.2 (coord change): coord_change_preserves_grammar = true — survived (SymPy proof)
- B3.3 (noncomm ablation): noncomm_ablation_degrades_grammar = true — survived (SymPy proof)
- B3.4 (rep demotion): n_load_bearing = 4, all operators required — survived
- Type1 geometry crosscheck: fully_matches = true — survived
- Type2 geometry crosscheck: fully_matches = false — OPEN (fiber/base grammar inverted)

Open: Type2 Weyl inversion documented but not resolved. B3 results do NOT
transfer to Type2 without additional work. See type2_weyl_inversion_status_note.md.

### Resolution 4: Weyl Working Layer

Status: OPEN (inherits Type2 gap from Resolution 3)

Sim: sim_weyl_geometry_ladder_audit.py
Artifact: weyl_geometry_ladder_audit_results.json

Results:
- Weyl-ambient rung has independent witness — survived
- Holonomy varies across torus ladder — survived
- witness_separable = true — survived
- Type2 inversion still open

### Resolution 5: Bridge Family Xi

Status: OPEN (evidence gathered, no closure)

Sims (A1/recon output, not B evidence):
- sim_xi_bridge_bakeoff.py → xi_bridge_bakeoff_results.json
- sim_history_vs_pointwise_ax0.py → history_vs_pointwise_ax0_results.json

Results:
- Chiral bridge: composite score 0.80, I_c > 0 on all 6 configs — survived
- History-window bridges lead pointwise by MI gap ~0.93 — survived
- hist_retro_exp wins Type1, hist_fe_indexed wins Type2 — no single winner
- Shell and point_ref: negative I_c everywhere — open (not killed, just weak)

Open: No single bridge winner selected. Chiral and history are structurally
different approaches. No closure claimed on Xi.

### Resolution 6: Cut / Entropy / Entanglement

**C2 (Entropy Structure):**

Status: SURVIVED

Sim: sim_c2_entropy_structure_search.py
Artifact: c2_entropy_structure_search_results.json

Results:
- C2_status: "Entropy Structure Admitted"
- 8/8 VN-positive stages: classical shortcut killed, purity proxy killed
- Shannon/purity shortcuts insufficient; VN entropy is necessary — survived

**C1 (Entanglement Witness):**

Status: OPEN

Sim: sim_c1_entanglement_object_search.py
Artifact: c1_entanglement_object_search_results.json

Results:
- 16/16 stages witnessed — survived
- MI-based fake_coupling_kill_count = 0 — MI does NOT kill fake coupling
- MI-based mispair_kill_count = 0 — MI does NOT kill mispair
- Concurrence/negativity fake coupling: 16/16 killed — survived
- Concurrence/negativity mispair: 8/16 killed — OPEN

The 8 unresolved mispair stages involve Fe/Fi (universally entangling operators).
Explained by c1_mispair_probe_results.json: operator-family-driven, not
chirality-driven. Structural, not a probe failure. Open design question
for the C1 contract.

### Resolution 7: Kernel Phi_0(rho_AB)

Status: OPEN (informative but embargoed pending Resolution 6 closure)

Sim (A1/recon output): sim_a0_kernel_discriminator.py
Artifact: a0_kernel_discriminator_results.json

Results:
- K1_Ic (coherent information): 5/6 — survived
- K2_MI (mutual information): 4/6
- K3_shell_Ic (shell-cut weighted): 4/6
- Winner: K1_Ic
- Bridge assumption: none (pure cut-state evaluation)

This does NOT unlock Resolution 7. Informative for kernel identity.
Embargoed until Resolution 6 closes.

### Resolution 8: Edge Writeback / Graph Topology

Status: SURVIVED

Sim: sim_edge_state_writeback.py
Artifact: edge_state_writeback_results.json

Results:
- P1-P5 all survived
- Ring topology closed: 64-element lookup fully populated
- 7/7 dynamic slot columns with nonzero variance
- TOPO_LEGAL has historical TopoNetX bridge evidence, but current tooling status treats `toponetx` as installed/not-actively-used until the live runtime path is re-confirmed
- CONST_SAT confirmed honest

---

## Additional Probes (A1/Recon Output)

These are reconnaissance artifacts, not formal ratchet evidence:

| Probe | Artifact | Key result |
|---|---|---|
| Hopf pointwise pullback | hopf_pointwise_pullback_results.json | Product pullback is trivially zero; nontrivial bridge required |
| Fiber/base transport test | fiber_base_transport_test_results.json | Ax2 transport does NOT change Ax0 kernel; separation survived |
| C1 mispair probe | c1_mispair_probe_results.json | Mispair is operator-driven, not chirality-driven |
| Pimono smoke test | pimono_smoke_test_output.json | {"status": "ok"} |

---

## Summary

| Resolution | What | Status | Blocking |
|---|---|---|---|
| 0 | F01 + N01 | Doctrinal | No sims |
| 1 | Charter (24 constraints) | Doctrinal | No validator |
| 2 | M(C) characterization | Doctrinal | No computation |
| 3 | Geometry / operators | OPEN | Type2 inversion |
| 4 | Weyl layer | OPEN | Inherits Type2 |
| 5 | Bridge Xi | OPEN | No winner selected |
| 6 C2 | Entropy structure | SURVIVED | — |
| 6 C1 | Entanglement witness | OPEN | MI dead, 8/16 mispair |
| 7 | Kernel | OPEN (embargoed) | Needs Resolution 6 |
| 8 | Edge writeback | SURVIVED | — |

Two resolutions survived: C2 entropy structure, Edge writeback.
Everything else is open or doctrinal.
