# QUARANTINE_EXPLORATORY: qit_live_loop_3q_v1

classification='scratch_diagnostic'; promotion_allowed=false.

`belief_bloch` is the reduced q0/signal-qubit projection of the 3q belief state, not the full 3q state.

This directory implements the 3-qubit live QIT loop over the 16 stage channels from `system_v7/constraint_core/engines/*_3q.py`. It is a deterministic diagnostic fixture and parity run, not admission evidence.

## v1.1 Contract

- R1: Belief updates use Lüders conditioning on the q0 projective outcome followed by the hill relaxation channel.
- R2: `efe_scores_16` is a schema-stable field name for a reactive-risk + entropy cost surrogate with persistence-prior preference; it is NOT full active-inference EFE and has no ambiguity/epistemic term.
- R3: The chosen stage channel is applied to belief as the predict step of the next tick. The world remains fixture-driven; actions feed back into belief prediction, not into fixture outcome generation.
- R4: NumPy, JAX, PyTorch, and Julia execute the entire per-tick computation in their own stacks. Only the fixture and final JSONL writing are shared.
- R5: The validator gates every per-tick comparison, including `efe_scores_16`, and requires exact action-index parity for all 300 ticks.
- R6: `surprise_bits` is an EPS-regularized Umegaki surrogate using `psd_floor` and `logm(obs + EPS I)`, not exact relative entropy.
- R7: `signal_povm` is fixture metadata echoed for audit, not used in inference.
- R8: `substrates/julia_loop.jl` implements the same R1-R3 transition in native Julia operations.
- R9: The Page-Hinkley + CUSUM online regime-shift detector is run over the fresh live stream and writes `results/live_300/detector_report.json`.

## Scope

- Substrates: NumPy oracle, JAX, PyTorch, Julia.
- World fixture: deterministic 300 ticks, seed `20260703`, no wall-clock input.
- Record stream: JSONL rows under `results/live_300/`.

## Mechanics

- Stage channels are 64x64 superoperators on vectorized 8x8 density matrices.
- Each substrate precomputes all 16 stage channels once, in stage order `(t, op)` from the 3q engine native map.
- Observation is the sampled q0 POVM outcome from `world_fixture.json`, lifted to `|0><0|` or `|1><1|` on q0 tensor maximally mixed q1q2.
- Per tick: previous chosen stage predicts belief, fixture outcome is Lüders-conditioned on q0, hill relaxation stores memory, then the next stage is chosen.
- `surprise_bits` is the EPS-regularized Umegaki surrogate in bits, not exact relative entropy.
- `fe_gradient` is the reduction in the same surrogate after Lüders conditioning.
- `efe_scores_16` computes reactive risk against the persistence-prior preference plus the entropy cost term.
- Deterministic tie-break: if multiple scores share the minimum within `1e-12`, the lowest stage index is chosen.

## Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_live_loop_3q_v1/qit_live_loop_3q_v1.py --ticks 300 --seed 20260703 --fresh

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_live_loop_3q_v1/substrates/numpy_oracle_loop.py --fixture system_v7/sims/qit_live_loop_3q_v1/results/live_300/world_fixture.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_live_loop_3q_v1/substrates/jax_loop.py --fixture system_v7/sims/qit_live_loop_3q_v1/results/live_300/world_fixture.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_live_loop_3q_v1/substrates/torch_loop.py --fixture system_v7/sims/qit_live_loop_3q_v1/results/live_300/world_fixture.json
JULIA_LOAD_PATH=@:@stdlib julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v7/sims/qit_live_loop_3q_v1/substrates/julia_loop.jl --fixture system_v7/sims/qit_live_loop_3q_v1/results/live_300/world_fixture.json

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_live_loop_3q_v1/qit_live_loop_3q_v1.py --validate-only --out-dir system_v7/sims/qit_live_loop_3q_v1/results/live_300
```
