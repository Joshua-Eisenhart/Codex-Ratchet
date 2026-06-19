# Independent audit verdict - topology_parity_guard_v2

Bottom line: `topology_parity_guard_v2` is `GENUINE-WITH-CAVEATS` as a scratch consumer guard, and the SECOND certificate is `BLOCKED`. The committed total-space complex really computes Betti `[1,1,1,1]` with no torsion, so the parity guard correctly fails against the carried S3-like Betti profile. The contradiction does not resolve as literal byte-level shift-blindness: the shifted and erased-shift matrices are not identical. The actual diagnosis is stricter and repairable: the emitted chain complex encodes the finite shifts as an exact mod-3 vertex-potential coboundary, so it is chain-isomorphic to the zero-shift product complex while the winding witness reads integer lift data outside that homology encoding.

Verdict: `GENUINE-WITH-CAVEATS`.

Claim ceiling: `scratch_diagnostic_consumer_guard_only_no_new_construction`; `promotion_allowed=false`; `formal_admission_allowed=false`; no homology certificate, SECOND certificate, formal admission, topology admission, bridge, physics, manifold, axis closure, or canonical-process claim is earned.

Freshness tier: `TIER-3 annotation-verify`. The prompt exposed the builder claims and the required contradiction. I recomputed the load-bearing arithmetic from source/result matrices and kept the surviving contradiction split explicit.

## What Was Checked

Read/write boundary:

- Read-only audit except this `audit_verdict.md`.
- No `git add`, commit, writer script, envelope writer, or validator `main()` was run.
- Normal result writers were not invoked because they rewrite result JSON files.
- Current packet status observed before this verdict: `?? system_v6/sims/topology_parity_guard_v2/`.

Standards:

- `system_v6/receipts/audit_standards_codex_v1.md`, especially G.2a idempotency-from-birth.
- `system_v6/receipts/audit_bar_calibration_20260610.md`.
- `system_v6/receipts/geometry_sim_program_canonical_20260610.md`.
- `system_v6/receipts/toolset_expansion_20260610.md`.

Source/result surfaces:

- `system_v6/sims/fiber_augmented_cover_v2/fiber_augmented_cover_v2_common.py`.
- `system_v6/sims/fiber_augmented_cover_v2/results/fiber_augmented_cover_v2_results.json`.
- `system_v6/sims/fiber_augmented_cover_v2/audit_verdict.md`.
- `system_v6/sims/topology_parity_guard_v2/topology_parity_guard_v2_common.py`.
- `system_v6/sims/topology_parity_guard_v2/results/topology_parity_guard_v2_results.json`.
- `system_v6/sims/topology_parity_guard_v2/validate_topology_parity_guard_v2.py`.
- `system_v6/sims/topology_parity_guard_v2/tests/test_topology_parity_guard_v2.py`.

## Arithmetic Verdict

Independent recompute of the committed total-space matrices:

| row | value |
|---|---:|
| chain dims | `C0=99, C1=375, C2=459, C3=183` |
| ranks | `rank(d1)=98, rank(d2)=276, rank(d3)=182` |
| Betti | `[1,1,1,1]` |
| `d1*d2` nonzero entries | `0` |
| `d2*d3` nonzero entries | `0` |
| SNF nonunit factors for `d1` | `[]` |
| SNF nonunit factors for `d2` | `[]` |
| SNF nonunit factors for `d3` | `[]` |

The no-torsion finding is real. More precisely, every nonzero Smith invariant of each boundary matrix is `1`: `d1` has `98` unit factors, `d2` has `276`, and `d3` has `182`. Therefore each boundary image is primitive in its ambient chain group; any homology subgroup quotient here is torsion-free. This independently supports "no torsion in H0..H3" without relying on the packet's shortcut torsion helper.

The shifted source rebuild also matched the committed matrix hashes:

| boundary | hash |
|---|---|
| `d1` | `305b45cb0c7048f794f892531b1244814e4ee650c339670108ca4ca9c13cb1bf` |
| `d2` | `6c593b1002dc256b78cd59767b4bc5fc91137a82a87b210b186cc3a11e7dcfef` |
| `d3` | `ed1dc588e4c3a6a80ed674439bbddd9933d6683f5831c1d55d32438bcd67aac7` |

So the guard's core arithmetic finding is not a presentation artifact.

## Decisive Diff

I rebuilt the v2 total-space complex from source with the shifts erased.

Two audit variants were checked:

- `zero_cover_only`: pass `zero_shift=True` to `build_cellular_cover(...)` while leaving the base edge shift fields as emitted by the v2 source.
- `zero_erased`: erase the base edge shift fields actually consumed by `build_total_space_cellular_structure(...)`, then build the zero-shift cover and total complex.

Direct matrix diff:

| diff | `d1` | `d2` | `d3` |
|---|---:|---:|---:|
| shifted vs `zero_cover_only` | `126` changed entries | `0` | `0` |
| shifted vs `zero_erased` | `126` changed entries | `354` changed entries | `228` changed entries |

This kills the literal "identical matrices" version of the diagnosis. The chain-complex emission is not byte-shift-blind.

The stronger surviving diagnosis is chain-isomorphism to the product complex. The source shift is computed from a vertex potential:

```text
shift(src,dst) = potential(dst) - potential(src) mod 3
```

The phase relabeling

```text
new_phase(cell, phase) = phase - potential(cell) mod 3
```

conjugates the shifted total complex to the zero-shift total complex. I checked the chain-map equations directly:

| boundary | phase-relabel chain isomorphism |
|---|---|
| `d1` | `true` |
| `d2` | `true` |
| `d3` | `true` |

The zero-erased complex also computes Betti `[1,1,1,1]` with no torsion. That is why the guard sees product homology. The finite chain complex is not carrying the integer clutching degree as a nontrivial homology class; it is carrying an exact mod-3 cocycle.

## Contradiction Adjudication

The winding witness remains genuine at its own ceiling:

```text
seam: 20 -> 17 -> 12 -> 15 -> 20
lifted steps: [1, 1, 1, 0]
total lifted shift: 3
fiber phase count: 3
directed winding: 1
```

The homology complex and the winding witness are not describing the same encoded object.

Live readings after computation:

- Killed: "the shifted and zero-shift matrices are identical." They are not.
- Killed: "the guard arithmetic is a false alarm." It is not; Betti `[1,1,1,1]` and no torsion recompute independently.
- Survives: "the v2 chain-complex encoding is product-equivalent." It is chain-isomorphic to zero shift by a global phase relabeling.
- Survives: "the winding witness reads committed lift data directly." It remains untouched by the homology failure.
- Refined: the named gap is not literal shift-blindness. It is integer-lift/cohomology encoding loss: the emitted finite chain complex reduces the shifts to an exact mod-3 coboundary and therefore cannot earn the intended lens-space-like topology.

## Lens-Space Expectation

The carried pre-registered S3-like profile `[1,0,0,1]` was underpowered because it omitted torsion. For a correctly encoded degree-1 discrete `Z_3` fiber construction, the expected profile for the next guard is:

```text
Betti: [1,0,0,1]
H1 torsion: Z/3
H0,H2,H3 torsion: none
```

That pre-registration refinement must be written before guard v3 reruns. The current guard's `[1,1,1,1]` with no torsion is exactly the product profile, which is consistent with the exact-coboundary diagnosis.

## What Is Untouched

The `b6=-b0*b3` law replication is untouched. It lives on the cover states, axis realizations, and law rows, not on the total-space homology certificate.

The winding witness is untouched. It reads the committed seam lift data directly and still reports directed winding `1`.

The `fiber_augmented_cover_v2` `GENUINE` verdict remains valid only at its bounded scratch ceiling. Its `d^2=0` and `chi=0` gates could not distinguish product-equivalent encoding from the intended twisted topology; that is an audit-tooth gap, not a retroactive fabrication finding.

The SECOND certificate is not earned. It is blocked on the encoding repair.

## G.2a And Consumer Discipline

G.2a held for this guard:

- builder packet does not write `audit_verdict.md`;
- validator delegates audit-file handling to `scripts/builder_audit_boundary.py`;
- `no_builder_audit_verdict=true`;
- `no_builder_audit_verdict_envelope_gate=true`;
- consumer boundary says no new cells, no target Betti fitting, no fresh wrong-gluing cell model, and no Betti citation from the builder packet.

The source-complex consumer discipline also held. The guard consumed the hash-pinned v2 matrices and did not construct replacement cells in the committed result. The audit-only zero-shift rebuild above is a diagnosis tool, not a promoted packet artifact.

## Repair Contract

Required v2.1/v3 repair:

1. `fiber_augmented_cover_v2.1` must emit boundary matrices whose chain homology actually threads the integer clutching/lens-space datum, not just an exact mod-3 vertex-potential relabeling.
2. `fiber_augmented_cover_v2.1` must also emit committed zero-shift and wrong-gluing control complexes, not just witness/law-refusal facts.
3. `topology_parity_guard_v3` must pre-register the refined lens-space expectation before running: Betti `[1,0,0,1]` plus `H1=Z/3`.
4. Guard v3 must rerun the shifted, zero-shift, and wrong-gluing complexes with torsion-aware homology.
5. Any future positive certificate must name the exact chain-level obstruction that prevents the phase relabeling above.

## Verification

No-write validation:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/topology_parity_guard_v2/tests
```

Result:

```text
5 passed in 22.27s
```

No-write payload validator function:

```text
validate_payload_no_write_ok=true
errors=[]
```

Independent arithmetic and diff script results:

```text
committed Betti=[1,1,1,1]
rank(d1)=98, rank(d2)=276, rank(d3)=182
d1*d2=0, d2*d3=0
boundary SNF nonunit factors: d1=[], d2=[], d3=[]
shifted source rebuild matched committed hashes=true
shifted vs zero_erased diff entries: d1=126, d2=354, d3=228
phase-relabel chain isomorphism: d1=true, d2=true, d3=true
zero_erased Betti=[1,1,1,1]
zero_erased boundary SNF nonunit factors: d1=[], d2=[], d3=[]
```

## Citation Rule

Future citations should say:

> `topology_parity_guard_v2` is a scratch consumer guard over the hash-pinned `fiber_augmented_cover_v2` chain complexes. A fresh audit independently recomputed the committed total-space homology as Betti `[1,1,1,1]` with no torsion and `d^2=0`; this blocks the SECOND certificate. The winding witness remains genuine at its own ceiling, but the emitted chain complex is product-equivalent: erased-shift matrices are not byte-identical to shifted matrices, yet the shifted complex is chain-isomorphic to zero shift by the global phase relabeling `phase -> phase - potential(cell) mod 3`. The correct defect is integer-lift/cohomology encoding loss, not literal byte-level shift-blindness. Next admissible repair: v2.1 must emit shift-threaded, zero-shift, and wrong-gluing complexes, and guard v3 must pre-register Betti `[1,0,0,1]` plus `H1=Z/3` before rerun. Ceiling: `scratch_diagnostic_consumer_guard_only_no_new_construction`; no SECOND certificate, formal admission, topology admission, bridge, physics, manifold, or canonical-process claim.
