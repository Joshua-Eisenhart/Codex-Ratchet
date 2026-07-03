
```json
"lr_status": {
  "dual_engine_run": false,
  "reason": "3q files expose the 16-stage contract, not separate runnable L/R sheet engines",
  "source_lr_partition": "t0-t3 left, t4-t7 right is documented outside the 3q constructors"
}
```

## 5. Emission To Lev Bridge

Stream convention should follow v0’s manifest/segment mechanics: v0 appends rows with `tick`, deterministic `t_iso`, `belief_bloch`, `surprise_bits`, `fe_gradient`, `stream_id`, and schema at [qit_live_loop_v0.py](/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/qit_live_loop_v0/qit_live_loop_v0.py:285).

For 3q, the bridge-facing `belief_bloch[3]` must be the reduced signal-qubit Bloch vector:

```text
rho_signal = Tr_{q1,q2}(belief_rho_8)
belief_bloch = [tr(rho_signal sx), tr(rho_signal sy), tr(rho_signal sz)]
```

Doc header must say: `belief_bloch is the reduced q0/signal-qubit projection of the 3q belief state, not the full 3q state.`

Extra stream fields:

```json
{
  "tick": 0,
  "t_iso": "2026-07-03T00:00:00Z",
  "schema": "cr.qit_live_loop_3q_v1.tick.v1",
  "stream_id": "qit_live_loop_3q_v1.live_300",
  "belief_bloch": [0.0, 0.0, 0.0],
  "belief_pauli_63": [],
  "surprise_bits": 0.0,
  "fe_gradient": 0.0,
  "chosen_action_index": 0,
  "chosen_stage": {"t": 0, "op": "Ti"},
  "efe_scores_16": [],
  "world_segment": "A_stationary",
  "signal_povm": {"p0": 0.0, "p1": 0.0},
  "classification": "scratch_diagnostic",
  "promotion_allowed": false
}
```

Mapping:

- `surprise_bits`: full 3q `F(obs_rho_8 || belief_rho_8)`.
- `fe_gradient`: full 3q free-energy reduction this tick.
- `belief_bloch`: q0 reduced projection only.
- `belief_pauli_63`: full internal state for parity/audit, not required by old Lev bridge but included in v1 diagnostic stream.

## 6. Runtime Budget

At `C^8`, density vectorization is 64-dimensional and each stage channel is a 64x64 superoperator. Current JAX/Torch/Julia engines compute matrix exponentials per terrain/stage; see JAX `expm(T_FLOW*gen_super(t))` at [jax_engine_3q.py](/Users/joshuaeisenhart/Codex-Ratchet/system_v7/constraint_core/engines/jax_engine_3q.py:66), Torch `torch.linalg.matrix_exp` at [torch_engine_3q.py](/Users/joshuaeisenhart/Codex-Ratchet/system_v7/constraint_core/engines/torch_engine_3q.py:68), and Julia `exp(T_FLOW*gen_super(t))` at [julia_engine_3q.jl](/Users/joshuaeisenhart/Codex-Ratchet/system_v7/constraint_core/engines/julia_engine_3q.jl:80).

Budget rule:

- Precompute the 16 stage superoperators once per substrate. Do not recompute `expm` per tick/action.
- Per tick cost after precompute: 16 candidate 64x64 matrix-vector products for EFE predictions, plus log/eigendecomp calls for `F` and entropy.
- Recommended first target: `300` ticks.
- Acceptable range: `200-400` ticks.
- Avoid `>400` until Julia+Torch timings are known.
- Numpy oracle may be slow if using RK4 `flow()` per stage per tick; for live loop parity, numpy should build oracle superoperators once from the same generator where possible, while preserving the existing oracle contract as the reference.

## 7. File Layout And Commands

Directory:

```text
system_v7/sims/qit_live_loop_3q_v1/
  README.md
  qit_live_loop_3q_v1.py
  world_fixture_3q.py
  common_3q.py
  substrates/
    numpy_oracle_loop.py
    jax_loop.py
    torch_loop.py
    julia_loop.jl
  results/
    live_300/
      world_fixture.json
      numpy_oracle_loop.jsonl
      jax_loop.jsonl
      torch_loop.jsonl
      julia_loop.jsonl
      parity_report.json
      lev_bridge_stream/
        segments_manifest.json
        segments/*.jsonl
      summary.json
      RESULTS.md
```

Entry commands:

```bash
# Generate deterministic world fixture and run all four substrates.
python3 system_v7/sims/qit_live_loop_3q_v1/qit_live_loop_3q_v1.py --ticks 300 --seed 20260703 --fresh

# Individual substrate reruns.
python3 system_v7/sims/qit_live_loop_3q_v1/substrates/numpy_oracle_loop.py --fixture system_v7/sims/qit_live_loop_3q_v1/results/live_300/world_fixture.json
python3 system_v7/sims/qit_live_loop_3q_v1/substrates/jax_loop.py --fixture system_v7/sims/qit_live_loop_3q_v1/results/live_300/world_fixture.json
python3 system_v7/sims/qit_live_loop_3q_v1/substrates/torch_loop.py --fixture system_v7/sims/qit_live_loop_3q_v1/results/live_300/world_fixture.json
julia system_v7/sims/qit_live_loop_3q_v1/substrates/julia_loop.jl --fixture system_v7/sims/qit_live_loop_3q_v1/results/live_300/world_fixture.json

# Validate parity and bridge stream.
python3 system_v7/sims/qit_live_loop_3q_v1/qit_live_loop_3q_v1.py --validate-only --out-dir system_v7/sims/qit_live_loop_3q_v1/results/live_300
```

Acceptance gates:

- All four substrate files exist and report `ticks=300`.
- All action indices match exactly per tick.
- Python trio parity passes `1e-10`.
- Julia parity passes `1e-9`.
- Lev stream verifies with deterministic segment hashes.
- `RESULTS.md` states projection boundary, L/R non-claim, and `scratch_diagnostic; promotion_allowed=false`.


