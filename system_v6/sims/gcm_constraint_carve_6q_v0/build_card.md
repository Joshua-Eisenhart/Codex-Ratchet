# Build Card - `gcm_constraint_carve_6q_v0`

Status: builder packet, scratch diagnostic.

Declared surface: layers 1-2 (+17 tensor) | carve | 6Q.

Authority:
- Owner priority: CLIMB the carve at 6Q while consuming existing 6Q feedstock.
- `gcm_constraint_carve_5q_v0` at `16837555a` with source packet `b8b6e777e`: replicate the state-artifacted pattern, full C1/C2/C3 matrix, content-addressed states, and count-fixture ceiling.
- consume existing 6Q feedstock by hash, never rebuild it: `geo_s1_scaling_stress_678q_exact_v0` at `b27d22317` and `stage_lifted_spinor_shell_n6_v0`.
- cross-rung target: 5Q carve survivors from `gcm_constraint_carve_5q_v0`.
- G.2a is wired from birth through the builder/audit boundary helper; this file is not an audit verdict.

Packet contract:
- every candidate's `rho_ABCDEF` is content-addressed and stored;
- full C1/C2/C3 matrix per candidate, never first-failed-only;
- 6Q candidate space is pinned and tractable: 547 5Q survivor product lifts plus 10 6Q boundary/feedstock/control anchors;
- representative 6Q rows include GHZ6, W6, cluster_linear_6, product, and a bounded W-like shell-weighted representative derived from stage-lifted n6 support rows;
- M(C)@6Q, quotient, and existence probes are emitted with a scratch-diagnostic ceiling;
- cross-rung rows include product embeddings and Tr_F rows against 5Q survivors;
- the cut lattice stores 31 bipartitions with names plus entropy/MI rows, but per-cut reduced matrices are not stored in this packet;
- 6-party monogamy is narrowed to the Osborne-Verstraete N-qubit CKW focus-qubit inequality where computable from stored pure states; no residual 6-tangle or higher-party residual allocation is claimed;
- floor rows extend to Cl(12) only by consuming existing feedstock rows;
- controls carry empty-C, cliff, erasure-bite, probe-scramble, source-recompute injection-red, and 1Q-5Q regressions/negatives.

Claim ceiling:
- `scratch_diagnostic`;
- state-artifacted 6Q count fixture;
- carrier-and-pins-relative;
- not THE manifold;
- not formal admission, bridge, axis, physics, SLOCC classification, or six-party entanglement-classification evidence.

Files:
- `gcm_constraint_carve_6q_v0_common.py`
- `gcm_constraint_carve_6q_v0.py`
- `gcm_constraint_carve_6q_v0_jax.py`
- `gcm_constraint_carve_6q_v0_pytorch.py`
- `gcm_constraint_carve_6q_v0_julia.jl`
- `gcm_constraint_carve_6q_v0_envelope.py`
- `write_envelope_spec.py`
- `validate_gcm_constraint_carve_6q_v0.py`
- `tests/test_gcm_constraint_carve_6q_v0.py`
- `results/*.json`

Verification:
```bash
SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
make helper-process-audit-strict
$SIM_PY system_v6/sims/gcm_constraint_carve_6q_v0/gcm_constraint_carve_6q_v0.py
$SIM_PY system_v6/sims/gcm_constraint_carve_6q_v0/gcm_constraint_carve_6q_v0_jax.py
$SIM_PY system_v6/sims/gcm_constraint_carve_6q_v0/gcm_constraint_carve_6q_v0_pytorch.py
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/gcm_constraint_carve_6q_v0/gcm_constraint_carve_6q_v0_julia.jl
$SIM_PY system_v6/sims/gcm_constraint_carve_6q_v0/write_envelope_spec.py
$SIM_PY system_v6/sims/gcm_constraint_carve_6q_v0/gcm_constraint_carve_6q_v0_envelope.py
$SIM_PY system_v6/sims/gcm_constraint_carve_6q_v0/validate_gcm_constraint_carve_6q_v0.py
$SIM_PY -m pytest -q system_v6/sims/gcm_constraint_carve_6q_v0/tests/test_gcm_constraint_carve_6q_v0.py
```

NO git add/commit.
