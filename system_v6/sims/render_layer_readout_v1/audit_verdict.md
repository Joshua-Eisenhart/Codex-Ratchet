# Independent audit verdict - render_layer_readout_v1

Audit mode: read-only audit with independent recomputation from source; live repo write scope was this file only.
Freshness tier: TIER-3 by `audit_standards_codex_v1` because the prompt supplied builder claims and v0 verdict language. Central rows below were recomputed from source in this audit.
Auditor: independent cross-backend auditor.

## Bottom Line

VERDICT: GENUINE-WITH-CAVEATS for a positive `own_readout_family` claim at `scratch_diagnostic` ceiling.

The v1 signed projection pin is natural enough for the v1 contract: it compares the committed render-update correction against the committed source-to-render direction, instead of comparing two nonnegative distances as v0 did. I found no cell-specific, trajectory-specific, or result-selected quantity in the pin beyond the v0 unreachability diagnosis itself.

The core positive claim is real: fresh recomputation gives the committed-edge witness gate `reshape=64`, `resist=92`, `neutral=42`; the readout row gives `reshape_cells=3`, `resist_cells=30`, `unique_render_sign_count=2`; v0 old-pin regression refuses readout rows; scrambled-error breaks the nonconstant readout; and all three lanes agree on the render sign-vector hash.

Caveat G1: the exact `3`-cell positive set is not stable across trajectory/convention probes. It is not one epsilon from constant, but the exact positive cells flicker under start-cell and generator-order changes. Cite the result as a two-sided signed render-update own-readout-family diagnostic, not as a stable invariant `3-of-33` cell set.

Caveat G2: the no-identity-leak control is field-level, not the full audit-standards predictor report. The source does not condition the readout on cell identity, but the packet does not emit `identity_leak_detected`, `identity_leak_excluded_best_accuracy`, or `identity_leak_exclusion_rule`; do not cite it as a full statistical independence row.

Accepted ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; no holodeck/FEP/physics/Axis-0/bridge/manifold/admission claim.

## Pin Naturalness

PASS. The build card pins:

```text
direction = unit(render - source)
direction_scalar = dot(realized - render, direction)
```

That is the signed render-update component along the committed prediction direction. The implementation matches it in `pin_value`: it builds `source_to_render`, `render_to_realized`, normalizes the source-to-render direction, then returns `realized_state_flow - source_to_render_flow`, equivalently signed `render_update_flow` (`render_layer_readout_v1_common.py:114-144`).

The pin references only source, render, and realized states from the committed carrier edge row (`render_layer_readout_v1_common.py:147-184`). The old v0 pin is retained separately as a negative control (`render_layer_readout_v1_common.py:94-99`, `275-287`). This is not a mirror artifact tuned to the observed `3` cells.

## Recomputed Counts

Fresh source recompute with `common.build_core()`:

```json
{
  "gate": {"reshape_the_render": 64, "resist_the_update": 92, "neutral_no_render_polarity": 42},
  "counts": {
    "reshape_cells": 3,
    "resist_cells": 30,
    "neutral_cells": 0,
    "unique_render_sign_count": 2,
    "axis0_disagreement_cells": 17
  },
  "reshape_cells": [11, 17, 27]
}
```

The gate is correctly before readout rows: `reachability_gate()` sweeps all committed edges before `build_packet_for_pin()` emits the trajectory/readout table, and failed gate returns `readout_table_ran=false` with no readout table (`render_layer_readout_v1_common.py:200-231`, `405-446`).

The strict source-backed three-engine validator returned:

```json
{"ok": true, "result_json": "system_v6/sims/render_layer_readout_v1/results/render_layer_readout_v1_envelope_results.json"}
```

The packet-local validator was also run read-only by monkeypatching the writer to a no-op; it returned `errors=[]` and would have written `all_pass=true`.

## Stability Teeth

The committed-edge gate itself has real margin: among all 198 committed edges, the nearest nonzero signed projection magnitude is `0.016685305471659`; positive edge count is `64` and negative edge count is `92`.

The aggregate readout margin is thinner. For the committed start-0 trajectory, positives are cells `[11, 17, 27]`; the closest positive is cell `17` at `0.00834265273583`, and the closest overall cell is a resist cell at `-0.008156173409501`. Epsilon widening leaves `3/30/0` unchanged through `eps=0.008`; at `eps=0.0082` one resist cell becomes neutral, and at `eps=0.0084` cell `17` also becomes neutral. This is thin, but not near constant.

Trajectory/convention probes do not preserve the exact `3`-cell set:

- all 33 start-cell trajectories with the same generator cycle remained nonconstant and two-sided, but positives ranged from `2` to `6` cells and the positive identities changed;
- cyclic generator-order variants gave either `[11, 17, 27]` or `[12, 20, 22, 27]`;
- reversed generator order gave `[4, 12, 27]`.

Therefore the exact `3`-cell readout flickers. The stable statement is only that this carrier and pin admit a nonconstant two-sided signed render-update family under the sampled committed trajectory variants. The exact `3/30` split is a start-0 packet row, not a stable cell-set invariant.

## Boundary And Controls

Boundary recompute: `relation_to_axis0_phi="different_distinction_from_axis0"` and `verdict="own_readout_family"`. The comparison is now meaningful because the render sign vector is nonconstant. The positive-predicate control can admit the exact Axis-0 anchor, so the boundary predicate is not a negative-only filter.

Controls:

- v0 old-pin regression: `reshape=0`, `resist=92`, `neutral=106`, `readout_table_ran=false`, `reproduces_unreachable_reshape=true`.
- scrambled-error: `same_cell_count=29`, `verdict="breaks-render-polarity"`.
- identity dynamics: degenerates the render readout, as expected.
- no identity leak: formula fields are source/render/realized/generator fields and the implementation does not use cell-id as a readout feature. Caveat G2 remains because the result lacks the full audit-standards predictor fields.

The boundary code maps nonconstant, non-alias, controls-passing rows to `own_readout_family` and `different_distinction_from_axis0` (`render_layer_readout_v1_common.py:290-318`). The source also emits disallowed claims that block Axis-0 admission, holodeck/FEP admission, formal admission, canonical status, and manifold claims (`render_layer_readout_v1_common.py:427-440`).

## G.2a

PASS from birth. The validator does not hard-require `audit_verdict.md` absence. It checks the build card for `builder_audit_boundary`, calls packet boundary checks, and delegates audit-file idempotency through `builder_audit_boundary_errors(...)` (`validate_render_layer_readout_v1.py:66-71`, `109-111`). This satisfies the G.2a rule that new validators use the shared boundary helper instead of hard absence checks (`audit_standards_codex_v1.md:170-177`).

## Doctrine And ECD.06

Doctrine expectation 2 answer: v1 answers the v0 void with an own readout family at scratch ceiling on this carrier, under the signed render-update projection pin. It does not rescue CP.12 or admit Axis-0; it reports a different distinction from Axis-0.

What ECD.06 may consume:

`render_layer_readout_v1: signed projection pin is natural and two-sided; committed-edge witness gate passes with 64 reshape / 92 resist / 42 neutral; start-0 readout is nonconstant with 3 reshape / 30 resist; boundary is different_distinction_from_axis0 / own_readout_family; v0 old-pin regression refuses rows; scrambled-error breaks; three-engine hashes align; ceiling scratch_diagnostic; promotion_allowed=false. Caveats: exact 3-cell set is not trajectory/convention-stable; no-identity-leak is field-level rather than full predictor-field standards report.`

What ECD.06 must not consume:

- no stable `3-of-33` cell-set invariant;
- no holodeck/FEP/physics/Axis-0 admission;
- no bridge, manifold, formal, or canonical claim;
- no full identity-independence statistic beyond field-level no-cell-id conditioning.

## Commands And Checks

Read-only checks run:

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# imported render_layer_readout_v1_common; ran common.build_core();
# recomputed gate counts, readout counts, sign vector, margins, v0 regression, scrambled control
PY
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/render_layer_readout_v1/results/render_layer_readout_v1_envelope_results.json
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# monkeypatched common.write_json to no-op; ran validate_render_layer_readout_v1.validate_payload();
# result: errors=[]
PY
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# swept all 33 start-cell trajectories and generator-order variants without writing repo result files
PY
```

Not run live in-place: the builder scripts and full pytest roundtrip as `main`, because those commands rewrite repo result receipts and the audit authorization allowed live repo writes only to this verdict file. Existing packet result files record all three lane `all_pass=true`, validator `all_pass=true`, and matching render sign-vector hashes.

## Citation Rule

Cite this packet only as:

`GENUINE-WITH-CAVEATS scratch diagnostic: natural signed render-update projection; two-sided committed-edge reachability; nonconstant own readout family different from Axis-0 on this carrier; v0-pin regression and scrambled control pass; exact 3-cell set not stable across trajectory/convention probes; no promotion/admission.`

Do not cite it as a stable cell-set invariant, CP.12/Axis-0 rescue, holodeck/FEP/physics admission, or canonical/formal/manifold evidence.
