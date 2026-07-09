# qit_full_type1_type2_64_live_v1

Status: scratch diagnostic only. This packet does not admit Axis0, FEP, physics,
manifold, production perception, or full QIT engine closure.

## What It Runs

This packet turns the live `ENGINE_64_SCHEDULE_ATLAS.md` chart into a finite
64-slot carrier:

- 4 loop objects: `T1_outer_deductive`, `T1_inner_inductive`,
  `T2_outer_inductive`, `T2_inner_deductive`
- 16 macro rows: 4 stages per loop object
- 4 substages per macro row: candidate, measurement, gate, receipt
- 64 slots total
- 32 Type-1 slots and 32 Type-2 slots
- 16 chart-locked macro cells and 48 bounded runtime probe cells

The object-formation test is intentionally narrow: ordered observations over
the finite stream recover the hidden loop object, while static/bag-erased
projections collapse object identity.

## Current Result

Fresh result paths:

- `results/qit_full_type1_type2_64_live_v1_results.json`
- `results/qit_full_type1_type2_64_live_v1_jax_results.json`
- `results/qit_full_type1_type2_64_live_v1_julia_results.json`
- `results/qit_full_type1_type2_64_live_v1_pytorch_results.json`
- `results/qit_full_type1_type2_64_live_v1_envelope_results.json`

Passed gates:

- ordered object recovery accuracy: `1.0`
- bag-topology control unique signatures: `1`
- PyTorch ordered readout accuracy: `1.0`
- PyTorch bag-control accuracy: `0.25`
- Julia/JAX/PyTorch survivor object-count divergence: `0.0`
- z3/cvc5 full-gate negation: `unsat`
- erased/bag control: `sat` / collapsed

## How To Run

From `/Users/joshuaeisenhart/Codex-Ratchet`:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1.py --fresh
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1_jax.py
/opt/homebrew/bin/julia --startup-file=no --project=system_v5/julia_carrier system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1_pytorch.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_full_type1_type2_64_live_v1/validate_qit_full_type1_type2_64_live_v1.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v7/sims/qit_full_type1_type2_64_live_v1/results/qit_full_type1_type2_64_live_v1_envelope_results.json --require-pytorch --strict-source-backed --require-tool-intent
```

## What It Does Not Prove

This is not live world perception. It is a finite ordered-object test over an
atlas carrier. It does not prove the 48 runtime probe cells are chart-closed,
that the atlas is final owner math, that PyTorch is primary engine evidence, or
that Lev mesh objects can now be produced in the wild.
