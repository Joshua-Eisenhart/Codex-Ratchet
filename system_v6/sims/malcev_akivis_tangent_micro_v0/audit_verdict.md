# Audit Verdict - malcev_akivis_tangent_micro_v0

Bottom line: **GENUINE-WITH-CAVEATS**. This packet earns an exact finite witness that the imaginary-octonion commutator algebra, consumed from the committed Julia carrier constants by SHA-256, is non-Lie but Malcev; it also earns the quaternion Lie control and the perturbed non-Malcev control. It does **not** earn discovery language, physics/carrier/bridge promotion, all-three-engine status, or a full Akivis-identity residual claim.

## Verdict

- Repo vocabulary: `GENUINE-WITH-CAVEATS`.
- Evidence ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, `claim_ceiling=tool_function_micro_only`.
- Citation-safe claim: `malcev_akivis_tangent_micro_v0` is a finite exact Malcev/non-Lie tangent micro over the pinned `algebra_structure_constants_v1.json` octonion constants: `J(e1,e2,e4)=-12e5`, both pre-registered Malcev forms vanish over all 343 basis triples, the quaternion `e1,e2,e3` subalgebra has Jacobi zero over its 27 triples, and one antisymmetric bracket perturbation fails Malcev with witness `-4e2`.

## Fresh Audit Checks

- Read-only boundary held. I did not rerun the packet scripts because Julia, JAX, envelope, and packet-local validator commands write result JSONs. I used read-only source/result inspection plus no-write recomputation.
- Current target packet is still working-tree evidence: `git status --short -- system_v6/sims/malcev_akivis_tangent_micro_v0` reports `?? system_v6/sims/malcev_akivis_tangent_micro_v0/`. No `git add` or commit was run.
- Committed carrier artifact verified: `git ls-files --stage system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json` shows it tracked, and `shasum -a 256` gives `824a0a2c794a949a83e4bd650c9620464b96eb0d1dcb3d0fe4901a4e86d05f2c`.
- Read-only generic validator import returned `generic_validate_errors []`; read-only builder-boundary import returned `builder_boundary_errors_pre_audit_file []`. The packet-local validator itself writes `validator_results.json`, so I did not invoke it directly in place.
- Independent no-write recomputation from the committed constants gave:
  - `[e1,e2]=2e3`, `[[e1,e2],e4]=-4e5`;
  - `[e2,e4]=2e6`, `[[e2,e4],e1]=-4e5`;
  - `[e4,e1]=2e7`, `[[e4,e1],e2]=-4e5`;
  - therefore `J(e1,e2,e4)=-12e5`.
- Compact Malcev instance recomputed on the same triple:
  - `[e1,e4]=-2e7`;
  - `J(e1,e2,[e1,e4])=-24e6`;
  - `[J(e1,e2,e4),e1]=-24e6`;
  - compact residual `0`.
- Expanded Malcev instance recomputed independently on the same triple:
  - expanded lhs `-24e6`;
  - expanded rhs `-24e6`;
  - expanded residual `0`.
- Quaternion control recomputed on `e1,e2,e3`: each cyclic nested bracket term is zero, so `J(e1,e2,e3)=0`.
- Perturbed control recomputed through the real perturbation path: after `C_bracket[e1][e1,e2] += 1` and antisymmetric mirror `-= 1`, compact residual on `e1,e2,e2` is `-4e2`.

## Panel-Match Table

| Panel / standard item | Audit result | Evidence |
|---|---|---|
| PANEL 6 q4, commit `eba5fdca0` | **PASS.** The packet matches the pre-registered row: imaginary octonion commutator is non-Lie but Malcev; grok compact form and gemini expanded form are both represented. | `cross_model_anchor_recompute_panel6_20260612.md` q4 says compact `J(x,y,xz)=J(x,y,z)x` and expanded bracket form are the two pre-registered forms. |
| Old-estate item 13 provenance | **PASS-WITH-CAVEAT.** The packet matches the finite identity check from pinned structure constants and tangent-only boundary. | `old_estate_mine_20260611.md` item 13 names the Malcev/Akivis tangent probe and says boundary is tangent identity only. Caveat: this packet implements Malcev and non-Lie Jacobiator evidence, not a full Akivis residual. |
| Carrier constants consumed by hash | **PASS.** Python and Julia both abort on artifact SHA drift before building brackets. | `malcev_akivis_tangent_micro_v0_common.py:21-23,60-74`; `malcev_akivis_tangent_micro_v0_julia.jl:16-18,58-68`; envelope records the same artifact hash at `results/..._envelope_results.json:87-98`. |
| Jacobiator exact nonzero witness | **PASS.** Fresh recomputation gives `J(e1,e2,e4)=-12e5`, matching envelope positive section. | Source computes `jacobiator` at `common.py:84-85` and all rows at `common.py:121-150`; envelope witness at `results/..._envelope_results.json:282-310`. |
| Compact Malcev form | **PASS.** Fresh recomputation of one instance gives zero residual, and code sweeps all 343 triples. | Compact residual is a distinct function at `common.py:88-89`; all-triple sweep at `common.py:123-125`; envelope records `malcev_compact_identity_holds=true`. |
| Expanded Malcev form | **PASS.** Fresh recomputation of one instance gives zero residual, and code sweeps all 343 triples separately from the compact function. | Expanded residual is a distinct function at `common.py:92-99`; all-triple sweep at `common.py:123-125`; Julia mirrors the separation at `malcev_akivis_tangent_micro_v0_julia.jl:79-90,114-118`. |
| Independence of the two forms | **PASS.** The expanded check is not derived from the compact boolean; it constructs lhs/rhs directly and has a separate failure scan. | `common.py:88-99,123-125,139-154`; `julia.jl:79-90,117-124,134-137`. |
| Quaternion control | **PASS.** Fresh recomputation gives `J(e1,e2,e3)=0`; result sweeps 27 triples over `e1,e2,e3`. | `common.py:126-131,155-160`; envelope boundary section at `results/..._envelope_results.json:61-76`. |
| Perturbed non-Malcev control | **PASS.** Fresh recomputation through the actual perturbation path gives residual `-4e2`. | Perturbation code at `common.py:114-118,132-143`; envelope negative section at `results/..._envelope_results.json:249-277`. |
| Spin(3) exact-finite-witness precedent, commit `c9f0075d7` | **PASS.** Claim language follows the precedent: exact finite witness of standard math, not discovery. | Spin(3) audit says exact finite witness, no discovery/engine/coupling at `clifford_spin3_double_cover_micro_v0/audit_verdict.md:3,33-48`; this packet uses `scratch_diagnostic` and finite claim ceiling. |
| Owner fence: nonassociative/octonion diagnostic only | **PASS.** The packet says nonassociativity is a diagnostic readout, not assumed source or physics/bridge claim. | Build card lines 18-24; envelope relevance fence at `results/..._envelope_results.json:312-318`. |
| SMT integer bindings | **PASS-WITH-CAVEAT.** z3 and cvc5 use integer variables and QF_LIA/integer constants; positive is `unsat`, flip controls are `sat`. Caveat: SMT binds computed flags, not raw residual tensors. | `common.py:170-221,227-239`; envelope proofs at `results/..._envelope_results.json:107-137`. |
| Honest mode / schema / validators | **PASS-WITH-CAVEAT.** Envelope has `three_engine_sim_result_v1`, two honest lanes, PyTorch omitted with reason, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, and existing validator result OK. Caveat: packet-local validator writes result JSON and will treat this auditor file as an expected builder-boundary failure if rerun in place after audit creation. | `envelope.py:84-181`; `validate_malcev_akivis_tangent_micro_v0.py:75-102,124-134`; existing validator JSON reports no errors. |

## Named Caveats

- **C1 - Working-tree packet evidence:** the target sim directory is untracked right now. This verdict audits the live codex1-built packet, not a committed sim packet.
- **C2 - SMT flag-level proof:** z3/cvc5 bindings are real integer solver checks, but they certify computed finite flags after exact residual enumeration. Do not cite them as an in-solver derivation of Malcev identities directly from raw structure constants.
- **C3 - Akivis name ceiling:** the packet title/provenance says `Akivis tangent`, and the Jacobiator/non-Lie readout is relevant to that neighborhood, but this packet does not implement the full Akivis identity residual involving associator constants. Cite as Malcev/non-Lie tangent micro unless a future packet adds the Akivis residual.
- **C4 - Two scoped engines, not all-three:** Julia and JAX both consume the same committed constants by hash; PyTorch is honestly omitted. Do not cite as a three-engine result.
- **C5 - Exact standard-math witness, not discovery:** like the Spin(3) precedent, this is an exact finite witness and control packet for known algebraic structure. It is not a discovered carrier, physics, engine, bridge, Moufang-loop, or admission result.
- **C6 - Validator placement:** because `audit_verdict.md` is auditor-owned, later packet-local validator reruns should be done in a temp copy or with the expected builder-boundary interpretation.

## Future-Citation Rule

Allowed citation:

> `malcev_akivis_tangent_micro_v0` is a `scratch_diagnostic` exact finite Malcev/non-Lie witness over the committed Julia carrier octonion structure constants: `J(e1,e2,e4)=-12e5`, both pre-registered Malcev forms vanish over all 343 basis triples, the quaternion subalgebra has Jacobi zero, and a one-entry bracket perturbation breaks Malcev.

Forbidden citation:

> This packet discovers a new nonassociative structure, proves a physics/carrier/bridge claim, establishes a Moufang-loop or full Akivis-identity result, supplies all-three-engine evidence, or promotes octonions/nonassociativity as an assumed source rather than a diagnostic readout lane.
