# M(C) Gap Table

Fence: M(C) v0 is `scratch_diagnostic`. Full M(C) is not admitted. Every carrier envelope cited here is still scratch/candidate unless explicitly noted otherwise.

Primary v0 result: `system_v5/ops/formal_scouts/results/foundation_foundation_r4_mc_profile_v0_envelope_results.json`

Related external envelopes inspected:

- `system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_envelope_xhigh_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r4_spinor_holonomy_path_integral_variant_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_r3_associator_xhigh_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r3_alternativity_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r3_sedenion_zerodivisor_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r3_g2_automorphism_xhigh_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_r3_octonion_cl6_link_xhigh_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r5_g2_su3_reduction_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r6_g2_associative_calibration_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r6_spin7_g2_calibration_forms_envelope_results.json`

Note: the two contract source docs named in the packet were not present at the exact paths `concepts/constraint-manifold-architecture.md` or `manifold-layers-and-sim-queue-capture-2026-06-08.md` in this checkout. The contract field list in the user packet is therefore the authority for field names here.

| M(C) field | Status | Evidence |
|---|---|---|
| `S` finite support | PRESENT-in-v0, but summarized rather than emitted as one complete support object | v0 `mc_profile_summary.grid_cardinality=125`, `mc_profile_summary.admitted_cardinality=27`; Julia leg `profile.grid_cardinality=125`, `sample_admitted_records[*].admitted_under_C=true` |
| `C` active density/probe constraints | PRESENT-in-v0 | v0 `C_constraints=["trace(rho)=1","rho=rho^dagger","PSD via 2x2 principal minors/eigenvalues","1/8 <= Tr(P rho) <= 7/8 for each P in M"]` |
| `C` includes `F01` | MISSING | No `F01`/`f01` field or value in v0 or inspected related envelopes |
| `C` includes `N01` | MISSING | No `N01`/`n01` field or value in v0 or inspected related envelopes |
| `C` includes probe rules | PRESENT-in-v0 | v0 `C_constraints[3]="1/8 <= Tr(P rho) <= 7/8 for each P in M"` and `M_probe_family` lists `P_z0`, `P_xplus`, `P_yplus` |
| `C` includes composition rules | EXTERNALIZED-to-`foundation_foundation_r4_spinor_holonomy_path_integral_variant_envelope_results.json`; not wired into v0 | spinor holonomy `M.explicit_probe_family=["ordered_product_spinor_SU2_loop","ordered_product_vector_SO3_loop","path_increment_sensitivity_probe"]`; v0 has no `composition` field |
| `M/P` probe-readout family | PRESENT-in-v0 | v0 `M_probe_family=[{"id":"P_z0","projector":"|0><0|"},{"id":"P_xplus","projector":"|+><+|"},{"id":"P_yplus","projector":"|i+><i+|"}]` |
| `~_M` probe-relative quotient | PRESENT-in-v0 | v0 `quotient_relation="rho ~_M sigma iff Tr(P rho)=Tr(P sigma) for every P in finite M"`; `mc_profile_summary.full_M_class_count=27` |
| `Adm_C(x)` admissibility predicate | PRESENT-in-v0 as evaluated predicate, not as one named total function | v0 `mc_profile_summary.admitted_cardinality=27`; Julia leg `sample_admitted_records[*].admitted_under_C=true`; JAX leg controls show `admitted_center.z3_status_under_C="sat"` and excluded controls `*_status_under_C="unsat"` |
| Order-sensitive composition | EXTERNALIZED-to-`foundation_foundation_r4_spinor_holonomy_path_integral_variant_envelope_results.json`; not wired into v0 | spinor holonomy `M.explicit_probe_family` includes ordered products; `S_mod_M.spinor_SU2_class="2pi_holonomy_minus_identity"` and `vector_SO3_class="2pi_holonomy_plus_identity"` |
| Bracketing / nonassociativity | EXTERNALIZED-to-`foundation_r3_associator_xhigh_envelope_results.json` and `foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_envelope_xhigh_results.json`; not wired into v0 | associator xhigh `M.explicit_probe_family=["associator[A,B,C] = (AB)C - A(BC)"]`, `S_mod_M.definition="(AB)C ~_M A(BC) iff associator[A,B,C] is zero"`, `negative_control_flip.O_all_zero_smt_unsat=true`; nonassoc discriminator `M.probe_family` includes `associator probe used for quotient visibility` and `quotient_summary.full_probe_signatures.O` has `associative=false` |
| Local relation/path rules | EXTERNALIZED-to-`foundation_foundation_r4_spinor_holonomy_path_integral_variant_envelope_results.json` and partially to `foundation_foundation_r6_g2_associative_calibration_envelope_results.json`; not wired into v0 | spinor holonomy `M.finite_probe_domain.loop_discretizations=[2,4,8,16,32,64]`; G2 calibration `S_mod_M.definition="S is the finite set of 35 coordinate 3-planes in Im(O); P ~_M Q iff their calibration/closure probe vector agrees"` |
| Candidate carrier/readout map | EXTERNALIZED-to-`foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_envelope_xhigh_results.json` and `foundation_r3_octonion_cl6_link_xhigh_envelope_results.json`; not wired into v0 | nonassoc discriminator `M.carrier_set_S=["R","C","H","O"]`, `quotient_summary.strong_cl6_7unit_admitted_carriers=["O"]`; octonion/Cl6 `M.observable_realization="Julia QuantumOptics NLevelBasis(8) operators i*L_ei are Hermitian finite observables"`, `quotient_summary.octonion_class.generated_rank=64`, `spinor_dim=8` |
| Axes `A_i:M(C)->V_i` | MISSING as axes from M(C) | Related envelopes expose scalar readouts, e.g. G2 `S_mod_M.class_dimensions.O=14`, G2/SU3 `fix_e1_stabilizer_dim=8`, Spin7/G2 `class_dimensions.Stab_Phi_Spin7=21`, but no inspected result defines axes `A_i` as maps out of the v0 M(C) object |
| Negative controls | PRESENT-in-v0 | v0 `negative_control_flip.drop_trace.before="unsat"` with `z3_after="sat"`/`cvc5_after="sat"`; same pattern for `drop_psd` and `drop_probe_bounds` |
| Evidence handles / receipts | PRESENT-in-v0 | v0 `source_path`, `result_path`, `source_sha256`, `engines.{julia,jax,pytorch}.result_path`, `crossover_proofs.{z3,cvc5}.ran=true`, `controller_reads_engine_results_after_lanes=true` |
| Claim ceiling | PRESENT-in-v0 | v0 `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`, `claim_ceiling="Foundation R4 M(C) profile v0 scratch diagnostic only... No promotion, no formal admission, no bridge or axis-level claim."` |
| One admitted finite object containing all contract fields | MISSING | v0 has no unified `M`, `C`, `S_mod_M`, `composition`, `bracketing`, `local_relation_path_rules`, `candidate_carrier_readout_map`, or `axes` object; related envelopes are separate scratch/candidate receipts |

## Minimum Work For Full M(C) v1

The minimum v1 is not another adjacent envelope. It needs one finite object that carries all contract fields together:

1. Define one explicit finite support `S`, not only counts. It should include the v0 density/probe support and the carrier/readout support that Stage 4 intends to build on.
2. Define one active constraint set `C` containing the v0 density/probe constraints plus the required `F01`, `N01`, composition, bracketing, local path, and carrier rules.
3. Define `Adm_C(x)` as an explicit predicate over that same `S`, and emit admitted/rejected records or a deterministic receipt sufficient to reconstruct them.
4. Wire `M/P` and `~_M` over the same object, with quotient keys produced from the full probe family rather than from the v0 density probes alone.
5. Move the nonassociative discriminator's bracketing into M(C) v1 if Stage 4 depends on the carrier. External bracketing evidence is not enough: the v1 carrier must include the bracketed composition/readout rule and the quotient relation must see it.
6. Wire order-sensitive composition and local path rules into the same object, not only the spinor holonomy side envelope.
7. Define the candidate carrier/readout map from M(C) into the octonion/Cl6/G2 carrier surface, with the negative controls kept attached to the same map.
8. Define axes `A_i:M(C)->V_i` as actual finite maps from the admitted M(C) object, not just scalar summaries from neighboring envelopes.
9. Preserve evidence handles and claim ceiling inside the v1 result. Until admission gates pass, the ceiling remains scratch/candidate.

Minimum gates before Stage 4 safely builds on the carrier:

- Contract lint: all M(C) fields present under one schema, with no external-only required field.
- Three-engine envelope gate: Julia/JAX/PyTorch lanes complete, `reads_peer_result=false`, source/result receipts present, and no hollow parity.
- Solver/control gate: z3/cvc5 or equivalent exact checks derive decisive constraints from bound finite data; drop/erase controls flip in the expected direction.
- Composition/bracketing gate: order-sensitive composition and nonassociative bracketing alter the quotient/admissibility when erased or replaced by associative controls.
- Carrier/readout gate: octonion/Cl6/G2 readout map is load-bearing, with quaternion/commutative/erased-structure controls still attached.
- Stage gate: `classification` must move by process, not prose. Current evidence supports scratch/candidate only; full M(C) v1 is not admitted until the validator for the full contract passes and writes an admitted receipt.
