# BUILD CARD - fiber_augmented_cover_v2_1

Source request: build `fiber_augmented_cover_v2_1` under
`system_v6/sims/fiber_augmented_cover_v2_1/`, file-disjoint, with no `git add`
or commit.

## Ceiling

- `classification=scratch_diagnostic`
- `claim_ceiling=axis_readout_candidate_only + decisive_repair_cover_no_admission`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- NO Betti and no homology computation in this packet. The packet emits
  hash-pinned chain complexes for guard v3 only.
- Boundary helper: `fiber_augmented_cover_v2_1_boundary.py` plus
  `scripts/builder_audit_boundary.py`.
- G.2a from birth: validators/tests delegate audit-file handling to the shared
  helper and do not require permanent absence of `audit_verdict.md`.

## Authority Read Order

1. `system_v6/sims/topology_parity_guard_v2/audit_verdict.md` at
   `2137ae3e8`: v2's old shifts `[1,1,1,0]` have integer-lift sum `3`, but
   mod-3 holonomy `0`; the finite complex is product-equivalent by a phase
   relabeling. Required repair: emit shifted, zero-shift, and wrong-gluing
   complexes for guard v3.
2. `system_v6/receipts/axis_work_order_20260612.md`, section
   `b6 CARRIER STATUS UPDATE 3`: the two live readings stay open until this
   decisive test. The old integer-lift witness is real at the old ceiling, but
   the honest finite invariant is the mod-|F| holonomy.
3. `fiber_augmented_cover_v2` at `cc2f61b2a`: committed CW base machinery to
   extend, not reinterpret.
4. `system_v6/receipts/audit_standards_codex_v1.md`: standards codex and G.2a
   bind from birth.

## Central Math Adjudication Before Building

For a degree-1 circle-bundle discretized with a `Z_3` fiber, the correct finite
clutching witness is seam holonomy `1 mod 3`, a generator. The old v1/v2 shifts
`[1,1,1,0]` sum to `3`, and `3 = 0 mod 3`; the old construction distributed one
full integer turn across the seam and the `Z_3` reduction killed it. That old
integer-lift winding remains a recorded fact about the old construction.

The v2.1 construction is a different pinned construction, registered by the
kill-then-earn cycle. It is not a reinterpretation of the old one. The new seam
steps are `[1,0,0,0]`, so:

- integer-lift sum: `1`
- mod-3 holonomy: `1`
- finite witness gate: pass only for the positive re-pin

## V2 Base Lock

The v2 CW base is unchanged by hash:

- source: `fiber_augmented_cover_v2_common.build_cellular_base()`
- expected base chain hash:
  `9d6655a51782305f80409cce0bd42a57329fb14ea19b05c32b95ec36016b883c`
- base counts remain `C0=33, C1=92, C2=61`, `chi=2`

## Fiber Augmentation

The v2.1 cover keeps the `33 x 3 = 99` cover-state surface used by the axis
realizations, with a new finite clutching pin:

- `|F|=3`
- seam loop: `20 -> 17 -> 12 -> 15 -> 20`
- v2.1 seam steps: `[1,0,0,0]`
- mod-3 holonomy: `1`
- old v2 regression seam steps: `[1,1,1,0]`, mod-3 holonomy `0`

## Guard V3 Control Family

The packet emits the full no-Betti control family guard v3 needs:

- `v2_1_shifted_degree_one_mod3`: shifted repair complex, mod-3 holonomy `1`,
  integer-lift sum `1`, fiber-order attachment coefficient `3`, `d^2=0`.
- `zero_shift_product_control`: zero-shift complex, mod-3 holonomy `0`,
  `d^2=0`.
- `wrong_gluing_generator_not_threaded_control`: wrong-gluing complex, generator
  seam row present but the chain attachment is not threaded, `d^2=0`.
- `old_v2_regression_coboundary_control`: old shifts rebuilt, integer-lift sum
  `3`, old winding `1`, mod-3 holonomy `0`, `d^2=0`.

All complexes are hash-pinned and record both invariants: mod-3 holonomy and
integer-lift sum. The packet does not compute Betti numbers.

## Axis Realizations And Law Table

- Axis0 is pulled back through the projection to committed v1/base Axis0 rows.
- Axis6 is pulled back through the projection to committed v1/base Axis6 rows.
- Axis3 is recomputed natively on cells and pinned finite fiber phases using the
  committed `gamma_in` / `gamma_out` predicates.
- The law row is `b6 = -b0*b3`, with all eight sign variants and binomial
  p-values.
- This is the third construction's row. The outcome is data, not a premise.

## Controls

- zero-shift product control: law rows refused.
- wrong-gluing control: law rows refused.
- old v2 regression: old integer winding preserved, finite mod-3 triviality
  reproduced.
- scrambled b6 control.
- convention-flip control.

## Boundaries

Allowed claims:

- v2.1 keeps the v2 CW base unchanged by hash.
- v2.1 is a different pinned finite clutching construction with seam holonomy
  `1 mod 3`.
- v2.1 emits shifted, zero-shift, wrong-gluing, and old-v2-regression chain
  complexes with `d^2=0` for guard v3.
- v2.1 records both mod-3 holonomy and integer-lift sum for the emitted
  complexes.
- v2.1 recomputes Axis0, Axis3, and Axis6 faithfulness obligations and the
  b6 law table at scratch-diagnostic ceiling.

Disallowed claims:

- Betti computation;
- homology certificate;
- lens-space certificate;
- SECOND certificate;
- formal admission;
- canonical by process;
- axis independence proof;
- bridge, physics, manifold, or axis-level closure;
- global disproof of the b6 law.

## Expected Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/fiber_augmented_cover_v2_1/fiber_augmented_cover_v2_1.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/fiber_augmented_cover_v2_1/fiber_augmented_cover_v2_1_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/fiber_augmented_cover_v2_1/validate_fiber_augmented_cover_v2_1.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/fiber_augmented_cover_v2_1/tests
```
