# Bounded Layer Flux And Axis0 Round 3 - 2026-05-23

Status: local Codex controller run, formal-scout receipts fresh-rerun validated.

This round responds to the correction that flux should not be tested as a loose
single-stage scalar. In this run, flux is treated as a candidate readout over a
bounded geometry stack where each layer constrains the next. The dense test is
kept per-engine because the requested 8-16 qubit range becomes expensive once
the full manifold is active at once.

## Scope

User-facing target:

- convert more of the physics / Axis0 / IGT / Holodeck language into
  constraint-native QIT math;
- run actual bounded sims rather than only prose;
- test flux on bounded geometry layers, not as an unconstrained stage readout;
- keep per-engine runs separated for computational tractability;
- preserve strict claim ceilings around physics, Axis0, flux, Holodeck, IGT,
  cognition, and game-theory promotion.

Implemented formal scouts:

1. `sim_bounded_layered_flux_geometry_probe.py`
   - 3-qubit and 8-qubit dense finite QIT stack.
   - Separate per-engine labels `E1` and `E2`.
   - Layer order: carrier polarity, bounded geometry links, stage operators,
     closure transport.
   - Controls: detached current, constraint bypass, product geometry, layer
     shuffled.
2. `sim_shell_cut_axis0_response_probe.py`
   - 4-qubit finite shell-cut graph-state fixture.
   - Candidate readouts: mutual information, coherent information,
     conditional mutual information, finite path entropy.
   - Controls: product state and local dephase perturbation.
3. `sim_stage_capability_state_sweep_probe.py`
   - 24 deterministic initial states.
   - 16 ordered token rows from current canonical QIT chart schedule.
   - Readouts: entropy delta, topology target pull, order gap, exposure,
     future optionality.
4. `sim_holodeck_science_world_memory_ablation_probe.py`
   - Finite two-qubit world/memory state.
   - Science-method loop: instrument, posterior update, effect score, memory
     cue, mutual information.
   - Controls: wrong memory, raw memory, product memory, passive/no active
     projection.

## Results

| Scout | Candidate Status | Main Metric | Interpretation |
| --- | --- | --- | --- |
| bounded layered flux geometry | `open_or_nonrobust_layered_flux_fixture` | survival rate `0.0`, survived `0/4` comparisons | User's bounded-layer requirement was implemented, but this flux readout is killed/nonrobust under controls. |
| shell-cut Axis0 response | `open_candidate_family_survived_fixture` | structured response norm `0.6515760520`; product response norm `0.0` | A finite shell-cut response exists in this fixture. It is not final Axis0; it needs stress controls. |
| stage capability state sweep | `open_or_nonrobust_under_state_sweep` | survival rate `0.0`, nonzero min-pairwise gaps but below robustness criteria | Ordered IGT/token rows have measurable separation after repair, but do not survive the state sweep. |
| Holodeck science world-memory ablation | `open_or_nonrobust_world_memory_fixture` | survival rate `0.0`; mean live-minus-control margin `-0.2619946621` | The finite world-memory loop is currently beaten by controls. This is a negative result for this memory fixture. |

## Validation

Commands run with the repo interpreter:

```text
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/sim_stage_capability_state_sweep_probe.py
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/sim_shell_cut_axis0_response_probe.py
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/sim_holodeck_science_world_memory_ablation_probe.py
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/sim_bounded_layered_flux_geometry_probe.py
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/lint_formal_scout_names.py ...
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/validate_formal_scout_results.py --fresh-rerun --fresh-rerun-timeout 180 ...
```

Validation result:

- formal scout filename lint: `all_pass=true`;
- fresh rerun validation: `all_pass=true`;
- all four receipts include `classification`, `TOOL_MANIFEST`,
  `TOOL_INTEGRATION_DEPTH`, boundary fences, and graveyard/nearby controls.

## Scientific Reading

The strongest positive result is not flux. It is the shell-cut response fixture:
a structured 4-qubit shell state has nonzero finite QIT readout response while
the product control collapses to zero in this fixture.

The strongest negative result is the bounded-layer flux fixture: even after
placing flux on the full bounded geometry stack, the current scalar comparison
does not survive any of the four tested comparisons. This does not kill flux as
a concept. It kills this dense 3/8-qubit layered scalar fixture as a promoted
flux law.

The Holodeck/science-method conversion is now executable in miniature, but this
specific world-memory construction is not load-bearing. Controls beat it across
the 16-seed sweep.

The IGT row grammar is measurable after the repair that adds terrain/topology
mixing to the token channel, but it is not robust enough to call the 16 rows
actual game-theory strategy classes yet.

## Claim Ceiling

Admitted:

- bounded finite QIT fixtures;
- executable scaffold for shell cuts, per-engine layered flux, token-row
  capability readouts, and Holodeck/science memory ablation;
- negative evidence where controls beat candidate claims.

Not admitted:

- final Axis0 / Phi0;
- final flux;
- physics model, gravity / Standard Model unification, Yang-Mills, Riemann, or
  P vs NP implications;
- final Holodeck world engine;
- final IGT game theory;
- psychology/cognition claims.

## Next Minimal Gates

1. Shell-cut stress sweep:
   - run the shell-cut candidate over seed families, graph rewires, local-unitary
     gauge transforms, product/commuting controls, and path-order scrambles.
2. Flux rescue/falsifier:
   - replace the current scalar with current-through-cut observables on 8-qubit
     MPS/process-tensor carriers;
   - keep per-engine isolation;
   - require survival against detached-current, product-geometry, and
     layer-shuffle controls.
3. IGT game-theory conversion:
   - build a finite payoff/readout table where minimax, maximax, maximin, and
     minimin are QIT selectors over channel outcomes;
   - test whether the 16 token rows produce strategy-specific equilibria or
     collapse under label scramble.
4. Holodeck science loop:
   - replace the two-qubit toy memory with a typed finite hypothesis bank;
   - add held-out observations and policy selection by expected evidence;
   - keep wrong-memory and passive-instrument controls.
5. Scaling boundary:
   - dense 16-qubit full-manifold flux is not the next move;
   - 16-qubit should use MPS/process tensors and a local cut observable, not a
     full dense density matrix.

