# Builder Self-Assessment: manifold_dynamic_chart_v2

## Status

Builder verdict: `implemented_for_local_validation`.

Ceiling: `scratch_diagnostic_axis0_experiment_v2_no_admission`.

This packet is the Axis-0 EXPERIMENT v2 stability-axis sweep requested by the card. It is not Axis-0 admission, bridge admission, final substrate choice, or formal/canonical evidence.

## What The Builder Claims

- The v0 density-state machinery is reused on the same Family A 33-cell carrier.
- The v0 regression corner is explicit and must reproduce `32/33 SPREAD`.
- The v1 anchor corner is explicit and must reproduce `amplitude_kicks/weak/shell_boundary/T=12/recovery_return_time`.
- The sweep grid covers the four v1 perturbation families plus projective purity resets, four strengths, three targets, relaxation-calibrated windows, and four classifiers.
- The relaxation windows are computed from the unperturbed generator-family transition spectrum before the sweep.
- The shell-weighted TV classifier is tested as a density-derived classifier, not as a label proxy.
- The agreement-threshold ladder tests common sign structure across families.
- Every grid row emits class distribution, majority baseline, best nonidentity predictor, stability count, negative-control verdict, and criterion verdict.
- The criterion string is in source and result: a candidate readout earns only if it beats the majority baseline, is stable across `>=2` perturbation families, and the negative controls fail it.
- Per-family perturbation bite gates refuse dead rows instead of smoothing them into results.
- G.2a idempotency-from-birth is implemented through `scripts/builder_audit_boundary.py`.

## Known Limits

- This remains chart-relative and coarse.
- The packet does not compute `Xi`, `rho_AB`, conditional entropy, coherent information, or shell-cut entropy.
- A row marked `EARNS_CANDIDATE_READOUT`, if any, is still only scratch diagnostic evidence under this carrier and grid.
- A `no_separation_anywhere` result would be an honest finding about this carrier/dynamics, not a theorem about Axis-0 generally.

## Builder/Audit Boundary

The builder did not write `audit_verdict.md`.

Independent audit can be added later without breaking the validator if its header declares independent/fresh/read-only audit status, per G.2a.
