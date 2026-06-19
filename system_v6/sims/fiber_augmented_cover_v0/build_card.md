# BUILD CARD - fiber_augmented_cover_v0

Source request: build the registered next structural object under
`system_v6/sims/fiber_augmented_cover_v0/`, file-disjoint, with no git add/commit.

## Ceiling

- `classification=scratch_diagnostic`
- `claim_ceiling=axis_readout_candidate_only + faithful_fiber_augmented_cover_b6_law_test_v0`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- No builder-authored `audit_verdict.md`.
- Boundary helper: `fiber_augmented_cover_v0_boundary.py`.

## Authority Read Order

1. b6 v1 verdict commit `03e606122`: law status is untested-pending-the-cover.
2. work-order commit `c2a978eae`: proof-backed fiber-augmented 33-cell cover is the registered next object.
3. Axis0 packet `5d330b427`: committed Axis0 readout on the Family A 33-cell carrier.
4. Axis3 packet `ce8c77355`: committed Hopf gamma predicates, `gamma_in` density-stationary and `gamma_out` horizontal with `A(dot gamma)=0`.
5. Axis6 packet `b6fafc67f`: committed precedence pair on the same 33-cell carrier as Axis0.
6. Hopf section packet `7e78f3829`: section/lift machinery used as source-backed construction context.

## Object

The packet builds a finite fiber-augmented 33-cell cover:

```text
cover state = (Family A 33-cell id, pinned U(1) fiber phase)
fiber phases per cell = {0, pi/2, pi, 3*pi/2}
projection pi(cover state) = 33-cell id
```

The quotient projection is computed. Base-lift edges project back to the committed
198 Family A carrier edges; fiber-cycle edges collapse inside projection fibers.

## Faithful Realizations

- Axis0: pulled back as `b0_cover(state)=b0_axis0(pi(state))`.
- Axis3: computed natively on each pinned finite fiber phase using the committed
  gamma predicates. Even phase slots use `gamma_in`; odd phase slots use
  `gamma_out`; the density-stationary and horizontal predicates are recomputed.
- Axis6: pulled back as `b6_cover(state)=b6_axis6(pi(state))`.

Faithfulness rows are emitted for all three axes. Axis3 is a source-backed
equivalent adapter on the finite fiber, not a proxy label on the 33-cell quotient.

## Law Test

The law row is:

```text
b6 = -b0*b3
```

where `b3` is the panel relation sign converted from the committed Axis3 placement
sign (`gamma_in -> +1`, `gamma_out -> -1`). The relation is evaluated after all
three signs are computed. The result may hold or fail; either outcome is the
scratch result.

## Controls

- v0 unfaithful Hopf transplant regression reproduced as contrast.
- v1 unfaithful 33-cell proxy regression reproduced as contrast.
- convention-flip control evaluates `b6=+b0*b3`.
- scrambled control replaces computed b6 with deterministic hash signs.
- panel anchor rows are preserved from the prior b6 packets.
- z3 and cvc5 row-local contradiction/erased-flip checks bind computed cover rows.

## Boundaries

Allowed claims:

- the finite cover exists as a scratch diagnostic object;
- the quotient projection to the 33-cell carrier is computed;
- Axis0 and Axis6 are faithful pullbacks;
- Axis3 is computed on the pinned finite fiber phases with committed predicates;
- the b6 law receives its first faithful-cover scratch test.

Disallowed claims:

- Axis3 placement on the 33-cell quotient without the finite fiber;
- axis independence proof;
- formal admission or canonical-by-process status;
- bridge, physics, or manifold claims.

## Expected Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/fiber_augmented_cover_v0/fiber_augmented_cover_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/fiber_augmented_cover_v0/validate_fiber_augmented_cover_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/fiber_augmented_cover_v0/tests
```
