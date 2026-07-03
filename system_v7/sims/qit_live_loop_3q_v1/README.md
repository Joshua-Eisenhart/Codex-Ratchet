# QUARANTINE_EXPLORATORY: qit_live_loop_3q_v1

classification='scratch_diagnostic'; promotion_allowed=false.

`belief_bloch` is the reduced q0/signal-qubit projection of the 3q belief state, not the full 3q state.

This directory implements the 3-qubit live QIT loop over the 16 stage channels from `system_v7/constraint_core/engines/*_3q.py`. It is a deterministic diagnostic fixture and parity run, not admission evidence.

## Scope

- Substrates: NumPy oracle, JAX, PyTorch, Julia.
- World fixture: deterministic 300 ticks, seed `20260703`, no wall-clock input.
- Record stream: JSONL rows under `results/live_300/`.

## Mechanics

- Stage channels are 64x64 superoperators on vectorized 8x8 density matrices.
- Each substrate precomputes all 16 stage channels once, in stage order `(t, op)` from the 3q engine native map.
- Observation is the sampled q0 POVM outcome from `world_fixture.json`, lifted to `|0><0|` or `|1><1|` on q0 tensor maximally mixed q1q2.
- `surprise_bits` is the full 3q Umegaki relative entropy `S(obs || belief)` in bits, following `lev_bridge_sim.py`.
- `fe_gradient` is the full 3q free-energy reduction for the pre-store belief update, following `lev_bridge_sim.py`.
- EFE scores follow `agent_loop_sim.py`: `risk - (S(belief) - S(post))`.
- Deterministic tie-break: if multiple EFE scores share the minimum, the lowest stage index is chosen.

## Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_live_loop_3q_v1/qit_live_loop_3q_v1.py --ticks 300 --seed 20260703 --fresh

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_live_loop_3q_v1/substrates/numpy_oracle_loop.py --fixture system_v7/sims/qit_live_loop_3q_v1/results/live_300/world_fixture.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_live_loop_3q_v1/substrates/jax_loop.py --fixture system_v7/sims/qit_live_loop_3q_v1/results/live_300/world_fixture.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_live_loop_3q_v1/substrates/torch_loop.py --fixture system_v7/sims/qit_live_loop_3q_v1/results/live_300/world_fixture.json
JULIA_LOAD_PATH=@:@stdlib julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v7/sims/qit_live_loop_3q_v1/substrates/julia_loop.jl --fixture system_v7/sims/qit_live_loop_3q_v1/results/live_300/world_fixture.json

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_live_loop_3q_v1/qit_live_loop_3q_v1.py --validate-only --out-dir system_v7/sims/qit_live_loop_3q_v1/results/live_300
```
