# CR repo — lean-out inventory and plan (2026-08-06)

Written in the repo. Every number below is measured, not estimated.
Nothing is moved or deleted by this document; it is the plan the
owner asked for before any surgery.

## Where the weight actually is

| Directory | Files | MB | md | py | json |
|---|---:|---:|---:|---:|---:|
| system_v7 | 1892 | **368** | 372 | 509 | 767 |
| system_v6 | 2928 | 146 | 714 | 1016 | 937 |
| system_v8 | 1339 | 98 | 46 | 819 | 347 |
| system_v4 | 7895 | 93 | 692 | 4657 | 584 |
| system_v5 | 2519 | 80 | 460 | 900 | 886 |
| READ ONLY Legacy core_docs | 285 | 30 | 118 | 55 | 68 |
| ratchet_engine | 99 | 11 | 26 | 12 | 42 |
| constraint_box | 374 | 6 | 74 | 227 | 51 |
| claimgate_plugin | 498 | 6 | 25 | 118 | 281 |

## The finding that decides the plan

The bulk is **not** docs and **not** philosophy. It is generated
result and receipt trees:

| System | Total MB | result/receipt files | result/receipt size |
|---|---:|---:|---:|
| system_v7 | 368 | 698 | **329 MB** |
| system_v8 | 98 | 1013 | 92 MB |
| system_v6 | 146 | 1425 | 79 MB |
| system_v5 | 80 | 694 | 11 MB |
| system_v4 | 93 | 489 | 3.9 MB |

**~515 MB of the ~800 MB repo is generated evidence.** Moving prose to
the wiki would shrink the repo by tens of MB; moving evidence to an
evidence store or DVC-tracked lane shrinks it by hundreds. Both are
worth doing, but the evidence lane is the one that changes the number.

## Three separations, in order of payoff

1. **Evidence out of source.** `results/`, `receipts/`, `sim_results/`,
   `runs/`, `logs/` under every system version move behind an evidence
   lane (the repo already has `.dvc/`), leaving code and contracts in
   git. Nothing is deleted; the index in `constraint_box` can point at
   hashes rather than trees.
2. **Prose out of the operational repo.** Doc-only trees —
   `READ ONLY Legacy core_docs` (118 md), `MODEL_DOSSIER` (23 md),
   `ROOT` (9 md), plus the docs subtrees inside v4/v5/v6 — go to the
   wiki, or to a separate projects folder, with a stub index left
   behind so nothing becomes unfindable.
3. **Version insight extraction, BEFORE anything moves.** The owner's
   standing observation: each CR version solved real problems whose
   solutions were then lost in the next version. So the move is
   preceded by an extraction pass that records, per version, what it
   uniquely solved and where that lives. A doc that is only "old" is
   archived; a doc that carries a solved problem is carried forward.

## Design constraint carried from CR history (do not lose this again)

Deterministic gating is not new work — it existed by v3: the boots and
threads a0, a1, b, sim were deterministic and not LLM-driven, intended
as Python code. The failure then was not the gates. It was that
**no exploration happened at the gates**: the models adopted the
ontology of the gate and turned hyper-conservative, refusing to send
anything out to explore. The owner had to drive order changes by hand.

ConstraintBox is the generalized form of those systems, and it
inherits that failure mode. So CB must keep an explicit exploration
lane separate from the controlled-evaluation lane, and PARKED must
mean "not yet admissible, keep exploring" rather than "stop." A gate
that produces conservatism has reproduced the v3 problem with better
receipts.

## Scope discipline, also from the owner

Getting the manifold layers and engines running is **not** proof of
the model. It establishes only that a running sim is possible. The
formal-proof track was set aside deliberately; conflating the two is
what stretched a straightforward sim into months of work. The repo
layout should keep `proof`, `sim`, and `evidence` as separate words
with separate directories, so the conflation cannot recur by accident.
