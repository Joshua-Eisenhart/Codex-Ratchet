# BUILD CARD -- engine_16_stage_definition_correspondence_v0

Owner challenge, binding for this packet: "you don't actually have the geometry and operators of each. and don't have them operating. you used jargon and no actual math."

Status: builder packet, not independent audit. Write boundary is `system_v6/sims/engine_16_stage_definition_correspondence_v0/` only. NO git add/commit. Builder must not write `audit_verdict.md`; builder prose goes in `builder_self_assessment.md`.

## Authority

- Current owner card in this session.
- Owner/operator source router: `/Users/joshuaeisenhart/wiki/concepts/igt-axes-terrain-source-extraction-2026-06-04.md`.
- Repo axes/operator router: `system_v6/receipts/doc_router_axes_terrains_operators_20260609.md`.
- Normalized terrain/operator map: `system_v6/receipts/terrain_operator_map_20260609.md`.
- Matrix64 mine: `system_v6/receipts/matrix64_mine_20260610.md`.
- Operator packet source: `system_v5/READ ONLY Reference Docs/operator math explicit.md`.
- Four-operator signed math source: `system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md`.
- Axis 4/5/6 source layout: `system_v5/ops/AXES_TERRAINS_OPERATORS_MANIFOLD_SOURCE_LAYOUT_20260522.md`.
- Prior discovered-16 packet: `system_v6/sims/eng64_stage_fingerprint_ids_v0/` at user-supplied hint `fab7b2253`.
- Prior 64-run: `system_v5/julia_carrier/eng_64_hexagram_julia_results.json` at user-supplied hint `23cfa5536`.
- Axis-4 fixture fence: `system_v6/sims/discrete_axis4_composition_v0/`, especially the `R_x` / `D_z` pin. This is a fixture, not canonical operator-stage admission.
- ECD.01 order-programmability reference: `system_v6/sims/ecd01_order_programmable_computer_v1/`, especially the `U=expm(R_x)` / `E=expm(D_z)` fixture usage.
- Standards codex: `system_v6/receipts/audit_standards_codex_v1.md`.
- Boundary helper: `scripts/builder_audit_boundary.py`.

## G.2a Boundary

G.2a idempotency-from-birth is binding. The validator and packet boundary helper delegate audit verdict handling to `scripts/builder_audit_boundary.py`; they must not hard-code permanent absence of `audit_verdict.md`. The builder result emits `no_builder_audit_verdict=true` and `no_builder_audit_verdict_envelope_gate=true`.

## G7 Definition Pin

Definitions are pinned before correspondence computation. The finite convention is:

1. Carrier: the one-qubit Bloch/density carrier used by `eng64_stage_fingerprint_ids_v0`; the representative input is that packet's `RHO_REPR`.
2. Base operator maps:
   - `Ti = D_z = diag(lambda, lambda, 1)` on Bloch coordinates.
   - `Te = D_x = diag(1, lambda, lambda)`.
   - `Fi = R_x(theta)`.
   - `Fe = R_z(theta)`.
3. Fixture parameters:
   - `lambda = 0.7`, carried from the Axis-4 `D_z` fixture.
   - `theta = pi/2`, carried from the Axis-4 `R_x` fixture.
4. Chirality convention:
   - `L` uses positive rotation angle.
   - `R` uses negative rotation angle.
   - Dephasing maps are chirality-invariant.
5. The 16 defined macro-stage maps are:
   - 2 chirality sheets `L/R`;
   - 2 dissipative T maps `Ti/Te`;
   - 2 rotation F maps `Fi/Fe`;
   - 2 order polarities.
6. Order convention:
   - `+` means T-family dominant: `T o F`.
   - `-` means F-family dominant: `F o T`.

This derives `2 x 2 x 2 x 2 = 16` finite maps. It is a proposal-level macro-stage definition. Where the owner sources underdetermine the exact chirality sign and the T/F pairing convention, this card pins them as a finite convention before any match result is computed.

## Required Computation

1. Emit every stage token as an explicit finite map:
   - base operators;
   - signed pair;
   - 3x3 Bloch matrix;
   - 4x4 affine channel matrix on `[1,x,y,z]`;
   - output density matrix on the representative carrier.
2. Emit geometry rows:
   - fixed-point subspace;
   - eigenvalues;
   - singular values;
   - determinant and spectral radius;
   - moved Bloch directions;
   - purity and von Neumann entropy effect.
3. Correspondence test:
   - compute each defined stage fingerprint by the exact `eng64_stage_fingerprint_ids_v0` machinery: flatten output `rho` to 8 real/imag floats, round by `FP_TOL=1e-7`, and hash to an `eng64_fp_*` ID;
   - compare the defined-16 fingerprint set to the discovered-16 component set;
   - emit the full 16x16 match matrix.
4. Emit the defined-stage non-equivalence matrix:
   - exact fingerprint alias/distinct status for every pair;
   - numeric fingerprint distance matrix.
5. Controls:
   - erase order polarity: both order variants use the same unordered `T o F` convention, and the 16 rows collapse toward 8;
   - erase chirality: L/R paired rows merge;
   - scramble operator assignments: deterministic operator remap must not improve correspondence;
   - identity stages: all stages collapse to 1.

## Fences

- `classification=scratch_diagnostic`.
- `promotion_allowed=false`.
- `formal_admission_allowed=false`.
- `claim_ceiling=macro_stage_definition_correspondence_proposal_only`.
- This packet does not admit engine stages.
- This packet does not claim Matrix64, QIT-engine, axis, bridge, manifold, physics, or consciousness admission.
- The substage convention remains unpinned. This packet is macro-stage-level only.
- The `R_x/D_z` fixture fence is carried.
- The `eng64` 64-run remains realization-relative and has no slot semantics admitted by this packet.
- Either correspondence outcome is valid: a match would support this realization-level proposal; a mismatch names aliases and missing counterparts.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_16_stage_definition_correspondence_v0/engine_16_stage_definition_correspondence_v0.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_16_stage_definition_correspondence_v0/engine_16_stage_definition_correspondence_v0_jax.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_16_stage_definition_correspondence_v0/engine_16_stage_definition_correspondence_v0_pytorch.py
julia --project=/Users/joshuaeisenhart/.local/share/sim-stack/julia_env system_v6/sims/engine_16_stage_definition_correspondence_v0/engine_16_stage_definition_correspondence_v0_julia.jl
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_16_stage_definition_correspondence_v0/engine_16_stage_definition_correspondence_v0_envelope.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_16_stage_definition_correspondence_v0/validate_engine_16_stage_definition_correspondence_v0.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/engine_16_stage_definition_correspondence_v0/results/engine_16_stage_definition_correspondence_v0_envelope_results.json
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/engine_16_stage_definition_correspondence_v0/tests
```
