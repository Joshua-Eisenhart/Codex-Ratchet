# Independent audit verdict - topology_parity_guard_v3

Bottom line: `topology_parity_guard_v3` is `GENUINE` as a working-tree
scratch-diagnostic consumer guard. `READING_A_REPAIRED_WINS`: the committed
`fiber_augmented_cover_v2_1` shifted-repair complex is finitely nontrivial at
this guard ceiling, with Betti `[1,0,0,1]` and `H1=Z/3`; the three controls
remain product-profile `[1,1,1,1]` with no torsion.

Verdict: `GENUINE`.

Claim ceiling: `scratch_diagnostic_consumer_guard_only_no_new_construction`;
`promotion_allowed=false`; `formal_admission_allowed=false`; not canonical by
process; not formal admission; not bridge, physics, manifold, or axis closure.
Status ladder: `passes local rerun` for an untracked working-tree packet, plus
consumes the clean committed `fiber_augmented_cover_v2_1` source at `eb96d0e87`.

Freshness tier: `TIER-3 annotation-verify`. The prompt exposed the builder
claim and decisive teeth, but I recomputed the load-bearing homology, hashes,
separability, reference gate, and validator/test state directly.

Read/write boundary: requested read-only except this file, no `git add` or
commit. I did not stage or commit. I did run the packet validator once; that
validator writes `results/topology_parity_guard_v3_validator_results.json` by
design. Treat that as an audit-hygiene note, not as math evidence.

## What was checked

- Current `HEAD` is `eb96d0e87`; `system_v6/sims/fiber_augmented_cover_v2_1`
  is clean against `HEAD`.
- The v3 packet directory is untracked in this checkout. This verdict cites it
  as a working-tree packet until it is committed.
- Governing arc checked: `2137ae3e8 -> eb96d0e87`, plus
  `system_v6/receipts/audit_standards_codex_v1.md`.
- Packet-local verification:
  - `validate_topology_parity_guard_v3.py`: `ok=true`, `errors=[]`.
  - `pytest -q -p no:cacheprovider system_v6/sims/topology_parity_guard_v3/tests`:
    `5 passed`.

## Pre-registration integrity

The decisive expectation was not invented by v3 after seeing results. The
committed guard-v2 audit and work order required v3 to pre-register Betti
`[1,0,0,1]` plus `H1=Z/3` before rerun. The committed v2.1 audit repeats the
same handoff: shifted row expects Betti `[1,0,0,1]` plus `H1=Z/3`; all three
controls expect Betti `[1,1,1,1]` with no torsion.

The v3 build card matches that committed handoff exactly. The file timestamp
alone is not the load-bearing proof because the v3 source files have mtimes
seconds before the build card; the load-bearing proof is the already-committed
handoff language in `2137ae3e8` and `eb96d0e87`, before the v3 packet was a
tracked object.

## Independent SNF recomputation

I recomputed from the committed v2.1 boundary matrices and chain hashes, not
from the v3 result rows:

| complex | chain hash check | boundary values `[d1,d2,d3]` | SNF | Betti | torsion |
|---|---|---:|---|---|---|
| `v2_1_shifted_degree_one_mod3` | matched `6afe8e...c75a` | `[0,3,0]` | `d2=[3]` | `[1,0,0,1]` | `H1=[3]` |
| `zero_shift_product_control` | matched `5315bd...bd76` | `[0,0,0]` | none | `[1,1,1,1]` | none |
| `wrong_gluing_generator_not_threaded_control` | matched `856ae6...4b8d` | `[0,0,0]` | none | `[1,1,1,1]` | none |
| `old_v2_regression_coboundary_control` | matched `151c47...0d5` | `[0,0,0]` | none | `[1,1,1,1]` | none |

The shifted row therefore has `H1 = Z/3`. The controls do not. This is the
decisive separator.

## Reference gate

The required independent references exist and pass:

| reference | `d2` | result |
|---|---:|---|
| `explicit_s3` | `1` | Betti `[1,0,0,1]`, no torsion |
| `explicit_s2xs1` | `0` | Betti `[1,1,1,1]`, no torsion |
| `explicit_lens_space_l31` | `3` | Betti `[1,0,0,1]`, `H1=Z/3` |
| degree-2 torsion trap | `2` | Betti `[1,0,0,1]`, `H1=Z/2` |

The `L(3,1)` reference is constructed in `run_reference_gate()` as
`one_cell_complex(3)` with `source_chain_sha256=null`; it is not loaded from the
v2.1 cover JSON or relabeled from the shifted row. It necessarily has the same
pure boundary hash as the shifted row because the test is that the shifted row
matches the independent `L(3,1)` chain profile through the same SNF machinery.

## Hashes, separability, and construction freedom

Hash loading held. The v3 source requires all four v2.1 `chain_sha256` values
and recomputes every sparse boundary matrix hash; mismatch raises `STOP`.

Math-content separability also held. Boundary-matrix-only hashing produced
exactly two pure complexes:

```text
441e18752b754fa7308ce0b820110457eeb0c311f07ad76d9ed30b6eaa1311e0
  v2_1_shifted_degree_one_mod3

ac7c846103ccd5e0c2adda58248357e9d19385f3369341485b37fb88b3d6b65b
  zero_shift_product_control
  wrong_gluing_generator_not_threaded_control
  old_v2_regression_coboundary_control
```

Zero construction freedom held for the consumed cover object: v3 consumes the
hash-pinned v2.1 matrices and does not introduce replacement cells or update
the work order. The only newly constructed complexes are the explicit
reference/negative-control calibration objects required by the build card.

## Consistency triangle

The three independent instruments cohere:

- v2.1 audit: shifted pure complex has `d2=[3]`, and the shifted row is not
  chain-isomorphic to the zero-boundary product controls.
- v3 homology: `d2=[3]` recomputes as Betti `[1,0,0,1]` with `H1=Z/3`.
- winding/holonomy data: v2.1 shifted seam `[1,0,0,0]` has integer lift `1`,
  mod-3 holonomy `1`, and generator gate `true`; old v2 regression keeps
  integer lift `3` but mod-3 holonomy `0`.

That triangle is exactly the repaired finite certificate. The old integer lift
alone was not enough; the repaired row has both generator holonomy and torsion
in the committed chain complex.

## G.2a

G.2a is satisfied from birth. The build card names it, the validator delegates
audit-file handling through `scripts/builder_audit_boundary.py`, and the
boundary helper accepts an independent/fresh/read-only audit header rather than
requiring permanent absence of `audit_verdict.md`.

## Final language

At this scratch-diagnostic consumer-guard ceiling, the v2.1 cover is
`FINITELY NONTRIVIAL`, certified by two independent instruments:

- mod-3 generator holonomy: seam `[1,0,0,0]`, integer lift `1`, mod-3 holonomy
  `1`;
- homology torsion of the committed shifted complex: `H1=Z/3`.

Reading B dies for the v2.1 construction. Reading B remains true for v1/v2 as
finite objects: their finite structures were product/trivial, so the old
finite-nontrivial and `S3-like` labels still need re-issue for v1/v2.

The corrected finite topology language is lens-space-like `L(3,1)`, not `S3`.
`L(3,1)` is not `S3`; the packet catches this by using
`expected_profile=lens_space_L31` and an explicit `L(3,1)` reference. Its
`explicit_s3` row is a calibration reference, not the target label.

The `b6 = -b0*b3` law is at-chance on all three constructions, including the
finitely certified v2.1 one. Strongest current law status:
`at_chance` for these 99 cover rows and pinned axis realizations, not global
disproof and not an axis kill.

Open: other carriers, other `|F|`, other admissible clutching choices, other
pre-pinned axis adapters, and any bridge/physics/manifold/topology admission
claim beyond this consumer guard.

## Citation rule

Future citation should say:

> `topology_parity_guard_v3` is a working-tree scratch-diagnostic consumer
> guard over the committed `fiber_augmented_cover_v2_1` matrices at
> `eb96d0e87`. It independently recomputes the shifted repaired complex as
> Betti `[1,0,0,1]` with `H1=Z/3`, while the zero-shift, wrong-gluing, and old-v2
> regression controls are Betti `[1,1,1,1]` with no torsion. This adjudicates
> `READING_A_REPAIRED_WINS`: v2.1 is finitely nontrivial at scratch-diagnostic
> consumer-guard ceiling, certified by mod-3 generator holonomy and homology
> torsion. v1/v2 remain finite-trivial/product-equivalent and their old
> nontrivial/S3-like labels re-issue. Use lens-space-like `L(3,1)`, not `S3`.
> The b6 law remains at-chance on v1/v2/v2.1 for these 99 rows and pinned axis
> realizations. No formal admission, canonical-process, bridge, physics,
> manifold, axis-closure, or global b6 claim.

Minimum citations:

- `system_v6/sims/topology_parity_guard_v3/build_card.md:43-85`
- `system_v6/sims/topology_parity_guard_v3/topology_parity_guard_v3_common.py:281-300`
- `system_v6/sims/topology_parity_guard_v3/topology_parity_guard_v3_common.py:331-355`
- `system_v6/sims/topology_parity_guard_v3/topology_parity_guard_v3_boundary.py:28-85`
- `system_v6/sims/fiber_augmented_cover_v2_1/audit_verdict.md:57-99`
- `system_v6/sims/fiber_augmented_cover_v2_1/audit_verdict.md:180-191`
- `system_v6/sims/topology_parity_guard_v2/audit_verdict.md:124-166`
- `system_v6/receipts/axis_work_order_20260612.md:68-84`
- `system_v6/receipts/audit_standards_codex_v1.md:141-165`
