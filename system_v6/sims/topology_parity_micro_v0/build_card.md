# BUILD CARD - topology_parity_micro_v0

Source request: build the old-estate TopoNetX/GUDHI Hodge-Betti row only now
that a current topology packet needs an independent guard for
`fiber_augmented_cover_v1`. Build is file-disjoint under
`system_v6/sims/topology_parity_micro_v0/`. No git add/commit.

## Ceiling

- `classification=scratch_diagnostic`
- `claim_ceiling=scratch_diagnostic_independent_topology_guard_for_fiber_augmented_cover_v1_only`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- Boundary helper: `topology_parity_micro_v0_boundary.py` plus shared
  `scripts/builder_audit_boundary.py`.
- G.2a from birth: the builder packet declares `no_builder_audit_verdict=true`
  and does not write its own audit verdict.

## Authority Read Order

1. `system_v6/receipts/old_sims_complete_consume_20260612.md`: the old row says
   `topology_parity_micro_v0` is admissible only if a current topology packet
   needs an independent Betti/Hodge guard.
2. `system_v6/sims/fiber_augmented_cover_v1/`: cover v1 supplies the 99 cover
   states, lifted base adjacency, zero-shift product control, source hashes,
   and audit ceiling.
3. `system_v4/probes/sim_toponetx_gudhi_hodge_betti_cross.py`: mechanics only.
   Reuse torus/disk/sphere controls and TopoNetX-Hodge versus GUDHI-Betti
   split. Do not inherit its old `canonical` label.

## Preregistered Math Expectation

These profiles are declared before computation:

| object | ideal topological model | expected Betti `b0,b1,b2,b3` |
|---|---|---|
| v1 degree-one cover | S3-like total space | `[1,0,0,1]` |
| v0 zero-shift product cover | S2xS1 product total space | `[1,1,1,1]` |

Parity question: does the independent finite-complex calculation distinguish
the nontrivial v1 cover from the zero-shift product as the bundle claim
predicts, especially `b1(v1)=0` versus product `b1>=1`?

## Complex Construction

The source packet does not emit a canonical triangulation. This micro packet
therefore constructs an explicit finite test complex:

```text
vertices = 99 cover states
edges = undirected non-self lifted base edges + pinned fiber-cycle edges
2-cells = flag triangles on that undirected adjacency graph
```

The same rule is applied to the degree-one v1 cover and the zero-shift product
cover. Source cover and transition-row hashes are emitted for both.

## Controls

The toolchain sanity gate runs before cover parity:

- torus reference: Betti `[1,2,1]`;
- disk reference: Betti `[1,0,0]`;
- sphere/tetrahedron-boundary reference: Betti `[1,0,1]`;
- mislabeled-complex negative: torus-as-sphere must fail the claimed sphere
  profile.

## Honest Outcomes

- Agreement with the preregistered profiles earns an independent topology
  guard for the cover claim.
- Computed profiles that differ but miss the ideal profiles mean the selected
  finite complex construction is too coarse or wrong for the ideal distinction.
- Equal computed profiles do not support the cover claim unless a stronger
  resolution/fidelity argument is added.

Any non-ideal outcome is reported as a discretization-fidelity caveat or a
finding against the complex-building choice, not papered over as cover evidence.

## Expected Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/topology_parity_micro_v0/topology_parity_micro_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/topology_parity_micro_v0/topology_parity_micro_v0_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/topology_parity_micro_v0/validate_topology_parity_micro_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/topology_parity_micro_v0/tests
```
