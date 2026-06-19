# Provenance - round3_s5_alias_pass_v0

Registry source: `system_v6/receipts/round3_discriminator_registry_20260611.md` at `de44219ed`.

## Quoted S5 Candidate Table

> Round-2 basis: `geo_s5_alternative_flow_families_v0` at `629deafb0`.
> Round-2 killed four broad alternatives while preserving
> `B_hamiltonian_only` as a quotient-level co-survivor that dies at mirror/N01.
>
> Round-3 finite space: committed-adjacent contraction-rotation mixtures and
> coefficient perturbations over the eight terrain ids.

| Candidate id | Finite representative | Closeness | Expected teeth row | Cost |
| --- | --- | --- | --- | --- |
| `S5.R3.0_committed_8` | eight committed terrain generators with source-locked `A,b` rows | control | none; anchor | light-symbolic |
| `S5.R3.1_alpha_mix_rotation_contraction` | convex generator mix `alpha*H + (1-alpha)*D` for `alpha in {1/4,1/2,3/4}` on the four L/R pairs | close mixed contraction-rotation neighbor | mirror structure and N01 full signature | heavy-local |
| `S5.R3.2_committed_coeff_epsilon` | exact coefficient perturbation `epsilon in {1/20,-1/20}` on one load-bearing off-diagonal slot per family | nearest coefficient neighbor | fixed-point/basin and N01 gap | heavy-local |
| `S5.R3.3_nonunital_weak_shift` | committed `A` with `b_z` shift in `{1/20,-1/20}` where validity survives | close non-unital neighbor | validity, fixed point, quotient 56/56 | heavy-local |
| `S5.R3.4_pairwise_LR_mirror_preserver` | finite rows chosen to preserve Se/Ne mirror continuum but perturb Ni/Si frames | mirror-law co-survivor stress | Ni/Si mirror classification | light-symbolic |
| `S5.R3.5_basin_preserving_null` | one deterministic affine family with same fixed point for `Se_Funnel_L` but altered transient rotation | near basin co-survivor | quotient survival plus time-flow/N01 row | heavy-local |

## Quoted Alias Rule

> Alias-detection rule: canonicalize each terrain family as the sorted eight-row
> tuple `(terrain_id, A_exact, b_exact, validity_class, fixed_point_exact,
> mirror_class, N01_signature)` using the source-approved Bloch convention. Exact
> row equality after the documented L/R mirror/convention map is `alias`. Matching
> only quotient `56/56` or a fixed point is `co_survivor`, not alias.

## Quoted Resource Guard

> The round-3 queue must run in two phases per layer:
>
> 1. Light-symbolic alias pass: compute canonical forms, alias classes,
>    co-survivor labels, and representative selection. This phase may include
>    exact symbolic simplification, rational/surd row comparison, graph
>    isomorphism on the finite listed graphs, and source-hash checks.
> 2. Heavy-local discriminator pass: run only for non-alias representatives that
>    remain open after the light pass.
>
> Stop rule: if all representatives in a layer are aliases or already classified
> as known co-survivors by the light pass, do not run a heavy battery for count
> inflation. Write the classification receipt and stop.
