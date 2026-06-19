# Independent audit verdict -- fiber_cover_incidence_structure_v0

Auditor: independent fresh Codex audit. I did not build this packet. I recomputed the derivation, incidence, and boundary rows from committed source data before accepting the packet prose.

## Verdict

VERDICT: PASS / SUSTAINED, with the Betti consumer still blocked.

Claim ceiling: `scratch_diagnostic_committed_incidence_structure_plumbing_only_no_betti`. This verdict admits incidence plumbing only. It does not admit Betti, homology, S3/S2xS1 topology, formal admission, physics, manifold, axis, or bridge claims.

Citation rule: cite this packet only for the committed-incidence plumbing facts below: 12 traced base 2-cells, zero introduced faces, explicit sparse boundary matrices, `d^2=0`, and Euler checks. Any citation must also state that Betti consumption remains blocked.

## Fresh Recompute

I imported `fiber_cover_incidence_structure_v0_common.py` and ran `build_fiber_cover_incidence_structure_object()` in memory, without running writer entrypoints. I compared the fresh selected payload fields against `results/fiber_cover_incidence_structure_v0_results.json`.

Fresh recomputation returned:

- face count: 12.
- `derivation_introduced_count = 0`.
- row-by-row source trace failures: 0. Every emitted face's four source edge IDs matched the committed carrier cycle vertices, and every face kept `introduced=false`.
- base cell counts: `C0=33`, `C1=198`, `C2=12`.
- base Euler characteristic: `33 - 198 + 12 = -153`.
- base `d1*d2` nonzero entries: 0.
- total-space cell counts: `C0=99`, `C1=693`, `C2=630`, `C3=36`.
- total-space Euler characteristic: 0.
- total `d1*d2` and `d2*d3` nonzero entries: 0.
- fresh `derivation_honesty`, base chain hash, total chain hash, and result summary matched the committed result JSON.

## Betti Fence

The packet result carries `betti_computed=false`, `betti_lane_status=blocked_until_source_side_exhaustive_2_cell_incidence_is_admitted`, and consumer boundary `do not compute or cite Betti from this packet while derivation_incomplete is true`.

I searched the packet for Betti references. I found only the explicit blocked/fence fields, disallowed-claim text, tests enforcing no top-level `betti` field, and no computed Betti profile. The consumer fence held.

## G.2a State

G.2a state: passes from birth. The build card declares G.2a from birth, the boundary helper is present, and the result carries `no_builder_audit_verdict=true` plus `no_builder_audit_verdict_envelope_gate=true`.

## Bottom Line

The audited claims survive exactly at plumbing level: the packet derives only 12 committed 4-cycle faces, introduces zero faces, has `d^2=0`, reports base Euler `-153`, and keeps Betti blocked.
