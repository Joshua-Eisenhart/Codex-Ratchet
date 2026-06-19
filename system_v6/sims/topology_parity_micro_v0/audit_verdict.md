# Independent audit verdict -- topology_parity_micro_v0

Auditor: independent fresh Codex audit. I did not build this packet. I recomputed the reference controls and cover flag-complex rows before accepting the packet prose.

## Verdict

VERDICT: PASS / HONEST NULL SUSTAINED.

Claim ceiling: `scratch_diagnostic_independent_topology_guard_for_fiber_augmented_cover_v1_only`. This verdict admits only the finite adjacency-derived parity guard result. It does not admit a cover claim, formal topology claim, canonical claim, physics/manifold/axis claim, or replacement of the `fiber_augmented_cover_v1` audit.

Citation rule: cite this packet only as an honest-null topology guard result for the selected finite complex construction. Any citation must include that the computed finite complex misses the preregistered ideal profiles and indicts resolution/complex construction, not the cover hypotheses.

## Fresh Recompute

I imported `topology_parity_micro_v0_common.py` and ran `build_topology_parity_object()` in memory, without running writer entrypoints. I compared the fresh selected payload fields against `results/topology_parity_micro_v0_results.json`.

Fresh recomputation returned exact sanity controls:

- torus reference expected `[1,2,1]`, GUDHI `[1,2,1]`, Hodge `[1,2,1]`, pass.
- disk reference expected `[1,0,0]`, GUDHI `[1,0,0]`, Hodge `[1,0,0]`, pass.
- sphere reference expected `[1,0,1]`, GUDHI `[1,0,1]`, Hodge `[1,0,1]`, pass.
- mislabeled torus-as-sphere negative passed by rejecting the claimed sphere profile.

Fresh cover flag-complex recomputation returned:

- `v1_degree_one_cover`: 99 vertices, 321 undirected non-self edges, 66 flag triangles, GUDHI Betti `[1,157,0,0]`, Hodge `[1,157,0]`, GUDHI/Hodge agree through `b2`.
- `zero_shift_product_cover`: 99 vertices, 321 undirected non-self edges, 72 flag triangles, GUDHI Betti `[1,151,0,0]`, Hodge `[1,151,0]`, GUDHI/Hodge agree through `b2`.
- fresh `controls`, `complexes`, `parity_adjudication`, and `result_summary` matched the committed result JSON.

## Null Language

The honest null is correct. The computed profiles differ at `b1=157` versus `b1=151`, but both miss the preregistered ideal profiles `[1,0,0,1]` and `[1,1,1,1]`. The packet's language correctly says resolution is insufficient and the selected flag-complex construction is indicted. It earns nothing for the cover hypotheses and kills nothing about them.

## G.2a State

G.2a state: passes from birth. The build card declares G.2a from birth, the boundary helper is present, and the result carries `no_builder_audit_verdict=true`.

## Bottom Line

The audited claims survive as an honest null only: the toolchain controls are exact, the cover flag-complex rows recompute exactly, and the result properly refuses to promote the non-ideal `b1=157/151` distinction.
