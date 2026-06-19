# BUILD CARD - sequential_inheritance_not_cycle_v0

Original card copied into this packet:

```text
# BUILD CARD — sequential_inheritance_not_cycle_v0 (the physics safe-order item 6)
You are codex2 (medium). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build in system_v6/sims/sequential_inheritance_not_cycle_v0/ (file-disjoint). NO git add/commit. Card into build_card.md; boundary helper FULLY.
Authority: the physics deep-read (35ed8142c — section B's sequential-universe rows w/ quotes + the safe-order item 6: 'parent/daughter record-retention toy with cycle-null controls'); the record machinery (the z4 convention bd7a54080; the inherited-record framing from the owner's sequential-universe doc). THE OBJECT: a finite parent-process -> daughter-process toy where the daughter's initial constraints inherit a RECORD of the parent's terminal structure (the record object constructed per the z4 standard) — the discriminator: inheritance (record-carrying) vs the CYCLE NULL (an eternal-return loop w/ no record) vs the RANDOM null (no inheritance) — the daughter's stability/structure rows must distinguish the three (computed; if they cannot, the inheritance claim has no teeth on this carrier — reported). FENCES: toy/fixture only; no cosmology admission; the owner's sequential-universe claim = the HORIZON this tests toward. Standard contract.
```

## Object

Finite parent terminal table: six parent orbits times four Z4 syndrome representatives, for 24 terminal rows.

Record object: packet-local Z4 syndrome distribution with entropy `log(4)` / two finite-counting bits, following the `bd7a54080` convention that record retention is not assigned as state loss.

Daughter regimes:

- `inheritance`: daughter initial constraint carries the parent terminal Z4 syndrome.
- `cycle_null`: daughter receives a one-step eternal-return phase shift, no retained record.
- `random_null`: daughter receives a deterministic non-inherited orbit-index initializer.

Discriminator rows:

- `inheritance` terminal structure matches: `24/24`; mean stability `1.0`.
- `cycle_null` terminal structure matches: `0/24`; mean stability `0.0`.
- `random_null` terminal structure matches: `6/24`; mean stability `0.25`.
- all three structure signatures must be distinct; otherwise `reported_if_no_teeth=true` and the packet fails.

Ceiling: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. This is a toy/fixture only. It does not admit cosmology, universe inheritance, dark sector, supervoid, or physics claims.

## TOOL_INTENT_MATRIX

| engine | load-bearing tool | exact observable/proof | gates |
| --- | --- | --- | --- |
| Julia | Graphs | `Graphs.SimpleDiGraph` parent->record->daughter support graph with 24 parent-record bridges | graph receipt, all_pass |
| Julia | Z3 | `Z3.Solver` binds computed daughter match counts and proves inheritance cannot collapse to null controls | crossover_proofs, all_pass |
| JAX/Python | sympy | `sp.log` exact Z4 record entropy expression from computed syndrome support | record object, all_pass |
| JAX/Python | z3 | `z3.Solver` binds computed daughter match counts and proves inherited stability beats both nulls | crossover_proofs, all_pass |
| JAX/Python | cvc5 | `cvc5.Solver` independently proves the same finite count inequalities | crossover_proofs, all_pass |
| PyTorch | torch_geometric | `torch_geometric.data.Data` support graph for parent->record->daughter bridge | graph receipt, all_pass |
| PyTorch | torch.func | `torch.func.vmap` computes per-row parent/daughter syndrome match vectors | discriminator counts, all_pass |
| Controller | build_three_engine_envelope | standard `three_engine_sim_result_v1` envelope helper | envelope shape, validator |

## Boundary Helper

Envelope construction uses `scripts/build_three_engine_envelope.py` through `sequential_inheritance_not_cycle_v0_envelope.py`. The packet validator nests `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent`.

## Expected Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/sequential_inheritance_not_cycle_v0/sequential_inheritance_not_cycle_v0_jax.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/sequential_inheritance_not_cycle_v0/sequential_inheritance_not_cycle_v0_pytorch.py
```

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/sequential_inheritance_not_cycle_v0/sequential_inheritance_not_cycle_v0_julia.jl
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/sequential_inheritance_not_cycle_v0/sequential_inheritance_not_cycle_v0_envelope.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/sequential_inheritance_not_cycle_v0/validate_sequential_inheritance_not_cycle_v0.py
```

## Fresh Builder Status

Date: 2026-06-12.

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/sequential_inheritance_not_cycle_v0/sequential_inheritance_not_cycle_v0_jax.py` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/sequential_inheritance_not_cycle_v0/sequential_inheritance_not_cycle_v0_pytorch.py` -> `ok:true`
- `JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/sequential_inheritance_not_cycle_v0/sequential_inheritance_not_cycle_v0_julia.jl` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/sequential_inheritance_not_cycle_v0/sequential_inheritance_not_cycle_v0_envelope.py` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/sequential_inheritance_not_cycle_v0/validate_sequential_inheritance_not_cycle_v0.py` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/sequential_inheritance_not_cycle_v0/results/sequential_inheritance_not_cycle_v0_envelope_results.json` -> `ok:true`

Computed discriminator: inheritance `24/24` terminal matches, cycle-null `0/24`, random-null `6/24`; all three structure signatures distinct; `reported_if_no_teeth=false`.
