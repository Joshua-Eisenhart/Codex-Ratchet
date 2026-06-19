# Build Card - `gcm_constraint_carve_4q_v0`

Status: builder packet, scratch diagnostic.

Declared surface: layers 1-2 (+17 tensor) | carve | 4Q.

Authority:
- Owner priority: it is going equal to and greater than 3 qubits; climb the qubit ladder.
- `gcm_constraint_carve_3q_v1` at `5544ad21c`: replicate the state-artifacted pattern, not the first-failed-label pattern.
- consume existing 4Q feedstock, never rebuild it: `geo_s1_four_qubit_support_exact_v0`, `stage_lifted_spinor_shell_n4_v0`, `terrain_spinor_flux_nest_n4_v0`.
- 3Q freeze lineage target: `gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5`, landed in this checkout and consumed by registry body hash.
- G.2a is wired from birth through the builder/audit boundary helper; this file is not an audit verdict.

Packet contract:
- every candidate's `rho_ABCD` is content-addressed and stored;
- full C1/C2/C3 matrix per candidate, never first-failed-only;
- 4Q candidate space is pinned and tractable: 545 product lifts from 3Q survivors plus 10 4Q boundary/feedstock/control anchors;
- representative entangled boundary rows include GHZ4, W4, and cluster-state reps from the lifted-ladder n4 feedstock context;
- M(C)@4Q, quotient, and existence probes are emitted with a scratch-diagnostic ceiling;
- cross-rung rows include product embeddings and partial-trace rows against 3Q survivors across the 7 bipartitions;
- 4-party CKW is the narrow Osborne-Verstraete focus-qubit inequality where computable from stored pure states; no residual 4-tangle or SLOCC separator is claimed;
- floor rows extend to Cl(8) on C^16 only by consuming existing feedstock rows;
- controls carry empty-C, cliff, erasure-bite, probe-scramble, source-recompute injection-red, and 1Q/2Q/3Q regressions.

Claim ceiling:
- `scratch_diagnostic`;
- state-artifacted 4Q count fixture;
- carrier-and-pins-relative;
- not THE manifold;
- not formal admission, bridge, axis, physics, or SLOCC classification evidence.

Files:
- `gcm_constraint_carve_4q_v0_common.py`
- `gcm_constraint_carve_4q_v0.py`
- `gcm_constraint_carve_4q_v0_jax.py`
- `gcm_constraint_carve_4q_v0_pytorch.py`
- `gcm_constraint_carve_4q_v0_julia.jl`
- `gcm_constraint_carve_4q_v0_envelope.py`
- `write_envelope_spec.py`
- `validate_gcm_constraint_carve_4q_v0.py`
- `tests/test_gcm_constraint_carve_4q_v0.py`
- `results/*.json`

Verification:
```bash
SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
make helper-process-audit-strict
$SIM_PY system_v6/sims/gcm_constraint_carve_4q_v0/gcm_constraint_carve_4q_v0.py
$SIM_PY system_v6/sims/gcm_constraint_carve_4q_v0/gcm_constraint_carve_4q_v0_jax.py
$SIM_PY system_v6/sims/gcm_constraint_carve_4q_v0/gcm_constraint_carve_4q_v0_pytorch.py
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/gcm_constraint_carve_4q_v0/gcm_constraint_carve_4q_v0_julia.jl
$SIM_PY system_v6/sims/gcm_constraint_carve_4q_v0/write_envelope_spec.py
$SIM_PY system_v6/sims/gcm_constraint_carve_4q_v0/gcm_constraint_carve_4q_v0_envelope.py
$SIM_PY system_v6/sims/gcm_constraint_carve_4q_v0/validate_gcm_constraint_carve_4q_v0.py
$SIM_PY -m pytest -q system_v6/sims/gcm_constraint_carve_4q_v0/tests/test_gcm_constraint_carve_4q_v0.py
```

NO git add/commit.
