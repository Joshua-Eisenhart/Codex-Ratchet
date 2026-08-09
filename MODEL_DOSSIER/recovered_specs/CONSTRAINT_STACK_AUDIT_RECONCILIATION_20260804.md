# Constraint-stack audit reconciliation — 2026-08-04

Source audit:
`/Users/joshuaeisenhart/Desktop/CONSTRAINT_STACK_AUDIT_AND_REPAIR_20260804.md`

Source SHA-256:
`776a68ffc92e2ea3534f5f3a1f9bbf1cb69e2926b6168841c2c799de62f8417c`

## Fresh local checks performed

The referenced `MANIFOLD_NESTED_BASIN_ENGINE_LAB_20260804_v1.zip` was extracted
and replayed locally:

- exact bundle manifest: 42/42 files;
- unit suite: 27/27;
- controller replay: `EXECUTED`, `ELIGIBLE_EXPLORATORY_EXECUTION`;
- controller result: 7 running plural-basin systems;
- independent consumer: 24/24;
- source boundary: `promotion_allowed=false`, MSS/physics/CR claims blocked.

The replay used CPython and the real `/usr/local/bin/node`. It did not run the
JAX, PyTorch, or Julia lanes; the lab README explicitly treats those as
unavailable in this execution environment. Archived multi-runtime receipts
remain provenance, not fresh replay evidence.

The freshly replayed lab result names seven plural-basin systems:

`cyclic-fibre-z4`, `cyclic-voltage-z3`, `eca-capacity-54-216`,
`fano-xor8-associative-control`, `octonion-o16-loop`, `q8-alternate-rules`,
and `signed-seam-z2`.

The lab's own machine-readable CB audit is `HOLD`, with three reproduced P0
findings: the weak public gate, receipt-directed dynamic import, and pending
states treated as admitting.

## What the audit confirms

### Engine side

The engine-first lab is materially stronger than the earlier M-star-only
slice. It contains 12 candidate systems, 7 plural-basin systems, exact
256-state visible maps, nested extension sets, basin feedback that enters the
visible transition, finite fuel-to-load conversion, full-load stall, and load
backpressure. It reports 58 nontrivial visible recurrent cycles under its
bounded wrapper. CPython and Node agree on the complete visible maps and
controls.

This is a working finite engine laboratory. It is not a selected geometry,
physical engine, MSS result, or CR validation. The larger engine state is
sampled through bounded trajectories; its complete multi-million-state basin
graph is not exhausted.

### CB side

The audit identifies three release-blocking defects in the current simulation
admission path:

1. `constraintbox.gate.run_gate` calls the weaker Python ClaimGate path, while
   the hardened shell hook performs strict intake, recomputation, seal, floor,
   and ledger stages. A duplicate-key hostile claim is admitted through the
   public Python API but blocked by the fired hook.
2. `verify_attractor_basin_envelope.py` dynamically imports the
   `controller.source_path` supplied by an envelope after checking only the
   envelope's self-declared hash. Untrusted envelope code can therefore run
   before rejection.
3. The fired hook treats `INSUFFICIENT_DEPTH` / pending-depth states as
   admitting (`ADMITTED_PENDING_DEPTH`). Strong simulation admission must make
   every state other than explicit `ELIGIBLE` non-admitting.

Additional open defects are the dual solver-version authority, 83 untriaged
portable-suite failures in the audit container, the v1 M-star target still
being pinned in the CB candidate-world adapter, incomplete lane independence,
and the under-specified v2 authored conventions.

## Current combined status

| Surface | Status | Ceiling |
|---|---|---|
| Engine-first finite lab | `passes local rerun` | exploratory engine/basin evidence |
| Attractor basins | `passes local rerun` | exact finite visible maps only |
| CPython/Node parity | `passes local rerun` | implementation parity, not blind independence |
| JAX/PyTorch/Julia for this lab | not freshly exercised | archived receipts only |
| CB Mini-Lev/capability scaffolding | exists/runs in source and receipts | not strong sim admission |
| CB public simulation gate | blocked | weak-vs-fired gate split |
| Model / CR | candidate executable hypotheses | no MSS, physics, ontology, or CR truth |

## Correct next order

1. Replace the public simulation gate and fired hook with one canonical,
   fixed-source, fail-closed gate.
2. Remove all envelope-controlled imports and confine artifacts to a
   controller-owned run root.
3. Make pending/unknown/unavailable states non-admitting.
4. Retarget the CB adapter to the v2 fixture and seal the authored conventions
   G1-G8.
5. Add fresh JAX, PyTorch, and Julia lanes against the same fixture and compare
   full maps, not aggregate counts.
6. Only then feed the candidate engine family tournament into CB telemetry and
   later MSS deletion.

No CB source was modified by this reconciliation. The audit is a source-
addressed diagnostic and repair queue.
