# BUILD CARD - fiber_augmented_cover_v1

Source request: build the v0 audit's named repair under
`system_v6/sims/fiber_augmented_cover_v1/`, file-disjoint from v0, with no git
add/commit.

## Ceiling

- `classification=scratch_diagnostic`
- `claim_ceiling=axis_readout_candidate_only + nontrivial_cover_faithful_fiber_augmented_cover_b6_law_test_v1`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- Boundary helper: `fiber_augmented_cover_v1_boundary.py` plus shared
  `scripts/builder_audit_boundary.py`.
- This builder card is not an independent audit verdict.

## Authority Read Order

1. v0 audit verdict commit `cf7fe65c4`: v0 had `|F|=4`, but all 792
   base-lift phase shifts were zero, so the law was tested on a trivial product
   bundle rather than the intended nontrivial object.
2. Panel 9 Q2: the witness is the sum of fiber phase transitions around a
   closed base equator; nontrivial bundle witness is `+/-1`, trivial product is
   `0`.
3. Panel 9 Q2 live divergence: `|F|=2` detects parity only unless directed
   orientation is otherwise recovered; v1 pins `|F|=3` as the minimum directed
   winding carrier.
4. Panel 9 Q3: independent random signs satisfy the product law at 50%; the
   panel threshold row names `N=33` with one-tailed 95% at `>=23` agreements.
5. v0 machinery: quotient projection, Axis0/Axis6 pullbacks, Axis3 native
   finite-fiber adapter, law rows, sign variants, controls, and row-local
   z3/cvc5 erased-flip checks are reused at scratch ceiling.

## Object

The packet builds a finite fiber-augmented 33-cell cover:

```text
cover state = (Family A 33-cell id, pinned directed U(1) fiber phase)
fiber phases per cell = {0, 2*pi/3, 4*pi/3}
projection pi(cover state) = 33-cell id
```

The committed equatorial loop is the actual closed directed loop in the
33-cell carrier:

```text
20 -> 17 -> 12 -> 15 -> 20
```

Its scaled coordinates are:

```text
[0,1,0] -> [0,0,1] -> [0,-1,0] -> [0,0,-1] -> [0,1,0]
```

The degree-1 clutching is discretized as lifted phase increments:

```text
[1, 1, 1, 0]
```

The raw accumulated phase shift is therefore `3`, and the directed
winding/Euler witness is `3 / |F| = 1`.

## Witness Gate

The witness gate runs before law rows:

```text
if computed_winding not in {-1, +1}:
    construction_status = construction_failed_trivial_bundle
    law_table_ran = false
    no b6_law_test or relation_table is emitted
```

The zero-shift product-bundle regression must compute witness `0`. Its v1 law
table is refused by the same gate; the historical v0 law result is preserved as
the at-chance negative-control reference.

## Faithful Realizations

- Axis0: pulled back as `b0_cover(state)=b0_axis0(pi(state))`.
- Axis3: computed natively on each pinned finite fiber phase using the committed
  gamma predicates. Phase slot `0` uses `gamma_in`; phase slots `1` and `2` use
  `gamma_out`.
- Axis6: pulled back as `b6_cover(state)=b6_axis6(pi(state))`.

Faithfulness rows are emitted for all three axes. Axis3 is a source-backed
equivalent adapter on the finite fiber, not a proxy label on the 33-cell
quotient.

## Law Test

Only after the witness gate passes, the law row is:

```text
b6 = -b0*b3
```

The packet owns the b6 consistency table, the full eight sign-convention
variants:

```text
s6*b6 = -(s0*b0)*(s3*b3)
```

and binomial p-values for each variant under the 50% null.

Either law outcome is the scratch result, now on the nontrivial cover object.

## Controls

- v0 zero-shift trivial product bundle regression: witness `0`; v1 law rows
  refused; v0 law result preserved as at-chance negative-control reference.
- v0 unfaithful Hopf transplant regression preserved as contrast.
- v1 unfaithful 33-cell proxy regression preserved as contrast.
- Convention-flip control evaluates `b6=+b0*b3`.
- Scrambled control replaces computed b6 with deterministic hash signs.
- z3 and cvc5 row-local contradiction/erased-flip checks bind selected computed
  cover rows.

## Boundaries

Allowed claims:

- the finite nontrivial cover exists as a scratch diagnostic object;
- the quotient projection to the 33-cell carrier is computed;
- Axis0 and Axis6 are faithful pullbacks;
- Axis3 is computed on pinned finite fiber phases with committed predicates;
- the b6 law is tested after a computed nonzero winding witness gate.

Disallowed claims:

- Axis3 placement on the 33-cell quotient without the finite fiber;
- axis independence proof;
- formal admission or canonical-by-process status;
- bridge, physics, manifold, or axis-level closure claims.

## Expected Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/fiber_augmented_cover_v1/fiber_augmented_cover_v1.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/fiber_augmented_cover_v1/fiber_augmented_cover_v1_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/fiber_augmented_cover_v1/validate_fiber_augmented_cover_v1.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/fiber_augmented_cover_v1/tests
```
