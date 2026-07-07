---
title: Axes 0-6 Full Layout, Relation Algebra, and Anti-Conflation Rules
created: 2026-07-03
updated: 2026-07-03
type: concept
tags: [concept, axes, qit, relation-algebra, anti-conflation, xor, orthogonality, source-extraction, measured]
framing: nominalist-constraint-admissibility
status: source-faithful extraction + measured matrix; claim ceiling scratch_diagnostic; no canon promotion
supersedes-extends: concepts/igt-axes-terrain-source-extraction-2026-06-04.md (extends; that doc remains the symbolic/routing source layer)
sources:
  - "~/Codex-Ratchet/system_v7/sims/AXES_FULL_EXTRACTION_20260703.md (repo commit f53880681)"
  - "~/Codex-Ratchet/system_v7/sims/AXIS_RELATION_ALGEBRA_EXTRACTION_20260703.md (repo commit 34d817e34)"
  - "~/Codex-Ratchet/system_v7/sims/axis_relation_matrix_probe_v0/ (repo commit 95df90d4d)"
  - "system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md"
  - "system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md"
  - "system_v7/constraint_core/reference_docs_from_josh/physics_program/working_math_scaffold_20260609.md"
  - "system_v7/constraint_core/reference_docs/engine_math/igt-pattern-explicit-math-reference.md"
  - "system_v7/constraint_core/reference_docs/engine_math/ENGINE_64_SCHEDULE_ATLAS.md"
  - "system_v6/receipts/owner_doctrine_axes_7_12_and_engine_capability_20260612.md"
---

# Axes 0-6: full layout, relation algebra, anti-conflation — 2026-07-03

Everything below is doc:line-cited in the two repo extraction files (sources
list). Status labels are per-source; nothing here is canon. Measured claims
cite the axis_relation_matrix_probe_v0 results (numpy+julia parity, 0 diffs).

## 0. The global lock

Axes are READOUT MAPS `A_i : M(C) -> V_i`, never primitive coordinates
(Scaffold:109; Deep:24-32). Terrains AND flux are geometry on the manifold,
not axes; flux is a candidate current family, "never as axis content"
(Scaffold:278-287, 309-311). An axis may READ geometry; it may never BE flux,
holonomy, or nesting. (Owner correction 2026-07-03: "I made mistakes putting
geometry in the axes" — the scaffold already carried this rule.)

## 1. Per-axis layout

### Axis 0 — the drive
- Splits {Ne,Ni} vs {Se,Si}: allostatic vs homeostatic polarity.
- Chart readout: `b0 = sign(cos 2eta) = sign(r_z)`, threshold eta=pi/4.
- Doctrine target (bridge form): `Phi_0(rho_AB) = -sum w_r S(A_r|B_r)
  = sum w_r I_c(A_r>B_r)` AFTER the bridge `Xi : geometry/history -> rho_AB`.
- STATUS: source-backed candidate; Xi bridge OPEN (the largest Axis-0 gap).
  Entropy-only readings structurally fail: entropy sees only Axis-1;
  Axis-2 is identically entropy-blind (two-sector theorem). Owner stance
  2026-07-03: proposed model may be correct, needs dual-ratcheting, NOT canon.
- Live alternatives held: local b0; averaged-state entropy; cut
  coherent-information functional; Xi_ref / Xi_shell / Xi_hist.

### Axis 1 — branch split (derived)
- Splits {Se,Ni} vs {Ne,Si}. Signs: chi1(Se)=chi1(Ni)=+1, chi1(Ne)=chi1(Si)=-1.
- KERNEL: unitary `Phi(rho)=U rho U†` vs proper CPTP `Phi(rho)=sum K rho K†`.
- Overlays (NOT kernel): isothermal/adiabatic, bath-gating, black/white layer.
- STATUS: source-locked semantic split; Axis-1 alone does not identify terrain.

### Axis 2 — representation frame
- Direct {Se,Ne} vs conjugated {Ni,Si}. Signs: chi2(Se)=chi2(Ne)=-1,
  chi2(Ni)=chi2(Si)=+1.
- KERNEL: direct `rho~=rho` vs conjugated `rho~=V_s† rho V_s` with transport
  correction `K = i V† V-dot`.
- MEASURED FACT (2026-07-03): identically entropy-blind — dS=0 exactly for any
  frame rotation (webui, 1.6e-15 over 200 states) = the two-sector theorem.
  Earned rosetta labels: Axis-2 = adiabatic/isentropic sector, Axis-1 =
  entropy-carrying sector — LABELS for measured behavior of pure moves only;
  composed engine legs do NOT sort this way (see 3d).
- STATUS: source-locked, strongest lower-stack anchor.

### Axis 3 — loop class (OPEN, contested)
- Strongest reading: fiber vs lifted-base on the spinor curves.
  Fiber `gamma_f(u) = psi(phi0+u, chi0; eta0)` — density STATIONARY (inner).
  Lifted-base `gamma_b(u) = psi(phi0 - cos(2 eta0) u, chi0+u; eta0)` — density
  TRAVERSING, horizontal `A(gamma_b-dot)=0` (outer).
- TWO b3 readouts, never conflate: geometry path (fiber|lifted_base) vs XOR
  chart-role (outer=+1, inner=-1). Type 2 SWAPS chart roles; the b6 law
  consumes chart-role, never raw path. Receipts must record BOTH.
- Live alternatives: L/R chirality; Type1/Type2 inversion; flux in/out.
  Flux discipline: Axis-3 may read loop class but does not OWN flux;
  flattening fiber/base is a flux CONTROL, not an Axis-3 identity.
- Proposed discriminator (wiki 2026-06-04): 16-row token table + density-motion
  observable, scored against inner/outer vs chirality vs Type partitions,
  with shuffle/chirality/path/degenerate-eta controls. NOT YET RUN.

### Axis 4 — loop order
- Inductive vs deductive. `Phi_D = U o E o U o E` vs reversed `Phi_I`;
  generator form `e^(tau_R L_R) e^(tau_C L_C)` vs reversed.
- First nontrivial difference ~ `tau_R tau_C [L_R, L_C]`.
  Witness: `||Phi_D(rho) - Phi_I(rho)||_1`; collapses under commuting controls.
- STATUS: strong runtime anchor (ax4 julia receipt). Taijitu spin-direction
  symbolic assignment OPEN (owner-reserved). No canonical +/- sign for b4.

### Axis 5 — operator family
- {Ti,Te} pinching/dephasing semigroups vs {Fi,Fe} rotation/unitary groups.
- Witnesses: entropy/purity/contractivity (T side) vs orbit/spectrum
  preservation (F side). T: dS>0 possible; F: dS=0.
- STATUS: strong. S-curve/lobe overlays open. No canonical +/- sign for b5.

### Axis 6 — composition precedence
- Token: up = operator written first; down = terrain written first.
- Channel order `Phi_T o O` vs `O o Phi_T`; primitive action side
  `L_A(rho)=A rho` vs `R_A(rho)=rho A`; gap `||A rho - rho A||_F`.
- Rows must record token_precedence, action_side, closure_type (primitive side
  actions are not physical channels without closure).
- LAW: `b6 = -b0*b3` (chart-role b3). Highest geometry-contamination risk.

### Axes 7-12 — informal tier
- "A big game-theory map"; each IGT agent carries a full engine; many-agent
  interaction readouts mirroring 1-6. Gated behind shell-local -> pairwise ->
  coexistence; no 7-12 packet may jump the coupling ladder (owner receipt
  2026-06-12).

## 2. The relation algebra (laws)

| Law | Form | Status |
|---|---|---|
| Axis-0 parity | `a0 = a1 XOR a2`; sign `chi0 = chi1*chi2` | dual-solver FORCED unique (z3+cvc5); erasing Ni constraint breaks uniqueness; not linearly separable (why single-readout Axis-0 attempts fail). THREE OBJECTS, never conflate: a0_discrete (terrain-sign XOR), b0_chart (sign cos 2eta), A0_bridge (Phi0 o Xi) — the XOR law is proven on a0_discrete; no eta-space flip-location theorem exists yet (open falsifier: perturb eta near pi/4, test whether discrete XOR predicts flip loci) |
| Axis-6 bilinear | `b6 = -b0*b3`, coefficient -1 uniquely forced, no linear law | dual-solver forced; MEASURED on the Type-1 GKSL engine: holds on all 48 defined rows. CHART-LOCAL: the SMT proof and the measurement consume chart/probe b0 (sign r_z), NOT bridge-A0 — the law is provisional until the Xi bridge exists (referee-adjudicated 2026-07-03) |
| Derived 3-axis | `b6 = -(b1*b2)*b3` via `b0 = b1*b2` | composition of the two laws; Axis-6 is downstream of three axes |
| Topology join | `A1 x A2 -> terrain`: CPTP/direct=Se, CPTP/conj=Ni, unitary/direct=Ne, unitary/conj=Si | source-locked; terrain is a function/readout table from the A1 x A2 readout values — the 4 functions are indexed by the product, not primitive |
| Token identity | `A1 x A2 x A5 x A6 = 16 ordered tokens` | counting law |
| Loop-placement | `A3 x A4 x A5 x A6 = 8 paired signatures, NOT 16` | same signature pairs two topology rows -> engine type NOT recoverable from A3xA4 alone |
| Terrain placements | terrain x sheet x path = 16 placements | generator/path objects, joined to tokens only by the engine chart |
| Access law | 8-of-16 forced (SMT) | manifold_laws_smt_proof |

Free-DOF structure: b1, b2, b3, b4, b5 are primitive free (5-free lattice,
coratchet_axis_orthogonality); b0 and b6 are DERIVED.

## 3. Measured matrix (axis_relation_matrix_probe_v0, Type-1 GKSL engine)

56 rows = 8 stages x 2 traversals x 7 states. numpy+julia parity 0 diffs.

a. `b6 = -b0*b3`: HOLDS, all 48 defined rows.
b. `a0`: honestly undefinable (no Xi bridge) — skipped.
c. Above 95% permutation null: a1-a5 and a4-b3 (both dual-SMT gated).
   - a4-b3: STRUCTURAL COUPLING within Type-1 — only 4/8 (a4,a6,b3)
     combinations reachable; the chart ties outer=deductive/inner=inductive.
     PREDICTION (falsifiable at type2 build): pooling Type-2 rows (opposite
     pairing) restores independence, 8/8 reachable. If not, coupling is
     deeper than type.
   - a1-a5: RESOLVED (v0.1, 2026-07-03): with the terrain-branch kernel
     (chi1 signs), a1_branch-a5 NMI = 0.000000 exactly, 4/4 combinations
     reachable — INDEPENDENT; the v0 proxy a1_opchar-a5 NMI = 1.000000 (it
     was the A5 bit renamed). Trap confirmed live; 5-free-DOF algebra upheld.
     Both proxies kept in the results as the anti-conflation teaching receipt.
   - a6: separable (confirmed own DOF).
d. Entropy-gradient sorting NULL at engine-leg level (entropy_gradient_axis
   probe, commit 89c58a893): no axis (nor operator class, 84th pct < 95% bar)
   sorts per-leg dS around real traversals — composition mixes terrain
   dissipation into every leg. Isolated-move adiabatic/isothermal split is
   real but near-definitional; it does NOT survive composition. Entropy does
   not factor along the loop legs.

## 4. Anti-conflation rules (one measurement each)

| Trap | Discriminator |
|---|---|
| Axis vs terrain/operator/token/engine layers | axes are projections over M(C); never absorb generators/channels/grammar/composition into an axis |
| A0 chart vs A0 bridge | `sign(cos 2eta)` is NOT `Phi0(Xi(.))`; bridge needs actual rho_AB / cut coherent information |
| A0 drive vs A5 entropy/dephasing | cut/feedback polarity vs fixed-algebra contraction+purity; different observables |
| A1 branch vs A5 operator family | A1xA2 topology-join test vs PTM/invariant operator split (the trap the v0 probe hit) |
| A2 frame vs A3 chart/path role | gauge/transport term (K_t) vs density-stationary/path-horizontal witness |
| A3 vs A4 vs A6 (three order-ish axes) | three different norms: `||rho_path(u)-rho(0)||` (A3) vs `||Phi_D-Phi_I||_1` (A4) vs `||A rho - rho A||_F` + closure (A6) |
| A3 raw path vs A3 chart role | Type-2 swaps roles; record geometry_path AND chart_role in every receipt |
| A4 CW/CCW overlay vs runtime order | predeclared symbol coding must predict the finite order split under commuting controls |
| A5 S-curve/lobe overlay vs family split | entropy/purity/orbit split must beat label shuffle |
| A6 token vs action side | related, not identical; record token_precedence + action_side + closure_type |
| 16 tokens vs 16 terrain placements | different objects; joined only by the engine chart |
| Flux as axis content | BANNED until admitted; ablation battery: remove chirality, flatten fiber/base, collapse seats, remove operator action, scramble scalars |
| IGT/Jung/I-Ching labels vs math | correlation layers; label shuffle must fail while operation-grounded claims survive |

## 5. Type-1 vs Type-2 (the non-reduction)

The docs refuse both reductions: NOT flux alone, NOT A3xA4 alone. Type 1 =
left / flux IN / H=+H0; Type 2 = right / flux OUT / H=-H0; atlas hard
non-claims: `type != flow != chirality != precedence`; "other flux-split
mechanisms remain open". The same (A3,A4) pairs occur in BOTH types (Type-1
outer=deductive, Type-2 outer=inductive), so type = combined chart vector:
sheet/chirality/H-sign + IN/OUT orientation + A3 loop-class placement + A4
order class. Flux may later COMPRESS part of the distinction; it is not
admitted as its definition. (Owner fork 2026-07-03 held: Reading B — flux in
the geometric constraint manifold, A3 = outer/inner on nested Weyl/Hopf —
is the closer reading, plus the sheet/H-sign ingredient.)

## 6. Open queue

- Xi -> rho_AB bridge extraction (Axis-0's missing object; load-bearing rung).
- Axis-3 discriminator sim (16-row token table + density-motion observable).
- a1 kernel re-extraction (v0.1 of the matrix probe) — resolve a1-a5.
- Type-2 build with the a4-b3 independence-restoration prediction as
  acceptance test.
- A0-A4 and A0-A5: no law, no independence statement — unmeasured pairs.
- Taijitu spin (A4 symbolic sign) — owner-reserved.
- 64-schedule dynamic distinctness/visitation — not established.

## 7. Referee round (2026-07-03, post-publication)

Three external referees (2x kimi, 1x qwen, verified) attacked this doc and the
ratchet formalization; codex adjudicated against sources. LANDED and repaired
above: chart-locality of both laws (a0_discrete/b0_chart/A0_bridge split),
XOR discrete-vs-continuous hole (flip-location falsifier queued), product
wording. LANDED on the ratchet spec (obligations added to its open list, repo
extraction doc): R5 fresh-token identity criterion missing; R6 mu needs
codomain/order/objective non-step predicate; observable-quotient criterion
underdefined; Xi_ref lacks quotient-lifting (demote to discriminator-only or
add the lift). MISREAD (held for the record): R3 counterexample fails
(intersections commute, as the spec says); R2/R5 compatibility needs the
new-branch identity caveat. Full adjudication in repo:
system_v7/sims/ (referee JSONs in session scratchpad; adjudication receipt).
