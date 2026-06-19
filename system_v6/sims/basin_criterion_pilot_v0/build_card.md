# basin_criterion_pilot_v0

Status: draft pilot card.
Phase: sim-wizard Phase 1 / build card, not build.
Cost class: LIGHT-SYMBOLIC where possible.
Tree authorization: parent may spawn bounded children for independent source slices, exact affine math, interval-box design, and audit; controller owns the final write.

## Goal

Turn `system_v6/receipts/attractor_basin_criterion_20260611.md` into the smallest executable v6 pilot:

1. Apply the criterion to committed S5 affine terrain flows.
2. Re-read conditioned `T_pi/6` shell failure semantics.
3. Run one ratchet-chain step against `ratchet_deep_chain_v0`.
4. Register the first sub-basin frontier without overclaiming affine rows.

## Inputs

- `system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_jax_results.json`
- `system_v6/sims/ratchet_s6_terrain_sweep_v0/results/ratchet_s6_terrain_sweep_v0_envelope_results.json`
- `system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json`
- commits: `6aa75cc96`, `826e716d1`, `7909b1b1b`, `a54224476`, `77fb7ca52`, `123b8e7d8`

## Envelope-Builder Rule

The pilot must write a normal v6 envelope with:

- `classification = "scratch_diagnostic"`
- `promotion_allowed = false`
- `formal_admission_allowed = false`
- non-empty `TOOL_MANIFEST`
- `TOOL_INTEGRATION_DEPTH`
- exact source/result hashes
- no broad queue launch
- no admission bypass

## Binding Basin-Packet Contract

The pilot is executable only if its result envelope carries the binding basin-packet contract explicitly.

M(C)-native fields:

- `S`: finite or bounded state/probe space.
- `Adm_C`: explicit admissibility predicate.
- `M(C) = {x: Adm_C(x)}`: admitted survivor set.
- `R_C`: explicit allowed update semigroup under `C`.
- trapping test: candidate `A` must satisfy `R_C(A) subset A`.
- basin readout: `B(A) = {x: omega_{R_C}(x) subset A}` where computed or bounded.
- ratchet fate: after tightening `C`, recompute `M(C)` and classify each basin as `survives`, `shrinks`, `SPLITS`, `metastable`, or `collapses`.

The 9 card requirements:

1. finite `S`;
2. `Adm_C`;
3. `R_C` explicit;
4. trapping test;
5. Lyapunov/monotone-exclusion observable;
6. escape tests;
7. basin partition (terminal vs metastable vs leaky);
8. the engine-DoF perturbation test;
9. the negative controls (similarity-only cluster, shuffled order, root-off, F01-only, N01-only, quotient-erased, commutative-collapse).

Key guard:

- Clustering/model agreement is NEVER a basin. State space + update rule + trapping + boundary/escape evidence required.
- Similarity, repeated motifs, provider/model agreement, or a plausible attractor package output may be useful diagnostics, but cannot promote basin language.
- Both audit families now enforce this: the repo basin/manifold contract and Hermes-patched `nonclassical-sim-contract-audit`.

Vocabulary discipline:

- Earn terms in this order: `terminal/closed communicating class` > `chain-recurrent class` > `nested basin` > `metastable set` > `almost-invariant set` > `communicating class`.
- Use `separatrix` or `basin boundary` only when the result names the tested boundary between retained states and escape/failure states.
- The Morse graph is the hierarchy graph over the earned classes. SCCs/communicating classes are not automatically basins; they need closure/trapping and escape/boundary evidence.

## Required Rows

1. `invariance`
   - exact for affine `M,b`;
   - shell normal/tangent defect for `T_pi/6`.

2. `attraction`
   - exact eigenstructure for affine rows;
   - fixed point and basin statement;
   - classify `Ne_Spiral_R` as invariant-not-attracting on the ball;
   - classify `Ni_Source_R` as whole-ball attracting to displaced interior fixed point.

3. `lyapunov_type`
   - compute `V_narrow` from ratchet/deep-chain denominator or chart volume;
   - report entropy deltas from committed ledger conventions;
   - mark `V_narrow` as the Lyapunov-type candidate and entropy as typed telemetry.

4. `failure_semantics`
   - for `T_pi/6`, classify both worked rows as `shell_breaking/neither/empty_conditioned_survivor`;
   - preserve zero-survivor result as failure evidence, not basin admission.

5. `sub_basin_frontier`
   - ask whether any committed affine terrain admits multiple attractors on the Bloch ball;
   - expected answer: no, not generically; affine rows yield unique fixed point, attracting slices, or non-attracting orbits;
   - frontier moves to nonlinear/composite/stage-word rows.

6. `binding_basin_packet_contract`
   - emit all 9 card requirements by name;
   - report pass/fail/blocked for each requirement;
   - classify the earned vocabulary term for each candidate region;
   - state whether the Conley/lattice rows instantiate the same finite Morse graph over communicating classes;
   - demote any missing row to `candidate`, `diagnostic_only`, or `blocked`, not `basin`.

7. `negative_controls`
   - `similarity_only_cluster`;
   - `shuffled_order`;
   - `root_off`;
   - `F01_only`;
   - `N01_only`;
   - `quotient_erased`;
   - `commutative_collapse`.

8. `engine_DoF_perturbation`
   - perturb at least one engine stage/readout coordinate;
   - measure whether basin membership, escape, stability, or subbasin transition changes;
   - if no measurable change is observed, classify the stage as a readout/label for this packet, not an earned DoF.

## Blind Expected Panel

`Ne_Spiral_R`:

- `charpoly = lambda*(lambda**2 + 4)`
- eigenvalues `0, +/- 2i`
- kernel `span((1,1,1))`
- whole ball / pure sphere: invariant, not attracting
- `T_pi/6`: `z_dot = sqrt(2)*cos(theta + pi/4)`, radial derivative `0`; shell not invariant

`Ni_Source_R`:

- `charpoly = lambda**3 + lambda**2 + (189/400)*lambda + 203/2400`
- eigenvalues have negative real part
- fixed point `((-8*(-8 + 5*sqrt(3))/203), 8*(8 + 5*sqrt(3))/203, 139/203)`
- fixed norm squared `37113/41209 < 1`
- whole ball basin to displaced interior point
- `T_pi/6`: `z_dot = sqrt(2)*cos(theta + pi/4)/5 + 1/4`, radial derivative `-1/8`; shell not invariant

## Suggested Worker Tree

- Parent A: source-lock S5/S6/deep-chain hashes and exact rows.
- Parent B: exact affine classifier for selected terrain rows.
- Parent C: Lyapunov/narrowing vs entropy-type audit.
- Parent D: sub-basin frontier design using interval-box graph / Attractors.jl route.
- Child lanes: one row or one source slice each; no shared writes.

## Stop Conditions

- Stop if a required parent result is missing or stale.
- Stop if the pilot would need to rewrite canonical result estates before the criterion is accepted.
- Stop if interval-box or Attractors.jl rows become the critical path; emit a blocked-reason artifact instead.
- Stop or demote if any of the 9 card requirements are absent from the envelope schema.
- Stop or demote if the result only shows clustering, repeated motifs, package agreement, or model agreement without finite `S`, explicit `R_C`, trapping, and boundary/escape evidence.

## Success Check

The pilot succeeds if it emits one scratch-diagnostic envelope that classifies the two panel rows, preserves zero-survivor failure semantics, identifies `ratchet_deep_chain_v0` as the first sub-basin target, leaves the nonlinear/composite frontier explicit, and carries all 9 binding basin-packet requirements with pass/fail/blocked status plus the clustering/model-agreement guard.

## Builder-Hardening Addendum

Scope: one bounded hardening round after `audit_verdict.md`; G1/G4/G5 stay as honest scope carried by name.

- G2 closed: `Se_Funnel_L` and `Ni_Pit_L` must be first-class `criterion_rows`, computed from the committed S5 affine rows and S6 conditioned-shell rows.
- G3 closed: the overearned finite-transition terminal-class label is forbidden in generated result rows and summary vocabulary. The earned wording for attracting affine rows is `attracting affine fixed point on the whole Bloch ball`.
- Success check: run the canonical envelope helper path by executing this packet, then quote `{"ok": true, "result_path": "system_v6/sims/basin_criterion_pilot_v0/results/basin_criterion_pilot_v0_envelope_results.json"}` and a validator `ok:true` result.
- Successor boundary: the explicit `R_C` transition-graph packet remains the named successor for terminal-class language, absent-exit proof, blocked controls, and finite transition partition work.
