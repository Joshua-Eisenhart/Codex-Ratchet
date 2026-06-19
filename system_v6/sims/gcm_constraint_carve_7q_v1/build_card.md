# Build Card - `gcm_constraint_carve_7q_v1`

Status: builder packet, scratch diagnostic.

Declared surface: layers 1-2 (+17) | carve | 7Q.

Authority:
- Owner priority: rebuild the 7Q carve after the SCALE-WALL finding without the v0 blob.
- `system_v6/receipts/carve_ladder_scale_wall_20260612.md`: the 7Q v0 pattern stored every 128x128 rho and produced a 1.1 GB JSON; v1 must be LEAN.
- 6Q discipline: `gcm_constraint_carve_6q_v0` keeps the full C1/C2/C3 matrix, display-only first-failed fields, product lift/retraction rows, cut caveats, narrowed CKW wording, controls, and G.2a.
- Consume 7Q feedstock by hash, never rebuild it: `geo_s1_scaling_stress_678q_exact_v0` and `stage_lifted_spinor_shell_n7_v0`.
- G.2a is wired from birth through the builder/audit boundary helper; this file is not an audit verdict.

LEAN packet contract:
- main result stores a hash per candidate rho, not a full matrix per candidate;
- main result stores the full C1/C2/C3 matrix for every candidate;
- NO every-candidate 128x128 rho blob;
- a separate bounded sample file stores full matrices only for GHZ7, W7, cluster_linear_7, about five survivors, and about five kills;
- candidate space is 548 6Q survivor product lifts plus 10 7Q anchors/controls, including GHZ7, W7, cluster_linear_7, and a shell-weighted W-like representative from `stage_lifted_spinor_shell_n7_v0`;
- M(C)@7Q, survivor/class counts, and quotient remain carrier-and-pins-relative count-fixture rows;
- cross-rung rows include 6Q product embedding and Tr_G retraction via hashes;
- 63 bipartitions are stored as entropy/MI summary rows only; per-cut reduced matrices are not stored;
- 7-party monogamy is narrowed to Osborne-Verstraete focus-qubit CKW checks on pure sampled rows; no residual 7-tangle or higher-party allocation is claimed;
- Cl(14) is consumed as feedstock, not rebuilt;
- controls carry empty-C, cliff, erasure-bite, probe-scramble, source-recompute injection-red, and 1Q-6Q regressions/negatives.

Claim ceiling:
- `scratch_diagnostic`;
- LEAN state-fingerprinted 7Q count fixture;
- carrier-and-pins-relative;
- not THE manifold;
- not formal admission, bridge, axis, physics, geometry, SLOCC classification, seven-party entanglement classification, 7Q registry freeze, or reduced-cut-state artifact evidence.

Files:
- `gcm_constraint_carve_7q_v1_common.py`
- `gcm_constraint_carve_7q_v1.py`
- `validate_gcm_constraint_carve_7q_v1.py`
- `tests/test_gcm_constraint_carve_7q_v1.py`
- `results/gcm_constraint_carve_7q_v1_results.json`
- `results/gcm_constraint_carve_7q_v1_sample_matrices.json`
- `results/gcm_constraint_carve_7q_v1_validator_results.json`

Verification:
```bash
SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba make helper-process-audit-strict
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba $SIM_PY system_v6/sims/gcm_constraint_carve_7q_v1/gcm_constraint_carve_7q_v1.py
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba $SIM_PY system_v6/sims/gcm_constraint_carve_7q_v1/validate_gcm_constraint_carve_7q_v1.py
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba $SIM_PY -m pytest -q -p no:cacheprovider system_v6/sims/gcm_constraint_carve_7q_v1/tests/test_gcm_constraint_carve_7q_v1.py
du -sh system_v6/sims/gcm_constraint_carve_7q_v1
find system_v6/sims/gcm_constraint_carve_7q_v1 -type f -size +50M -print
```

NO git add/commit.
