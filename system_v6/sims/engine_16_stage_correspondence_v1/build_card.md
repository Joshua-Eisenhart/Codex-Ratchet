# BUILD CARD -- engine_16_stage_correspondence_v1

Status: builder packet, not independent audit. Write boundary is `system_v6/sims/engine_16_stage_correspondence_v1/` only. NO git add/commit. Builder must not write `audit_verdict.md`; builder prose goes in `builder_self_assessment.md`.

## Authority

- Current owner build card in this session.
- Registered hypothesis: `system_v6/receipts/ratchet_geometry_order_hypothesis_20260612.md`, commit hint `c74e2db99`.
- First parked proposal/baseline: `system_v6/sims/engine_16_stage_definition_correspondence_v0/`; its baseline result is `MISMATCH`, `0/16` exact matches, 12 defined components.
- Fingerprint reference: `system_v6/sims/eng64_stage_fingerprint_ids_v0/`, commit hint `fab7b2253`; its hash method is reused unchanged.
- Terrain source estate: `system_v6/sims/geo_s5_terrain_flows_v0/` and source docs named in that packet. This packet consumes the generator rows as pinned scratch source, not as S5 canonical completion.
- GCM substrate registry: `system_v6/sims/gcm_object_id_freeze_v0/results/gcm_object_id_freeze_v0_registry.json`.
- Standards codex: `system_v6/receipts/audit_standards_codex_v1.md`.
- Boundary helper: `scripts/builder_audit_boundary.py`.
- Substrate helper: `scripts/gcm_substrate_check.py`.

## Declaration

- layer: `15 ordered compositions`
- integration: `integrated-onto-the-carve`
- carrier floor: `1Q`
- classification: `scratch_diagnostic`
- claim ceiling: `hypothesis_test_only`
- promotion allowed: `false`
- formal admission allowed: `false`

## G.2a Boundary

G.2a idempotency-from-birth is binding. The validator and packet boundary helper delegate audit verdict handling to `scripts/builder_audit_boundary.py`; they must not hard-code permanent absence of `audit_verdict.md`. The builder result emits `no_builder_audit_verdict=true` and `no_builder_audit_verdict_envelope_gate=true`.

## Substrate-First Pin

Every accepted result must pass `scripts/gcm_substrate_check.py` with:

- `gcm_object_id=gcmobj_a40e54e13cec01466c9d675028b3574b`
- `registry_body_sha256=0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`
- at least one real frozen survivor, quotient class, or candidate-region lineage id.

The packet also emits a lineage-free negative JSON. That negative must fail the substrate helper; a green lineage-free negative invalidates the packet.

## G7 Definition Pin

Definitions are pinned before correspondence computation.

### Four Terrain Flow Realizations

The owner hypothesis names four `T_tau` maps on `D(C^2)`. The committed S5 terrain estate has eight sheeted generator rows, so this packet pins one finite-time generator per terrain before scoring:

| `T_tau` | hypothesis role | committed generator row | source ref | finite-time pin |
|---|---|---|---|---|
| `T_Se` | expansion-family terrain | `Se_Funnel_L` | `terrain math.md:76` | `exp(t X_Se)` at `t=1` |
| `T_Ne` | circulation terrain | `Ne_Vortex_L` | `terrain math.md:78` | `exp(t X_Ne)` at `t=1` |
| `T_Ni` | contraction/attractor terrain | `Ni_Source_R` | `terrain math.md:81` | `exp(t X_Ni)` at `t=1` |
| `T_Si` | retention/strata terrain | `Si_Citadel_R` | `terrain math.md:83` | `exp(t X_Si)` at `t=1` |

This is a hypothesis realization choice. It is not terrain-family canon. The measured finite map character is emitted per row so labels cannot substitute for the actual affine map.

### Native Pairing Convention

The owner-forwarded convention is pinned verbatim:

- `Ti <-> D_z`
- `Te <-> D_x`
- `Fi <-> R_x`
- `Fe <-> R_z`
- `Se/Ne` are native to the z-side maps.
- `Ni/Si` are native to the x-side maps.

Fixture values:

- dephasing/contraction parameter `lambda = 0.7`
- rotation angle `theta = pi/2`
- terrain flow time `t = 1`

### Required 16-Row Table

Build exactly these ordered compositions:

| Stage | Composition |
|---|---|
| `TiSe` | `T_Se o D_z` |
| `SeTi` | `D_z o T_Se` |
| `FiSe` | `T_Se o R_x` |
| `SeFi` | `R_x o T_Se` |
| `TiNe` | `T_Ne o D_z` |
| `NeTi` | `D_z o T_Ne` |
| `FiNe` | `T_Ne o R_x` |
| `NeFi` | `R_x o T_Ne` |
| `TeNi` | `T_Ni o D_x` |
| `NiTe` | `D_x o T_Ni` |
| `FeNi` | `T_Ni o R_z` |
| `NiFe` | `R_z o T_Ni` |
| `TeSi` | `T_Si o D_x` |
| `SiTe` | `D_x o T_Si` |
| `FeSi` | `T_Si o R_z` |
| `SiFe` | `R_z o T_Si` |

## Required Computation

1. Emit the four terrain flows as explicit affine maps on Bloch coordinates and density matrices.
2. Emit all 16 compositions as explicit affine channel matrices and output density matrices.
3. Apply the `eng64_stage_fingerprint_ids_v0` fingerprint method unchanged:
   - apply the stage channel to the same representative `RHO_REPR`;
   - flatten output `rho` row-major as real/imag pairs;
   - round by `FP_TOL=1e-7`;
   - hash with `eng64.component_id_for_fingerprint`.
4. Emit the 16x16 match matrix against the discovered-16 component IDs.
5. Emit the hypothesis verdict:
   - `full_bijection`
   - `partial` with failing stage pairings named
   - `0-match_again`
6. Emit the diff against `engine_16_stage_definition_correspondence_v0`: changed stage math, score movement, and which changes moved the needle.
7. Controls:
   - order-erasure: unordered pair composition must collapse the 16 toward 8;
   - pairing-scramble: a wrong-pairing variant must score worse, or the result must explicitly report that the pairing convention is doing nothing;
   - label-permutation invariance: label changes must not affect fingerprints;
   - commuting-pair honest-null: where `T_tau` and `O` commute, the two orders are the same stage and must be reported as such, not forced to 16.

## Fences

- This packet is a scratch diagnostic hypothesis test only.
- No stage admission either way.
- No Matrix64 admission.
- No QIT-engine admission.
- No axis, bridge, manifold, physics, or target-system claim.
- Either correspondence outcome is the result. The builder must not tune after seeing the match matrix.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_16_stage_correspondence_v1/engine_16_stage_correspondence_v1.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_16_stage_correspondence_v1/engine_16_stage_correspondence_v1_jax.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_16_stage_correspondence_v1/engine_16_stage_correspondence_v1_pytorch.py
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/engine_16_stage_correspondence_v1/engine_16_stage_correspondence_v1_julia.jl
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_16_stage_correspondence_v1/engine_16_stage_correspondence_v1_envelope.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_16_stage_correspondence_v1/validate_engine_16_stage_correspondence_v1.py
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_substrate_check.py system_v6/sims/engine_16_stage_correspondence_v1/results/engine_16_stage_correspondence_v1_envelope_results.json
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/engine_16_stage_correspondence_v1/results/engine_16_stage_correspondence_v1_envelope_results.json
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/engine_16_stage_correspondence_v1/tests
```
