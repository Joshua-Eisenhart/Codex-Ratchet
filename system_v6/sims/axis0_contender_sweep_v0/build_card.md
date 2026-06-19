# BUILD CARD - axis0_contender_sweep_v0

## Purpose

Run the registry-bound phase-1 light pass for Axis-0 contender probes.

Binding registry:
`system_v6/receipts/axis0_contender_probe_registry_20260612.md`
at commit `31dfd11b6`.

Anchor:
`system_v6/sims/discrete_axis0_field_v0/` at the committed first-candidate
lineage. This packet uses its committed 33-cell Family A carrier, ordered
`cell_id=0..32`, generator-labelled edges, and exact outgoing-gradient readout.

## Boundary

Classification: `scratch_diagnostic`.

Promotion allowed: `false`.

Formal admission allowed: `false`.

This packet may report:

- exact 33-entry vectors for CP.0, CP.1, CP.2, and CP.10;
- canonical alias forms computed before teeth rows;
- exact alias pair table for computed light representatives;
- registry-named light teeth exclusions with witnesses;
- CP.3-CP.9 as `co-survivor-open` and queued-heavy when no source-backed
  33-cell adapter exists in phase 1;
- controls for anchor self, deliberate alias, and deliberate different-axis
  readout.

This packet may not report:

- Axis-0 admission;
- "THE Axis-0 readout";
- merged co-survivors;
- heavy-local adapter results;
- bridge, physics, or manifold promotion;
- candidates added after result inspection.

## Honest Mode

Mode: exact/light.

Lanes:

- Python/JAX-role lane: exact `Fraction` rows, `networkx` graph observables,
  `sympy` exact symbolic support marker, `z3`, and `cvc5`.
- Julia mirror lane: reads the committed anchor envelope, recomputes the light
  CP.1/CP.2/CP.10 counts, and binds the verdict table with `Z3.jl`.
- PyTorch: honestly omitted. No tensor/autograd/neural claim path is scoped by
  this phase-1 light pass.

SMT binds the computed verdict-table counts and light-row disagreement counts.
Flip controls mutate CP.1 disagreement to zero and must become SAT.

## Wizard Route Note

Wizard v4.2 Max Assembly was attempted locally with:

```bash
python3 scripts/wizard_v4_2.py --level high --loop 1 --task "Build axis0_contender_sweep_v0 inside system_v6/sims/axis0_contender_sweep_v0 only; registry-bound phase-1 light pass over axis0 contender probes; no git add/commit."
```

The route command produced no usable receipt output after roughly one minute
and was stopped. Native Codex subagent fanout was blocked by the current tool
policy because the user did not explicitly request subagents/delegation. This
packet therefore records a partial/blocked Wizard route and relies on direct
tool execution, exact validators, and file-disjoint artifacts.

## Commands

Run from repo root:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/axis0_contender_sweep_v0/axis0_contender_sweep_v0.py
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/axis0_contender_sweep_v0/axis0_contender_sweep_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/axis0_contender_sweep_v0/axis0_contender_sweep_v0_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/axis0_contender_sweep_v0/results/axis0_contender_sweep_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/axis0_contender_sweep_v0/validate_axis0_contender_sweep_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/axis0_contender_sweep_v0/tests
```

## Expected Verdicts

| Candidate | Verdict | Status |
|---|---|---|
| `A0.CP.0_committed_signed_outgoing_gradient_flux` | `alias-of-anchor` | computed |
| `A0.CP.1_unweighted_edge_gradient_count_balance` | `excluded-by-Hamming-disagreement-from-committed-sign-vector` | computed |
| `A0.CP.2_incoming_vs_outgoing_gradient_current` | `excluded-by-source-sink-imbalance` | computed |
| `A0.CP.3_entropy_gradient_sign` | `co-survivor-open` | queued-heavy, adapter required |
| `A0.CP.4_pauli_participation_feedback_polarity` | `co-survivor-open` | queued-heavy, adapter required |
| `A0.CP.5_flux_direction_annular_or_edge_current` | `co-survivor-open` | queued-heavy, adapter required |
| `A0.CP.6_flux_continuity_n3_n4_current_sign` | `co-survivor-open` | queued-heavy, adapter required |
| `A0.CP.7_lyapunov_descent_direction` | `co-survivor-open` | queued-heavy, adapter required |
| `A0.CP.8_hopfield_energy_gradient_sign` | `co-survivor-open` | queued-heavy, adapter required |
| `A0.CP.9_holonomy_spectrum_sign` | `co-survivor-open` | queued-heavy, adapter required |
| `A0.CP.10_transition_graph_in_out_degree_imbalance` | `excluded-by-degree-teeth-wrong-distinction` | computed |

Controls:

- `control.anchor_self`: `alias-of-anchor`.
- `control.sign_flipped_monotone_reparameterized_anchor`: `alias-of-anchor`.
- `control.axis6_style_order_readout`:
  `not-axis0-contender-by-distinction-boundary`.
