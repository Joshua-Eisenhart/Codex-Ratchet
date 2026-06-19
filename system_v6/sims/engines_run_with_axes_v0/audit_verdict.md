# Audit Verdict: engines_run_with_axes_v0

Bottom line: **GENUINE-WITH-CAVEATS**. The packet runs Carnot and Szilard stroke fixtures as actual 33-cell carrier transitions, then applies the committed axis readout tables unchanged to the post-stroke trajectories. It is not BY_CONSTRUCTION as a table readback, but its ceiling is only a local classical baseline for future ECD/QIT discriminators.

## Verdict

- Verdict: `GENUINE-WITH-CAVEATS`
- Claim ceiling: `classical_engine_axis_signature_baseline_only`
- Status ladder: `exists + fresh local rerun passes`; not promoted, not canonical, not formal admission.
- Freshness tier: `TIER-2 results-available`. I read packet source/result and recomputed from source; I did not rely on a prior audit verdict.
- Write boundary: read-only except this file. Runner and validator entrypoints were rerun with output paths monkeypatched to `/tmp` so repo result JSONs were not rewritten.
- Citation rule: cite this only as `classical_baseline_for_future_qit_engine_signature` / `baseline for ECD discriminators`; do not cite it as QIT capability evidence, thermodynamic heat-bath dynamics, axis admission, full Axis-5 evidence, bridge/physics evidence, or a nonclassical engine result.

## What Passed

Fresh validator rerun:

- Actual runner entrypoint with `/tmp` output: exit `0`, `all_pass=true`.
- Actual validator entrypoint with `/tmp` output: exit `0`, `ok=true`, `errors=[]`.
- Read-only validator call on committed result: `validate_payload(...) == []`.
- Fresh `build_packet()` matched committed result core fields: carrier, running engines, comparison, controls, ledger continuity, axis locks.
- Tests: `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/engines_run_with_axes_v0/tests` -> `5 passed in 5.20s`.

Source path:

- The packet imports the parent carrier/readout builders directly (`engines_run_with_axes_v0_common.py:41-50`) and builds parent objects through `rebuild_committed_carrier()`, `build_axis0_object()`, `build_axis6_object()`, `build_axis4_object()`, and `build_axis5_object()` (`engines_run_with_axes_v0_common.py:177-186`).
- Stroke execution is real transition lookup over the running cell vector, not a declared output table (`engines_run_with_axes_v0_common.py:392-459`).
- Axis signatures are looked up from parent axis tables on post-stroke cells (`engines_run_with_axes_v0_common.py:305-389`).
- Validator requires 33 states, 198 carrier edges, 4 strokes per engine, no missing transitions, unchanged axis locks, computed comparison, identity degeneracy, shuffled N01 changes, ledger continuity, and classical-baseline fences (`engines_run_with_axes_v0_common.py:699-775`).

## Recomputed Teeth

1. **Actual 33-row dynamics.** I independently rebuilt the carrier edge lookup and recomputed Carnot stroke 0, `hot_isothermal_expansion` with generator `Ne_Spiral_R`, from initial cells `0..32`.
   - Recomputed after-cells:
     `[7, 1, 5, 0, 15, 4, 8, 14, 19, 22, 3, 12, 2, 6, 23, 11, 16, 21, 9, 26, 30, 20, 29, 10, 13, 18, 24, 28, 17, 32, 27, 31, 25]`
   - `trajectory_len=33`, `changed_cell_count=30`, `manual_equals_result_trajectory=true`.
   - The committed result records the same 33 trajectory rows and `transition_count=33` (`results/engines_run_with_axes_v0_results.json:1531-1772`).

2. **Axis readouts unchanged.** I diffed current parent readout sources against their pinned commits:
   - Axis 0 `5d330b427`: diff exit `0`.
   - Axis 6 `b6fafc67f`: diff exit `0`.
   - Axis 4 `99c4f84b3`: diff exit `0`.
   - Axis 5 partial `99906e7d7`: diff exit `0`.
   The result source locks also name those parent paths and hashes (`results/engines_run_with_axes_v0_results.json:56-85`). No fork finding.

3. **Post-stroke axis counts.** For the same Carnot stroke 0, I recomputed axis counts directly from parent tables over the recomputed post-cells:
   - Axis 0: `{-1: 17, 0: 1, 1: 15}`
   - Axis 6: `{-1: 14, 0: 5, 1: 14}`
   - Axis 4: `{-1: 14, 0: 5, 1: 14}`
   - Axis 5-family: `{dephasing_gradient_side: 66, unitary_hamiltonian_side: 66}`
   These match the result row (`results/engines_run_with_axes_v0_results.json:1505-1528`).

4. **Identity-control degeneracy.** Recomputed identity control had `all_strokes_identity=true`, `degenerate_signatures=true`, and one unique signature hash across four identity strokes. The result records the same degenerate hash repeated four times (`results/engines_run_with_axes_v0_results.json:188-200`).

5. **Shuffled-order N01 signatures.** Recomputed shuffled order `[0, 2, 1, 3]` changed both engine signatures:
   - Carnot canonical `6cb0ae5e6d87a167b91848a1fa6df3c6d7e8aaa4b4c4b4938b891dd4448d5001` vs shuffled `53dfbbb3e47f91b1bf783850fdb76db2be350c5b98cda7a7ff0e8c0b7436d673`; final cells unchanged.
   - Szilard canonical `63f9c91cc0ad0c6d0be53f0b9d94929900ac7c4d5b6dc516d42f432daefaead2` vs shuffled `0ea682a900c6cf67a367d4727fee4b3e1aa033f898ec471aad754b14140f310d`; final cells changed.
   The result records those same hashes and flags (`results/engines_run_with_axes_v0_results.json:201-230`).

6. **Carnot vs Szilard four aligned rows.** Recomputed comparison equals the result. All four aligned stroke rows differ on `axis0`, `axis6`, `axis4`, and `axis5_family` (`results/engines_run_with_axes_v0_results.json:104-170`). This is computed from trajectories and readouts, not copied from a declared comparison table. Caveat: the aligned comparison is under the packet-local stroke-to-generator fixture (`engines_run_with_axes_v0_common.py:225-251`), so cite it as a fixture-computed baseline, not an intrinsic Carnot-vs-Szilard theorem.

## Caveats

- `G1 untracked packet`: `git status --short system_v6/sims/engines_run_with_axes_v0` reports `?? system_v6/sims/engines_run_with_axes_v0/`. This audit can say the local packet exists and passes fresh local rerun; it cannot say the packet is committed in this checkout.
- `G2 fixture boundary`: the stroke-to-generator map is explicitly a packet fixture over committed generator names (`build_card.md:31-36`). The all-four aligned-row difference is real computation under that fixture, but not a thermodynamic model or QIT capability result.
- `G3 Axis-5 partial fence`: Axis 5 is only the committed partial operator-family readout (`axis5_operator_family_half_only`), and the packet keeps full Axis-5 admission out of scope (`results/engines_run_with_axes_v0_results.json:235-243`, `277-285`).

## Circularity Check

- `frozen-factor echo`: not found. Rows run over the same moving 33-cell carrier; no frozen complementary factor is projected as moving structure.
- `definitional circularity`: not found on the claim path. The identity engine is definitionally identity, but it is only a negative/control row, not the positive baseline claim.
- `rule-table readback`: not found as a promoted invariant. The packet intentionally consumes parent readout tables; it does not claim to rediscover the parent axes. Citations must point back to parent axis packets for axis validity.
- `post-hoc statistic`: not found. No significance statistic or selected target set is used.
- `shift-relabeling`: not found. Carnot/Szilard strokes are not relabeled calibration rows; they run explicit generator sequences.
- `structure-by-symmetry`: not found. The checked rows are enumerated transitions and table lookups, not inferred from symmetry alone.

## Boundaries

The classical-baseline fence held. The result classifies the row as `classical_baseline`, sets promotion and formal admission false, includes a divergence log only for a future QIT comparison, and lists disallowed claims including QIT admission, nonclassical superiority, thermodynamic heat-bath dynamics, axis admission, full Axis-5 completion, physics, and bridge admission (`results/engines_run_with_axes_v0_results.json:87-95`, `186-187`, `235-249`, `295-297`).

No-identity-leak and positive-boundary rules are not directly claim-bearing here because this packet does not claim a new independence predicate or contender admission. If citing parent axis independence, cite the parent packet's identity-leak caveats, not this baseline packet.
