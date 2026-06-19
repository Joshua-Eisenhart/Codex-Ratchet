# Independent audit verdict - basin_two_engine_joint_v4_within_sector_v0

auditor: independent Codex audit
audit mode: read-only audit, except this `audit_verdict.md`
freshness_tier: TIER-2 results-available
standards_codex: `system_v6/receipts/audit_standards_codex_v1.md`
standards_commit: `c83842e5518d43250f3847fd2cc92d5519260fbd`
claim_ceiling: `scratch_diagnostic`
promotion_allowed: false
formal_admission_allowed: false

## Bottom Line

VERDICT: GENUINE-WITH-CAVEATS.

The packet's reported honest zero is supported for the registered hunt: all registered state-dependent flux-flip laws ran across both scoped v3 rows and both engines; all three backends agree on `genuine_hit_count=0`; the conserved-flux and flux-erased controls reproduce the expected v4/v3 structures; and the projection/symmetry filters are not vacuous because a true within-sector split or true in-class flip shape can pass them.

Registration-entry sentence: `basin_two_engine_joint_v4_within_sector_v0` is the corrected target's first registered hunt after `40f010040`: zero genuine hits for within-sector splitting or in-class flux flipping, scoped only to the five in-card laws: `conserved_flux_control`, `direction_sheet_opposing_current`, `arrival_current_negative`, `arrival_current_positive`, and `current_sign_change`.

This does not canonically disprove flux-based within-sector structure. It excludes the registered law family under this packet's v4 machinery and current finite realization.

## What Was Checked

- Registration: `build_card.md` pins one conserved control plus four candidate flux-flip laws. The envelope records the same five-law family, consumes the `40f010040` owner-registration receipt, the v4 flux packet at `a38a9f712`, the flux-emergence discriminator, and the v3 convention sweep.
- Law coverage: envelope extraction found 20 law/variant/engine rows total and 16 candidate rows after excluding `conserved_flux_control`.
- Backend agreement: JAX, Julia, and PyTorch all report `genuine_hit_count=0`; primary terminal-count maps agree; envelope divergence on `genuine_hit_count` is `0.0`.
- Double test: recomputed `arrival_current_negative / A_readout_transition_dwell / L` directly from the source functions. It produced two terminal classes of size `28,28`, `10` flip edges, no projection pass, no symmetry-orbit pass, and `genuine_count=0`.
- Filter reachability: a tiny constructed strict within-sector terminal and a tiny constructed in-class flip terminal both pass `projection_test_pass`, `symmetry_orbit_test_pass`, and `genuine_candidate_under_panel6_q3`. So the zero is not vacuous by impossible filters.
- Controls: direct recomputation returned flux-erased continuity `all_pass=True`, A sync count `28`, D sync count `24`, conserved-flux rows `[28,28]` and `[24,24]`, and 20 order-shuffle rows all marked run.
- Validators: packet-local validator returned `ok: true`; strict source-backed three-engine validator with PyTorch and tool intent returned `ok: true`.

## Registered Law Family

The registered laws are not strawman in the narrow process sense: they are explicit in-card, finite, predeclared before this packet's results, and source-linked through the parent lineage. The inherited `direction_sheet_opposing_current` law is the v4 signed-sector law; the other three candidate laws are finite current-sign variants over boundary arrivals and sign changes.

The family is still small. It is a valid first hunt, not an exhaustive flux-law space. The verdict must not be cited as "no flux law can work"; it is "no registered law in this finite family worked."

## Double-Test Detail

Recomputed row:

```text
law = arrival_current_negative
variant = A_readout_transition_dwell
engine = L
erased_terminal_count = 1
erased_terminal_sizes = [28]
flux_terminal_count = 2
flux_terminal_sizes = [28, 28]
flip_edges = 10
projection_any = False
symmetry_any = False
genuine_count = 0
all_absent_exit = True
```

Both terminal classes contain both flux values and include in-class flip edges, but each projects to the full erased terminal core and has a flux-involution partner. That is exactly the artifact shape the corrected panel-6 criterion was supposed to reject: full projection echo plus symmetry-sector duplication, not a genuine within-sector split.

Filter reachability check:

```text
within_shape: projection_test_pass=True, symmetry_orbit_test_pass=True, genuine_candidate_under_panel6_q3=True
in_class_flip_shape: projection_test_pass=True, symmetry_orbit_test_pass=True, genuine_candidate_under_panel6_q3=True
```

So a genuine row could have passed if the registered dynamics produced one.

## Controls

The conserved-flux control reproduces the v4 sector decomposition:

```text
A_readout_transition_dwell: L [28, 28], R [28, 28]
D_matrix64_b_order_overlay: L [24, 24], R [24, 24]
```

The flux-erased continuity control reproduces the corrected v3 baselines:

```text
A_readout_transition_dwell sync count = 28
D_matrix64_b_order_overlay sync count = 24
per-engine A terminal size = [28]
per-engine D terminal size = [24]
```

This satisfies the control side of the corrected target: the packet keeps the v4 sector structure visible while preventing it from counting as a genuine hit.

## Standards-Codex Disposition

- `frozen-factor echo`: not the active species here; the packet is not claiming frozen complementary-factor counts.
- `definitional circularity`: not found for the zero. The filters can admit positives, and the candidate rows are rejected by computed terminal/projection/orbit facts.
- `rule-table readback`: not found for the verdict count. The packet recomputes finite transition graphs and terminal structures; it does not accept the law metadata as the result.
- `post-hoc statistic`: not found. The law family is in-card and closed before adjudication.
- `shift-relabeling`: not found.
- `pre-registration boundary`: satisfied for the finite law family, but not exhaustive over all possible future flux-law variants.
- `file/builder boundary`: builder did not author this file; envelope has `no_builder_audit_verdict=true`.

## Caveats

G1 `registered_family_scope`: the zero is only over the five in-card laws. The flux estate can still support later registered variants, especially global-binding/per-stage-flip or richer current-law families not enumerated here.

G2 `solver_scope`: z3/cvc5/Julia-Z3 bind computed count identities with flipped expected-count controls. They do not independently prove SCC reachability from first principles; the graph computations carry that part.

G3 `freshness_tier`: this is TIER-2, not full-blind TIER-1. I read the result JSONs and build card, then recomputed targeted rows and validators. I did not rerun the writer leg scripts because the audit write boundary only allowed `audit_verdict.md`.

G4 `untracked_packet_state`: this packet directory is currently untracked in git. That does not change the local audit result, but it means commit provenance for the new packet itself is not yet a durable repository fact.

## Verification Commands

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py
-> ok=True install_state=stable_observed
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/basin_two_engine_joint_v4_within_sector_v0/validate_basin_two_engine_joint_v4_within_sector_v0.py
-> ok: true, errors: []
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/basin_two_engine_joint_v4_within_sector_v0/results/basin_two_engine_joint_v4_within_sector_v0_envelope_results.json
-> ok: true
```

```text
targeted direct recomputation of arrival_current_negative / A_readout_transition_dwell / L
-> projection_any=False, symmetry_any=False, genuine_count=0, all_absent_exit=True
```

```text
tiny passing-shape reachability probe
-> within-sector shape passes; in-class flip shape passes
```
