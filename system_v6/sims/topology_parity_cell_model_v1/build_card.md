# BUILD CARD - topology_parity_cell_model_v1

Source request: build the named follow-up for a higher-fidelity cell model for
the `fiber_augmented_cover_v1` topology guard under
`system_v6/sims/topology_parity_cell_model_v1/`, file-disjoint, with no git
add/commit.

## Ceiling

- `classification=scratch_diagnostic`
- `claim_ceiling=scratch_diagnostic_independent_topology_guard_for_fiber_augmented_cover_v1_only`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- Boundary helper: `topology_parity_cell_model_v1_boundary.py` plus shared
  `scripts/builder_audit_boundary.py`.
- G.2a from birth: the builder packet declares
  `no_builder_audit_verdict=true`; this card and packet are not an independent
  audit verdict.

## Authority Read Order

1. `system_v6/sims/topology_parity_micro_v0/`: v0 is the honest null. It used
   flag complexes on raw lifted adjacency and got cover Betti profiles
   `[1,157,0,0]` and `[1,151,0,0]`, indicting resolution, not the cover.
2. `system_v6/sims/fiber_augmented_cover_v1/`: v1 supplies the committed
   33-cell base carrier, `|F|=3`, the equatorial loop
   `20 -> 17 -> 12 -> 15 -> 20`, and seam shifts `[1,1,1,0]`.
3. This packet may reuse v0 sanity fixtures and preregistered profiles, but it
   must not reuse v0's raw-adjacency flag-complex rule for the cover rows.

## Preregistered Profiles

Declared before computation:

| object | ideal topological model | expected Betti `b0,b1,b2,b3` |
|---|---|---|
| v1 degree-one cover | S3-like total space | `[1,0,0,1]` |
| zero-shift product cover | S2xS1 product total space | `[1,1,1,1]` |

## Cell Rules Pinned Before Computation

These rules are derived from the bundle construction, not from the desired
Betti output.

Base cell source:

```text
base patches = the committed 33 Family-A carrier cells from fiber_augmented_cover_v1
fiber cells = one finite directed circle fiber per base patch, with |F|=3 phase samples
seam loop = 20 -> 17 -> 12 -> 15 -> 20
pole cells = [0,0,-2] and [0,0,2]
```

Base 2-sphere rule:

```text
Use the committed base as a 2-sphere cell surface for the bundle guard:
the 33 base patches are the source patch cover. The expanded chain model keeps
33 directed band/pole faces around one closed cellular latitude with north and
south endpoints:
  C0(base)=<south,north>
  C1(base)=<meridian_0,...,meridian_32>, each south -> north
  C2(base)=<face_0,...,face_32>, with d(face_i)=meridian_{i+1}-meridian_i.
The seam/pole witness is the committed equatorial loop and the pole cells from
fiber_augmented_cover_v1. The homology-reduced Euler complex is also emitted as
a torsion/control view of the same clutching degree. No boundary entry is fitted
from target Betti numbers.
```

Total space rule:

```text
For each base k-cell e and fiber j-cell f, emit a product cell e x f of
dimension k+j. In the expanded 33-face model:
  C0 = base C0 x fiber C0
  C1 = (base C1 x fiber C0) plus (base C0 x fiber C1)
  C2 = (base C2 x fiber C0) plus (base C1 x fiber C1)
  C3 = base C2 x fiber C1

d uses the tensor-product boundary rule plus one construction-derived clutching
entry:
  d2(face_0 x fiber0) includes degree(clutching) * (south x fiber1)
  degree(clutching) = sum(lifted seam shift steps) / |F|
```

Gluing rule:

```text
Across a seam edge a -> b with shift s in Z/|F|, glue
(a, phase p) to (b, phase p+s mod |F|).
The cellular obstruction is the accumulated lifted shift around the closed
equatorial seam. The v1 cover has shifts [1,1,1,0], sum 3, |F|=3, degree 1.
The zero-shift product has sum 0, degree 0.
```

Stop condition:

```text
Run reference fixtures first with the same boundary-matrix machinery.
If explicit S3 does not return [1,0,0,1] or explicit S2xS1 does not return
[1,1,1,1], report machinery_insufficient and do not compute cover rows.
```

## Controls

- v0 torus/sphere/disk fixtures recomputed through the cellular boundary
  machinery.
- Mislabeled negative: torus-as-sphere must fail.
- Deliberately wrong gluing: erase the v1 seam shifts; the Betti profile must
  move to the product profile.
- Torsion trap: a reduced Euler degree `2` model has the same field Betti as
  S3-like `[1,0,0,1]` but has `H1 = Z/2`; the packet must report that Betti
  alone is underpowered for that control.

## Honest Outcomes

- `distinction_resolved_degree_one_side`: reference gate passes and v1/product
  profiles match the preregistered distinction under the construction-derived
  gluing rule.
- `machinery_insufficient`: reference fixtures fail; cover rows are skipped.
- `still_insufficient`: reference fixtures pass but cover profiles do not match
  the preregistered profiles; report the named obstruction.

Any result remains an independent topology guard at scratch-diagnostic ceiling
only. It is not a new bundle claim, formal admission, axis proof, bridge claim,
or physics/manifold claim.

## Expected Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/topology_parity_cell_model_v1/topology_parity_cell_model_v1.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/topology_parity_cell_model_v1/topology_parity_cell_model_v1_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/topology_parity_cell_model_v1/validate_topology_parity_cell_model_v1.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/topology_parity_cell_model_v1/tests
```
