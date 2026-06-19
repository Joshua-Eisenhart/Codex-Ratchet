# Missing-Things Audit 2026-06-10

Status: read-lane audit receipt.

Read discipline: `geo_s3`, `geo_s4`, `geo_s5`, `geo_s6`, `geo_s7`, and ladder-related packet evidence were read from committed content with `git show HEAD:<path>`. Live-tree reads were only used for repo listing/status and non-mutating audit commands outside those active mutation lanes.

Scope: committed geometry estate under `system_v6/sims/geo_*`, the named reconciliation packets `mct_*`, `bloch_root_admissibility_discriminator_v0`, `dual_stack_carnot_szilard_hopf_weyl_probe`, `spinor_network_hopf_weyl_testbed`, and committed ladder/formal-scout surfaces when the audit question named gamma splits or nested Hopf/Weyl lineage.

Checks used:

- `git ls-tree -r --name-only HEAD ...` to build the committed path set.
- `git show HEAD:<path>` for active geometry packet source/results.
- Envelope source inspection for gate derivation.
- A direct path/hash verifier over committed JSON result pairs: 179 explicit `*_path`/`*_sha256` checks, 177 matched committed bytes, 2 were external `/tmp` source links.

Severity key: HIGH can invalidate reproducibility or cross-packet reuse; MEDIUM is a real gap but bounded by current scratch/diagnostic ceilings; LOW is a clarity or automation gap with local evidence intact.

## Executive Findings

| Class | Severity | Finding |
| --- | --- | --- |
| M1 seed/determinism | HIGH | RNG packets pin seeds in source but do not declare those seeds in result/PIN surfaces. Byte-stable reruns are source-stable, not receipt-stable. |
| M2 envelope gate honesty | MEDIUM | No in-scope envelope was pure `all_pass=true` transcription. Most gates are computed over leg data. S7 has a meta-gate weakness: `cross_engine_fatality` duplicates prior gate truth instead of running an independent fatality comparison. |
| M3 convention ledger | HIGH | Bloch `r_y`, holonomy, entropy, and S2/S6/S7 area conventions are pinned. Octonion table orientation is not estate-reconciled between Bloch and MCT nonassoc/weld packets. |
| M4 value reconciliation | MEDIUM | `h(eta)`, torus areas, and gamma splits agree where mappings are explicit. Quotient counts across MCT/Bloch/lens are not comparable without a missing convention map. |
| M5 control coverage | HIGH | Local can-fail controls are strong, but no estate-wide controls cover stochastic seed declaration, cross-packet convention maps, quotient-count reconciliation, or lineage-source availability. |
| M6 lineage graph | HIGH | Committed direct source/artifact hashes mostly verify. Broken/unverifiable links remain: two `/tmp` directive sources, MCT wiki source refs without committed hash capture, and a missing canon artifact receipt path while its carrier artifact/source bytes do verify. |

## M1 Seed And Determinism

Packets with sampling or Monte Carlo:

| Packet | Sampling present? | RNG seed declared in result/PIN? | Rerun reproducibility mechanism | Severity |
| --- | --- | --- | --- | --- |
| `geo_s1_exact_closure_v0` | Yes; Haar/non-Haar diagnostic samples. | No. Seeds are only in source: `60611`, `60612`, `60613`, plus seeded Gaussian helper. | Pinned source hash plus hardcoded `jax.random.PRNGKey(...)`; no result-level seed ledger. | HIGH |
| `geo_s1_finite_phase_lens_v0` | Yes; Haar orbit samples and Monte Carlo volume comparison. | No. Seeds are only in source: `60217`, `60218`, `70_000+n`, `70217`. | Pinned source hash plus source-level JAX/Torch seed calls; no result-level seed ledger. | HIGH |
| `geo_s1_quaternion_model_v0` | Yes; Haar quaternion samples and path samples. | No. Seed parameter is in source helper, not emitted in result/PIN. | Pinned source hash plus source helper `haar_quaternions(n, seed)`; result does not expose seed list. | HIGH |
| `geo_s1_spinor_hopf_free_v0` | Yes; dense samples and clustered controls. | No. Seeds are only in source: `10_000+n`, `55`, `56`, `57`. | Pinned source hash plus source-level `PRNGKey(...)`; no result-level seed ledger. | HIGH |
| `bloch_root_admissibility_discriminator_v0` | Deterministic pseudo-sampling over finite seed indices. | Partly. `seed` exists as deterministic function input, but no result-level sampling ledger. | Recomputed from deterministic `unit_vector(dim, seed)` style loops, not RNG state. | LOW |

Packets with sample wording but no RNG dependency:

| Packet/group | Finding |
| --- | --- |
| `geo_s1_two_qubit_boundary_exact_v0`, `geo_s1_three_qubit_floor_exact_v0`, `geo_s1_four_qubit_support_exact_v0`, `geo_s1_five_qubit_safety_margin_exact_v0`, `geo_s1_scaling_stress_678q_exact_v0` | Exact finite labels/states or algebraic stress rows; no RNG seed required. |
| `geo_s2_connection_flux_foliation_v0`, `geo_s3_density_observable_v0`, `geo_s4_operator_stage_v0`, `geo_s5_terrain_flows_v0`, `geo_s6_stacked_flows_hopf_v0`, `geo_s7_discrete_refinement_v0` | Deterministic symbolic rows, finite grids, exact validators, or discrete convergence curves; no RNG seed required. |
| `mct_dynamic_admissibility_packet_v0`, `mct_nonassoc_weld_packet_v0`, `dual_stack_carnot_szilard_hopf_weyl_probe`, `spinor_network_hopf_weyl_testbed` | Deterministic finite fixtures or pinned constants; no RNG seed required for committed result values. |

Conclusion: RNG packet values were reproduced through pinned source, not through a receipt-declared seed mechanism. This is a pinned-undeclared gap, not evidence of copied H-pattern values.

## M2 Envelope Gate Honesty

| Envelope packet | Gate source | Classification | Notes |
| --- | --- | --- | --- |
| `geo_s2_connection_flux_foliation_v0` | `all_pass = all(gates.values())` over engine leg pass, exact controls, copied inputs, source hash, and ceiling fields. | Computed gate | Honest envelope aggregation. |
| `geo_s3_density_observable_v0` | `all_pass = all(gates.values())` over engine legs, conventions, alternatives, controls, source hash, and required receipts. | Computed gate | Honest envelope aggregation. |
| `geo_s4_operator_stage_v0` | `all_pass = all(gates.values())` over leg data, basis conversion, source receipts, SMT scope, and no-peer-read gates. | Computed gate | Honest envelope aggregation. |
| `geo_s5_terrain_flows_v0` | `all_pass = all(gates.values())` over leg data, generator consistency, flow round-trip, controls, cross-engine row agreement, and source locks. | Computed gate | Honest envelope aggregation. |
| `geo_s6_stacked_flows_hopf_v0` | `all_pass = all(build_gates.values())` over engine legs, cross-engine signature, loop-order controls, matrix/placement counts, copied inputs, and source hash. | Computed gate | Honest envelope aggregation. |
| `geo_s7_discrete_refinement_v0` | `all_pass = all(gates.values())`; most gates computed from leg data, exact validators, interval certs, curves, and source hashes. | Computed with weak meta-gate | `cross_engine_fatality` is set to `all(value is True for key,value in gates.items() if key != "cross_engine_fatality")`; this duplicates previous gate truth instead of independently comparing fatal signatures. |
| `mct_dynamic_admissibility_packet_v0` | Boolean conjunction over leg pass, gates present/pass, all controls fired, ceiling, presentation receipts, defaults, sheet/quotient checks, and source hash. | Computed gate | Honest envelope aggregation; already notes future validator gaps. |
| `mct_nonassoc_weld_packet_v0` | Boolean conjunction over leg pass, carrier artifact/provenance, controls, ceiling, and source hash. | Computed gate | Honest envelope aggregation; canon receipt path gap is lineage, not all_pass transcription. |
| `bloch_root_admissibility_discriminator_v0` | Boolean conjunction over leg pass, T checks, source hash presence, carrier artifact, and controls. | Computed but leg-trusting | Gate is not transcription, but some strength comes from leg-level all_pass rather than recomputing every scalar in envelope. |
| `dual_stack_carnot_szilard_hopf_weyl_probe`, `spinor_network_hopf_weyl_testbed` | Boolean conjunction over leg pass, controls, pins, source hashes, and no-peer-read gates. | Computed but compact | Acceptable for bounded packets; not an estate-level convention reconciliation gate. |

## M3 Cross-Packet Convention Ledger

| Convention axis | Committed pins found | Cross-packet status |
| --- | --- | --- |
| Bloch `r_y` sign | S1/S3 pin `bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)` and `Hopf_y=+2Im(z1*conj(z2))`. S4/S5 use `source_locked_standard_bloch=(sigma_x,sigma_y_standard,sigma_z)` with `J=diag(1,-1,1)` conversion into S1 pinned basis. | Locally consistent when `J` is carried. MEDIUM risk for any consumer that reads S4/S5 rows as S1-pinned without conversion. |
| Orientation and Stokes sign | S2 pins `F=-2*sin(2*eta)deta wedge dchi`, physical integral `-2*pi`, and `c1=1`. S7 pins Stokes as `h(eta_j)-h(eta_i)+Phi_ij=0`. | Consistent across S2/S6/S7. |
| Holonomy sense | S2 distinguishes accumulated `phi`, endpoint global spinor phase, and Berry phase. S6 imports `h_eta=-2*pi*cos(2*eta)` and lifted chart base-loop count. S7 uses the same target. | Consistent where explicit. |
| Rotation handedness | S4 pins `R_x`, `R_z` in standard Bloch basis; S5 pins `H0=(sigma_x+sigma_y+sigma_z)/sqrt(3)`, `H_L=+H0`, `H_R=-H0`; both carry `J` conversion. | Locally pinned. No cross-packet contradiction found. |
| Entropy base | S3 hardens primary entropy to natural log `e` / nats, with log2 bits marked auxiliary. MCT dynamic records entropy in nats for `H_Q`/`A_Q`. | Consistent for primary values; auxiliary bits are labelled. |
| Octonion table orientation | Bloch root carries `octonion_permutation_old_to_new=[0,3,2,1,6,7,4,5]`, signs `[1,-1,1,1,-1,-1,1,-1]`, and sedenion lift rule over both halves. MCT nonassoc weld carries committed basis lift `perm=[0,1,2,3,4,7,6,5]`, signs `[1,1,1,1,1,-1,1,-1]`, bracket convention `left`. | HIGH gap: both are explicit, but no committed estate ledger proves these two orientation maps are mutually reconciled or intentionally different. |

## M4 Cross-Packet Value Reconciliation

| Quantity | Packets compared | Result |
| --- | --- | --- |
| `h(eta)` | S2, S6, S7 | Agreement under the pinned formula `h(eta)=-2*pi*cos(2*eta)`. S2 rows give `-sqrt(3)*pi`, `-pi`, `0`, `pi`, `sqrt(3)*pi`; S6 imports the same pin; S7 uses the same target/Stokes sign. |
| Torus physical area | S2, S7 | Agreement. S2 pins `physical_area=2*pi**2*sin(2*eta)`. S7 `area_target` rows match: `pi^2` at `pi/12` and `5*pi/12`, `sqrt(3)*pi^2` at `pi/6` and `pi/3`, `2*pi^2` at `pi/4`, `sqrt(2)*pi^2` at `pi/8` and `3*pi/8`. |
| S7 convergence | S7 internal | No target divergence. Coarse residuals are not monotone for every eta; rate claims must stay bounded to fitted discrete convergence, not exact monotone convergence. |
| Quotient counts | MCT dynamic, lens packet, Bloch root | Not directly comparable. MCT dynamic has support size `384`, class count `24` without phase/carrier retained, and `192` with phase included. Lens rows count phase-orbit samples/orbits over `N`. Bloch root counts base/fiber dimensions and finite nonassoc/Fano witnesses. Missing convention map prevents honest numeric diff. |
| Gamma/chirality splits | S1 scaling stress, S3 directive/addendum, ladder formal-scout surfaces | Agreement at formula level: chirality split is `2^(n-1)+2^(n-1)`, with `gamma5` split `2+2` and rungs `6 -> 32+32`, `7 -> 64+64`, `8 -> 128+128`. |

## M5 Control-Coverage Matrix

| Claim class | Can-fail controls found | Gap |
| --- | --- | --- |
| Bloch density/observable identities | Wrong `sigma_y`, nonlinear expectation echo, wrong fidelity convention, commuting probe simplex, bad measurement update, non-CPTP expansive controls. | No estate-wide convention ledger gate; consumers can still mix S1-pinned and standard Bloch basis without a global check. |
| Connection/holonomy/Stokes/area | Wrong sign/orientation controls, exact SMT Stokes checks, lifted/base loop distinction, interval/exact-strength validators, S7 discrete convergence. | S7 cross-engine fatality meta-gate is not independent. |
| Operator/channel/terrain stages | Basis conversion controls, source-locked row checks, generator derivation, flow round-trip, hardcoded/source echo controls, basin/orbit negative controls. | Good local coverage; cross-packet reuse still relies on carrying `J` and source-locked basis labels. |
| Stacked loop/order/terrain action | U/E loop order controls, commuting zero-gap control, noncommuting positive gap, Uhlmann-smuggle boundary, Matrix64 overlay counts. | No new mixed holonomy admitted; coverage is bounded to restricted/stacked finite packet. |
| Quotient/admissibility packets | Label shuffle, quotient erasure, phase inclusion/exclusion, presentation-coordinate receipts, nonfree-action diagnostics. | No cross-family quotient-count reconciliation control across MCT/lens/Bloch. |
| Nonassoc/octonion/sedenion table use | Orientation flip controls, alternativity controls, sedenion norm-law failure, raw artifact witness, source artifact hashes. | No estate-level octonion orientation map reconciliation between Bloch and MCT weld. |
| Gamma/chirality/rung splits | Representation bounds, corrupted gamma signs, finite Pauli extension checks, formal scout gate shape. | Local agreement found; no single cross-packet reconciliation gate yet. |
| Stochastic/sample diagnostics | Source-pinned seeds in RNG packets; exact routes demote sample rows where appropriate. | HIGH uncovered class: no result/PIN seed ledger or byte-recompute seed manifest for RNG packets. |
| Lineage/source availability | Direct source/artifact hashes in most result JSONs. | External `/tmp` directive links, wiki source refs without committed hash capture, and missing canon receipt path remain. |

Uncovered claim classes:

1. Estate-wide seed declaration and byte-recompute control for stochastic diagnostics.
2. Estate-wide convention-map control for Bloch sign, holonomy sense, rotation handedness, entropy base, and octonion orientation.
3. Cross-packet quotient-count reconciliation control.
4. Direct lineage availability control for every cited source ref, including wiki and temporary directive sources.
5. Independent envelope meta-gate control for fatal cross-engine comparison.

## M6 Lineage Graph

Direct committed path/hash verifier result: 179 explicit path/hash pairs checked; 177 matched committed bytes; 2 were external `/tmp` directive source links and cannot be verified from committed content.

| Link class | Status | Severity | Finding |
| --- | --- | --- | --- |
| Engine/envelope `source_path` and `source_sha256` pairs | Verified for committed repo paths | LOW | Direct source hashes match `HEAD` bytes for in-scope committed JSON path/hash pairs. |
| S7 `core_source_path`/wrapper paths | Verified after schema-aware check | LOW | S7 has both `core_source_path/core_source_sha256` and wrapper `source_path/source_sha256`; both are committed and hash-match when paired correctly. |
| `geo_s3` and `geo_s4` copied directive source | Unverifiable | HIGH | Both cite `/tmp/claude_s1_qubit_ladder_corrected_message_20260610.md` as `source_path` with hash `80c567...`; `/tmp` is not committed source. |
| MCT dynamic `source_refs` | Unverifiable from committed estate | HIGH | Several refs point to `/Users/joshuaeisenhart/wiki/...` without committed hash capture in the packet result. `mct_wiki_source_map_20260610.md` is committed, but the external wiki refs themselves are not source-hash traced here. |
| Canon algebra carrier artifact | Artifact/source verified; receipt path broken | MEDIUM | `system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json` hash `824a0a...` matches committed bytes, and generator `system_v5/julia_carrier/canon_algebra_artifact_v1.jl` hash `029907...` matches. The cited receipt path `system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json` is not committed at `HEAD`. |
| Bloch/MCT carrier orientation lineage | Partly verified | HIGH | Artifact bytes verify, but the Bloch orientation map and MCT committed basis lift are not reconciled by a committed map-of-maps ledger. |

## Bounded Remediation List

1. Add a seed ledger to each RNG packet result/PIN: seed list, RNG API, sample counts, and byte-stable rerun command. Start with `geo_s1_exact_closure_v0`, `geo_s1_finite_phase_lens_v0`, `geo_s1_quaternion_model_v0`, and `geo_s1_spinor_hopf_free_v0`.
2. Add an estate convention ledger and validator that reads committed results and fails on unmapped Bloch basis, holonomy sense, entropy base, rotation handedness, or octonion orientation reuse.
3. Add a cross-packet value reconciliation script for `h(eta)`, torus area targets, quotient-count families, and gamma/chirality splits. The quotient section must first define the mapping; until then it should report incomparable, not divergent.
4. Fix S7 `cross_engine_fatality` so it independently compares fatal cross-engine signatures instead of duplicating the truth of all previous gates.
5. Replace `/tmp` directive source refs in committed results with committed copied-source paths, or mark them explicitly as unavailable external prompts with no source-hash claim.
6. For MCT source refs, add committed source snapshots or source-hash receipts for the referenced wiki slices. Do not rely on absolute wiki paths as committed lineage.
7. Commit or retarget the canon algebra artifact receipt path. The artifact and generator hashes verify, but the cited `system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json` path is broken at `HEAD`.
8. Add an octonion orientation reconciliation receipt between Bloch root's `old_to_new` map and MCT weld's committed basis lift before any cross-packet nonassoc claim is promoted.
