# QICS Entropy DPI Numeric Oracle v0

This is a bounded, deterministic `scratch_diagnostic` packet for one QICS API
surface: fixed-input minimization over `qics.cones.QuantRelEntr`.

The packet uses three fixed full-rank Hermitian density pairs. For each pair it
solves the original epigraph problem and the images under computational
pinching and a depolarizing map. Every QICS value is compared with a separate
spectral Umegaki implementation. Both value streams must contract for every
accepted map.

Two controls are deliberately excluded. Transposition fails the complete
positivity certificate, while multiplication by `1.10` fails trace
preservation and density-output validation. Neither control invokes QICS or
contributes to the accepted contraction count.

## Pinned Runtime

- QICS checkout: `/Users/joshuaeisenhart/GitHub/qics`
- QICS commit: `be18e5ef07258dec9e5db6bb18c1ee9b2003d545`
- QICS version: `1.1.3`
- Python: `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/qics-1.1.3-py311/bin/python`

The run rejects a dirty or differently pinned QICS checkout. Bytecode writes
are disabled so the checkout and interpreter environment remain read-only.

## Rerun

```sh
/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/qics_entropy_dpi_numeric_oracle_v0/run_all.sh
```

`run_all.sh` writes `result.json` and `rerun_result.json`, validates each, and
requires byte-for-byte equality. It does not call or edit shared runners.

## Evidence Boundary

QICS is load-bearing: all nine accepted cases must solve, match the independent
spectral calculation, and satisfy the QICS-side contraction checks. The
spectral calculation cannot substitute for a failed or absent QICS solve.

The ceiling is the fixed finite packet only. Promotion, formal admission, and
stage movement are false. Blocked consumers are listed in `spec.json` and both
result files.
