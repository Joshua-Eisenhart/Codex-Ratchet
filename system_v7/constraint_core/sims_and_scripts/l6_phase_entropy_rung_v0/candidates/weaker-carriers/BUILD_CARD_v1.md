# Build card v1 — weaker-carriers candidate family (l6_phase_entropy_rung_v0)

Lane: CANDIDATE FAMILY weaker-carriers. Deliberately WEAK non-entropic carriers that any
entropy-typed candidate must beat: raw phase-sign lookups, single-bit readouts, constant baselines.

## Hard rules (binding)

- Work ONLY inside `/Users/joshuaeisenhart/Codex-Ratchet/system_v7/constraint_core/sims_and_scripts/l6_phase_entropy_rung_v0/candidates/weaker-carriers/`.
- NEVER delete, move, or modify any existing file anywhere in the repo. Read other constraint_core files read-only.
- NO gate logic anywhere: no survivor/frontier/minimality adjudication, no verdicts about the rung.
  Emit values, deltas, sign predictions, and alias groups only.
- Deterministic: seed 0 everywhere a seed is possible (no randomness is actually needed).
- Every output JSON carries `"classification": "scratch_diagnostic"` and `"promotion_allowed": false`.
- Float comparisons are tolerance-based, never `==`.

## Inputs (read-only)

- Surface rows: `/Users/joshuaeisenhart/Codex-Ratchet/system_v7/constraint_core/sims_and_scripts/l6_phase_entropy_rung_v0/surface/surface_v1.json`
  - Use `row_blocks.fixture_observations` — 18 rows, fields per row:
    `row_id` (0..17), `radial_index` (0..8), `orientation` (±1), `a`, `chern_signed`,
    `entropy_bits`, `negativity`, `purity`, `shell_radius`.
- Demanded edge families: `/Users/joshuaeisenhart/Codex-Ratchet/system_v7/constraint_core/sims_and_scripts/l6_phase_entropy_rung_v0/surface/demand_families_v1.json`
  - `families.{factorization_boundary(16), marginal_entropy_level(72), orientation_winding(9), shell_position(72)}`,
    each edge has `row_i`, `row_j` (row_ids into fixture_observations).
- Record sha256 of both input files in every output.

## Deliverables (all in the lane directory)

1. `variants_v1.json` — the declared variant roster (data file, shared by all legs). Schema below.
2. `julia_leg.jl` — Julia engine leg. Run as:
   `JULIA_PROJECT=$HOME/.julia/environments/v1.12 /opt/homebrew/bin/julia julia_leg.jl <surface_path> <variants_path> <out_path>`
   Uses JSON3 + LinearAlgebra. Computes, per variant, the functional value for each of the 18 rows in Float64,
   implementing each subfamily formula NATIVELY in Julia (no shelling out to python, no reading precomputed values).
   Writes `julia_values_v1.json`: `{"leg":"julia","julia_version":...,"values":{variant_id:[18 floats in row_id order]}}`.
3. `jax_leg.py` — JAX engine leg. Must set `JAX_ENABLE_X64=1` (via os.environ before importing jax, and also honor env).
   Interpreter: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`. Implements every subfamily formula with
   jax.numpy ops (`jnp.where`, `jnp.sign`, `jnp.mod`, ...) on float64 device arrays — NOT plain-python arithmetic.
   Writes `jax_values_v1.json` (same shape, plus `"x64_enabled": true` asserted from `jax.config`).
4. `torch_leg.py` — Torch engine leg, same interpreter. All row fields as `torch.tensor(..., dtype=torch.float64)`;
   formulas via torch ops (`torch.where`, `torch.sign`, `torch.fmod`, ...). Writes `torch_values_v1.json`.
5. `numpy_control.py` — comparison-only control leg (numpy float64). Writes `numpy_control_values_v1.json`.
   It is NOT one of the three engines; label it `"role": "control_comparison_only"`.
6. `compiler.py` — orchestrator, same interpreter. It:
   - loads surface + demand families, sha256s them;
   - invokes the four legs as SUBPROCESSES (julia via the exact command above; python legs via the sim-stack interpreter),
     or accepts `--skip-run` to reuse existing leg output files;
   - assembles `behavior_v1.json` (schema below);
   - computes per-variant `cross_substrate_max_delta` = max over rows of max pairwise |Δ| among the THREE engine legs
     (julia, jax, torch), and separately `numpy_control_max_delta` = max over rows/engines |engine − numpy_control|;
   - computes induced sign predictions per demanded edge family: for edge (i,j),
     `sign = 0 if |F_j − F_i| <= 1e-12 else (+1 if F_j > F_i else −1)`, using the JULIA leg values as the stated
     prediction source (`"sign_source_leg": "julia"`), and records `legs_sign_agreement` per family = whether all
     three engine legs induce the identical sign array (boolean — data, not verdict);
   - computes alias groups: `value_aliases` = groups of variants whose julia per-row value vectors match within 1e-12
     componentwise; `sign_profile_aliases` = groups whose full induced-sign profiles (all four families) are identical;
   - PRINTS to stdout exactly two headline lines at the end:
     `VARIANT_COUNT: <n>` and `WORST_CROSS_SUBSTRATE_DELTA: <float>`;
   - writes `behavior_v1.json` (append-only versioning: never overwrite a different existing version; v1 is new here).

## Variant roster (all must be implemented in ALL four legs, keyed by variant_id)

Subfamily `raw_phase_sign_lookup` (non-entropic raw lookups):
- `W01_orientation_lookup`: F = orientation
- `W02_chern_sign_lookup`: F = sign(chern_signed)
- `W03_chern_raw_lookup`: F = chern_signed

Subfamily `single_bit_readout` (F in {0.0, 1.0}; strict inequalities as written):
- `W04_entropy_bit_thr050`: F = 1 if entropy_bits > 0.5 else 0
- `W05_entropy_bit_thr010`: F = 1 if entropy_bits > 0.1 else 0
- `W06_entropy_bit_thr090`: F = 1 if entropy_bits > 0.9 else 0
- `W07_negativity_bit`: F = 1 if negativity > 0.0 else 0
- `W08_purity_bit_thr075`: F = 1 if purity < 0.75 else 0
- `W09_radius_bit_thr050`: F = 1 if shell_radius > 0.5 else 0
- `W10_radial_parity_bit`: F = radial_index mod 2 (as float)
- `W11_orientation_bit`: F = 1 if orientation > 0 else 0
- `W12_radial_msb_bit`: F = 1 if radial_index >= 4 else 0
- `W13_a_bit_thr_pi8`: F = 1 if a > pi/8 else 0 (pi from the substrate's own constant)

Subfamily `constant_baseline`:
- `W14_constant_zero`: F = 0
- `W15_constant_one`: F = 1

`variants_v1.json` schema: `{"schema_version":"l6_phase_entropy_weaker_carriers_variants/1.0",
"classification":"scratch_diagnostic","promotion_allowed":false,
"variants":[{"variant_id","subfamily","parameters":{...},"formula":"<one-line human formula>"}]}`.
Parameters must carry every numeric threshold explicitly (e.g. `{"field":"entropy_bits","threshold":0.5,"direction":">"}`).

## behavior_v1.json schema

```
{
  "schema_version": "l6_phase_entropy_weaker_carriers_behavior/1.0",
  "classification": "scratch_diagnostic",
  "promotion_allowed": false,
  "lane": "candidates/weaker-carriers",
  "family_intent": "deliberately weaker non-entropic carriers that entropy-typed candidates must beat; values and predictions only, no gate logic",
  "seed": 0,
  "sources": {"surface_v1.json": {"path","sha256"}, "demand_families_v1.json": {"path","sha256"}},
  "engines": {"julia": {...versions/env...}, "jax": {...,"x64_enabled":true}, "torch": {...,"dtype":"float64"},
              "numpy_control": {..., "role":"control_comparison_only"}},
  "row_ids": [0..17],
  "sign_tie_tolerance": 1e-12,
  "variants": [
    {"variant_id","subfamily","parameters","formula",
     "per_row_values": {"julia":[18],"jax":[18],"torch":[18],"numpy_control":[18]},
     "cross_substrate_max_delta": float, "numpy_control_max_delta": float,
     "sign_source_leg": "julia",
     "induced_sign_predictions": {"factorization_boundary":[{"row_i","row_j","sign"}x16],
       "marginal_entropy_level":[x72], "orientation_winding":[x9], "shell_position":[x72]},
     "legs_sign_agreement": {"factorization_boundary":bool, ...}}
  ],
  "alias_groups": {"value_aliases":[[variant_ids]...], "sign_profile_aliases":[[variant_ids]...]},
  "summary": {"variant_count": int, "worst_cross_substrate_delta": float,
              "worst_numpy_control_delta": float}
}
```

## Verification commands (run these; all must exit 0)

```
cd /Users/joshuaeisenhart/Codex-Ratchet/system_v7/constraint_core/sims_and_scripts/l6_phase_entropy_rung_v0/candidates/weaker-carriers
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 compiler.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -c "import json; b=json.load(open('behavior_v1.json')); assert b['summary']['variant_count']==15; assert b['summary']['worst_cross_substrate_delta']<1e-9; assert all(len(v['per_row_values'][k])==18 for v in b['variants'] for k in ('julia','jax','torch','numpy_control')); assert all(len(v['induced_sign_predictions']['orientation_winding'])==9 for v in b['variants']); print('SHAPE_OK')"
```

If the julia subprocess fails under your sandbox (e.g. cannot write its compile cache), do NOT fake or copy its
values from another leg: leave the leg script correct, report the sandbox failure, and stop — the verifier will run
it outside the sandbox. Never substitute one leg's numbers for another's.

## STOP condition

STOP when the six deliverable files exist, `compiler.py` has been run (or run to the point the sandbox allows),
the two verification commands pass (or the julia-sandbox exception above is reported), and the two headline lines
(`VARIANT_COUNT`, `WORST_CROSS_SUBSTRATE_DELTA`) have been printed. Do not expand the variant roster beyond W01–W15,
do not touch any file outside the lane directory, do not write any additional markdown reports.
