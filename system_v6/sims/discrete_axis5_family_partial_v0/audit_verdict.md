# Independent Audit Verdict - discrete_axis5_family_partial_v0

Bottom line: `GENUINE-WITH-CAVEATS` for the partial Axis-5 operator-family half only. The packet source-locks `{Ti,Te}` versus `{Fi,Fe}` by computed witnesses on the shared 33-cell carrier, preserves the weak boundary control, keeps label drift unresolved, and honors the substage-product block. It is not a full Axis-5 result.

Freshness tier: `TIER-2` (`results-available`). I read the build card/source/result JSONs before recomputation, and there was no prior `audit_verdict.md` in the packet at audit start.

## Citable Sentence

`discrete_axis5_family_partial_v0` supports a citable partial Axis-5 readout: on the Family-A 33-cell carrier, the source-locked `{Ti,Te}` dephasing/gradient-side operators separate from the `{Fi,Fe}` unitary/Hamiltonian-side operators by entropy/contractivity versus exact purity/orbit-preservation witnesses, with the full `axis5 x axis6` substage product still blocked on the missing owner-pinned transition convention.

## Checks

- Standards used: `system_v6/receipts/axes45_deep_vein_20260612.md`, `system_v6/receipts/audit_standards_codex_v1.md`, `system_v6/receipts/axis_work_order_20260612.md`, and the same-carrier Axis 0/6/4 result surfaces.
- Runtime doctor: `ok=True`; sim-stack Python and Julia carrier project were stable, with no repo-local env pollution or active installers observed.
- Generic three-engine validator: `ok=True` for `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/discrete_axis5_family_partial_v0/results/discrete_axis5_family_partial_v0_envelope_results.json`.
- Packet validator called read-only through `validate_payload(...)`: `ok=True`, no errors. I did not run the packet validator main because it writes `validator_results.json`.
- Tests: `python -m pytest -q -p no:cacheprovider system_v6/sims/discrete_axis5_family_partial_v0/tests` gave `2 passed`.

## Witness Recompute

I recomputed two dephasing-side rows and two unitary-side rows independently from the formulas, not from the packet prose.

- `Ti`, `cell_id=0`, input `[-1,0,0]`: exact post `[-7/10,0,0]`; radius squared contracts from `1` to `49/100`; entropy delta recomputed `0.4227090878059909`, matching result `0.422709087805991`.
- `Te`, `cell_id=1`, input `[-1/2,-1/2,-1/2]`: exact post `[-1/2,-7/20,-7/20]`; radius squared contracts from `3/4` to `99/200`; entropy delta recomputed `0.17383159857114944`, matching result `0.173831598571149`.
- `Fi`, `cell_id=0`, input `[-1,0,0]`: exact purity before/after `1 -> 1`; exact purity delta `0`; orbit norm preserved.
- `Fe`, `cell_id=0`, input `[-1,0,0]`: exact post `[0,-1,0]`; exact purity before/after `1 -> 1`; exact purity delta `0`; orbit norm preserved.

The primary table reports `66` `dephasing_gradient_side`, `66` `unitary_hamiltonian_side`, and `0` primary `boundary` rows across all three lanes. The shuffled-order control preserves those counts.

## Boundary Control

The weak-dephasing-near-unitary control is present and correctly classified as `boundary`: `q=1e-12`, entropy/purity/norm deltas rounded to `0.0`, and classification `boundary` under `BOUNDARY_EPS=1e-8`. This control could fail under the packet's own logic: with ordinary dephasing strength, the same witness path leaves the boundary band and classifies as `dephasing_gradient_side`.

## Partial Fence

The partial fence is honored on every checked surface.

- Top-level ceiling: `classification="scratch_diagnostic"`, `claim_ceiling="axis_readout_candidate_only"`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- Disallowed claims include `axis admission`, `Axis-5 completion`, `axis5_axis6_substage_product`, `Matrix64 completion`, `label drift resolution`, `bridge admission`, and `physics`.
- `substage_product_status.status="blocked"`, `substage_product_built=false`.
- Four `substage_product_rows` exist only as `blocked_not_built`, with reason `substage_transition_convention_not_owner_pinned`.
- Every family-table row checked has `substage_product_built=false`.

## Label Drift

Label drift handling is honest. Every family-table row uses `classification_source="computed_witnesses_not_label_resolution"` and `label_drift_resolution="unresolved_carried_as_annotation"`. The packet preserves both `FeFi-vs-TeTi` and `FeFi-vs-TiTe` as unresolved variants, while using `{Ti,Te}` versus `{Fi,Fe}` as the runtime anchor.

## Independence Rows

Packet-carried no-identity-leak rows pass for 0/5 and 6/5:

- Axis 5 from Axis 0 majority accuracy: `0.5`.
- Axis 0 from Axis 5 majority accuracy: `0.5151515151515151`.
- Axis 5 from Axis 6 majority accuracy: `0.5`.
- Axis 6 from Axis 5 majority accuracy: `0.42424242424242425`.
- Operator-label identity leak is explicitly detected at `1.0` and excluded.

Axis 4 is present on the same 33-cell carrier, but the target packet does not carry a packet-level 4/5 independence row. Auditor-only recomputation found the analogous 4/5 majority rows would be non-perfect (`0.5` and `0.42424242424242425`) with the same operator-label leak excluded, but this is not target-packet evidence.

## Caveats

- `G1_partial_only`: the verdict applies only to the operator-family half. The full `axis5 x axis6` substage product remains blocked.
- `G2_label_drift_unresolved`: `FeFi-vs-TeTi` and `FeFi-vs-TiTe` are annotations only; no symbolic label resolution is earned.
- `G3_tier2_not_blind`: this is a fresh recompute audit, but not full-blind; packet results were available before recomputation.
- `G4_missing_packet_4_5_row`: same-carrier Axis 4 exists, but 4/5 independence is not carried inside this packet. The auditor-only 4/5 side-check passes non-perfect recovery, but future citation should not describe packet-carried 4/5 evidence until the row is added.
- `G5_lane_signature_shape`: JAX and PyTorch result signatures match; Julia's signature differs because its lane result is thinner. The accepted parity is count/control/proof parity, not byte-identical row payload parity.

## Full Axis-5 Requirement

Full Axis 5 needs the substage pin. The owner/source convention must specify what the four substages are, the two Axis-5 states, the two Axis-6 states inside the product, order within a stage, wrap/advance rules, Matrix64/Carnot product mapping if used, the observable that distinguishes substages, and which symbolic labels are load-bearing versus decorative. Until then, only the partial `{Ti,Te}` versus `{Fi,Fe}` operator-family readout is citable.
