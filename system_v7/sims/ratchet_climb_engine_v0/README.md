# ratchet_climb_engine_v0

Executable Ratchet Runbook climb over the reused `ratchet_formal_gates_v1` finite carrier.

Status: `SCRATCH_DIAGNOSTIC`, `promotion_allowed=false`, `formal_admission_allowed=false`, capstone `DRAFT_UNAUDITED`.

This sim does not rebuild R1-R6. It reuses the formal-gate carrier and lock properties, then runs the climbing process:

1. Measure distinction loss.
2. Try the current structure Minimalist-first.
3. Admit only the weakest sufficient ladder lift.
4. Lock each attempt with an R5 token-identity receipt.
5. Project back down and record the residual.
6. Run label-shuffle, commuting-order, lower-layer-can-do-it, and non-definitional SMT flip controls.
7. Repeat across three varied probe/constraint orders for attractor measurement.

Fresh run commands:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/ratchet_climb_engine_v0/ratchet_climb_engine_v0_jax.py
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v7/sims/ratchet_climb_engine_v0/ratchet_climb_engine_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/ratchet_climb_engine_v0/ratchet_climb_engine_v0_numpy.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/ratchet_climb_engine_v0/check_agreement.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v7/sims/ratchet_climb_engine_v0/results/ratchet_climb_engine_v0_three_engine_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v7/sims/ratchet_climb_engine_v0/ratchet_climb_core.py system_v7/sims/ratchet_climb_engine_v0/ratchet_climb_engine_v0_jax.py system_v7/sims/ratchet_climb_engine_v0/ratchet_climb_engine_v0_numpy.py system_v7/sims/ratchet_climb_engine_v0/check_agreement.py
```
