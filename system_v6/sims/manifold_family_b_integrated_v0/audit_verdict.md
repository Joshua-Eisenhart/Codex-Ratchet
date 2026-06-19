# manifold_family_b_integrated_v0 Audit Verdict

Bottom line: `VERDICT: GENUINE-WITH-CAVEATS`, scratch diagnostic only.

This is not merely parent rows wearing an integration costume. The packet does run one Family B
object across B1-B4, rebuilds the 384 -> 288 + 96 compression flow from pinned MCT carrier rows and
compression predicates, reconstructs B3/B4 locally, and its hash-chain heads match the parent by
recomputation. It is not a clean full-card pass: the deep-chain layer is locally hardcoded rather
than programmatically rebuilt from the pinned ratchet parent rows, B3's Z4 co-citation is not
row-local, the trajectory artifact is weaker than the unified-run mechanism, and raw parent payloads
leak `axis0_*` fields through B2.

## Verdict

Accepted claim:

- `manifold_family_b_integrated_v0` is a real scratch-diagnostic Family B integrated run over one
  shared Hopf-torus chart carrier.
- It may be cited as a can-fail integrated B packet only with the caveats below.
- It must not be cited as canonical, formal admission, a Family A/B weld, two-engine evidence,
  axis/bridge/physics evidence, or a fully independent Julia/JAX/PyTorch full-object implementation.

Decisive question:

- B2/B3/B4 are rebuilt against the shared object rather than imported as finished parent rows.
- B1 recomputes the right chain values inside the packet, but the packet code does not consume the
  parent ratchet chain rows as the live computation source. That keeps the overall verdict below
  `GENUINE`.

## Recompute Reality

Independent recomputation from the parent ratchet result rows gave:

- denominator product: `16`;
- final volume: `pi**2/4`;
- entropy deltas: `-log(4), -log(2), -log(2)`;
- composite orbit: `Z4 x Z2`, orbit order `8`, max element order `4`, no order-8 element.

Independent recomputation from the pinned MCT carrier and CFR predicate definitions gave:

- step 0: `384 -> 288`, emitted `96`, defect `0`;
- step 1: `288 -> 192`, emitted `96`, defect `0`;
- step 2: `192 -> 96`, emitted `96`, defect `0`;
- cardinality conservation: `384 = 288 + 96`;
- hash-chain heads matched parent by recomputation:
  - `41d0113914c03390eac69b7e6ba7763d439dd275e981458bb90b5b4eef14e3ff`
  - `f78beccf9623dd94a9316e03132616bb250e85ee5b0186e02b356db207138b47`
  - `20d5517a287c8f351a396e4001927cf8a9b789029788c6c4a6ff1a5ce15c8961`

## v0-Lesson Checklist

- G1: `PASS-WITH-CAVEAT`. `parent_hash_pins` lock result JSONs only, and audit verdict hashes are
  segregated under citation-context hashes. Caveat: B1's computation does not consume the pinned
  `ratchet_deep_chain_v0` row ledger directly.
- G2: `PASS-WITH-CAVEAT`. Every reduced/derived row carries parent caveat labels, and the
  `manifold_entropy_ledger_v0:CAVEAT_SIGNED_LENS_DELTA_LABEL` caveat is carried. Caveat: B3's
  `z4_syndrome_record_v0` co-citation exists at layer level, not on the `B3_full_record` and
  `B3_erased_record` rows themselves.
- G3: `PARTIAL`. The trajectory artifact has one `state_object_id`, persisted step rows, SHA
  sidecar, and `STEP_DEPENDENT` versus `CARRIED` classification. It is weaker than
  `manifold_unified_run_v0`: the sidecar verifies stable JSON payload hash, not file bytes, and the
  artifact lacks unified-style `trajectory_step_id`, `row_step_lineage_id`, and `row_step_class_why`
  fields.
- G4: `PASS-WITH-SCOPE`. The declared mode
  `julia_orbit_counts_plus_shared_python_common_builder` matches the code. Julia independently
  recomputes orbit/cardinality counts with Graphs/Z3; JAX/PyTorch use the shared Python common
  builder for the full B object. This is honest limited scope, not three independent full-object
  backends.
- G5: `PASS-WITH-CAVEAT`. B1-B4 decorative detectors are real input perturbations that change each
  layer's own row signature. B4 clears the A v0 L5 weakness enough for scratch use, but its
  perturbation is still a signed-lens-label perturbation, not a new numeric ledger derivation.

## Kill Controls

Controls rerun/inspected as can-fail checks:

- stale-import control fires: `z4_order 4 -> 5` changes the deep-chain denominator, and the first
  compression predicate perturbation changes the dependent hash head;
- order-shuffled `N01` fires: chain row signature changes where order matters;
- erased-record defect computes `ln4`;
- quotient-erased fires with nonzero raw-reconstruction mismatch;
- every B1-B4 decorative detector fires and changes that layer's row signature.

## Fences

Passed:

- no Family A result rows are used on the claim path;
- `family_a_rows_used=false` and `two_engine_rows_used=false`;
- B3's record side is constructed as syndrome tables; it is not `record := loss`;
- class language is bounded as chart-relative in the declared claim surface.

Failed/weak:

- The literal "no axis language anywhere" fence is not fully satisfied. B2 raw record entries embed
  full parent `canonical_probe_row` payloads, and those rows carry `axis0_b0` and `axis0_eta`.
  I found this in the emitted envelope/spec payload, not in a positive axis claim. It is still a
  fence leak because the build card said no axis language anywhere.
- Raw parent row embedding is wider than the Family B fence needs. Future packets should project
  only B-scoped carrier/predicate fields before emitting integrated artifacts.

## Validators And Tests

Fresh checks run:

- packet validator function rerun against
  `system_v6/sims/manifold_family_b_integrated_v0/results/manifold_family_b_integrated_v0_envelope_results.json`:
  `ok=true`, `errors=[]`;
- `scripts/validate_three_engine_sim_result.py` validation function rerun across all 16 combinations
  of `require_pytorch`, `require_source_backed`, `strict_source_backed`, and `require_tool_intent`:
  all passed;
- pytest rerun in a disposable repo-shaped copy so the live repo result artifacts were not rewritten:
  `6 passed, 50 subtests passed`.

SMT status:

- denominator, compression, and record SMT rows bind computed values with `UNSAT` identities and
  `SAT` erased/perturbed flips;
- Julia Z3 lane binds orbit/cardinality values in its limited Julia scope.

Package observables:

- accepted as honest for this declared mode. Julia's package-backed contribution is orbit/cardinality
  counts, while JAX/PyTorch provide package-backed probes around the shared Python common builder.

## Named Caveats

- `G1_DEEP_CHAIN_PIN_CONSUMPTION_IS_THIN`: B1 has the right result and controls, but it hardcodes the
  seven-step chain locally instead of deriving the live B1 rows from the pinned ratchet parent result
  ledger.
- `G2_RECORD_ROW_Z4_COCITATION_NOT_ROW_LOCAL`: B3 co-cites `z4_syndrome_record_v0` at layer level,
  but record rows do not each carry the Z4 co-citation.
- `G3_TRAJECTORY_SHA_AND_LINEAGE_WEAKER_THAN_UNIFIED_MECHANISM`: the B trajectory artifact is present
  and payload-SHA verified, but it is not the stronger unified-run trajectory mechanism.
- `G4_BACKEND_SCOPE_HONEST_BUT_JULIA_NOT_FULL_OBJECT`: declared mode is honest, but Julia is not an
  independent full B1-B4 implementation.
- `G5_AXIS_FENCE_LEAK_IN_RAW_RECORD_PAYLOAD`: raw parent probe rows carry `axis0_*` fields into the
  B artifact.
- `G6_RAW_PARENT_ROW_EMBEDDING_OVERWIDE_FOR_FENCE`: B2 embeds full parent support/probe rows where a
  projected Family B witness table would be cleaner and safer.

## Future-Citation Rule

Allowed citation:

`manifold_family_b_integrated_v0 is a GENUINE-WITH-CAVEATS scratch-diagnostic Family B integrated run
that recomputes the main Hopf-torus chain/compression/record/ledger anchors, with caveats
G1-G6 from its audit_verdict.md.`

Required suffix:

`Not canonical, not formal admission, not a Family A/B weld, not two-engine evidence, not
axis/bridge/physics evidence, and not an independent full-object Julia/JAX/PyTorch implementation.`

Forbidden citation:

- Do not cite it as `GENUINE` without caveats.
- Do not fold it into Family A or use it as proof that A and B already weld.
- Do not cite raw B2 record payloads as axis-safe until the `axis0_*` leak is projected away.

## A+B WELD / Super-Sim v2 Must Add

The A+B weld must add, at minimum:

1. Separate pinned state objects for Family A and Family B, with neither object folded into the other.
2. A declared weld map saying exactly which coordinates/quotients are shared, related, or independent.
3. B-scoped projection of raw parent records before artifact emission; no `axis0_*` leakage.
4. Programmatic B1 consumption of the pinned ratchet row ledger, or an explicitly derived local pin
   block that the stale-import control mutates directly.
5. Row-local Z4 co-citation on B3 record rows.
6. Unified-style trajectory lineage: file-byte SHA, stable payload SHA, `trajectory_step_id`,
   `row_step_lineage_id`, and `row_step_class_why`.
7. A backend contract decision: either keep the honest shared-common-builder mode, or implement
   independent full-object Julia/JAX/PyTorch lanes and validate them as such.
8. Cross-family controls: A-only perturbation does not move B anchors, B-only perturbation does not
   move A anchors, and weld-only perturbation moves only admitted weld rows.
9. SMT rows that bind Family A values, Family B values, and the weld relation, each with decisive
   erased/perturbed flips.

## N01 Wording Annotation

`N01_LABEL_MISMATCH`: the order-control row in this packet is a constraint-chain order check, not a two-engine N01 directed-stage-loop check.

Correct citation: the chain order control is `constraint-application-sequence SHA change`: reordering the Z4 lens and phase-window steps changes the intermediate denominator sequence and row signature while leaving the final denominator at `16`.

Do not cite this row as a stronger N01 claim. Cite it only as order-sensitivity of the geometric constraint application sequence.
