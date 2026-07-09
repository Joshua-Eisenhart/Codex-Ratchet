# qit_projection_battery_v0

Status: `scratch_diagnostic`.

This packet is a projection-battery scout over the finite parent packet
`qit_full_type1_type2_64_live_v1`. It asks a narrower question:

Can several partial MMM-style views of the same finite carrier converge back to
the same four object cards while erased controls fail at chance?

## Claim Ceiling

Allowed:

- finite partial-view convergence over the v1 object-card carrier;
- projection hashes and anti-hashes for four scratch object cards;
- bounded MMM analogy for partial business/domain vocabularies;
- source-backed JAX, Julia, and PyTorch lanes over the same finite battery.

Blocked:

- live perception;
- production object factory;
- Axis0, FEP, Xi/Phi0, physics, or manifold admission;
- ontology writer or MMM-driver admission;
- Lev mesh runtime integration;
- remote peer graph mutation.

## Teeth

The nominal battery uses five partial views:

- `maintenance_mmm`
- `finance_mmm`
- `safety_mmm`
- `planning_mmm`
- `ontology_mmm`

The masks intentionally exclude direct loop and engine labels. Those fields
exist in the parent carrier and would trivially identify the four objects, so
this packet records them only as an overclaim hazard.

The pass condition is:

- nominal mean held-out projection accuracy is at least `0.85`;
- bag-erased and view-erased controls remain at or below `0.25`;
- z3 and cvc5 prove the negated gate is `unsat`;
- Julia, JAX, and PyTorch independently pass with no peer-result reads;
- engine object-count and view-count divergence are both zero.

Current measured result:

- nominal mean held-out accuracy: `0.9`
- bag-erased mean: `0.25`
- view-erased mean: `0.25`
- engines: `julia`, `jax`, `pytorch`
- divergence: `0.0`

## Rerun

From repo root:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_projection_battery_v0/qit_projection_battery_v0.py --fresh
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_projection_battery_v0/qit_projection_battery_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_projection_battery_v0/qit_projection_battery_v0_pytorch.py
/opt/homebrew/bin/julia --project=system_v5/julia_carrier system_v7/sims/qit_projection_battery_v0/qit_projection_battery_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_projection_battery_v0/qit_projection_battery_v0_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_projection_battery_v0/validate_qit_projection_battery_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v7/sims/qit_projection_battery_v0/results/qit_projection_battery_v0_envelope_results.json --require-pytorch --strict-source-backed --require-tool-intent
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v7/sims/qit_projection_battery_v0/qit_projection_battery_v0.py system_v7/sims/qit_projection_battery_v0/qit_projection_battery_v0_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v7/sims/qit_projection_battery_v0/tests
```

## Lev Boundary

The envelope includes a host-consumer contract for Lev:

- `truth_state: proposed`
- `evidence_kind: measurement`
- `decision_ceiling: accepted_as_evidence_only`
- `graph_mutation_allowed: false`
- `compositor_apply_allowed: false`
- `mesh_projection_allowed: false`
- `source_boundary_mutated: false`

CR object ids and survivor hashes are evidence keys only. They are not Lev
entity ids.
