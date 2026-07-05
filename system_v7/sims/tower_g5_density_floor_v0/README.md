# tower_g5_density_floor_v0

G5 rho-first density floor assembly for `D(H), H=C^2`.

This rung is `classification=scratch_diagnostic` and `promotion_allowed=false`.
It computes, independently in Julia, JAX, and PyTorch:

- quotient-to-rho lift: identical probe statistics reconstruct the same rho;
- installed-not-forced record: rho is installed by a removable downstream-operator closure demand;
- downstream licensing check: a unitary and Z-dephasing are expressible on rho, not on a bare quotient label;
- negative controls: distinct statistics separate, and label shuffle preserves rho.

Run from this directory:

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier tower_g5_density_floor_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 tower_g5_density_floor_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 tower_g5_density_floor_v0_pytorch.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 check_agreement.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 /Users/joshuaeisenhart/Codex-Ratchet/scripts/validate_three_engine_sim_result.py --require-pytorch results/tower_g5_density_floor_v0_three_engine_results.json
```
