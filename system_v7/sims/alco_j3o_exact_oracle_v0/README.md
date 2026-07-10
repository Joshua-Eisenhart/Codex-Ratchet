# ALCO J3(O) Exact Oracle v0

This is a bounded, deterministic `scratch_diagnostic` packet. It compares the
repo's local rational Albert formulas with package-native exact arithmetic from
ALCO 1.1.2 under GAP 4.16.0.

## Claim ceiling

The packet can support only this claim: for the frozen seeded and structured
vectors in this packet, ALCO's exact Albert product, trace, determinant,
generic minimal polynomial, and quadratic representation agree with an
independent exact-rational implementation of the local formulas.

ALCO has no spectral log, entropy, channel, DPI, engine, Axis0, perception,
object, or physics authority. Passing this packet does not promote or formally
admit any sim, theorem, bridge, axis, manifold, or physics claim.

## Pinned runtime

- ALCO checkout: `/Users/joshuaeisenhart/GitHub/alco`
- required ALCO commit: `e10ec05acbdf6e7d312d3d35d757771b9fdbc7ec`
- GAP binary: `/Users/joshuaeisenhart/.local/share/codex-ratchet/gap/alco-1.1.2/gap-4.16.0/gap`
- GAP home: `/Users/joshuaeisenhart/.local/share/codex-ratchet/gap/alco-1.1.2/home`
- installed ALCO package path: `/Users/joshuaeisenhart/.local/share/codex-ratchet/gap/alco-1.1.2/gap-4.16.0/pkg/alco`

The installed ALCO path must resolve to the pinned checkout. The result packet
records file hashes for every named source, hashes the complete ALCO tracked
tree and ResClasses package tree, and hashes the GAP and Python executables.
Generated result artifacts are excluded from the source manifest to avoid
self-referential hashes.

## Exact surfaces

- Four LCG-seeded triples of 27 rational coordinates: seeds `7`, `29`, `101`,
  and `20260709`.
- One structured `e1*e2` product witness that must be killed when the local
  multiplication entry is corrupted.
- Exact product, trace, determinant, cubic coefficient list, `U_x(y)`, and
  `U_y(x)` comparisons.
- Cayley-Hamilton, `U_x(1)=x^2`, quadratic homogeneity, determinant covariance,
  and the quadratic fundamental formula.
- The API boundary `SimpleEuclideanJordanAlgebra(4,8)=fail`.

The local Fano basis is mapped into ALCO's basis by
`e1:e2,e2:e4,e3:e1,e4:e3,e5:e5,e6:-e6,e7:e7`. The GAP oracle checks all local
Fano cycles and all 27 coordinate round trips before emitting cases.

## Run

```bash
python3 run_oracle.py
python3 validate_oracle.py
```

The controller writes:

- `alco_j3o_exact_oracle_result.json`
- `alco_j3o_exact_oracle_validation.json`
- `RESULTS.md`

The output contains no timestamp or unseeded randomness. Repeating the run in
the same pinned environment must reproduce byte-identical JSON artifacts.
