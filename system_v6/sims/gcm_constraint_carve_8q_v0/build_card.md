# Build Card - `gcm_constraint_carve_8q_v0`

Status: builder packet, scratch diagnostic.

Declared surface: layers 1-2 (+17) | carve | 8Q.

Authority:
- Owner priority: rebuild the 8Q carve after the SCALE-WALL finding without the v0 blob.
- `system_v6/receipts/carve_ladder_scale_wall_20260612.md`: the older full-rho-per-candidate pattern scale-walled; this 8Q packet must stay LEAN.
- 7Q v1 discipline: `gcm_constraint_carve_7q_v1` keeps the full C1/C2/C3 matrix, display-only first-failed fields, product lift/retraction rows, cut caveats, narrowed CKW wording, controls, and G.2a while storing only hashes plus bounded samples.
- Consume 8Q feedstock by hash, never rebuild it: `geo_s1_scaling_stress_678q_exact_v0` and `stage_lifted_spinor_shell_n8_v0`.
- G.2a is wired from birth through the builder/audit boundary helper; this file is not an audit verdict.

LEAN packet contract:
- main result stores a hash per candidate rho, not a full matrix per candidate;
- main result stores the full C1/C2/C3 matrix for every candidate;
- NO every-candidate 256x256 rho blob;
- a separate bounded sample file stores full matrices only for GHZ8, W8, cluster_linear_8, about five survivors, and about five kills;
- candidate space is 549 7Q survivor product lifts plus 10 8Q anchors/controls, including GHZ8, W8, cluster_linear_8, and a shell-weighted W-like representative from `stage_lifted_spinor_shell_n8_v0`;
- M(C)@8Q, survivor/class counts, and quotient remain carrier-and-pins-relative count-fixture rows;
- cross-rung rows include 7Q product embedding and Tr_H retraction via hashes;
- 127 bipartitions are stored as entropy/MI summary rows only; per-cut reduced matrices are not stored;
- 8-party monogamy is narrowed to Osborne-Verstraete focus-qubit CKW checks on pure sampled rows; no residual 8-tangle or higher-party allocation is claimed;
- Cl(16) is consumed as feedstock, not rebuilt;
- controls carry empty-C, cliff, erasure-bite, probe-scramble, source-recompute injection-red, and 1Q-7Q regressions/negatives.

Claim ceiling:
- `scratch_diagnostic`;
- LEAN state-fingerprinted 8Q count fixture;
- carrier-and-pins-relative;
- not THE manifold;
- not formal admission, bridge, axis, physics, geometry, SLOCC classification, eight-party entanglement classification, 8Q registry freeze, or reduced-cut-state artifact evidence.

Files:
- `gcm_constraint_carve_8q_v0_common.py`
- `gcm_constraint_carve_8q_v0.py`
- `validate_gcm_constraint_carve_8q_v0.py`
- `tests/test_gcm_constraint_carve_8q_v0.py`
- `results/gcm_constraint_carve_8q_v0_results.json`
- `results/gcm_constraint_carve_8q_v0_sample_matrices.json`
- `results/gcm_constraint_carve_8q_v0_validator_results.json`

Verification:
```bash
SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba make helper-process-audit-strict
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba $SIM_PY system_v6/sims/gcm_constraint_carve_8q_v0/gcm_constraint_carve_8q_v0.py
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba $SIM_PY system_v6/sims/gcm_constraint_carve_8q_v0/validate_gcm_constraint_carve_8q_v0.py
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba $SIM_PY -m pytest -q -p no:cacheprovider system_v6/sims/gcm_constraint_carve_8q_v0/tests/test_gcm_constraint_carve_8q_v0.py
du -sh system_v6/sims/gcm_constraint_carve_8q_v0
find system_v6/sims/gcm_constraint_carve_8q_v0 -type f -size +50M -print
```

NO git add/commit.
