# qit_bidirectional_science_type1_type2_v0

Status: `scratch_diagnostic`.

This packet builds on `qit_projection_battery_v0` and asks whether the same
finite object family can survive two different science-method orders:

- Type-1: candidate-first confirmation.
- Type-2: measurement-first reconstruction.

Both methods run over the same four projection object cards and five partial
MMM-style views. The packet is a bounded method comparison, not full QIT engine
admission.

## Claim Ceiling

Allowed:

- finite Type-1 and Type-2 method comparison over existing projection object cards;
- six-stage method receipts for candidate, measurement, counter-projection, update, falsifier, and receipt;
- unique-win table comparing Type-1-only wins, Type-2-only wins, shared wins, and shared failures;
- source-backed Julia, JAX, and PyTorch agreement over object count and trial count;
- Lev evidence-import sketch with graph mutation blocked.

Blocked:

- live perception;
- production object factory;
- Axis0, FEP, Xi/Phi0, physics, or manifold admission;
- ontology writer or MMM-driver admission;
- Lev mesh runtime integration;
- remote peer graph mutation.

## Teeth

Current measured result:

- paired method trials: `40`
- Type-1 nominal accuracy: `1.0`
- Type-1 wrong-candidate accepted rate: `0.1`
- Type-2 nominal accuracy: `0.9`
- Type-2 bag-erased accuracy: `0.25`
- Type-2 view-erased accuracy: `0.25`
- unique-win table: `18` shared wins, `2` Type-1-only wins, `0` Type-2-only wins, `0` shared failures
- Julia/JAX/PyTorch object-count divergence: `0.0`
- Julia/JAX/PyTorch trial-count divergence: `0.0`
- z3/cvc5/Julia Z3 method-gate negation: `unsat`

Interpretation:

- Type-1 is stronger when a candidate object card is already declared and must
  survive held-out counter-projection.
- Type-2 is stronger as a formation method: it starts from a measurement view
  and creates a candidate, but it remains ambiguous on underdetermined
  single-view buckets.

## Rerun

From repo root:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/wizard_v4_3_object_preservation.py validate --input system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0_object_card.json --out system_v7/sims/qit_bidirectional_science_type1_type2_v0/results/qit_bidirectional_science_type1_type2_v0_v43_validation.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0.py --fresh
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0_pytorch.py
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_bidirectional_science_type1_type2_v0/validate_qit_bidirectional_science_type1_type2_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v7/sims/qit_bidirectional_science_type1_type2_v0/results/qit_bidirectional_science_type1_type2_v0_envelope_results.json --require-pytorch --strict-source-backed --require-tool-intent
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0.py system_v7/sims/qit_bidirectional_science_type1_type2_v0/qit_bidirectional_science_type1_type2_v0_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v7/sims/qit_bidirectional_science_type1_type2_v0/tests
```

## Lev Boundary

The envelope includes a Lev host-consumer contract:

- `truth_state: proposed`
- `evidence_kind: measurement`
- `decision_ceiling: accepted_as_evidence_only`
- `graph_mutation_allowed: false`
- `compositor_apply_allowed: false`
- `mesh_projection_allowed: false`
- `source_boundary_mutated: false`

CR object ids and survivor hashes are evidence keys only. They are not Lev
entity ids.
