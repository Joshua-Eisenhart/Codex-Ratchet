# BUILD CARD v2 (REBUILD after DECORATIVE): axis_independence_discriminators_036 — carrier-coupled 3x3 independence matrix

The v1 build was adjudicated DECORATIVE for its independence evidence (audit_verdict.md in the sim folder — read it FIRST; all seven findings H1-H7 TRUE). This v2 rebuilds the core per the audit's seven Required Gaps. Rebuild IN PLACE: keep audit_verdict.md untouched (append-only history), replace the leg/envelope sources and regenerate all results. The v1 claim values are NOT pinned — they were fixture artifacts; v2 values come from the carrier.

CLAIM UNDER TEST (unchanged): Axis 0 (response) / Axis 3 (placement) / Axis 6 (precedence) polarities are independent as measured behaviors — diagonal-dominance of the 3x3 vary/hold matrix — now computed through ONE SHARED CARRIER STATE, not isolated fixture fields.

Ceiling: scratch_diagnostic, promotion_allowed=false, formal_admission_allowed=false, axis0_status=readout_only_no_closure, named functionals only, no IGT, Axis-4 distinct from Axis-6, b6=-b0*b3 never cited as independence evidence.

## The seven v2 requirements (audit Required Gaps, verbatim intent — each is a build gate)

V1. CARRIER-COUPLED OBSERVABLES: one shared state object per matrix cell — (family, placement, precedence, terrain channel, operator, rho, evolved intermediates) — with ALL THREE observables computed from that shared evolved state. An observable that reads only its own axis's input field is a build failure. Every vary operation perturbs the shared state; every observable is recomputed from the result.

V2. RECOMPUTED AXIS-0: the response class computed by evolving delta_rho through the COMMITTED terrain generator forms (import the source-locked terrain packet path, as matrix64 did — terrain_operator_precedence_64_matrix_jax.py:247-268 is the precedent), with the named PPR functional applied to the evolved output. NO finals[family] coefficient templates. Compare resulting scales to the blind sheet's committed-form expectations (Ne ~ +0.08037, Se ~ -0.001813) and report agreement/divergence vs blind explicitly.

V3. RELABEL-AND-RECOMPUTE SHUFFLE: permute family labels while holding computed dynamics fixed; recompute Axis-0 classes from the functional; label-derived classes must break, computed classes must survive — both directions emitted.

V4. CAN-FAIL ERASURE CONTROLS: every erasure control recomputes the erased channel/loop/precedence map and compares to the non-erased positive. No x-x patterns, no pass=True, no hardcoded zeros. Each control must be able to fail and the receipt must show what value it would have taken on failure.

V5. RAW-VALUE SMT: z3 AND cvc5 bind raw/scaled computed PPR/density/gap values (the actual observable numbers), deriving diagonal-dominance as inequalities over them; erased control flips to SAT. No moved/not_moved integers.

V6. HONEST PYTORCH ROLE: either a genuine torch-side carrier sensitivity (torch.func jacobian THROUGH the torch-native recomputation of the shared-state evolution — not coords*scales) or an explicit demotion field pytorch_role="supportive_graph_only". No synthetic diagonal vectors.

V7. REAL AXIS-4 CELL: compute Phi_D = U∘E∘U∘E vs Phi_I = E∘U∘E∘U (the committed scaffold §15 forms) on the shared carrier with Axis-6 held; the Axis-4 observable = the D/I order gap; show it moves under loop-order variation and holds under precedence variation, separately from fiber/base density visibility.

## Reuse (cite lineage)

Committed mct carrier; committed source-locked terrain + operator packets (IMPORT their code paths, as matrix64 did — matched mirrors must be labeled per the matrix64 precedent); the committed matrix64 anchors as cross-checks (its 0.0815 gap etc. — agreement is a smoke test, the computation must be this packet's own imported-source path).

## Controls (all can-fail)

relabel-and-recompute shuffle (V3), per-axis erasure controls (V4), commuting distinct-pair control (zero gap), erased-precedence merge, vary-operation purity receipts (each vary shown to change only its polarity IN THE SHARED STATE: emit the before/after state diff), blind-scale comparison row (V2).

## Engines (three-engine claim-bearing; identical PIN)

Julia = canon (imports/mirrors source-locked forms, labeled honestly). JAX = sweep + z3/cvc5 raw-value proofs. PyTorch per V6. NumPy control-lane only. Emit source_sha256 fields per current convention.

## Files

Same folder (system_v6/sims/axis_independence_discriminators_036/): replace leg/envelope sources, regenerate results/, update build_card.md to THIS card (v1 card content preserved at the bottom under a SUPERSEDED heading), DO NOT touch audit_verdict.md.

## Acceptance (re-run mechanically)

Legs exit 0 fresh; validator --require-pytorch ok:true (+ --require-source-backed recorded); V1-V7 each with named computed receipt fields; vary-purity state diffs emitted; blind-scale comparison row present; all controls fired with can-fail evidence; ceiling exact.

## SUPERSEDED v1 BUILD CARD

# BUILD CARD: axis_independence_discriminators_036 — the 3x3 vary/hold response matrix (spine, post-R2)

One object, one claim, one card. CLAIM UNDER TEST: the three polarity degrees of freedom — Axis 0 (response: allostatic/positive-feedback vs homeostatic/negative-feedback), Axis 3 (placement: fiber/inner loop vs base/outer loop), Axis 6 (precedence: operator-first vs terrain-first) — are INDEPENDENT as measured behaviors: varying each one moves its own named observable and does not flip the class of the other two, on the committed carrier with the committed forms. Independence = diagonal-dominance of the computed 3x3 response matrix under the named observables ONLY. This is a discriminator receipt, NOT axis-level admission, NOT Axis-0 closure.

Ceiling: classification="scratch_diagnostic", promotion_allowed=false, formal_admission_allowed=false; axis0_status="readout_only_no_closure"; no Ne/Ni/Se/Si claim fields beyond explicitly named functionals; no IGT content; Axis 4 (deductive/inductive loop order) stays a SEPARATE DOF — never merged with Axis 6; b6=-b0*b3 scaffold consistency is NOT an independence proof and must not be cited as one.

## Read first (binding)
1. system_v6/receipts/axis_independence_mine_20260610.md — THE SPEC: per-axis source map §A, the 3x3 design table §B (implement it as written), fences §D
2. system_v6/sims/mct_dynamic_admissibility_packet_v0/ — carrier (lineage cite)
3. system_v6/sims/terrain_generator_sheet_packet/ + source_locked_operator_base_packet/ — committed forms (reuse, cite)
4. system_v6/sims/terrain_operator_precedence_64_matrix/ — committed precedence machinery + the F8 orthogonality cell values (Axis-4 inner 2.455493422156577e-16 / outer 0.7071067811865476 / Axis-6 gap 0.08151115599412681) as anchors; reuse its Delta computation lineage
5. system_v5/READ ONLY Reference Docs/terrain math.md:43-49 (fiber density-stationary / base density-visible — the Axis-3 MUST-MOVE law)

## PIN block (frozen; identical across legs)
- the 3x3 protocol from the mine receipt §B verbatim: for each axis i, a pinned VARY operation (flip only that polarity) and two pinned HOLD constraints; per cell (i,j) a named observable O_j with a PREDECLARED class criterion (sign/class for Axis 0 via the named PPR functional; loop-class fiber-vs-base via density-delta tolerance for Axis 3; precedence sign/gap class for Axis 6) and tolerance.
- POSITIVE SENSITIVITY REQUIREMENT: every MUST-NOT-MOVE observable must also appear as a MUST-MOVE cell somewhere in the matrix (so "didn't move" is never explained by an insensitive observable).
- pinned states/forms: committed terrain laws (8), operators (4 base x 2 precedence), sheets L/R; pinned rho and sweep subset cited from the committed packets.
- named functionals only: the Axis-0 functional is named (e.g. PPR per the mine receipt) with its formula quoted from source; no personality-label fields.

## Build gates
G1. The full 3x3 matrix computed: 9 cells, each with the named observable's value under the vary operation, the class verdict (moved/not-moved per predeclared criterion), and raw numbers emitted.
G2. Diagonal: all three MUST-MOVE cells move (Axis 0 sign/class flips per family; Axis 3 fiber~0 vs base-visible per terrain math :43-49; Axis 6 gap nonzero/sign flip).
G3. Off-diagonal: all six MUST-NOT-MOVE cells hold class (raw magnitudes may vary; class criteria predeclared — no post-hoc tolerance adjustment).
G4. Axis-4 boundary cell: vary Axis-4 loop order with Axis-6 held and vice versa (reuse the committed F8 machinery); report independent movement; explicit field axis4_distinct_from_axis6=true backed by the two computed values.
G5. Controls: commuting control collapses the Axis-6 diagonal to ~0; label shuffle leaves all class verdicts invariant; per-axis erasure controls (sheet erasure H_L=H_R kills the Axis-0-relevant sheet distinction where applicable; nesting/loop erasure kills Axis-3's law; precedence erasure merges Axis-6 pairs) each fire.
G6. Load-bearing SMT (z3 AND cvc5): derive diagonal-dominance for at least the Axis-6 row from computed values (real rows -> UNSAT for "diagonal cell = 0 while off-diagonals move"; erased control -> SAT). No hardcoded literals.
G7. Result language: "independence under the named observables and pins" only; no axis admission, no closure, no doctrine promotion.

## Engines (three-engine claim-bearing; identical PIN)
Julia = canon. JAX = the vary/hold sweep batch + z3/cvc5. PyTorch = its own scoped lane (e.g. class-verdict matrix + autograd sensitivity rows), independent computation, no core-import wrapping (the R1 lesson). NumPy control-lane only.

## Files to create (one folder, atomic)
system_v6/sims/axis_independence_discriminators_036/
  axis_independence_discriminators_036_julia.jl / _jax.py / _pytorch.py / _envelope.py
  build_card.md (verbatim copy)
  results/*.json
No audit_verdict.md. No edits to existing files.

## Acceptance (re-run mechanically)
Legs exit 0 fresh; validator --require-pytorch ok:true; PIN identical with all reuse lineages cited; G1-G7 fields present; controls fired with values; the 3x3 matrix complete with predeclared criteria quoted; ceiling + fence fields exact.
