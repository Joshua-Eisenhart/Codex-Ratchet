# audit_verdict.md - engine_readout_spinor_lift_v0

Auditor: codex1 cross-backend audit
Builder: codex2
Date: 2026-06-11
Mode: read-only audit except this `audit_verdict.md`

## Verdict

VERDICT: SURVIVES_WITH_NAMED_CAVEATS as a `scratch_diagnostic`.

The packet earns the scoped closure claim:

1. density/readout level repeats the committed e2d9d5407 classes;
2. phase-sensitive spinor-lift readouts separate the second 360 traversal from the first for all 16 committed strategy analogs;
3. density/projective quotient erasure maps the lift result back to the committed e2d9d5407 repeat classes byte-consistently.

It does not earn strategy promotion, engine admission, formal admission, physics admission, PyTorch/graph coverage, or any stronger "720 loop manifold" interpretation. Owner vocabulary around a 720 loop manifold remains fenced as interpretation, not an admitted engine/physics object.

## Named Caveats

- CAVEAT_UNTRACKED_PACKET: `git status --short` shows `?? system_v6/sims/engine_readout_spinor_lift_v0/`. This audit verifies the on-disk packet but does not make it committed.
- CAVEAT_SCRATCH_CEILING: envelope, JAX, and Julia results all keep `classification: scratch_diagnostic`, `promotion_allowed: false`, and `formal_admission_allowed: false`.
- CAVEAT_SCHEMA_NAME: envelope schema is `three_engine_sim_result_v1`, but the honest engine contract says the lanes are `julia` and `jax`; PyTorch is omitted because there is no graph/network/autograd claim path. Do not count this as three-engine coverage.
- CAVEAT_SHUFFLED_WORD_INHERITED: shuffled-word control is inherited from the committed density parent; the lift packet does not reclassify shuffled-word rows.
- CAVEAT_ANTI_COLLAPSE_NOT_RESOLVED: the lift checks the committed 16x16 indistinguishable groups but does not split them; parent slot-copy groups remain indistinguishable.

## Commands And Fresh Checks

- `sed -n '1,240p' system_v6/receipts/audit_bar_calibration_20260610.md`
- `git show --stat --oneline e2d9d5407 -- system_v6/sims/engine_readout_strategy_fidelity_v0`
- `git show e2d9d5407:system_v6/sims/engine_readout_strategy_fidelity_v0/results/engine_readout_strategy_fidelity_v0_envelope_results.json | shasum -a 256`
- `shasum -a 256 system_v6/sims/engine_readout_strategy_fidelity_v0/results/engine_readout_strategy_fidelity_v0_envelope_results.json`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_readout_spinor_lift_v0/validate_engine_readout_spinor_lift_v0.py`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ...` fresh in-memory recomputation from `engine_readout_spinor_lift_v0_jax.py` without rerunning writers.

Validator result before this audit file existed:

```json
{"ok": true, "result_json": "/Users/joshuaeisenhart/Codex-Ratchet/system_v6/sims/engine_readout_spinor_lift_v0/results/engine_readout_spinor_lift_v0_envelope_results.json"}
```

Fresh recomputation summary:

```json
{
  "strategy_count": 16,
  "separated_count": 16,
  "still_repeating_count": 0,
  "all_separation_rows_match_stored": true,
  "selected_rows_match_stored": true,
  "quotient_hash_recomputed": "b2bb268ac1b77ce750efc002cf816ed20c7f7a2a2825407fb98cafaad5364587",
  "quotient_hash_parent": "b2bb268ac1b77ce750efc002cf816ed20c7f7a2a2825407fb98cafaad5364587",
  "quotient_control_match_stored": true,
  "phase_randomized_match_stored": true,
  "reference_independence_match_stored": true,
  "dist_anti_rows_match_stored": true,
  "z3_match_stored": true,
  "cvc5_match_stored": true
}
```

The committed parent result is hash-bound and current-checkout byte-identical to commit `e2d9d5407`:

```text
5c8d4861307e04b2855dcfe6c15abea0b8ae0843e9e8663570af008d59d19ee3
```

## Q1 - Lift Readouts

PASS.

The construction is pinned in `engine_readout_spinor_lift_v0_jax.py`:

> "readout=density_labels_plus_reference_overlaps"

and the row construction states:

> "same stage-word density labels plus phase-sensitive overlaps <psi_ref|psi(t)>"

with:

> "the second 360 traversal is the spinor-lift sheet -psi(t)"

Source trace:

- `PIN_SPEC` binds parent `e2d9d5407`, `n=8`, `mode=FIELD`, and the readout surface in `engine_readout_spinor_lift_v0_jax.py:54-60`.
- references are `basis_zero`, `seeded_complex`, and `word_mean` in `engine_readout_spinor_lift_v0_jax.py:287-299`.
- each row records `overlap_360`, `overlap_720_second_half`, lift gap, sign residual, phase-erased intensity gap, and separation in `engine_readout_spinor_lift_v0_jax.py:312-368`.
- the 16 lift analogs trace to the same four base strategies expanded over stage slots in `engine_readout_spinor_lift_v0_jax.py:107-148` and `:320-371`, matching the committed strategy mapping in parent `engine_readout_strategy_fidelity_v0`.

## Q2 - Separation Table

PASS.

The load-bearing table says:

- `separated_count: 16`
- `still_repeating_count: 0`
- every row has `separates_720_from_360: true`
- every row also has `density_quotient_repeats: true`
- every row has `phase_randomized_repeats: true`

Fresh recomputation matched all stored separation rows exactly.

Spot recomputation 1, `type1_outer_deductive_slot_Se`:

- `separates_720_from_360: true`
- `density_quotient_repeats: true`
- seeded reference minimum lift gap: `0.122809784507`
- basis reference gap: `2.0`
- phase-erased intensity gap: `0.0`
- source row shows second-half overlaps are the negatives of first-half overlaps.

Spot recomputation 2, `type1_inner_inductive_slot_Se`:

- `separates_720_from_360: true`
- `density_quotient_repeats: true`
- seeded reference minimum lift gap: `0.088912328063`
- basis reference minimum lift gap: `1.801990465923`
- phase-erased intensity gap: `0.0`
- source row shows second-half overlaps are the negatives of first-half overlaps.

There is no repeating lift analog in this packet. Therefore the requested "one repeating if any" case is answered as: none exist under the stored and recomputed separation table. The committed prediction is confirmed per strategy: the sign flip is visible in phase-sensitive overlap rows for all 16 strategy analogs and erased by density/projective rows.

## Q3 - Density Quotient Erasure

PASS, byte-consistent.

The decisive control passes:

- `all_density_sha256_repeat: true`
- `density_repeat_failures: []`
- `parent_groups_reused_exactly: true`
- `collapses_to_committed_repeat_result: true`
- parent double groups hash: `b2bb268ac1b77ce750efc002cf816ed20c7f7a2a2825407fb98cafaad5364587`
- lift quotient groups hash: `b2bb268ac1b77ce750efc002cf816ed20c7f7a2a2825407fb98cafaad5364587`

This ties the packets exactly: e2d9d5407 says density/readout double-720 repeats the 360 classes, and the spinor-lift packet maps back to those same classes under density quotient erasure.

## Q4 - Anti-Collapse Groups

PASS for honesty; FAIL for resolution.

The lift readout does not separate the committed 16x16 indistinguishable slot-copy groups. It checks them and leaves them still indistinguishable.

Fresh recomputed example:

```json
{
  "parent_readout": ["LOSE", "WIN", "LOSE", "WIN"],
  "parent_strategies": [
    "type1_outer_deductive_slot_Se",
    "type1_outer_deductive_slot_Ne",
    "type1_outer_deductive_slot_Ni",
    "type1_outer_deductive_slot_Si"
  ],
  "lift_unique_signature_count": 1,
  "lift_splits_parent_group": false,
  "finding": "still_indistinguishable"
}
```

All four parent groups have the same shape: `lift_unique_signature_count: 1`, `lift_splits_parent_group: false`, `finding: still_indistinguishable`.

## Q5 - Controls

PASS with named caveats.

- Phase-randomized control fires: `kills_separation: true`, `phase_randomized_failures: []`; the control replaces `<ref|psi>` with `|<ref|psi>|^2`, erasing the global sign.
- Density quotient control fires: all density hashes repeat and the parent group hash is byte-consistent.
- Reference independence passes for the three scoped references: `basis_zero`, `seeded_complex`, `word_mean`. Minimum gaps are `1.801990465923`, `0.088912328063`, and `1.900024615586`, respectively. Honest characterization: the sign law is reference-independent for non-orthogonal references; this packet verifies three deterministic nonzero-overlap references, not every possible reference.
- Shuffled-word control is inherited from e2d9d5407: `copied_parent_control: true`, `failure_count: 4`. This is adequate as a parent-control carry-forward but not a fresh shuffled-word lift reclassification.

## Q6 - Standard Contract

PASS with schema/name caveat.

- Parent lineage present: automaton parent, committed density parent at `e2d9d5407`, terrain Weyl spinor parent, and cost discriminator parent are declared with sha256s.
- Real Julia leg present: `engines.julia.ran: true`, `QuantumOptics` and `Z3` load-bearing, `strategy_count: 16`, `lift_separated_count: 16`, `lift_still_repeating_count: 0`, `parent_groups_split_by_lift: 0`.
- Honest mode present: `mode: FIELD`; envelope engine contract says `mode: julia_canon_plus_jax_diagnostic`.
- Torch omission is honest: "No PyTorch lane is scoped because there is no graph/network/autograd claim path." This is not a PyTorch or three-engine proof.
- z3/cvc5/Julia-Z3 proof route passes with erased controls: z3, cvc5, and Julia Z3 all report `verdict: unsat` for the violation query and `control_verdict: sat` for density-erased/projective signs.
- Capability/tool receipts are one-to-one enough for the claim: QuantumOptics -> `two_pi_spinor_sign_and_density_erasure`; Z3.jl, z3, and cvc5 -> `computed_separation_identity_with_erased_flip`; numpy -> overlap and density quotient rows.
- No fixture wording was found as a claim support surface; the result is framed as an n=8 loop-local statevector/readout packet, not a generic fixture promotion.
- Versions/seeds present: Python lane records `seed: 20260611`, `numpy: 2.3.4`, `z3-solver: 4.16.0.0`, `cvc5: 1.3.3`; Julia lane records package use through `QuantumOptics`, `Z3`, `JSON`, `LinearAlgebra`, `SHA`.
- Runtime preflight passed: sim-stack Python `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`; Julia `/opt/homebrew/bin/julia`; active Julia project `system_v5/julia_carrier/Project.toml`.
- Ceiling is explicit: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Q7 - Closure

PASS at the scoped diagnostic ceiling.

Precise closure picture:

- Readout/density level: repeats. The committed parent e2d9d5407 has `unique_readouts_360: 4`, `unique_readouts_double_720: 4`, and `double_720_separates_more_than_360: false`.
- Lift level: separates 720 from 360 for all 16 strategy analogs under phase-sensitive overlap readout.
- Quotient map: applying the density/projective quotient erases the lift sign and collapses the packet back to the committed e2d9d5407 classes byte-consistently.
- Anti-collapse groups: not resolved. The lift does not split the committed slot-copy groups; it only confirms they remain indistinguishable under this lift readout.

What is not earned:

- no strategy promotion;
- no engine admission;
- no formal admission;
- no physics claim;
- no PyTorch/graph/autograd claim;
- no admitted manifold or loop-manifold object;
- no claim beyond the n=8 loop-local spinor-lift readout and its density quotient control.

