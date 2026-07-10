# Claude Science 97 / UP-129 / UP-130 Audit

**Date:** 2026-07-09
**Classification:** external-packet intake plus local falsification and replacement scout
**Promotion allowed:** false

## Packet Identity

`/Users/joshuaeisenhart/Desktop/97.zip`

- SHA-256: `23f455a7cf609e533cdff307edda99c9ca77980c2e2932d76c800b26327aee98`
- ZIP members: 457 files; archive CRC and path inspection pass
- relative to `95.zip`: four added source/result files, zero removed files,
  and three changed control files (`run_all.py`, `MODEL_LAYER_LEDGER.md`,
  `CHANGELOG_HARDENING.md`)
- additions: the UP-129 SINDy repair and UP-130 four-substage source/result pairs

The packet contains no packaged `run_all_report.json`. A fresh isolated run in
`/tmp/cr97-intake-20260709` produced:

```text
135 pass / 0 fail / 0 skip -> GREEN
```

Fresh report SHA-256:
`e4ef52ca434e2b474b9d35180ebb7a75071bbaf4586d2dff022f67a432b07555`.

Accepted public status for the packet: **passes local rerun**. This status says
the runner's declared checks pass; it does not admit the checks' semantics.

Both new sources fail the current sim-contract linter with six violations in
total: each lacks a module-level classification, tool manifest, and integration
depth declaration.

## UP-130 Disposition

The source-locked audit is:

`system_v7/constraint_core/sims_and_scripts/four_substages_up130_fabrication_audit_sim.py`

It binds to the exact UP-130 member SHA-256
`6d412087c47b12dbf82b982589c801e531e8fff1c0398bdb117a64bd084b3741`
and passes its contract lint and fresh local rerun. Verdict:

```text
UP130_OVERCLAIM_CAUGHT
```

Measured failures in the advertised derivation:

- `exp(-i*pi*sigma/2)` is a 180-degree Bloch rotation, not a quarter turn;
- the two adjoint channels commute to numerical precision
  (`3.46e-16` Frobenius commutator norm);
- every leg is unitary and the largest measured entropy change is
  `3.89e-16` nats, so no entropy gradient or pawl runs;
- `both_directions(word)` is only `count(A)==2 and count(B)==2`, which fixes
  length four before the scan;
- `AB`, `AAAA`, and the half-leg control do not isolate their claimed gates;
- `ABAB` and `BABA` are one cyclic orbit, not two chiral cycle classes;
- comparing the pre-forced length four to a chart that already has four steps
  is consistency, not independent derivation.

Grok 4.5 independently returned the same audit under xAI request
`6fe30217-7bf6-9553-9be7-689d4fd1e754`. This is external advisory evidence;
the local audit sim is the mechanical receipt.

UP-130 is rejected for four-substage, entropy-ratchet, chirality, and engine
claims. Its surviving content is only the elementary identity that two
commuting Pauli adjoint half-turns produce a balanced alternating period-two
word whose square is the identity.

## UP-129 Disposition

The source's degree-one SINDy ratio is reproducibly large and recovers terrain
position permutation `(1,4,3,2)` across eight seeds. That supports a narrow
terrain-position diagnostic.

It does not support its stronger Type-2/operator-order conclusions:

- `Ti` and `Te` are implemented as reversible Pauli conjugations rather than
  source dephasing channels;
- `Fi` and `Fe` are implemented as identity;
- the Type-2 loops share the same four terrain names but have disjoint
  `(terrain, operator)` and `(terrain, operator, sign)` tuples;
- replacing every operator with identity still passes `8/8`, preserves the
  permutation, and increases the minimum ratio to about `9.32e4`;
- the result field claiming the same tuples reversed is not backed by a tuple
  equality test.

Accepted ceiling: a scratch diagnostic that degree-one SINDy recovers the
positional order of four toy terrain generators. It does not establish
source-faithful operator carry, Axis-6 content, or Type-2 engine equivalence.

## Replacement Structural Scout

The local replacement scout is:

`system_v7/sims/four_substages_dual_product_v0/`

It starts from the source-backed operator-algebra table:

| Pauli/Bloch operator axis | dephasing/pinching | unitary/rotation |
|---|---|---|
| `z` | `Ti` | `Fe` |
| `x` | `Te` | `Fi` |

Julia Canon uses QuantumOptics and Graphs.jl. JAX independently infers the
classes from finite channel action, entropy change, and transfer matrices;
Z3 and cvc5 verify the measured signature collision flip. Neither engine reads
the other's result. The validator passes all 14 parity checks.

Measured conditional result:

- four structural cells;
- parameter variants quotient to the same four classes;
- one-coordinate MSS adjacency forms `K2 box K2 = C4`;
- two oriented traversals, one cycle modulo reversal:
  `Ti-Fe-Fi-Te-Ti` and `Ti-Te-Fi-Fe-Ti`;
- erase either coordinate: two classes and no four-cell cycle;
- remove any cell: no closed Hamiltonian cycle;
- allow diagonal jumps: cycle uniqueness is lost;
- add a `y` axis: six classes and length-six cycles.

Grok 4.5 request `0d9764d7-4270-9323-82c7-8c4ef9c21355` agrees with the
ceiling: this is a conditional graph theorem and independently reproduced
operator quotient, not a physical or engine derivation.

Accepted status: **passes local rerun** as `scratch_diagnostic`.

## Exact Current Boundary

The new scout establishes a plausible structural origin for a four-element
operator cycle, conditional on four premises:

1. the source-selected `x/z` operator axes are complete for this layer;
2. pinching and unitary automorphism are the complete operator-family split;
3. every cell must be visited;
4. MSS permits only one-coordinate movement.

It does **not** prove that each of the 16 macro stages contains these four maps
as sequential substages, that a fixed Axis-6 sign is inherited through the
cycle, or that any beat is dynamically necessary or useful.

### Follow-on execution result

`system_v7/sims/stage16x4_system_id_instrument_v0/` now performs that next
bounded execution test. Both candidate orientations run across all 16 source
slots under one inherited sign, external system-ID tools recover the held-out
maps, and removal, duplication, reversal, wrong-sign, terrain-erasure,
operator-erasure, and permutation controls all move the endpoint beyond fit
noise.

This closes sequential execution and local dynamic necessity **conditional on
the supplied four-cell architecture and one finite house-map
parameterization**. It does not repair the premise boundary of this audit:
four is still not emitted by independent geometry-first and entropy-first
ratchets, and the held-out transition task is not yet a business/object task.

The active repo's broader harness now reruns at `123/0/0`. Packet 97 remains a
separate isolated `135/0/0` receipt. The active evidence envelope reports
formation loss `43.546185436758485`, so neither green count may be used to
claim perception or object usefulness.

That execution bridge now exists. The next experiment must remove its supplied
four-count: enumerate a larger candidate pool, run independent geometry-first
and entropy-first ratchets, intersect only their measured survivors, and then
feed the emitted sequence into the same held-out controls. A separate SME
object fixture must test whether those beats improve useful work rather than
only reproducing their authored transition map.
