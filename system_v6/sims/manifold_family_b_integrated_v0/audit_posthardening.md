# manifold_family_b_integrated_v0 Post-Hardening Audit

Bottom line: `VERDICT: HARDENING_CLEAN`.

Commit `29e133f2f` stands. I found no out-of-scope regression in the focused five-check scope.

## Scope

Independent post-hardening verification of round 1 only:

1. B1 pinned ratchet ledger path is live.
2. `axis0_` leakage is projected out of scoped artifacts.
3. B3 record rows carry row-local `z4_syndrome_record_v0` co-citation and state-plus-record convention.
4. Trajectory lineage has file-byte SHA, stable payload SHA, step ids, lineage ids, and class reasons.
5. Hardened sources stay traceable to fixes 1-4, weld anchors are unchanged, and validators still pass.

I did not edit `audit_verdict.md`. I did not run `git add` or commit.

## Check 1 - B1 Pin Path

Result: `PASS`.

Fresh live-path control through `manifold_family_b_integrated_v0_common.deep_chain_layer()`:

- baseline final denominator: `16`;
- mutated pin path: `B1.pinned_ratchet_row_ledger.derived_pin_rows[1].factor`, changed in memory from `4` to `5`;
- mutated final denominator: `20`;
- baseline exact final volume: `pi**2/4`;
- baseline entropy deltas: `["-log(4)", "-log(2)", "-log(2)"]`;
- baseline reduced-row denominators matched `pinned_ratchet_row_ledger.derived_pin_rows`;
- pin block SHA changed under mutation.

This confirms the deep-chain values flow through the live B1 pin block, not a stale imported constant.

## Check 2 - Axis0 Projection

Result: `PASS`.

Command:

```text
rg -n "axis0_" system_v6/sims/manifold_family_b_integrated_v0/manifold_family_b_integrated_v0_envelope_spec.json system_v6/sims/manifold_family_b_integrated_v0/results/manifold_family_b_integrated_v0_envelope_results.json system_v6/sims/manifold_family_b_integrated_v0/results/manifold_family_b_integrated_v0_trajectory_artifact.json
```

Output was empty. The spec, envelope, and trajectory artifacts contain no `axis0_` hits.

## Check 3 - Row-Local Co-Citation

Result: `PASS`.

B3 record rows inspected:

- `B3_full_record`;
- `B3_erased_record`.

Both rows carry:

- `co_citation: system_v6/sims/z4_syndrome_record_v0/results/z4_syndrome_record_v0_envelope_results.json`;
- `state_plus_record_convention_label: finite_counting_state_plus_record`.

## Check 4 - Trajectory Lineage

Result: `PASS`.

Trajectory artifact checks:

- stable payload/content SHA recomputed: `3f0653ac95b27bb4b89dd6846961d0ade20dab0902a370e17a464c4ec02c5728`;
- stored `content_sha256`: `3f0653ac95b27bb4b89dd6846961d0ade20dab0902a370e17a464c4ec02c5728`;
- file-byte SHA recomputed: `26e608dc8cb75e2d78737355e268e6c0b6ab246363c7361a98e56b77da39b424`;
- sidecar SHA: `26e608dc8cb75e2d78737355e268e6c0b6ab246363c7361a98e56b77da39b424`;
- step row count: `16`.

Spot checks:

- row `0`, `B1_step_1`: `STEP_DEPENDENT`; reason says row was recomputed from current trajectory step input. This matches actual B1 pin-derived step dependence.
- row `4`, `B1_step_5`: `CARRIED`; reason says row was carried unchanged across this bounded Family B trajectory. This matches the parent-row class assigned for parent steps after step 4.
- row `7`, `B2_step_0`: `STEP_DEPENDENT`; reason says row was recomputed from current trajectory step input. This matches B2 predicate-flow dependence.

Each spot-checked row has non-empty `trajectory_step_id` and `row_step_lineage_id`.

## Check 5 - Regression And Validators

Result: `PASS`.

Diff/state notes:

- `git log --oneline -- system_v6/sims/manifold_family_b_integrated_v0` shows only `29e133f2f` for this packet, so there is no separate committed pre-hardening source tree to diff against.
- I therefore checked current committed sources against the stale `audit_verdict.md` caveats and the four `Round 1 hardening note` fixes in `build_card.md`.
- The current worktree has no tracked diff from `29e133f2f` under `system_v6/sims/manifold_family_b_integrated_v0`.
- The hardening touchpoints found in source/tests/validator map to the four named fixes: B1 pin block consumption, B2 `axis0_` projection, B3 row-local co-citation, and trajectory SHA/lineage fields.
- I found no additional tracked change in the target packet that indicates a new claim surface, Family A use, two-engine use, axis/bridge/physics promotion, or claim-ceiling change.

Weld anchors remain byte/value-matched:

- deep-chain denominator: `16`;
- exact volume: `pi**2/4`;
- entropy deltas: `["-log(4)", "-log(2)", "-log(2)"]`;
- compression counts: `384`, `288`, `96`;
- hash-chain heads:
  - `41d0113914c03390eac69b7e6ba7763d439dd275e981458bb90b5b4eef14e3ff`;
  - `f78beccf9623dd94a9316e03132616bb250e85ee5b0186e02b356db207138b47`;
  - `20d5517a287c8f351a396e4001927cf8a9b789029788c6c4a6ff1a5ce15c8961`;
- conservation defect: `0.0`.

Read-only packet validation:

```text
packet_validator.validate_payload(envelope) -> []
```

Strict three-engine validator:

```text
PYTHONPATH=scripts /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/manifold_family_b_integrated_v0/results/manifold_family_b_integrated_v0_envelope_results.json
```

Output:

```json
{
  "ok": true,
  "result_json": "system_v6/sims/manifold_family_b_integrated_v0/results/manifold_family_b_integrated_v0_envelope_results.json"
}
```

## Final Verdict

`HARDENING_CLEAN`.

No revert/fix is indicated by this focused post-hardening audit.
