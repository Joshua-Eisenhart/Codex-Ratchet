# BUILD CARD -- eng64_stage_fingerprint_ids_v0

Owner card: small additive hardening packet. No git add/commit.

## Authority

- Primary audit: `system_v6/sims/iching_symmetry_match_v0/audit_verdict.md`
  - User-supplied audit commit/hash hint: `2b32714a0`
  - Caveat 5 requires future `eng_64` estates to emit stable per-stage fingerprint IDs/component IDs so downstream packets do not infer quotient classes from labels/collapse pairs.
- Source/result estate, read-only:
  - `system_v5/julia_carrier/eng_64_hexagram_julia.jl`
  - `system_v5/julia_carrier/eng_64_hexagram_julia_results.json`
- Reference downstream inference:
  - `system_v6/sims/iching_symmetry_match_v0/iching_symmetry_match_v0.py`
  - `system_v6/sims/iching_symmetry_match_v0/results/iching_symmetry_match_v0_results.json`

## Object

Compute label-free per-stage behavioral fingerprints for the committed `eng_64` stage schedule by porting the committed 2x2 density-channel fingerprint algorithm into this packet.

Emit one results JSON mapping:

- `stage`
- `fingerprint`
- stable `fingerprint_id`
- stable `component_id`
- component partition

The fingerprint definition must be pinned in-card and in-result: apply the committed stage operation to the deterministic representative L-Weyl density matrix, flatten `rho_out` to eight real/imag floats, round by `FP_TOL=1e-7`, and hash the vector. Stage labels, engine text, direction text, and collapse pair text are excluded from the fingerprint.

## Checks

- Fresh component count recovers `n_distinct=16`; this is a check, not an assumption.
- The committed `eng_64` result also reports `fingerprint_counts.n_distinct=16`.
- Label permutation leaves fingerprint IDs unchanged.
- Two stages in each same component have equal fingerprints when recomputed independently.
- Fresh vector-derived components match the committed collapse-graph components as a parity check.

## Fences

- STRICTLY ADDITIVE: write only inside `system_v6/sims/eng64_stage_fingerprint_ids_v0/`.
- Do not modify the committed `eng_64` estate.
- No git add/commit.
- `classification` is `scratch_diagnostic`.
- `promotion_allowed=false`; `formal_admission_allowed=false`.
- Downstream-plumbing only.
- This unblocks a Matrix64 behavior packet by providing stable IDs; it does not claim Matrix64 behavior, `eng_64` promotion, 64-behavior isomorphism, QIT admission, or physics admission.
