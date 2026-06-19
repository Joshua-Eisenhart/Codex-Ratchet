# gcm_constraint_carve_3q_v1 Build Card

Builder: Codex. Scope: file-disjoint packet under `system_v6/sims/gcm_constraint_carve_3q_v1/`.

No `git add` or commit is allowed for this build.

## Declaration

- Coordinates: layers 1-2 (+17) | carve | 3Q.
- Classification: `scratch_diagnostic`.
- Promotion: false.
- Formal admission: false.
- Standards: Codex binds G.2a from birth; builder/audit boundary helper is used.
- Substrate: substrate-first with hardened 1Q and 2Q lineage consumption.

## Controlling v0 Fail

The v0 audit verdict is the repair contract:

- Artifact the actual states: every candidate's `rho_ABC` is stored under a content id; every survivor carries the state content id and survivor state entry in the results.
- Emit the full constraint matrix per candidate: C1, C2, and C3 are independently computed pass/fail rows for every candidate. The kill ledger is the full matrix, not a first-failed label.
- Recompute CKW from the stored `rho_ABC`: per-party one-tangles, pairwise tangles, inequalities, and margins are recomputed for each tripartite-entangled survivor.
- State the GHZ/W rows from the matrix: GHZ fails C2 and C3; W fails C3 only. The asymmetry is the finding and remains at that strength.
- Strict fixes: Julia `Graphs` is actually imported and used; helper preflight is green; the climb ledger lock is refreshed from disk.

## Regression Fixture

- Candidate count: 552.
- Survivor count: 545.
- Quotient class count: 9.
- Product-lift count from 2Q: 544.
- Tripartite-entangled survivor count: 1.

## Controls

- 1Q substrate regression.
- 2Q substrate regression.
- Lineage-free negative stays red.
- Terrain-blindness predicate guard.
- Injection-red terrain/atlas predicate control.
- Empty constraint and overconstrained controls.
- Probe scramble control.

## Ceiling

This packet is not a QIT-floor admission, not a SLOCC GHZ/W separator, not a manifold/axis/bridge result, and not physics evidence. It is a repaired count fixture and state-artifacted 3Q scratch diagnostic.
