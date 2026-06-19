# manifold_unified_run_v0 build card

classification: `scratch_diagnostic`
promotion_allowed: `false`
formal_admission_allowed: `false`
mode: `RATCHETED`

Scope: one bounded unified scratch run over the committed integrated n=3 seed. The run applies one sequence, `leaf-conditioning -> lens quotient -> terrain restriction`, over one persisted step-trajectory artifact. Step-dependent families are recomputed per step; step-invariant families are carried with a stated justification that the conditioned object is unchanged for that layer at that step. This packet does not claim every layer family is freshly recomputed at every step.

Step-dependent families: `s2_geometry`, `s5_s6_terrain_flow`, `flux_continuity`, `entropy_ledger_row`, and `deformation_mode`.

Step-invariant families: `s3_density_probe`, `spinor_signed_rows`, `s5_s6_leakage_rows`, and `s6_taxonomy`.

Primary parents:

- `terrain_spinor_flux_nest_n3_v0` at commit hint `1b36e4a3c`
- `manifold_entropy_ledger_v0` at commit hint `a54224476`
- `mct_dynamic_deformation_v0` at commit hint `cdf437053`

Fence: no manifold-level admission, no bridge/axis claim, no `M(C,t)` theorem, and no new parent-rigidity theorem. The packet consumes finite rigidity rows from `mct_dynamic_deformation_v0` and only reports local cross-layer consistency and named findings for one simultaneous run.
