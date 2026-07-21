# 02 — Layers 0-4: the primitive through the eight terrains, in explicit detail

## Bottom line

Layers 0-4 name: the declared primitive (0), the qubit carrier and its Hopf
map (1), the nested-torus geometry and its flux (2), the two Weyl-chirality
sheets (3), and the eight terrain generators (4). Every layer from 1 to 4
has a genuine, machine-checked core. Every layer from 1 to 4 also carries at
least one control that a 2026-07-20 fresh audit found to be
by-construction — unable to fail regardless of the physics — and at least
one independent, more skeptical 2026-07-11 audit that reads the same
territory and returns `NOT_ADMITTED` rather than `EARNED`. Layer 0 has no
sim status at all: it is the declared root, not a computed result, and both
the primary ledger and the independent audit agree on that point without
qualification.

The single most load-bearing finding for this file: the "two Weyl sheets"
claim (Layer 3) is real as an algebraic conjugation identity (ρ_R =
conj(ρ_L) exactly reverses flux and Berry phase) and is not established as
two independently-verified physical chiralities. Three separate sources —
the primary ledger's own header caveat, an independent 2026-07-11 audit,
and a 2026-07-20 fresh audit of the newest sims — converge on that same
qualification from three different angles. That is a genuine convergence,
named as such below, not a single source repeated three times.

## Scope and sources

Read for this file:

- `system_v7/constraint_core/MODEL_LAYER_LEDGER.md`, Layer 0-4 sections
  (lines 1-100), plus UP-121, UP-139, and UP-142 (later addenda in the same
  file, located by grep, not in the original read list, pulled in because
  the task asked for the QGT weld and the Spohn/Uhlmann pair by name and
  those objects live only in these addenda, not in the Layer 0-4 block
  itself).
- `system_v7/constraint_core/ratchet/manifold_evidence/MANIFOLD_RATCHET_STATE_REPORT.md`
  in full (377 lines). This read is not optional: `system_v7/constraint_core/CLAUDE.md`
  states as a binding instruction, "Before discussing any manifold layer,
  read `ratchet/manifold_evidence/MANIFOLD_RATCHET_STATE_REPORT.md`," and
  this file discusses manifold layers throughout.
- `system_v8/nested_manifold/rungA_carrier_to_flux.py` and
  `system_v8/nested_manifold/rungB_sheets_sixteen.py`, full source, plus
  their raw receipts (`system_v8/nested_manifold/results/rungA/receipt.json`,
  `.../rungB/receipt.json`) — read directly, not taken on any summary's
  word. Every rungA/rungB number cited below is read from these two JSON
  files.
- `system_v8/nested_manifold/results/RUNGS_ABCE_AUDIT_VERDICT.md` (the
  2026-07-20 fresh audit).
- `ROOT/ROOT_CARD.md` in full.
- `system_v8/nested_manifold/manifold_one.py` (docstring only, for how
  rungs A/B/C/D/E compose) and `system_v8/nested_manifold/rungC_joint_cuts.py`
  (header and checks list only, to test the ROOT_CARD citation below — see
  the QGT section).
- `system_v8/negative_sims/commuting_flux.py` and its receipt — found via
  ROOT_CARD's own citation, not the original read list; read because it
  reuses rungA's own functions and bears directly on Layer 2.

Evidence-tier discipline used throughout: numbers attributed to a receipt
JSON I opened directly (rungA, rungB, the audit verdict, commuting_flux)
carry the tag `[receipt-verified]`. Numbers attributed to UP-121/UP-139 or
the state report's own prose carry the tag `[ledger-reported]` or
`[state-report]` — I read that prose directly, but did not re-open the
older system_v7 sim scripts or their raw result JSON behind UP-121/UP-139
in this session.

## A numbering collision, named before anything else

This repository uses the word "layer" for at least three incompatible
numbering schemes, and the state report itself flags this in its own
section 5 ("Numbering and source integrity"). This file uses exactly one
of them — the one the task's own layer descriptions match verbatim — and
names the other two so they are never silently cross-wired.

1. **Primary ledger scheme (used by this file).**
   `MODEL_LAYER_LEDGER.md` Layer 0 = foundation, Layer 1 = the carrier
   (H = C², Hopf fibration), Layer 2 = geometry (nested Hopf tori + flux),
   Layer 3 = Weyl sheets, Layer 4 = the eight terrains, continuing to
   Layer 17. This is the scheme named in the build task and the one used
   below.
2. **"Manifold spine" scheme.** The same ledger file, much later (lines
   957-1040), restarts a *different*, finer-grained L1-L4 under the
   heading "MANIFOLD SPINE RATCHET," explicitly marked `[hypothetical
   lane]`: L1 = probe-quotient floor, L2 = density-rank strata + partial-
   trace marginals, L3 = spinor/phase/projective surface + Hopf skeleton,
   L4 = local Weyl factors (state *factorizability*, i.e. whether a
   multi-qubit state is a tensor product — not chirality). This is the
   scheme the `MANIFOLD_RATCHET_STATE_REPORT.md` audits, L0 through L15+.
   Its L4 is not the primary ledger's Layer 3; the word "Weyl" names two
   unrelated objects across these two schemes.
3. **`nested_manifold` rung scheme.** rungA's own docstring numbers its
   internal layers L2 (density carrier) through L6 (chirality); rungC
   continues to L7 (joint cuts). This is a third, independent count, again
   overlapping in digits with schemes 1 and 2 while naming different
   content at each digit.

Below, "Layer N" (capitalised, no "L" prefix) always means scheme 1. Where
scheme-2 or scheme-3 evidence is cited, it is written as "the state
report's L*N*" or "rungA's internal L*N*" to keep the schemes visibly
separate.

## Status-label key

- `EARNED` / `CANDIDATE` / `OPEN` — the primary ledger's own three-way
  label, as printed in that file. Reproduced here as a quotation of the
  ledger's claim, not independently upgraded.
- `exists < runs < passes local rerun < canonical by process` — the
  project's status ladder (`CLAUDE.md`). Nothing in this file reaches
  `canonical by process`; the ceiling on every sim named below is
  `scratch_diagnostic` / `promotion_allowed: false`, stated explicitly in
  every receipt.
- `genuine (can-fail)` vs `by-construction (cannot fail)` — the 2026-07-20
  audit's own distinction, applied per check, not per file. A file can
  contain both kinds of check.
- `NOT_ADMITTED` — the state report's own verdict token: the script passed
  locally, but the object it names has not been shown forced from a prior
  admitted layer.

## Master table

| Layer | Geometry object | Entropy functional | Formal names | Nicknames / jargon | Sim status |
|---|---|---|---|---|---|
| 0 — foundation | none; declared primitive only: a probe-relative indistinguishability relation ~ under an active probe family M | none primitive; no scalar entropy at this layer | constrained distinguishability; probe-relative indistinguishability; root axiom a=a iff a~b; F01 (finitude), N01 (order/history) | "the primitive," "the root," entropic monism's "one substance" | `ROOT_DECLARED`, not a computed layer. Ledger 0.0-0.4 and the state report's L0 agree without qualification: nothing here is earned, nothing here is meant to be. |
| 1 — carrier | H = C²; ρ = (1/2)(I + r·σ); Hopf map π(ψ) = (2Re(z1*z2), 2Im(z1*z2), \|z1\|²-\|z2\|²) sending S³ → S² | von Neumann S(ρ) = −Tr[ρ log ρ]; S(ρ(η)) peaks at η=π/4 (the Clifford torus), S = ln2 | Hilbert-space carrier; Bloch ball; Hopf fibration; von Neumann entropy | "the carrier," "the qubit," "the spinor" | Ledger 1.1-1.3 `EARNED`. rungA reruns the carrier + Hopf/Berry-curvature piece; monopole check agrees to ~9.1e-5 (finite-difference-limited, not machine precision) `[receipt-verified]`. State report's L1-L3 independently: `PASSES_LOCAL`, `NOT_ADMITTED` as forced-from-root; names a hard-coded `and True` tautology in a *related but distinct* fixture's control `[state-report]`. |
| 2 — geometry / flux | Nested Hopf-torus leaves T_η, η∈(0,π/2); connection A, curvature F = dA; per-shell holonomy −2π cos²η; cross-shell flux Φ(η_i,η_j) = −π(cos2η_i − cos2η_j) | No new functional at this layer in the primary ledger; the state report's closest candidate is the flat commuting relative-entropy Hessian g_rr = 1/(1−r²), g_ηη = 4 | Berry/Pancharatnam connection and curvature; discrete Stokes theorem; commuting relative-entropy Hessian | "flux needs nesting," "the strip," "the leaves" | Ledger 2.1-2.3 `EARNED`, sign/normalisation corrected 2026-07-09. rungA's discrete-Stokes identity genuine, diff ~2e-10, `[receipt-verified]`, survived the 2026-07-20 audit. Two of rungA's nine checks are by-construction tautologies per that same audit. State report's L5-L7 independently: on its installed branch "nesting" collapses to one invertible scalar, and the phase direction flux needs is erased on the same marginal that carries the entropy metric — `NOT_ADMITTED` `[state-report]`. |
| 3 — Weyl sheets | ρ_L: ṙ = +2n×r (H_L = +H₀); ρ_R: ṙ = −2n×r (H_R = −H₀); equivalently ρ_R = conj(ρ_L) | None new; tests whether Layer-4-style entropy functionals agree on conjugate sheets | Weyl chirality; conjugate representation; geometric-phase sign; eight-of-sixteen access | "L and R engines," "the two engine types," "a person IS one chirality" | Ledger 3.1-3.4 `EARNED`, exact to 1e-16 in the fixture. rungA reproduces the flux sign-flip exactly (not adjudicated genuine-vs-by-construction by the 2026-07-20 audit — an open gap, not a verdict either way) `[receipt-verified]`. rungB's entire right sheet flagged by-construction by that audit — confirmed forensically here: its own conjugate-dynamics deviation reads exactly 0.0, not merely small `[receipt-verified]`. State report's L8 (Chern orientation, the nearest analog) and the primary ledger's own top-of-file caveat both say the same thing independently: orientation/conjugation reversal is real, a physical-chirality bridge is `NOT_ADMITTED`. |
| 4 — eight terrains | Eight GKSL generators on C², each pinned to a declared fixed point: t0 Funnel damp(σ+) z=+0.713 … t7 Citadel projective(σz) z=+0.094 (full table below) | Non-unitality functional ‖L(I)‖ (√2 on the four damping terrains, 0 elsewhere); 14-feature dynamical fingerprint | GKSL / Lindblad generator; fixed point (stationary state); non-unitality | "terrain," "the 8 terrains"; cognitive-function labels (Se-in, Ne-in, …) are candidate/witness-tier only, per `CLAUDE.md` rule 4 — never sim-earned physics | Ledger 4.0-4.9 `EARNED` (fixed points, non-unitality theorem, max-differentiation fingerprint mean 5.5 / min 0.35). Not re-run by rungA/B: rungB's G1-G8 bank is a *different*, non-identical eight-generator set. rungB left-sheet entropy laws survived the 2026-07-20 audit (with one honestly-disclosed divergence and one degenerate-identity caveat, named below); right sheet by-construction. State report's nearest analog (L12, region/terrain candidates): `DOWNSTREAM_FIXTURES_EXIST__NOT_ADMITTED` `[state-report]`. |

Layer 5 (the four operators) begins immediately after Layer 4 in the
primary ledger and is out of scope for this file.

---

## Layer 0 — the primitive

The owner's own words anchor this layer, quoted from `ROOT/ROOT_CARD.md`
point 7: "entropic monism is central... there is only one kind of
substance — constraint on distinguishability. Identity is not primitive;
it emerges from indistinguishability under probes (a=a iff a~b)."

`MODEL_LAYER_LEDGER.md` states this directly, in four sub-rows that are
already deflationary in the ledger's own text, not softened here:

- 0.0 Primitive: "OWNER CONSTRAINT: constrained distinguishability. No
  object, equivalence, quotient, finite support, entropy, geometry, or
  carrier is primitive."
- 0.1 Probe quotient a~b: "REALIZED LATER FIXTURE... this does not place ~
  at root; reflexive/symmetric/transitive closure and object persistence
  must be earned."
- 0.2 C1 Finitude: "ACTIVE SCOPE + REALIZED... does not prove a globally
  smallest grain or select a unique finite carrier."
- 0.3 C2 Non-commutation: "REALIZED IN FIXTURES. [A,B]≠0 is load-bearing in
  named tests; commuting controls close their measured order gaps."
- 0.4 Emergent identity/object: `CANDIDATE`. A stable probe-relative
  quotient is one object-forming route; weaker, partial/contextual
  presentations remain live challengers.

The independent 2026-07-11 state report gives the same layer a status
token, in its own scheme's L0: `ROOT_DECLARED__NO_MANIFOLD_OBJECT`, with
the note "no scalar entropy is primitive. A finite distinction-loss
gradient is derived only after observations, candidates, and a live demand
exist."

**Sim status.** There is nothing to run here and neither source claims
otherwise. Layer 0 is the one layer in this file with no divergence
between sources — the ledger, its own top-of-file caveats, and the
independent audit all treat it as declared, not computed.

## Layer 1 — the carrier

**Geometry object.** The two-level Hilbert space H = C², carried as a
density matrix ρ = (1/2)(I + r·σ) on the Bloch ball (ledger 1.1, `EARNED`).
The Hopf fibration π: S³ → S² sends a normalised spinor ψ = (z1, z2) to the
Bloch point π(ψ) = (2Re(z1*z2), 2Im(z1*z2), \|z1\|² − \|z2\|²) — this is
literally the `hopf()` function in `rungA_carrier_to_flux.py`
(lines 55-59), applied to the spinor family ψ(η,φ,χ) = (e^{iφ}cosη,
e^{iχ}sinη) used throughout rungA and rungB. Ledger 1.2, `EARNED`: global
phase is invisible to the fiber (fiber-blindness) to 1e-15.

**Entropy functional.** Von Neumann entropy S(ρ) = −Tr[ρ log ρ] (natural
log, matching `rungB_sheets_sixteen.py`'s `vn()` function). Ledger 1.3,
`EARNED (exact)`: S(ρ(η)) peaks at η=π/4 (the Clifford torus), S = ln2.
The state report's section 3 derives an independent, equivalent form on a
different (two-qubit Schmidt) parametrisation: S(r) = h₂((1+r)/2) with
r = cos2η, which peaks at r=0 — the same η=π/4 point, reached by a
different route. This is a genuine convergence of two independent
derivations on the same peak location, named as such rather than treated
as one fact stated twice.

**Sim status.** rungA's L2/L3 (its own internal numbering, scheme 3 above)
genuinely runs the density carrier and the Hopf/Berry-curvature piece.
Concretely, at η₀=0.6 (polar angle θ=1.2 on the base sphere), a finite-
difference plaquette of link phases (spacing p=1e-3) gives
F_numeric = 0.4661100783538946 against the exact Dirac-monopole form
F_exact = 0.5·sinθ = 0.46601954298361314 — a difference of ~9.05e-5
`[receipt-verified, rungA/results/rungA/receipt.json]`. This is a
discretization-limited agreement (the check's own tolerance is 1e-3), not
a machine-precision identity; it should not be quoted as exact.

Independently, the 2026-07-11 state report audits the same territory more
skeptically under its own L1 ("probe quotient") and L3 ("spinor/projective/
Hopf proposal"), on a *different* fixture than rungA. Its verdicts:
`PASSES_LOCAL__DEFINITIONAL_QIT_FIXTURE__NOT_ADMITTED` (L1) and
`PASSES_LOCAL__ONE_CONTROL_INCOMPLETE__NOT_ADMITTED` (L3). The L3 audit
names a specific defect: "the supposed fiber-load-bearing control contains
`and True`," i.e. a hard-coded tautology dressed as a check, in that
fixture — not in `rungA_carrier_to_flux.py`, which this session read
directly and found no such construction in. The two findings should not be
merged: they audit related but distinct scripts, and the defect belongs to
the older one.

## Layer 2 — geometry (nested Hopf tori + flux)

**Geometry object.** Nested Hopf-torus leaves T_η foliate the Hopf base by
η ∈ (0, π/2). Two related-but-not-identical connection presentations
appear across the sources read for this file, and this file does not
silently unify them:

- rungA's own docstring: "A = d(φ) + cos(2η) d(χ)," realised as U(1) link
  phases Arg⟨ψ_k\|ψ_{k+1}⟩ on a discretised χ-loop (χ running 0→2π at
  fixed η and fixed φ₀=0.3).
- The state report's independently-derived connection, on the *φ*-loop
  instead: A = i⟨ψ\|dψ⟩ = −cos²η dφ, giving curvature F = dA = sin2η dη∧dφ.

Both give the same per-shell holonomy number, −2π cos²η — ledger 2.1
(`EARNED`, sign/normalisation corrected 2026-07-09 "after a codex/loop-back
audit + independent reproduction," fixing a prior factor-of-(-2) error)
and the state report's L7 ("discrete holonomy matches −2π cos²η within
9.7e-7"). The two connections are complementary presentations on the
torus's two independent non-contractible loop classes (χ-circle and
φ-circle), not the same formula written twice; this file reports the
holonomy *number* as doubly confirmed and the connection *1-form* as
stated two different ways by two different sources.

Cross-shell flux (ledger 2.2, `EARNED`, same 2026-07-09 correction):
Φ(η_i,η_j) = −π(cos2η_i − cos2η_j).

**Entropy functional.** The primary ledger does not attach a new entropy
functional to Layer 2 — flux is stated as a purely geometric fact there.
The closest candidate object is the state report's section-3 commuting
relative-entropy Hessian on the same η parametrisation: g_rr = 1/(1−r²),
g_ηη = g_rr(dr/dη)² = 4 — explicitly flat (no intrinsic Riemann
curvature) on this branch. This object is the "g" side of the QGT weld
discussed in its own section below.

**Sim status — rungA, `[receipt-verified]`.** At η1=0.4, η2=0.9:

- `L5_discrete_stokes_flux_equals_strip_sum`: flux_relative_holonomy
  (h1−h2, the χ-loop holonomy difference across the two leaves) =
  −2.9025821900968336; strip_plaquette_sum (independently summed over a
  300×400 plaquette grid of the enclosed strip) = −2.902582190097077.
  These agree to ~2×10⁻¹⁰ against a stated tolerance of 1e-6 — a genuine,
  can-fail discrete-Stokes identity (two independently-computed quantities
  that need not have agreed), and it PASSED. The closed-form continuum
  prediction, stored for comparison only and not gated,
  analytic_2pi_dcos2eta = +2.9025451113597893, matches the same magnitude
  to ~3.7e-5 (discretisation-level, N=400 loop steps, not machine
  precision; note the code stores this value without the ledger's leading
  minus sign, so it is a magnitude check, not a signed identity check).
- `C2_contractible_loop_has_flux_without_nesting`: a small loop drawn
  directly on the base sphere (radius 0.15 around polar angle θ0=1.0, no
  torus leaves involved) carries phase 0.035242173664010466 — nonzero,
  as expected for an ordinary single-qubit Berry phase around a
  finite solid angle. This is disclosed in rungA's own docstring as the
  honest boundary of "flux needs nesting": that claim binds the
  non-contractible leaf-loop classes specifically, not all loops.
- `C5` pattern-cycle check (reusing θ=1.2 = 2η₀ from the Berry-curvature
  check above, not a fresh value): closed-loop Pancharatnam phase
  γ_L = 2.003191860155644 against half the solid angle,
  Ω/2 = 2.0032121941545813 — agreement to ~2×10⁻⁴, an independent
  cross-check of the same monopole charge via a different route (closed-
  loop phase rather than local curvature integration).
- Two of the nine checks in this file are by-construction, per the
  2026-07-20 audit, and this session's own read of the code confirms why:
  `C1_flatten_nesting_kills_flux` computes
  `loop_holonomy(chi_loop(eta1)) - loop_holonomy(chi_loop(eta1))` — the
  *same* η1 passed twice, not η2 flattened to η1 as its own docstring
  claims. This is an X−X=0 tautology; it cannot fail regardless of any
  physics. `C4_scrambled_interior_endpoint_invariant` sums consecutive
  holonomy differences along a permuted path of intermediate leaves — a
  telescoping sum that algebraically collapses to
  loop_holonomy(η1) − loop_holonomy(η2) for *any* permutation, again
  independent of nesting physics.
- Ledger 2.3 (A=0 ablation, "flat carrier → curvature vanishes → holonomy
  0," `EARNED`) was not found as an explicit check inside
  `rungA_carrier_to_flux.py` in this session's read; it is not re-verified
  here and should not be assumed re-run by rungA.

**A negative control on the same machinery.** `system_v8/negative_sims/commuting_flux.py`
reuses rungA's own `loop_holonomy`/`chi_loop` functions and forces every
stage generator to commute. Result, `[receipt-verified]`: flux collapses
exactly to 0.0 from a reference of −1.7552066813286045, and order-
sensitivity collapses exactly to 0.0 from a reference gap of
1.8521911441491752 — both simultaneously, verdict `FAILED_AS_EXPECTED`
(a negative control that correctly fails, i.e. correctly loses its signal
when the noncommuting structure it depends on is removed).

**Sim status — the independent 2026-07-11 audit, `[state-report]`.** On its
own installed branch (the pure two-qubit Schmidt family, a different
fixture from rungA), the state report finds that "nested shell," Schmidt
spectrum, entropy, purity, and negativity are "mutually translatable" —
one invertible scalar r=cos2η carries every stated obligation, and "a
torus interior, adjacency law, composition law, or perturbation response
has not been forced" (L5, `LOCAL_IDENTITIES_SURVIVE__NAMED_GEOMETRY_NOT_MSS__NOT_ADMITTED`).
It further finds a specific obstruction between the metric and the flux:
the marginal (traced-out) state that carries the radial entropy metric has
g^marginal_φφ = 0, while the flux's phase direction needs the *global*
pure-state curvature F_φφ = sin²2η > 0 — the phase direction the metric
would need is erased exactly where the entropy interpretation lives (L7,
`BERRY_MATH_PASSES__L6_TO_L7_COIDENTITY_OBSTRUCTED__NOT_ADMITTED`). rungA's
flux computation runs on the global pure spinor directly, so it does not
contradict this finding — but it also does not resolve it, because rungA
never traces out to the marginal the state report's metric is defined on.

## Layer 3 — Weyl sheets

**Geometry object.** Two Bloch-vector flows on the same C² carrier: ρ_L
with ṙ = +2n×r (H_L = +H₀), ρ_R with ṙ = −2n×r (H_R = −H₀) — ledger 3.1,
`EARNED`, exact to 1e-16 in the fixture. In `rungB_sheets_sixteen.py`, with
n chosen real (n_y=0), this is realised concretely as H_R = −H_L and
ρ_R = conj(ρ_L): the conjugate representation *is* the sign-flipped
Hamiltonian sheet for a real n, "executed not asserted" per the file's own
docstring.

Ledger 3.2 (`EARNED`, dynamical): engine type = global loop sign — left
engine all +geometric-phase, right all −. Ledger 3.3 (`EARNED`):
eight-of-sixteen access — left sheet reaches in-terrains t0-t3, right
reaches t4-t7; forcing a stage onto the wrong sheet flips its geometric
phase 8/8. Ledger 3.4 (`EARNED`): the two 8-sets are pole-mirrors,
t0/t4 z*=±1, t2/t6 z*=∓1 (sum 0) — as *stated* in 3.4. Note this is a
rounded/idealised statement: Layer 4's own computed fixed points give
t0 z=+0.713 and t4 z=−0.709 (sum ≈ +0.004, not exactly the ledger's
"sum 0"), and t2 z=−0.707, t6 z=+0.711 (sum ≈ +0.004 also). This is a
small internal-consistency gap between 3.4's rounded prose and 4.0-4.7's
actual computed values, flagged here rather than silently harmonised.

**Entropy functional.** No new functional is defined at Layer 3 itself;
the question this layer poses for entropy functionals built at Layer 4 is
whether they agree, sheet for sheet.

**Sim status — rungA, `[receipt-verified]`.** `L6_conjugate_bundle_reverses_flux`
and `C3_chirality_erasure_kills_split`: flux_left = −2.9025821900968336,
flux_right = +2.9025821900968336 (sum < 1e-9). This check is **not**
named in the 2026-07-20 audit's list of either by-construction or
survived-genuine checks for rungA — the audit is silent on it specifically.
This file records that as an open, unaudited item rather than assigning it
a verdict the audit itself did not give.

**Sim status — rungB, `[receipt-verified]`, explicitly adjudicated.** The
2026-07-20 audit states: "rungB C2+C3 — THE ENTIRE RIGHT SHEET is
conj(left) forced by construction: gamma_R = −gamma_L identically, so the
'16-grid (2 sheets x 8 generators)' carries only 8 generators of
independent content." This session's own read of the raw receipt confirms
the forensic signature of that verdict directly: `C3_max_deviation_G1_G4`
reads `[0.0, 0.0]` — not merely small, exactly zero on both tested
trajectories. An independently-integrated right-sheet trajectory that
happened to match a genuinely different physical process would be
expected to show RK4 floating-point residue at the 1e-12 to 1e-15 level;
an exact 0.0 is the signature of an algebraic substitution (ρ_R ≡
conj(ρ_L) by construction, not by independent integration converging on
the same answer). The audit lists rungB's *left-sheet* trajectory laws
(Spohn, Lueders, echo, the noncommuting order-gap with its commuting
collapse) as genuine and can-fail, i.e. surviving the attack; the right
sheet supplies no independent evidence beyond that.

**Sim status — the independent 2026-07-11 audit and the ledger's own
caveat, `[state-report]`.** The state report's nearest analog is L8
(Chern bundle vs. cut lattice, its own numbering conflict, named in its
own section 5). Computed there: for the chosen spinor section,
(1/2π)∫F = +0.999998; orientation reversal gives −0.999998; an
independently-computed constant-section control gives 0.000000 exactly
(the negative control fires correctly). Its verdict: "Calling its
orientation sign a physical Weyl chirality or engine type requires an
additional implemented map; orientation reversal by itself does not
supply it" — `CHERN_FIXTURE_PASSES__LAYER_ID_CONFLICT__PHYSICAL_CHIRALITY_NOT_EARNED`.

This is the same qualification the primary ledger prints about itself, at
its own top of file, before any of its Layer 3 rows: "Chern orientation
has no implemented physical-chirality bridge. Treat every conflicting
EARNED row below as fixture-local historical prose."

**Synthesis (not collapsed).** Three sources, three different audit dates,
three different specific fixtures, one converging qualification: the
*algebraic* conjugate-symmetry (reversing sign under conjugation/
orientation-reversal) is real, exact, and repeatedly reproduced. The
*physical* claim — that this construction yields two independently-real
engine types, such that "a person IS one chirality" — is not earned by
any of this evidence. This file holds both readings open rather than
picking one: the math is solid; the physical interpretation built on top
of it is a live, unadmitted claim, not a refuted one.

## Layer 4 — the eight terrains

**Geometry object.** Eight GKSL (Gorini-Kossakowski-Sudarshan-Lindblad)
generators on C², each pinned to a declared scratch fixed point (ledger
4.0-4.7, all `EARNED`):

| Terrain | Nickname | Generator | Unitality | Fixed point z* |
|---|---|---|---|---|
| t0 | Funnel (Se-in) | damp(σ+) | non-unital | +0.713 |
| t1 | Vortex (Ne-in) | depolarizing | unital | 0.000 |
| t2 | Pit (Ni-in) | damp(σ−) | non-unital | −0.707 |
| t3 | Hill (Si-in) | projective(σz) | unital | +0.070 |
| t4 | Cannon (Se-out) | damp(σ−) | non-unital | −0.709 |
| t5 | Spiral (Ne-out) | depolarizing | unital | 0.000 |
| t6 | Source (Ni-out) | damp(σ+) | non-unital | +0.711 |
| t7 | Citadel (Si-out) | projective(σz) | unital | +0.094 |

The parenthetical cognitive-function labels (Se-in, Ne-in, and so on) are
`CLAUDE.md`'s own boundary case: rule 4 in `system_v7/constraint_core/CLAUDE.md`
states that all such vocabulary lives in `data_json/rosetta_layer.json` at
candidate/witness tier, never inside a sim as sim-earned physics. They are
reproduced here as the nicknames the task's own table column asks for, not
as an upgraded claim.

**Entropy functional.** Non-unitality theorem (ledger 4.9, `EARNED,
exact`): ‖L(I)‖ = √2 for the four damping terrains (t0, t2, t4, t6), 0 for
the rest — named in the ledger as "the physical surplus." Max-
differentiation (ledger 4.8, `EARNED`): all eight terrains are distinct
under a 14-feature dynamical fingerprint, mean pairwise distance 5.5,
minimum 0.35 (the t3-t7 pair, both projective-Si generators, "nearly
sheet-symmetric — the real bottleneck, not a bug").

**Sim status — rungA/rungB do not re-run this table.** `rungB_sheets_sixteen.py`
builds a *different*, non-identical eight-generator bank — G1 depolarizing
GKSL, G2 Lueders instrument branch, G3 amplitude damping at N=0, G4
damping overshoot, G5 Stone unitary group, G6 Hahn echo, G7 pinching, G8
block consolidation — built to test entropy-monotonicity *laws* across the
two Weyl sheets, not to re-derive t0-t7's specific fixed points. This file
does not present rungB as a re-verification of Layer 4's table; it is
parallel, thematically adjacent work on a separate object.

`[receipt-verified]` results, left sheet (survived the 2026-07-20 audit):

| Generator | Law tested | Key figures |
|---|---|---|
| G1 depolarizing | Spohn entropy production σ ≥ 0 along the flow | min ΔS step 6.156523513212164e-09 > 0; final trace-distance to I/2 = 8.763712424017345e-04 |
| G2 Lueders branch | unread instrument measurement strictly raises entropy | branches pure and complete to <1e-14; entropy gap +0.27652087787382273 |
| G3 amplitude damping (N=0) | reversed relative entropy D(ρ*‖ρ(t)) monotone down | 1.5383009629521016 → 4.4849712118753127e-04; the *forward* D(ρ(t)‖ρ*) is +∞ at this fixed point — recorded as a genuine divergence, not patched |
| G4 damping overshoot | von Neumann entropy shows an interior hump while relative entropy stays monotone | S: 0.1071 → peak 0.6906 → 0.0005; relative entropy monotone straight through the hump |
| G5 Stone unitary | dS_vN = 0 exact; phase-measure Shannon entropy still grows | max \|ΔS_vN\| = 3.2529534621517087e-14 (effectively zero); Shannon entropy 0.325 → 0.684 over roughly a quarter period, but recurrent — no arrow on this row |
| G6 Hahn echo | free dephasing kills ensemble coherence; the echo refocuses it | coherence 0.0150 → 1.0 exactly; entropy 0.6930 → ~0.0 — recoverable, not produced (frequencies are static; no spectral diffusion) |
| G7 pinching | Shannon identity S(Pρ) = H(p) exact | agreement to <1e-12; degenerates to a rank-1 special case — the *nontrivial* grouping identity is earned only on G8 |
| G8 block consolidation (4-dim) | grouping identity S(Pρ) = H(p) + Σp_j S(ρ_Bj), nontrivial | LHS 1.2465510180931967 ≈ RHS 1.246551018093197 (<1e-12); block entropies [0.6016, 0.5030], both > 0.1 |
| C1 control | noncommuting order-gap fires, commuting pair collapses it | gap_noncommuting = 0.20396437252368657; gap_commuting = 4.8711331280463745e-17 |

Right-sheet copies of all eight generators exist in the same receipt with
matching figures, but per the 2026-07-20 audit and this session's own
confirmation (Layer 3 section above), they are forced mirrors of the left
sheet, not independent evidence.

**Sim status — the independent 2026-07-11 audit, `[state-report]`.** The
nearest analog in that scheme is L12, "regions / terrain candidates":
"terrain and region-discovery scripts exist as downstream fixtures,"
missing "a prior admitted geometry, observable-defined region competitors,
topology/connectedness controls, and an order-open gate" —
`DOWNSTREAM_FIXTURES_EXIST__NOT_ADMITTED`. This is not a contradiction of
the ledger's `EARNED` rows: it is a different question. The ledger's
`EARNED` asks whether generator X's fixed point is computed correctly
(yes, at fixture-local scope). The state report's `NOT_ADMITTED` asks
whether "terrain" is a forced region of a prior admitted manifold, rather
than a hand-installed table (not shown). Both can be true at once; this is
the status-ladder distinction, not a disagreement over the arithmetic.

---

## The flux formula, consolidated

Per-shell holonomy: **−2π cos²η** (ledger 2.1; state report L7 confirms to
9.7e-7; rungA's own C5 cross-check via closed-loop Berry phase confirms
the same monopole charge to ~2e-4 by a different route).

Cross-shell flux (the "flux requires nesting" claim, in its precise scope
— non-contractible leaf-loop classes only, per rungA's own C2 disclosure):
**Φ(η_i, η_j) = −π(cos2η_i − cos2η_j)** (ledger 2.2, both corrected
2026-07-09 by a factor of −2 after independent cross-reproduction).
rungA's directly-computed discrete value at η1=0.4, η2=0.9 is
−2.9025821900968336, matching its own independently-computed strip-
plaquette sum to ~2e-10 (the genuine discrete-Stokes identity) and the
continuum closed form to ~3.7e-5 (discretisation-limited).

## The QGT weld, Q = g + (i/2)F

`ROOT/ROOT_CARD.md`'s receipts section states this under owner points 2
("the dual") and 6 ("unity target"): "QGT Q = g + (i/2)F — metric =
Hessian of Umegaki relative entropy, flux = its imaginary partner. One
object. [rungB/C receipts; chain identities exact]."

This session tested that citation directly: `rungB_sheets_sixteen.py` and
`rungC_joint_cuts.py` were both read (rungB in full, rungC's header and
checks list), and neither computes a Hessian, a metric tensor, or a QGT
object — confirmed by grep for `Hessian`, `metric`, `QGT`, `g_` across
both files, no hits beyond a `Bures` distance check inside rungD
(`D3_inner_fixed_point_moves_bures`, a different object again — a Bures
*distance* moving with a fixed point, not a metric-tensor construction).
The citation "[rungB/C receipts]" for this specific identity does not hold
up against the two named files' actual content.

The identity ROOT_CARD names — BKM (the Hessian of Umegaki relative
entropy) — is genuinely computed elsewhere, in two independent places, to
comparable precision:

- Ledger UP-139 `[ledger-reported]`: "BKM = Hessian of the Umegaki
  relative entropy to 4e-8" (reported as a non-gating self-consistency
  check).
- State report section 3, `[state-report]`: BKM coefficient and Umegaki-
  relative-entropy Hessian agree at 4.491500, difference 8.1e-8.

Two independent computations agreeing on the same self-consistency
identity to ~1e-7-1e-8 is a genuine convergence, named here as such.

But UP-139 directly interrogates the harder question — is BKM the *same*
object as the standard quantum geometric tensor's metric part (SLD/QFI,
the Fubini-Study-family object textbooks pair with Berry curvature in
Q=g+iF/2) — and its own verdict, after a four-model adversarial panel
(Gemini-3.1-pro, Grok-4.5, Qwen-3.5, GLM-5.2), is "a genuine fork":
`[ledger-reported]`

- On a noncommuting mixed direction: g_SLD = 1.000 vs g_BKM = 1.076
  (differ by 0.076; would be ~0 if the same metric).
- Near-pure states: SLD = 1.0 vs BKM = 4.6.
- The two metrics coincide *only* on the commuting/classical submanifold
  (both = classical Fisher, 1.190476) — and UP-139's own correction notes
  this coincidence is guaranteed there by the Morozova-Chentsov theorem
  (every monotone metric reduces to classical Fisher on commuting states),
  so it is a consistency check, not evidence the metrics are the same
  object generally.

The state report's independent route arrives at a complementary
obstruction, not the same one restated: on its radial/commuting branch,
BKM, SLD/Bures, Wigner-Yanase, and RLD all agree to 1.78e-15 — so on that
specific branch you cannot tell which metric "is" the QGT's real part,
because they are indistinguishable there. And critically: the marginal
state that carries this radial entropy metric has g^marginal_φφ = 0
exactly, while the flux needs the global pure state's F_φφ = sin²2η > 0 —
the phase direction the flux is built from is erased on precisely the
state the entropy metric is defined on (`L6_to_L7_coidentity_obstructed`,
above).

**This file holds two readings open, per the anti-collapse discipline,
rather than picking one.**

- Reading A (definitional): "g" in the owner's Q=g+iF/2 is, by
  declaration, whatever the model's own forced pawl-metric is (BKM,
  conditional on the DPI-forced relative-entropy pawl of UP-121, not
  re-derived independently). Under this reading the weld is a naming
  choice, and it is self-consistent — BKM's own definition checks out to
  ~1e-7-1e-8 in two independent computations.
- Reading B (standard-QGT): if "g" is meant to be the textbook object
  paired with Berry curvature — SLD/QFI/Fubini-Study — then g ≠ BKM off
  the classical submanifold, per a four-model-audited "genuine fork," and
  even restricted to BKM alone, the state that carries it has no phase
  direction left for F to attach to.

No sim read for this file computes g and F together, on the same state,
and checks Q=g+iF/2 as one executed numerical identity. The flux half (F)
is genuinely, repeatedly, independently computed. The metric half (g),
under the specific identification g=BKM, is also genuinely computed
elsewhere. The weld — the two as real and imaginary parts of one tensor,
checked together — is an assembled framing, not an executed result.

## The Spohn/Uhlmann stroke pair

Two complementary forms of the same relative-entropy monotonicity
principle, at two different time-granularities:

- **Spohn stroke (continuous, differential form).** Entropy production
  σ(t) = −d/dt D(ρ(t)‖ρ*) = dS_vN(t)/dt ≥ 0 along a GKSL semigroup flow
  toward its own fixed point ρ*. Genuinely computed on trajectories (not
  just endpoints) in `rungB_sheets_sixteen.py`'s G1 row: min step
  6.156523513212164e-09 > 0 on the left sheet, `[receipt-verified]`,
  survived the 2026-07-20 audit. G3/G4 exercise the same principle on
  damping generators, including the honestly-disclosed finding that the
  *forward* Spohn form diverges at a pure fixed point (N=0) and only the
  reversed, invariant-reference form stays finite — recorded, not
  smoothed over.
- **Uhlmann stroke (general, single-map form).** The data-processing
  inequality: S(N(ρ)‖N(σ)) ≤ S(ρ‖σ) for any completely-positive
  trace-preserving map N — proved in general by Uhlmann, extending
  Lindblad's 1975 semigroup-specific result. Ledger UP-121
  `[ledger-reported, not independently re-opened this session]`: "0
  violations over 200 random density pairs under a lossy Kraus channel...
  max drop 3.47. Theorem (Lindblad 1975, Uhlmann), not an assumption."
  The same UP-121 entry computes the equality condition (exact Petz
  recovery marks DPI-tightness, Pearson correlation 1.0000 between
  ΔS=0 and recovery-exactness) and shows Umegaki is one member of an
  entire forced operator-convex family (Petz quasi-entropies) that all
  pawl uniformly, not a hand-picked special case.

Together, these two license the same monotonicity principle at both
granularities the model uses: Spohn for what a continuously-running
terrain does every instant (Layer 4's generators), Uhlmann/Lindblad for
what any discrete instrument or channel application does in one step
(rungB's own G2 Lueders-branch row is exactly this case). This pairing is
Layer-4-and-beyond material — it depends on Layer 4's generators and
reaches toward the later operator/stage layers — not core Layer 0-2
content; it is placed here because the task named it explicitly and its
two halves live in exactly the sims audited above.

---

## Honest summary: genuinely simmed vs by-construction, Layers 0-4

| Layer | Genuinely simmed (can-fail, survived) | By-construction (cannot fail) | Not admitted (independent audit) |
|---|---|---|---|
| 0 | — (nothing computed; declared root) | — | State report L0: `ROOT_DECLARED__NO_MANIFOLD_OBJECT` |
| 1 | rungA density carrier + Hopf/Berry-curvature-monopole check (diff ~9.1e-5) | — (none found in rungA) | State report L1/L3: `PASSES_LOCAL...NOT_ADMITTED`; names an `and True` tautology in a related, non-rungA fixture |
| 2 | rungA discrete-Stokes flux identity (diff ~2e-10); C2 contractible-loop boundary disclosure; C5 independent Berry-phase cross-check; commuting_flux.py negative control (flux and order-gap both collapse to exactly 0.0 together) | rungA C1_flatten (X−X=0 tautology, confirmed by direct code read); rungA C4_scrambled (telescoping-sum identity) | State report L5-L7: nesting collapses to one scalar on its branch; metric and flux phase-direction do not co-exist on the same (marginal) state |
| 3 | rungA flux sign-reversal under conjugation (not adjudicated either way by the 2026-07-20 audit — an open gap) | rungB's entire right sheet (C2+C3), confirmed forensically by an exact 0.0 conjugate-dynamics deviation | State report L8 + the primary ledger's own header caveat, independently: Chern/orientation math survives, physical-chirality bridge `NOT_ADMITTED` |
| 4 | rungB left-sheet entropy laws (Spohn, Lueders, damping monotonicity, Stone-unitary exactness, echo refocusing, noncommuting order-gap with commuting collapse) — with two disclosed findings (G3 forward-form divergence, G7 degenerate identity), not smoothed | rungB right-sheet copies of all eight generators (same construction as Layer 3) | State report's L12 analog: `DOWNSTREAM_FIXTURES_EXIST__NOT_ADMITTED`. Ledger's own t0-t7 table is `EARNED` at fixture-local scope but is a *different* generator set from rungB's G1-G8, not re-verified by it |

## Source manifest

- `system_v7/constraint_core/MODEL_LAYER_LEDGER.md` — Layer 0-4 (lines
  1-100), UP-121 (~line 2650), UP-139 (~line 3146), UP-142 (~line 3236).
  Read directly, this session.
- `system_v7/constraint_core/ratchet/manifold_evidence/MANIFOLD_RATCHET_STATE_REPORT.md`
  — full file (377 lines), read directly, this session, per the binding
  instruction in `system_v7/constraint_core/CLAUDE.md`.
- `system_v8/nested_manifold/rungA_carrier_to_flux.py` — full source, read
  directly.
- `system_v8/nested_manifold/rungB_sheets_sixteen.py` — full source, read
  directly.
- `system_v8/nested_manifold/results/rungA/receipt.json` — full, read
  directly.
- `system_v8/nested_manifold/results/rungB/receipt.json` — full, read
  directly.
- `system_v8/nested_manifold/results/RUNGS_ABCE_AUDIT_VERDICT.md` — full,
  read directly.
- `ROOT/ROOT_CARD.md` — full, read directly.
- `system_v8/nested_manifold/manifold_one.py` — docstring only.
- `system_v8/nested_manifold/rungC_joint_cuts.py` — header + checks list
  only (used to test the ROOT_CARD QGT citation, not for its own Layer-5+
  content).
- `system_v8/nested_manifold/rungD_schur_nesting.py` — checks list only
  (same reason).
- `system_v8/negative_sims/commuting_flux.py` and
  `system_v8/negative_sims/results/commuting_flux/receipt.json` — full,
  read directly; found via ROOT_CARD's own citation, not the original read
  list.

Two files already existed in `MODEL_DOSSIER/` when this file was written —
`05_ENGINE_STAGES_LOOPS_CYCLES.md` and `07_RATCHET_ACTUAL_STATE.md` — from
a parallel lane of the same dossier series. This file's structure and
evidence-tier discipline follow the pattern already established there;
its content is independent and does not depend on either.
