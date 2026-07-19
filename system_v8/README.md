# system_v8 — base-first Ratchet (owner spec, 2026-07-18)

v8 corrects the standing error named by the owner: every prior system jumped
to a loaded manifold (Shannon entropy, Fisher, U(1), Hopf, octonions) before
the base structure was ever compared. v8 starts at the base and earns
structure by executable comparison only.

Authority: the owner's 2026-07-18 base-Ratchet specification (pasted prompt,
top authority per standing rules) and the owner-authored Pack 177 v2 kernel
(ROOT_RATCHET_KERNEL.md), whose input receipts are copied hash-bound into
`inputs/` (see `inputs/INPUT_HASHES.sha256`).

## Binding rules encoded here

- The ratchet can only compare possible things: every base candidate must be
  SIMULATED, then compared. Prose elimination is invalid.
- Base primitives allowed: finite realized domain; distinctions derived from
  constraints (u !~ v iff some admissible context separates them). Forbidden
  as primitives: probability, metric, time, causality, coordinates, observer,
  linearity, dynamics.
- Comparison is witness-only (requirement kill / strict structure deletion /
  fewer unobserved choices). No witness in either direction = both retained.
- Frontier recurrence: F_{t+1} = unbeaten(F_t U Purgatory_t U new simulated
  candidates). Purgatory is universally re-offerable.
- Ladder: R0 admissibility relation -> R1 nested compatibility (relations,
  not functions) -> R2 ordered relations -> R3 persistent distinctions.
  Noncommutation is earned only if T2.T1 and T1.T2 stay distinguishable.

## Contents

- `kernel_tick/` — the first executed Root-Ratchet kernel tick (r -> r+1):
  the compiled obligation for `src-1858a5f7dbbb248f` executed against the
  live hash-locked contextuality source; held-out fence; dual-solver
  (z3+cvc5) outcomes; F_r {3,33,78,108,147,177,222,252} -> F_{r+1} {222};
  7 kills to Purgatory with deletion witnesses. Receipt:
  `kernel_tick/receipts/tick_receipt_20260718.json`.
- `base_campaign/` — the executable base-structure campaign: 9 candidates
  (relations, incidence, partitions, graphs, simplicial, posets, matroids,
  transducers, distributions) run on 2 real packets under the same O/R/N.
  Computed base frontier F_1 = {b0_unrestricted_relation,
  probe_response_incidence}; 7 in Purgatory with witnesses; noncommutation
  NOT earned at this level (restriction composition is intersection).
  Six carriers (rebit, complex density matrix, Jordan, Clifford/spinor,
  quaternionic, octonionic) are PROPOSED_NOT_YET_SIMULATED — neither
  frontier nor Purgatory until executable.
- `inputs/` — hash-bound copies of the Pack 177 v2 receipts and census code
  the runs consume (source tables, fuel obligations, raw source-locked
  bundle, `eval_anf` census).

Rejected as a v8 foundation: the codex branch
`codex/v8-local-pawl-foundation-20260718` builds its base on primitive
probability vectors and relative entropy, which the base spec forbids as
primitives. It is retained on its branch as a contrast exhibit only.

## Status labels

Everything here is `passes local rerun` at best (deterministic byte-identical
receipts). Nothing is canonical. `promotion_allowed: false` and
`formal_admission_allowed: false` on all receipts. Claim ceiling:
packet-relative comparison over anonymous source packets; no scientific,
physical, or canonical claim.

## Rerun

```
python3 system_v8/kernel_tick/tick_r1_contextuality_obligation.py <fresh-out-dir>
python3 system_v8/base_campaign/base_ratchet_campaign.py <fresh-out-dir>
```

Both refuse to overwrite existing output directories.
