# Type-1 Engine v0

Source: `system_v7/sims/TYPE1_ENGINE_EXTRACTION_20260703.md`.

Ceiling:

- `QUARANTINE_EXPLORATORY`
- `classification="scratch_diagnostic"`
- `promotion_allowed=false`
- `formal_admission_allowed=false`

This implements the Type-1 chart only: flux `IN`, `H=+H0`, four terrains, four operators, eight stages, outer deductive loop, inner inductive loop, and double traversal. The terrain equations are ONE CANDIDATE realization, not settled math (`ATLAS:82-85`).

## Substrates

- `type1_engine_v0_numpy.py`: NumPy/SciPy finite-time GKSL superoperator leg.
- `type1_engine_v0_julia.jl`: independent Julia finite-time GKSL superoperator leg, with `QuantumOptics.entropy_vn` used for entropy fingerprint values.
- `validate_type1_engine_v0.py`: parity validator and `results/RESULTS.md` writer.

JAX and torch legs are not in this v0; they are queued only.

## Source Pins

- Type-1 terrains: `IGT:484-489`, `ATLAS:103-110`.
- Operators: `SIGNED:136-557`.
- Type-1 stages: `IGT:529-534`.
- Traversals: `IGT:464-469`, `IGT:517-525`.

## Open Gaps

- Terrain parameters and exact `L` operators remain candidate terrain math, not closed math (`ATLAS:82-85`, `ATLAS:118-129`).
- MBTI labels are attached from the owner xlsx, not from the four markdown engine docs; labels are annotation only and never load-bearing.
- Axis-0 is not built here. No `Xi` mapping from geometry to `rho_AB` is implemented.
- No 720 closure claim is made. The result reports measured finite traversal closure norms only.

## Run

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 type1_engine_v0_numpy.py
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier type1_engine_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 validate_type1_engine_v0.py
```
