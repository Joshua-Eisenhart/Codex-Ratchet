# BUILD CARD - axis_triple_consistency_b6_v1

Source request: build the shared-carrier follow-up to `axis_triple_consistency_b6_v0` inside
`system_v6/sims/axis_triple_consistency_b6_v1/`, file-disjoint, with no git add/commit.

## Ceiling

- `classification=scratch_diagnostic`
- `claim_ceiling=axis_readout_candidate_only + shared_carrier_blocker_and_proxy_consistency_row_only`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- No `audit_verdict.md`; the builder boundary helper is load-bearing through the local object,
  envelope, and validator.

## Authority Read Order

1. v0 negative build plus audit at `f2b16cbf5`, especially Reading A:
   realization-unfaithful is the strongest live reading.
2. `system_v6/receipts/axis_work_order_20260612.md`
3. `system_v6/receipts/cross_model_anchor_recompute_panel6_20260612.md`
4. `system_v6/receipts/cross_model_anchor_recompute_panel8_20260612.md`
5. `discrete_axis0_field_v0` and `discrete_axis6_precedence_v0`
6. `discrete_axis3_placement_v0`, especially `gamma_in`/`gamma_out` semantics.
7. `manifold_super_sim_v2_weld` as related-not-shared context only.

## Object

The requested faithful shared-carrier object is:

```text
b6 = -b0*b3
```

with `b0`, `b3`, and `b6` all realized faithfully on one carrier before the relation is checked.
The preferred carrier is the committed Family A 33-cell object, because Axis0 and Axis6 already
share it.

The committed Axis3 semantics are stricter than an inner/outer label:

- `gamma_in`: density-stationary inner/fiber loop.
- `gamma_out`: density-traversing outer/base loop with `A(dot gamma)=0`.

The current 33-cell carrier has cells and generator-labelled transitions, but no source-backed
hidden fiber phase, connection-form row, or adapter that computes `gamma_in`/`gamma_out` on those
33 cells. Therefore this packet records:

- `shared_carrier_status=blocked_open_no_faithful_axis3_on_33_cell_adapter`
- a 33-cell Axis3 inner/outer proxy table as contrast only;
- no faithful all-three consistency table;
- no restoration or killing of Reading A.

## Sign Ledger

| layer | fiber / gamma_in | base / gamma_out | neutral |
|---|---:|---:|---:|
| committed Axis3 placement sign | -1 | +1 | 0 |
| panel relation `b3` sign | +1 | -1 | 0 |

Panel 6 q2 anchors remain:

| anchor | b0 | b3 | target b6 |
|---|---:|---:|---:|
| `eta=pi/6`, fiber | +1 | +1 | -1 |
| `eta=pi/3`, base | -1 | -1 | -1 |

Panel 8 q1 controls remain:

- scrambled baseline chance: `1/2`;
- global b-convention flip target: `b6 = +b0*b3`.

## Required Checks

- Rebuild the committed Family A 33-cell carrier through the Axis0 source helper.
- Recompute Axis0 signs and Axis6 precedence signs through their committed source helpers.
- Run the faithful Axis3-on-33 carrier gate before any relation claim.
- Compute the proxy b3 signs independently from shell placement, not from `b0*b6`.
- Emit per-row sign vectors and hashes from Julia, JAX, PyTorch, and envelope.
- Evaluate panel 6 q2 anchors.
- Preserve panel 8 q1 convention-flip and scrambled controls.
- Reproduce the v0 Hopf-transplant negative as a contrast row.
- Use row-local z3 and cvc5 bindings with erased flips.
- Run the standard envelope helper, local validator, generic three-engine validator, and pytest.

## Result Summary

Faithful shared-carrier gate:

```text
blocked_open_no_faithful_axis3_on_33_cell_adapter
```

No current repo carrier hosts all three faithfully:

- Family A 33-cell carrier hosts Axis0 and Axis6 faithfully, but only a proxy Axis3 placement readout here.
- Family B Hopf carrier hosts Axis3 faithfully, but Axis0/Axis6 there are transplant/proxy rows as in v0.
- The weld records related/quotient accounting and B3 conservation accounts, not a shared Axis3 placement adapter.

Proxy contrast summary:

| scope | total | agreement | violations | non-neutral agreement |
|---|---:|---:|---:|---:|
| 33-cell proxy contrast | 33 | 16 | 17 | 15/32 |
| v0 Hopf transplant contrast | 48 | 16 | 32 | 16/32 |

## Consistency Table

This table is a proxy contrast only. `b3` is the panel relation sign, not an admitted faithful
Axis3-on-33 sign.

| cell | coord_scaled | b0 | b3 | b6 | -b0*b3 | holds | proxy class |
|---:|---|---:|---:|---:|---:|---|---|
| 0 | `[-2, 0, 0]` | -1 | -1 | 1 | -1 | NO | gamma_out_like_outer_base_proxy |
| 1 | `[-1, -1, -1]` | -1 | -1 | 1 | -1 | NO | gamma_out_like_outer_base_proxy |
| 2 | `[-1, -1, 0]` | -1 | -1 | 1 | -1 | NO | gamma_out_like_outer_base_proxy |
| 3 | `[-1, -1, 1]` | -1 | -1 | 1 | -1 | NO | gamma_out_like_outer_base_proxy |
| 4 | `[-1, 0, -1]` | 1 | -1 | 1 | 1 | yes | gamma_out_like_outer_base_proxy |
| 5 | `[-1, 0, 0]` | -1 | 1 | 1 | 1 | yes | gamma_in_like_inner_fiber_proxy |
| 6 | `[-1, 0, 1]` | -1 | -1 | 1 | -1 | NO | gamma_out_like_outer_base_proxy |
| 7 | `[-1, 1, -1]` | 1 | -1 | 1 | 1 | yes | gamma_out_like_outer_base_proxy |
| 8 | `[-1, 1, 0]` | 1 | -1 | 1 | 1 | yes | gamma_out_like_outer_base_proxy |
| 9 | `[-1, 1, 1]` | 1 | -1 | 1 | 1 | yes | gamma_out_like_outer_base_proxy |
| 10 | `[0, -2, 0]` | -1 | -1 | -1 | -1 | yes | gamma_out_like_outer_base_proxy |
| 11 | `[0, -1, -1]` | -1 | -1 | -1 | -1 | yes | gamma_out_like_outer_base_proxy |
| 12 | `[0, -1, 0]` | -1 | 1 | -1 | 1 | NO | gamma_in_like_inner_fiber_proxy |
| 13 | `[0, -1, 1]` | -1 | -1 | -1 | -1 | yes | gamma_out_like_outer_base_proxy |
| 14 | `[0, 0, -2]` | 1 | -1 | 0 | 1 | NO | gamma_out_like_outer_base_proxy |
| 15 | `[0, 0, -1]` | 1 | 1 | 0 | -1 | NO | gamma_in_like_inner_fiber_proxy |
| 16 | `[0, 0, 0]` | 0 | 0 | 0 | 0 | yes | neutral_center_no_hopf_phase |
| 17 | `[0, 0, 1]` | -1 | 1 | 0 | 1 | NO | gamma_in_like_inner_fiber_proxy |
| 18 | `[0, 0, 2]` | -1 | -1 | 0 | -1 | NO | gamma_out_like_outer_base_proxy |
| 19 | `[0, 1, -1]` | 1 | -1 | 1 | 1 | yes | gamma_out_like_outer_base_proxy |
| 20 | `[0, 1, 0]` | 1 | 1 | 1 | -1 | NO | gamma_in_like_inner_fiber_proxy |
| 21 | `[0, 1, 1]` | -1 | -1 | 1 | -1 | NO | gamma_out_like_outer_base_proxy |
| 22 | `[0, 2, 0]` | 1 | -1 | 1 | 1 | yes | gamma_out_like_outer_base_proxy |
| 23 | `[1, -1, -1]` | 1 | -1 | -1 | 1 | NO | gamma_out_like_outer_base_proxy |
| 24 | `[1, -1, 0]` | 1 | -1 | -1 | 1 | NO | gamma_out_like_outer_base_proxy |
| 25 | `[1, -1, 1]` | -1 | -1 | -1 | -1 | yes | gamma_out_like_outer_base_proxy |
| 26 | `[1, 0, -1]` | 1 | -1 | -1 | 1 | NO | gamma_out_like_outer_base_proxy |
| 27 | `[1, 0, 0]` | 1 | 1 | -1 | -1 | yes | gamma_in_like_inner_fiber_proxy |
| 28 | `[1, 0, 1]` | -1 | -1 | -1 | -1 | yes | gamma_out_like_outer_base_proxy |
| 29 | `[1, 1, -1]` | 1 | -1 | -1 | 1 | NO | gamma_out_like_outer_base_proxy |
| 30 | `[1, 1, 0]` | 1 | -1 | -1 | 1 | NO | gamma_out_like_outer_base_proxy |
| 31 | `[1, 1, 1]` | -1 | -1 | -1 | -1 | yes | gamma_out_like_outer_base_proxy |
| 32 | `[2, 0, 0]` | -1 | -1 | -1 | -1 | yes | gamma_out_like_outer_base_proxy |

## Reading A Adjudication

The faithful-carrier version does not yet restore the relation and does not kill Reading A.

Reason: the requested faithful all-three carrier is unavailable in the current repo evidence. The
33-cell proxy table can fail, and does fail, but it is not faithful Axis3 placement. Therefore the
v0 audit's Reading A remains live: the v0 failure may still be realization-unfaithful, and the next
admissible move is a proof-backed fiber-augmented 33-cell cover or explicit adapter that computes
`gamma_in`/`gamma_out` predicates per 33-cell row before the relation is checked.
