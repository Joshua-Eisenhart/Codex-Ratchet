# Manifold Layer Order + Per-Layer Completeness Contract (DRAFT)

ASSISTANT-GLOSS: status: DRAFT. claim_ceiling: doctrine draft, no admission of anything.
This file is the CAMPAIGN INSTRUMENT, not a result. It reconciles four source orderings into
one numbered layer sequence (Part A) and fixes a mechanical per-layer "done" checklist (Part B).
Passing the Part B checklist for a layer means that layer reached `canonical by process` for its
rung; it does NOT promote the tower, and it does NOT admit any downstream physics/ToE claim.
No file under `scripts/` is edited or proposed for edit here. Owner labels are quarantined to the
legacy-label note at the end; the body uses pure-math vocabulary.

SOURCES (all read 2026-06-14; the four orderings reconciled below):
- `system_v6/receipts/nesting_law_final_object_spec_20260612.md` — the layer ledger (sections 5-27)
  + the final-object formula `X_{<=N}^max` + the compatibility law + the section-5 predicted-modification rule.
- `system_v6/foundations/v7_gate_grounding_law_DRAFT_20260614.md` — the axiom-grounded gate stack
  + b_kernel 7-stage exclusion-first pipeline + the L0 19-lexeme allow-list.
- `system_v4/probes/SIM_TEMPLATE.py` — the per-sim packet contract (manifest, integration depth,
  three-part test body, claim-ceiling field block).
- `CLAUDE.md` Sim Requirements + the Hard Stage Gate ORDER + the four status labels.
- The 27-layer software-stack ordering and the math-only / qubit-depth-axis plan orderings as forwarded.

DIVERGENCE DISCIPLINE: where the four sources disagree on order, framing, or priority, the fork is
recorded as a NOTED FORK and BOTH readings are kept live. Nothing is collapsed to a false winner.

---

## Part A — The Canonical Ordered Manifold Layer List

The single numbered sequence below runs UP from the distinguishability/probe-quotient floor. It is the
RECONCILED reading of the four source orderings. Each layer carries: the math object it adds, the
qubit depth where it first becomes nontrivial, the gating/deferred status, and any noted fork.

The reconciliation rule used: all four sources route micro (spinors / probe quotient) -> density / partial
trace -> connections / curvature / flux -> cut lattice / entropy -> maps / order -> regions -> trajectories ->
exceptional group structures. That common direction is the spine; the divergences are local.

### A.0 Root (NOT a layer — the source)

- **L0 — root constraints.** F01 (simultaneous-distinguishability surface), N01 (order/persistence),
  probe-relative identity `a = a iff a ~ b`, finitude. This is the SOURCE of the tower, not a numbered
  manifold layer. It is enforced as the b_kernel allow-list + DERIVED_ONLY guard, not as a sim.
  (gcm-stack layer 0; v7-gate-law Part 1.) Not buildable as a packet; it is the admission floor.

### A — The numbered layers

| # | Layer (math object added) | First nontrivial depth | Status | Source map |
|---|---|---|---|---|
| 1 | **Probe-quotient floor** `S/~_M`: finite set `S` of density matrices, probe family `M` of Pauli expectations, the equivalence `rho_a ~_M rho_b iff tr(rho_a P)=tr(rho_b P) for all P in M`, and the quotient. | 1q | ACTIVE | nesting "Pauli-string probes + the probe quotient"; gcm 1-6; plan Task 1-2 |
| 2 | **Density-rank strata + partial-trace marginals**: dim `4^n - 1` rank strata (NOT a Bloch ball), `Tr_{A\B}`, the marginal maps. | 2q | ACTIVE | nesting "density rank strata"; gcm 6-7; plan Task 3-4 |
| 3 | **Spinor / phase / projective surface** `CP^{2^n-1}` + local Hopf skeleton `S^1->S^3->S^2` per factor; `(S^1)^n/S^1 = T^{n-1}`. | 1q (pure), nests at 2q+ | ACTIVE | nesting "spinors/phase/projective", "local Hopf skeleton"; gcm 3-5 |
| 4 | **Local Weyl factors** (PRODUCT states only; entangled states keep mixed marginals). | 2q | ACTIVE | nesting "local Weyl factors"; gcm 13-14 |
| 5 | **Nested tori -> PREDICTED-MODIFIED shells** (section-5 rule): at higher rungs these are marginal-radius SHELLS + Schmidt strata, NOT literal product tori. | 2q (shells), 3q (Schmidt strata) | ACTIVE | nesting "nested tori -> AT HIGHER RUNGS: marginal-radius shells + Schmidt strata"; gcm 12 |
| 6 | **Metric layer RESTRICTED to survivors** + induced geometry `G_A = InducedGeometry(X_A^max)` recomputed on survivors; nearest-neighbor graph changes per constraint. | 2q | NOT STARTED | nesting "the metric layer RESTRICTED to survivors"; plan Task 5-6 |
| 7 | **Local + global connections / curvature / FLUX (geometric, feedstock)** + the lift-erasure verdicts. `F = dA`, holonomy. | 2q | NOT STARTED | nesting "connections/curvature/flux"; gcm 8-11 (feedstock, NOT runtime flux) |
| 8 | **The CUT LATTICE**: `2^{n-1}-1` bipartitions (1Q:0, 2Q:1, 3Q:3, 4Q:7, ... 8Q:127). | 2q (first cut), 3q (QIT floor) | ACTIVE | nesting "THE CUT LATTICE"; plan Task 12 |
| 9 | **Schmidt strata per cut** (rank tuples across cuts). | 3q | PARTIAL (computed in the tower fixture) | nesting "Schmidt strata per cut" |
| 10 | **Entropy per cut availability** (von Neumann `S_A`, `S_AB`, `I_AB`, conditional, coherent-information forms) — DERIVED measure, not master variable. | 2q (`S_A`), 3q (`I(A:B|C)`) | PARTIAL | nesting "entropy per cut availability"; plan Task 4, 13 |
| 11 | **Channels / flows / the 16 ordered maps per block** `B subset A`; the explicit map library + order/noncommutation matrix `delta(A,B,rho)`. | 2q | NOT STARTED | nesting "channels/flows/the 16 ordered maps"; plan Task 7-8 |
| 12 | **Region discovery from observables** (inequality, connected component, cell membership, equivalence class). | 2q | NOT STARTED | gcm 16-20; plan Task 9-10 |
| 13 | **Flux-fate** (`Delta h` or lift-erased + rank / `S` / purity) — runtime/QIT flux. | 3q+ | NOT STARTED (needs nesting + multi-qubit depth) | nesting "flux-fate"; gcm 24 |
| 14 | **The runner / QCA** + finite transition trajectories (`tau: Z -> V`, cycles, absorbing sets, time-indexed observables). | 2q+ | NOT STARTED | nesting "the runner/QCA"; gcm 21-23; plan Task 11, 13 |
| 15 | **Cl(2n) + chirality projectors** `P_L / P_R`. | 3q | NOT STARTED | nesting "Cl(2n) + chirality projectors" |

### Gated / deferred layers (named, not scheduled — each needs its explicit licensing object)

| # | Layer | LICENSING CONDITION (no packet until this exists) | Status |
|---|---|---|---|
| G1 | **The G2 layer** | explicit 7D real readout space `W_A` (dim 7, in `span{P_alpha}`) + the pinned 3-form `phi = e123+e145+e167+e246-e257-e347-e356` + the tests (3-form preservation, cross-product closure, associator visibility/erasure, compact-vs-split branch). | DEFERRED |
| G2 | **SU(3)** = `Stab_G2(u)`, `G2/SU(3) = S^6` | G1 licensed first (stabilizer reduction is downstream of G2). | DEFERRED |
| G3 | **Spin(7)** via Cayley form `Omega = dt^phi + *phi` | the 8D extension (8D readout space) defined. | DEFERRED |
| G4 | **Spin(8) triality** | the three explicit maps `8v -> 8s -> 8c -> 8v`. | NAMED, NOT SCHEDULED |
| G5 | **F4** = `Aut(J3(O))` | the 27D Jordan target `J`, Jordan product `A o B = (AB+BA)/2`. | NAMED, NOT SCHEDULED |
| G6 | split `G2(2)` + the sedenion zero-divisor boundary | CONTROLS for G1-G5 (run as negative controls, not promoted). | NAMED, NOT SCHEDULED |

### Higher-rung licensing (section-5 predicted-modification rule — binding for layers 3-5, 9, 13)

When a layer is nested UP a rung, its geometry is the PREDICTED MODIFIED object, NOT the naive product:
- local Weyl factors (L4) apply to PRODUCT states only; entangled states keep mixed marginals.
- nested tori (L5) become marginal-radius SHELLS + Schmidt strata at higher rungs, NOT literal product tori.
- A layer that asserts product-form geometry where the law predicts the modified shell/strata form is WRONG
  and must be demoted, regardless of how clean its numbers look.

### NOTED FORKS (held divergent — owner decides; do NOT collapse)

1. **Framing depth.** nesting-law = mathematical specification (does the inverse-limit object exist?);
   gcm-stack = software architecture (how are components staged?); the math-only plan = procedural build
   schedule (what to build, in what order). They AGREE on content and direction; they differ in framing.
   The numbered list above is the math-object reading; the gcm-stack and plan are alternative indexings of
   the same objects.

2. **Entropy vs geometry order.** gcm-stack puts geometric curvature/flux (L7) BEFORE entropy cuts; the
   plan treats entropy (L10) and geometry (L6-7) as PARALLEL, informing each other. The list keeps both:
   L6-7 are listed before L8-10 to match the gcm ordering, but the contract (Part B box vi/vii) does NOT
   forbid computing entropy before flux. FORK: locked-order (flux first) vs parallel. Owner-tunable.

3. **Terrain-families vs region-discovery.** gcm-stack presupposes terrain laws (its layers 16-17) as an
   intermediate that LICENSES region discovery; the plan constructs regions DIRECTLY from observables
   (its Task 9), no terrain layer. The list adopts the plan's reading (L12 = region discovery from
   observables) and routes the terrain-family vocabulary to the legacy-label quarantine. FORK: do regions
   derive from terrain laws, or do terrain realizations emerge post-hoc from region behavior? Owner-tunable.

4. **Feedstock vs runtime flux split.** gcm-stack splits geometric flux (L7, "feedstock, NOT runtime") from
   runtime/QIT flux (L13, "open, needs nesting + multi-qubit depth"); the nesting-law treats flux as ONE
   layer; the plan defers flux. The list keeps the gcm dual-flux split (L7 feedstock, L13 runtime). FORK:
   one flux layer or two. Owner-tunable.

5. **QCA / ring-checkerboard run-surface.** the nesting-law lists "the runner/QCA" as a standard layer (L14);
   gcm-stack flags it as an UNEXPLORED third substrate; the plan omits it. The list places it at L14 as the
   nesting-law has it, but flags it NOT STARTED with the gcm caveat. FORK: is QCA in the base build or a
   deferred surface substrate? Owner-tunable.

6. **The G-tower reduction order** (GL -> O -> SO -> U -> SU -> Sp) proposed by the geometry-stack-ratchet
   doctrine as a locked, order-rigid reduction chain. It does NOT appear in the nesting-law, gcm-stack, or
   plan. It is recorded here as a CANDIDATE horizontal constraint-order theory (how reductions compose),
   NOT folded into the vertical layer list. FORK: is the G-tower the ratchet mechanism, or is ratcheting
   defined per-layer by the within-layer licensing conditions (Part B box vi)? Owner-tunable; held live.

7. **L3 micro-object merger** (caught by the WF#4 fresh audit). The numbered list folds nesting-law item-1
   (spinors / phase / projective `CP^{2^n-1}`) and item-3 (local Hopf skeleton) into one L3, though the
   source SEPARATES them by item-2 (local Weyl factors, here L4). FORK: is the spinor/projective surface one
   object with the Hopf skeleton, or two layers with the Weyl factors between them? Recorded, not collapsed;
   owner-tunable.

---

## Part B — The Per-Layer Completeness Contract

This is the MECHANICAL checklist that DEFINES "this layer is done." A layer is `canonical by process`
for its rung ONLY when every box (i)-(xiv) below is checked with a cited artifact path from this
session. If any box is empty, the layer's honest status is the highest ladder label actually reached
(`exists` < `runs` < `passes local rerun`), and the unchecked boxes are NAMED in the ledger row.

A green checklist promotes the LAYER at its RUNG. It does NOT promote the tower (see box ix) and does
NOT admit any downstream physics/ToE/bridge/axis claim. Trust the result-JSON over any verdict prose.

### Box (i) — MAX SIM-SET ENUMERATED for the layer

- The packet states the FINITE state set explicitly (multiple candidate states, not one), as exact
  data (rational coordinates / sparse density recipes), so the quotient is computed, not asserted.
- The packet is SIM_TEMPLATE-derived (`system_v4/probes/SIM_TEMPLATE.py`): probe family `M` named,
  constraint set `C` named, TEMPLATE renamed. A non-template packet cannot be canonical.
- `classification` is one of `classical_baseline | canonical | scratch_diagnostic | tool_lego_fit_probe`,
  set EXPLICITLY. `canonical` is set only when every other box passes. `tool_lego_fit_probe` carries
  `promotion_allowed: false` and is pre-admission evidence only.
- TOOL_MANIFEST complete: every tool has `tried`, `used`, and a NON-EMPTY `reason`. Import-presence is
  not integration. TOOL_INTEGRATION_DEPTH set to `load_bearing | supportive | None` (never `decorative`).
- AT LEAST ONE non-baseline tool (outside numpy) is `load_bearing` for the admissibility claim, and its
  `load_bearing` status is backed by a PASSING CAPABILITY PROBE (the real criterion), not the assertion
  that it "feeds all_pass."
- FOREIGN_RUNTIME_MANIFEST + CANON_RUNTIME filled when Julia/JAX/PyTorch are actually called;
  `semantic_owner = julia` when Julia owns the algebra; no `.numpy()`/`np.asarray`/pickle/csv/pandas
  exchange across the runtime boundary.
- Run with the Makefile `PYTHON` interpreter (codex-ratchet env); exit 0 (`runs`) is necessary, not sufficient.

### Box (ii) — POSITIVE + BOUNDARY tests present and populated

- POSITIVE: admitted configs under `C`, MULTIPLE candidate states, expected admissibility from prior
  analysis, a SECOND-PROBE cross-check, and a surviving-alternatives note.
- BOUNDARY: a config near the admissibility edge, what `M` returns there, and a sharp-vs-gradient label.
- `all_pass` is `True` only if every admission test survived AND every exclusion test confirmed exclusion
  AND `criteria_checked` names exactly which criteria (C1/C2/...) were checked, with the result-file path cited.

### Box (iii) — ALL THE NEGATIVES (the flip-controls / falsifiers — must GENUINELY FIRE)

Exclusion is the PRIMARY signal; UNSAT is the primary proof form. Each falsifier below must actually
produce the OPPOSITE outcome IN THIS RUN, recorded with evidence in the negative/exclusion section. A
negative that returns the same result as the positive is a decorative stub and FAILS the box.

The fixed negative roster (every applicable one must fire at THIS layer's rung):

1. **PRODUCT-STATE-NEGATIVITY-ZERO** — a separable/product control yields ZERO entanglement negativity;
   entangled survivors yield strictly NONZERO. A product state with nonzero negativity = broken probe.
2. **PERTURBED-MARGINAL-FAILS** — a deliberately perturbed marginal VIOLATES the compatibility law
   `Tr_{A\B}(rho_A) ~_B rho_B` (the perturbed candidate is excluded). Proves the compatibility check has teeth.
3. **SCRAMBLED-PIN / SCRAMBLED-SHA** — scrambling the pinned anchor (SHA / frozen spectrum / pinned `rho(p)`)
   makes the integrity / spec-match check FAIL. A scrambled pin that still passes = pin not load-bearing.
4. **ALTERNATE-PROBE-FAMILY** — re-running under a different admitted probe family `M'` CHANGES the
   quotient/admissibility verdict where the claim says it should (and is invariant only where invariance
   is the claim). A probe swap that never changes anything = probe not resolving structure.
5. **LINEAGE-REMOVED-FAILS** — removing the declared ancestry (F01/N01 markers, the shared-object lineage
   id that defines "nested") makes the nesting/ancestry admission FAIL. Proves nesting was load-bearing, not labeled.
6. **REAL-vs-ERASED SMT FLIP** — the load-bearing z3/cvc5 proof is REAL -> UNSAT (or genuinely SAT) and an
   erased/negated-structure variant FLIPS for a MATH/STRUCTURAL reason (sign flipped, additivity negated,
   closure broken), NOT a count change. Each solver's real-and-erased verdicts recorded SEPARATELY.
7. **FAILING-CONTROL-MUST-FIRE (not-forced discriminator)** — the control that SHOULD survive the bare
   root actually SAT (e.g. associative quaternions passing the bare root so `forced=FALSE` is shown), and
   the structure excluded under the installed carrier constraint actually UNSAT. BOTH directions observed.
8. **VALUE-COUPLED GEOMETRY CONTROL** — a control differing ONLY in the load-bearing geometry (e.g. plain
   `S^2` vs nested Hopf running the SAME machinery) DECIDES load-bearing-vs-decorative: if the flat/alternate
   control REPRODUCES the law -> the nested geometry is decorative (demote); if it CANNOT -> nesting is
   load-bearing. The control is RUN, not asserted.
9. **FLIP-CONTROLS ON THE ENTROPY/NEGATIVITY DIRECTION** — entangled-vs-separable (or W-vs-GHZ
   admissibility, per-cut CKW) controls DIVERGE in the predicted direction across the cut lattice.
   Identical outputs for entangled and separable inputs flag a psi-INDEPENDENT (decorative) quantity.
10. **PER-RUNG LADDER NEGATIVES** — the negatives FIRE at EACH claimed rung, not only at 1q. A control that
    fires at 1q but is absent at 2q/3q does NOT discharge the ladder.
11. **NO DECORATIVE NEGATIVES** — every negative/flip/falsifier produces the opposite outcome in this run,
    recorded with evidence. A negative-control section that never diverges from the positive is decorative.
12. **BYTE/EXACTNESS-CLASS STABILITY AS A NEGATIVE TELL** — if `all_pass` is byte-identical across engines
    that should compute by DIFFERENT methods, treat it as a decorative-proof tell (mirroring, not
    independent confirmation). Agreement must be on INVARIANTS to the exactness class; a blind-method
    mismatch is a finding-to-reconcile, not an auto-fail.

A negative on this roster that does not APPLY at a given layer (e.g. no SMT proof at this rung) is marked
`N/A with reason`; a negative that applies but does not fire FAILS the box.

### Box (iv) — QUBIT-LADDER DEPTH to useful + one beyond

- Per-rung evidence across a ladder of Hilbert-space depths UP TO a DECLARED useful depth PLUS ONE step beyond.
- 1q RUNS but is NOT valid alone: a validity-claiming sim that is 1q-only VIOLATES the gate. Only an honest
  non-validity-claiming `scratch_diagnostic` / `classical_baseline` / `tool_lego_fit_probe` packet may be 1q-only.
- The QIT floor is 3Q; 1Q/2Q never prove a multi-qubit claim.
- The packet records `ladder_useful_depth` + its evidence and `ladder_one_beyond` + its evidence.
  (Enforced by `validate_qubit_ladder_depth.py`.)

### Box (v) — PASSES THE FULL AXIOM-GROUNDED GATE STACK

Every applicable gate below returns clean on THIS packet (the GROUNDED gates from the v7 gate-grounding law;
the four FLAGGED schema gates are process hygiene, not admission gates, and are not folded in here):

- `validate_math_only_packet.py` — math-only / definedness. NOTE: the gate is CURRENTLY a ~17-token
  BLACKLIST; the axiom-true target is the b_kernel definedness ALLOW-LIST (L0's 19 primitives or earned
  registry admission). This box requires the ALLOW-LIST intent, and FLAGS the blacklist-vs-allow-list gap
  rather than treating a blacklist-pass as definedness-complete. RESOLUTION PATH:
  `v7_gate_grounding_law_DRAFT_20260614.md` Part 4 (the definedness fence), gated on the admitted-math-term
  registry prerequisite; until that lands, a blacklist-pass satisfies this box only PROVISIONALLY and the
  gap is NAMED in the layer's ledger row.
- `validate_name_math_correlation.py` — any name token claiming math evidence has the math present, with
  F01/N01 lineage; no bare derived-only term (`equal`/`equality`/`identity`) smuggled in (DERIVED_ONLY_GUARD).
- `validate_two_tier_authority.py` — a positive verdict is externally affirmed by a COMMITTED audit
  receipt; a self-asserted positive with no committed audit authority is an overclaim and is rejected.
- `validate_smt_not_tautology.py` — any z3/cvc5 proof tagged `load_bearing` is GENUINE math structure
  (sign relation, holonomy, additivity, an inequality/winner between two DISTINCT measured reals), NOT a
  `count == constant`/`count == product` tautology; count-only proofs demote to `supportive`.
- `validate_three_engine_sim_result.py` (`--require-pytorch` for v1 envelopes) — Julia Canon authoritative
  + JAX batched/exhaustive workhorse + PyTorch graph/network/autograd; engine tool claims align with declared
  load-bearing packages; parity asserted on INVARIANTS to the exactness class (not echoed psi, not blanket
  byte-stability); a blind-method mismatch is a finding-to-reconcile, not an auto-fail.
- `validate_v7_admission.py` ancestry gate — any claim naming a downstream object (axis/manifold/bridge/
  engine) shows F01/N01 lineage in structured keys, and that lineage is itself admitted (no forward
  reference to an unadmitted antecedent) — the `M(C)` build-order embargo on the admission surface.
- `validate_result_integrity.py` — the SHA pin is a static finite anchor; no timestamp/working-tree drift
  relative to the pinned witness.
- `validate_qubit_ladder_depth.py` — box (iv) above, mechanically.

### Box (vi) — NESTED onto the prior layer via the compatibility law + extension fibers computed

- For every nonempty `A` and every `B subset A`: `rho_A in X_A^max` and `Tr_{A\B}(rho_A) ~_B rho_B` (the
  COMPATIBILITY LAW), with `G_A = InducedGeometry(X_A^max)` RECOMPUTED on survivors (geometry never relabeled).
- The extension fibers `F_n(rho) = { rho' : Tr(rho') ~ rho }` are ENUMERATED as data (fiber sizes recorded).
- RATCHET-WITHIN-LAYER: `X_{A,k+1} = { rho in X_{A,k} : C_{A,k+1}(rho, geometry ALREADY induced) }`, with
  geometry recomputed per constraint step (order-sensitive, no free-swap).
- The compatibility check is computed from partial traces, NOT by label echo (a fresh audit that finds
  label-echo compatibility FAILS this box — see the inverse-limit tower's own flip condition).
- WITHIN-PACKET NEGATIVE CONTROL (required): the packet includes a KNOWN-INCONSISTENT pair — a marginal
  that should NOT land in its parent class — and SHOWS the computed partial-trace check correctly REJECTS it
  while a label-echo would wrongly pass it. A box-vi with no such control is label-echo-untested and FAILS.

### Box (vii) — SECTION-5 PREDICTED-MODIFICATION forecast RECORDED AND CHECKED

- The packet records the section-5 forecast text for this rung (the predicted modified geometry: nested tori
  -> marginal-radius shells -> Schmidt strata -> rank-tuple lattice, per depth).
- The packet CHECKS the forecast against the COMPUTED geometry and records `forecast_matches_computed`
  per rung with the computed evidence (radii / rank tuples), not just the prediction.
- A layer that computed product-form geometry where the law forecasts the modified shell/strata form is
  WRONG even if forecast text was recorded — the CHECK must agree, not just exist.

### Box (viii) — FRESH-CONTEXT AUDIT (builder != auditor)

- The builder's verdict on its own work is NEVER evidence, and NO SINGLE MODEL is trusted. Validity
  requires a MULTI-MODEL CROSS-AUDIT: codex2 (the solid arbiter, across effort levels) + at least TWO
  VARYING finder models (grok / gemini / OpenRouter), each re-deriving from the artifacts INDEPENDENTLY in
  fresh context. The finder models' job is to FIND (hot/hallucinating is a FEATURE — the variation the
  strict gate selects on), NOT to authorize. Disagreements are HELD (not auto-merged, no majority vote) and
  resolved by the strict gate stack + codex2, not by vote. A single-model audit does NOT discharge this box.
- The cross-audit comes back clean on BOTH implementation and documentation before any `canonical by
  process` label.
- High-rigor closure applies because this work will be cited / used to change infrastructure.
- A build-self-assessment file marked `does_not_self_upgrade: true` is NOT a fresh audit; it is the build's
  own claim and leaves this box OPEN.

### Box (ix) — NESTING-LAW VALIDATION QUEUE position recorded

- The layer states WHERE it sits in the tower queue, so "done at this rung" is distinguished from "tower
  complete": `<=2Q tower launched` / `<=3Q on the 3Q v1 landing` / `flux-fate column` / `G2 attach after
  3Q v1` / `Spin(7)/triality/F4 named-not-scheduled`.
- A green box (i)-(viii) at one rung does NOT mean the tower is complete; the queue position is the honest
  scope statement.

### Box (x) — STATUS-LABEL HONESTY (binds the row)

- Report only `exists < runs < passes local rerun < canonical by process`; never imply a higher label from
  a lower one. Never write "verified/confirmed/all pass" without naming which criteria were checked and
  citing this session's result-file path. Trust the result-JSON over verdict prose.

### Box (xi) — CLAIM-CEILING FIELDS bound

- `claim_ceiling`, `next_lego_target`, `promotion_condition`, `blocked_until`, `demotion_condition`,
  `out_of_scope` all set; `surviving_alternatives` non-empty if any alternatives remain.

### Box (xii) — BUILD-ORDER / STAGE-GATE position correct

- The layer sits at the correct stage of the binding ORDER: tool -> tool-integration -> ALL lego rows one
  by one until the lego stage is complete (by current receipts/gates) -> couplings -> coexistence/topology/
  emergence -> bridge/axis. No coupling/pairwise/coexistence work is started on a few strong locals; no
  bridge/axis claim without steps 1-5 evidence.

### Box (xiii) — PER-LAYER ENTROPY / READOUT FAMILY DECLARED + NESTING-LICENSED (gcm SUPPLEMENT 2)

- The packet DECLARES this layer's OWN admissible entropy/readout family explicitly (von Neumann of WHICH
  reduced object, typed entropies, production-vs-content, conditional / coherent-information forms) — never
  "entropy" in general. Entropy is a DERIVED measure, not the master variable.
- The packet NAMES the nesting row that LICENSES that family: the lower layer (SAME carved object, SAME ID
  lineage) whose enabling state / cut / channel / record makes each entropy form available. Owner rule:
  "each layer can process different forms of entropy, and the nesting constrains that."
- An entropy/readout form used WITHOUT its enabling lower layer present = a VIOLATION the box FAILS
  (the entropy-type co-ratchet: a type is admissible only after its enabler exists).

### Box (xiv) — THE SEVEN AUDIT QUESTIONS answered (gcm SUPPLEMENT 1)

The packet answers all seven, each with a cited artifact path; "cannot answer" = not a full rich sim for
this layer and the box FAILS:

1. Which LAYER (from Part A)? 2. Which NESTING RELATION? 3. Which QUBIT DEPTH? 4. Which SURFACE / NETWORK
(the substrate the sim runs on — chart / spinor-surface / QCA ring-checkerboard)? 5. Which THREE ENGINES ran
(Julia canon + JAX batched + PyTorch graph/autograd), LOAD-BEARING not parity-decorative? 6. Which
ENTROPY/READOUT FAMILIES were VARIED (ties to box xiii)? 7. What BROKE when depth / nesting / surface was
REMOVED (ties to the box-iii negatives)?

---

## DONE rule (binding)

A layer is **DONE** (`canonical by process` at its rung) ONLY when boxes (i) through (xiv) are ALL checked
with cited artifact paths from this session, including box (viii) fresh-context audit. Otherwise its status
is the honest ladder label actually reached and the missing boxes are NAMED in the ledger
(`manifold_layer_ledger_20260614.md`). A green Part-B checklist at one rung is "this layer passes at this
rung," never "the tower is complete" and never a downstream physics/ToE/bridge/axis admission.

---

## Legacy-Label Quarantine

ASSISTANT-GLOSS: owner labels (terrain, engine-tier, axis, stage, runtime, shell, flux as a project noun,
rpf, retrocausal, possibility_field, ratchet, basin, gcm, allostatic, homeostatic, holodeck, rosetta,
manifold-as-project-noun, attractor, wiggle, nonclassical, overlay, Phi0, Xi) are NOT admitted math
vocabulary in this contract. Where the body needs the underlying math, the math object is named directly
(probe quotient `S/~_M`, partial trace `Tr_{A\B}`, Schmidt strata, von Neumann entropy `S_A`, cut lattice,
induced geometry `G_A`, Clifford `Cl(2n)`, G2 / Spin(7) / Spin(8) / F4 as standard Lie-group names). The
owner labels appear only as quarantined provenance, never as the noun a layer is built on.
