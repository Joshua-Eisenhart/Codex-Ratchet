# The Ratchet Runbook — DRAFT (owner doctrine, 2026-06-15)

**Status:** owner-authored doctrine, captured verbatim-faithful. DRAFT, not canon-by-process. This is the *process* spec (how to run the ratchet as a repeatable discipline across domains), complementing the *object* spec [[ratchet_definition_and_emergence_spec_DRAFT_20260614]] and the static-floor spec [[mss_and_rung_climb_foundations_DRAFT_20260615]]. The ratchet is a repeatable process that takes many apparent domains/perspectives and forces them through one admissibility machine.

**The missing explicit sentence:**
> The ratchet is the ordered process by which weak structures are tested against constraints, killed when they fail, and replaced only by the weakest stronger structure that preserves the lost distinction.

Sharper:
> The ratchet is how "same thing from different perspectives" becomes explicit without collapsing those perspectives into one premature model.

---

## 1. The root object
Everything starts as **constrained distinguishability** — not entropy, geometry, spinor, QCA, Hopfield, HR, or finance. All of those are **views/readouts** of constrained distinguishability:

```
entropy      = how many distinctions remain / are hidden / are erased
geometry     = relation-shape among distinctions
QCA          = local ordered update of distinctions
Hopfield     = memory-basin view of distinctions
QIT          = probe/cut/channel calculus of distinctions
spinor       = lifted carrier preserving phase/path/orientation distinctions
dictionary   = lexical/social distinction system
OpenHR       = career-potential distinction graph
OpenFinance  = resource/weakness/capacity distinction graph
LevOS        = executable graph/proof/runtime for admitted distinctions
```

Run rule: **do not ask "which one is fundamental?" Ask "what distinction does each view preserve, erase, or expose?"** (Consistent with the wiki frame: root = constraint on distinguishability; MSS = meta-gate not root ontology; density/spinor/geometric structure downstream unless forced.)

## 2. What makes it a ratchet
Four pressures: **F01 finitude** (finite candidates/supports/probes/receipts); **exclusion-first** (constraints kill/park/narrow); **N01 noncommutation** (order matters → history matters); **MSS / weakest-survivor gate** (never admit stronger structure if weaker carries the distinction). Irreversible because every admit/reject/park enters a ledger; a later layer cannot pretend an earlier failure did not happen.

## 3. The Ratchet Loop (every step has this exact form)
```
1. Object              — what finite thing is tested?
2. Perspective/Readout — which view (entropy, geometry, QCA, spinor, dictionary…)?
3. Weakest current structure — least-assumptive structure carrying the distinction
4. Constraint pressure — which constraint/probe/order/bracket/cut tests it?
5. Failure mode        — what distinction is lost, erased, merged, undefined?
6. Weakest lift        — next minimal stronger structure preserving that distinction
7. Projection back down — what does the lift reduce to under the weaker readout?
8. Residual            — what remains invisible/erased after projection?
9. Controls            — what would prove this was ornamental/metadata-only/label-forced?
10. Receipt            — ACCEPT / REJECT / PARK with evidence
```

## 4. The formal object (ratchet state)
```
R_t = (X_t, P_t, Q_t, G_t, E_t, H_t)
  X_t = current finite survivor set
  P_t = active probe family
  Q_t = quotient / visible distinction classes, X_t / ~P_t
  G_t = induced geometry / relation structure
  E_t = entropy-readout suite licensed at this layer
  H_t = history: receipts, graveyard, branch ledger, controls
```
Update: `X_{t+1} = { x ∈ X_t : Adm_C(x, P_t, Q_t, G_t, E_t, H_t) = 1 }`, then recompute `Q_{t+1}, G_{t+1}, E_{t+1}` on the *altered* survivor set (the nested-manifold correction: geometry recomputes after each carve; the next constraint acts on the altered geometry, not the original free one).

### 4a. Formal structure of the update (companion, Claude — to be fleet-vetted)
The supplied update operators `{σ_i}` (each `σ_i(X) = {x ∈ X : Adm_{C_i}(...)}`) are **contractions** (`σ(X) ⊆ X`) and generate a **finite transformation monoid** on the survivor lattice. Reading: **finitude+DCC are forced** (give termination); the **monoid `⟨σ_i⟩` is supplied** (this is the §2 N01 pressure made structural — and the fleet's correction that dynamics is installed, not derived). Concrete controls for §9: a genuine ratchet step is **non-commutative** (generators don't commute) AND **aperiodic / group-free** (a reversible step would be a group element → Krohn-Rhodes reset/flip-flop = memory-with-no-undo). Both are decidable finite checks; the J-order of the monoid IS the ratchet's "order."

## 5. Weakest-possible-structure ladder (the main discipline)
Start with the weakest thing that could carry the distinction; lift only on proven failure.
```
0. no primitive identity
1. finite distinguishability
2. finite support S
3. probe family P
4. quotient S/~P
5. admissible survivor set M(C)
6. ordered local update
7. ring-checkerboard / finite run-surface
8. entropy/readout suite
9. state functional ω
10. density/operator ρ, only if forced
11. Hopf/projective lift, only if quotient erases phase/path
12. Weyl/spinor lift, only if orientation/chirality/720°/path data matters
13. Clifford / G-structure, only if closure demands it
14. tensor/cut/correlation geometry
15. smooth manifold / metric / field language as late approximation
```
Every arrow must answer: what failed below? what distinction was lost? why is this the weakest repair? what does it project back to? what residual does it preserve? (The manifold is the *history of presuming less, then ratcheting only where weaker structure fails.*)

## 6. "Many things are the same thing" → one-object / many-projections registry
For every concept, a row: `Name / Root object (= constrained distinguishability) / View type / What it preserves / What it erases / Weakest layer / Stronger lifts / Controls / Status`. Rule: **different domains are not different roots — they are different licensed projections of the same constrained-distinguishability process.** This prevents false separation. (Operationalized by `one_object_many_projection_registry_v0`, §10.1.)

## 7. Ratchet status labels (no unlabeled enthusiasm)
```
RAW_INTUITION      owner idea, not yet structured
PERSPECTIVE_ROW    mapped as a view of constrained distinguishability
CANDIDATE_OBJECT   has object/probe/constraint form
SCRATCH_DIAGNOSTIC sim/reasoning exists, no promotion
PASS_LOCAL         local rerun passes
ADMITTED_LAYER     survives controls and receipts
PARKED             plausible but not currently load-bearing
REJECTED           killed by control, contradiction, or stronger/weaker failure
GRAVEYARD_KEEP     rejected but kept as warning/comparison
```

## 8. The actual run order
- **Phase A — Root compression.** Force every idea into: "This is a view of constrained distinguishability as ____."
- **Phase B — Weakest-carrier test.** Can finite support + probes + quotient carry it? If yes, do not lift. If no, document the failure.
- **Phase C — Projection test.** For every stronger structure (spinor→density→vector; private graph→public credential; operating reality→KPI): what did the quotient erase? was the erased thing load-bearing? (Canonical spinor example: density quotient kills global spinor phase, lifted path, 720° return, holonomy conventions, chirality/lift, some bracketing.)
- **Phase D — Controls.** label shuffle; metadata-only; same-cardinality different-adjacency; commuting-order; random-support; quotient-erasure; lower-layer-can-do-it. If lower structure does the same work, **demote the lift.**
- **Phase E — Receipt and ledger.** ACCEPT / REJECT / PARK / KEEP-as-graveyard. No ambiguous "interesting."

## 9. Ratchet agents (five roles; Minimalist goes FIRST)
```
1. Mapper          — converts ideas into one-object/many-projection rows
2. Minimalist      — argues the weaker structure is enough  (GOES FIRST)
3. Lift Advocate   — argues the stronger structure is needed
4. Control Auditor — designs controls that could kill the lift
5. Receipt Clerk   — updates status, graveyard, branch ledger, next sim queue
```
> Presume less before admitting more.

## 10. The sim queue that makes it real (do not jump to the whole theory)
```
1. one_object_many_projection_registry_v0       map entropy/geometry/QCA/Hopfield/spinor/dictionary/OpenHR/OpenFinance as projections
2. weakest_structure_ladder_gate_v0             per projection: weakest carrier + first known failure
3. entropy_geometry_coratchet_floor_v0          capacity/quotient entropy + geometry from finite support
4. ring_checkerboard_support_three_presentation_consistency_v0   flat/spherical/nested-ring agree or fail
5. quotient_erasure_discriminator_v0            what density/vector/public-score readouts erase
6. spinor_quotient_freedom_discriminator_v0     when spinor/lift is load-bearing vs ornamental
7. geometric_constraint_ratchet_v0              ordered constraints → recompute survivor/geometry/entropy per carve
8. openhr_openfinance_as_social_ratchet_v0      same process over social/business dictionaries
```

## 11. Core doctrine to give agents (top of every run)
```
Do not unify by flattening.
Unify by finding the common root process: constrained distinguishability.
Every domain is a perspective/readout of that root.
Every stronger structure is guilty until weaker structures fail.
Every quotient must report what it erases.
Every admitted layer must project back down.
Every failure must enter the graveyard.
Every acceptance needs controls and receipts.
```

## 12. Shortest usable runbook
```
FOR EACH idea/domain/layer:
1. Translate: "This is constrained distinguishability viewed as ____."
2. Find weakest carrier (finite support, probe quotient, ordered update…).
3. Test whether weaker carrier preserves the needed distinction.
4. If yes: reject/demote stronger layer.
5. If no: define exact failure.
6. Admit weakest stronger lift only.
7. Project back down and list erased residuals.
8. Run controls.
9. Record status: accept / reject / park / graveyard.
10. Add next sim/proof obligation.
```

## 13. Workflow discipline (runtime gates — added 2026-06-15 after the first full run + Hermes audit)
Every ratchet workflow MUST obey these or it does not count as a run:
1. **THREE separate axes — never collapse them, and `evidence_grade` is NOT promotion** (codex/Hermes audit):
   ```
   lifecycle_status: RAW_INTUITION|PERSPECTIVE_ROW|CANDIDATE_OBJECT|SCRATCH_DIAGNOSTIC|PASS_LOCAL|ADMITTED_LAYER|PARKED|REJECTED|GRAVEYARD_KEEP
   evidence_grade:   none | adjudication_only | evidence_grade   # adjudication=multi-model says likely; evidence=an EXECUTABLE non-definitional flip ran
   claim_ceiling:    scratch_diagnostic | pass_local | admitted_layer
   ```
   A row can be `evidence_grade` while still `scratch_diagnostic` — evidence-grade does not raise the claim ceiling. Refuted sims emit `classification: broken`, `graveyard_keep: true`, `accepted_claims: []`, `rejected_claims: [...]`, and `evidence_eligible: false`; the ladder gate dereferences these (fail-closed) and will not let a refuted/broken/stale/circular sim back an evidence_grade row.
2. **Role-failure reroute (no fake full-run).** If a required role/model fails, quota-caps, or emits null: reroute once to an alternate model class; if still missing, mark that row `PARTIAL`, not full. (Live example: gemini quota 429 killed the Minimalist on 2/4 projections AND the holonomy audit — those were PARTIAL, not full.)
3. **Minimalist-first is mandatory** (enforces MSS): Minimalist runs first ("can the weaker structure do this?"); only on "no" does the Lift-Advocate argue; then the Control-Auditor tries to kill the lift.
4. **Every gate needs a bias-check.** A strict gate that rejects a lift needs a control proving it is not rejecting BY CONSTRUCTION. The control must FLIP — and the flip must NOT be definitional. ONE genuine non-circular bias-check exists: `finite_contextuality_assignment_smt_lift_discriminator_v0` (contextuality, z3+cvc5 UNSAT↔SAT — a real feasibility solve). The holonomy attempt `finite_cycle_z_n_holonomy_section_lift_discriminator_v0` was judged CIRCULAR by the fleet (6/6: `lift_forced := not section_exists` bakes the flip in) — a cautionary example: a flip that is a definitional restatement is not a bias-check.
5. **F01 is a declared SCOPE BOUNDARY, not an empirical discriminator** (codex/Hermes correction). Under F01 continuous carriers are OUT OF SCOPE by axiom — this does NOT "prove continuous lifts unnecessary." Caveat 3 is therefore *converted into a finitude/scope statement*, NOT "solved by evidence." Write it exactly that way: do not claim F01 empirically refutes the continuum.
   - **And beware the dual tautology trap:** "no lift forced beyond the quotient" is near-trivially true under finitism (finite data has finite look-up models), and means *underdetermined by this probe*, NOT *spurious*. A "lift" earns admission only if it COMPRESSES/PREDICTS new (held-out / unobserved-context) distinctions — not by re-encoding observed statistics. Context-indexing a model is a LIFT (the context-label is structure), not a free quotient, unless a strict structure-preserving criterion is met.
6. **Capstones are `DRAFT_UNAUDITED` until a fresh-context audit returns.** Do NOT commit a claim-bearing capstone result as earned before fresh-context critics + arbiter finish. (Live failure: the `contextuality_as_installed_context_independence` capstone was committed + celebrated, then the deep audit found it a by-construction tautology. Audit the capstone hardest, not least.)
6. **Standard workflow receipt schema** (every ratchet workflow returns this; "nice synthesis" never replaces it):
   ```yaml
   artifact_paths: []
   commands_run: []
   model_roles_completed: []
   model_roles_rerouted: []      # or model_roles_partial
   controls_executable: true|false
   status_ceiling: SCRATCH_DIAGNOSTIC|ADJUDICATION_GRADE|EVIDENCE_GRADE
   what_was_killed: []
   what_survived: []
   next_required_discriminator: ""
   ```
7. **Every adjudication must become a discriminator.** When the ledger names the next test, build+run it — no asking. (And expect the barrier to find the first discriminator circular, as it did the holonomy one — that is the loop working.)

## Final formulation
The ratchet is not a list of favorite structures. It is the process that prevents favorite structures from entering too early. It begins with constrained distinguishability and the weakest possible survivor. Ordered constraints carve the survivor set; after every carve, geometry and entropy are recomputed. A stronger structure is admitted only when the weaker loses a distinction that remains load-bearing under active probes. All apparent domains — entropy, geometry, spinors, QCA, Hopfield, dictionaries, OpenHR, OpenFinance, Leviathan, LevOS — are projections of the same root process, not separate roots.

> **The ratchet is disciplined non-collapse: preserve many perspectives as projections of one root process, while admitting stronger structure only when weaker structure provably fails.**
