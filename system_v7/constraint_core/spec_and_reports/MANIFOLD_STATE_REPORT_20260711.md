# The geometric constraint manifold — actual state, layer by layer

Date: 2026-07-11. Every number below was **computed by running the sim**, not copied from a stored
`pass:True`. The load-bearing "entropy IS geometry" identity (L6) was **re-derived independently here**
from two different definitions (see §L6). Claim ceiling for the whole ladder: `scratch_diagnostic`,
`promotion_allowed = false`. This is a realization of the manifold under installed QIT assumptions
(the complex qubit carrier); it is NOT a proof that this carrier is the globally-forced weakest route.

Sim: `sims_and_scripts/manifold_build_ladder.py` (JAX float64) + the per-layer spine sims
`manifold_L5..L8_*.py`. All run green in the 146-sim harness.

---

## What the manifold actually is

One object: a **dual ratchet** where geometry and entropy are the same tensor, built up in layers,
each layer earned by a computation that a control **must** be able to fail. The carrier is a single
complex qubit ρ (a 2×2 density matrix); the dynamics are GKSL (Lindblad) generators; the 8 "terrains"
are 8 specific generators. "Walk the co-ratchet state" = walk these layers, not find a separate object.

The build order is **empirical** — a layer is admitted only when a binding test on the prior survivors
forces it. The ledger numbering (L1…L8) is a route through the dependency DAG, **not** a runtime law and
**not** canon (owner doctrine: ordering is not canon).

---

## Layer L1 — carrier: a normalized qubit state exists
- **Math:** ψ = (cos0.3, sin0.3·e^{i0.7}); check ⟨ψ|ψ⟩ = 1.
- **Measured:** ‖ψ‖² = 1.000000000000. **Earned.**
- **Meaning:** the weakest thing that persists between "static fuzz frames" is a norm-preserving carrier
  on S³ ⊂ ℂ² — a spinor. This is L1 because F01 (finitude) + N01 (noncommutation) are satisfiable by ℂ².

## Layer L2 — geometry: the Hopf chart lands on the Bloch sphere
- **Math:** Hopf chart (η,χ) → ψ → ρ = |ψ⟩⟨ψ| → Bloch vector r = (Tr ρσx, Tr ρσy, Tr ρσz); check ‖r‖ = 1.
- **Measured:** ‖r‖ = 1.000000000. **Earned.**
- **Meaning:** the state space is not a bag of amplitudes — it is a curved surface (the 2-sphere), and the
  chart coordinates are (η,χ). Geometry enters here, as the *shape of the carrier*, not as an added axis.

## Layer L3 — Weyl / chirality: the two sheets precess oppositely
- **Math:** evolve ρ₀ under H_L = +H₀ and H_R = −H₀ for t=0.5; measure ‖r_L − r_R‖.
- **Measured:** chirality split = **0.238004** (control: same H would give 0). **Earned.**
- **Meaning:** left- and right-handed engines are genuinely different channels, not a relabeling.
  This is where the "left-chiral universe / antimatter is the right sheet" claim lives.

## Layer L4 — transport + nesting: flux needs ≥2 shells
- **Math:** flux Φ(η_i,η_j) = 2π(cos2η_i − cos2η_j); ablation A=0 (single shell) → Φ=0.
- **Status:** **Earned** (verified in `flux_nesting_ablation_jax.py`). Flux is a *cross-shell* property;
  a single shell carries none. This is why "flux needs nesting" — it is geometry, not an axis.

## Layer L5 — placement: 8 terrains are valid CPTP semigroups, and are distinct SHELLS
- **Math (ladder):** evolve ρ₀ under each of the 8 GKSL terrain generators for t=2; the evolved ρ must stay
  a physical state (min eigenvalue ≥ 0).
- **Measured:** terrains_CPTP = **8/8**. **Earned.**
- **Math (spine sim `manifold_L5_nested_shells_schmidt_strata`):** two states that L4 calls *equally*
  "non-product" (negativities 0.4207 and 0.4869) sit on **different L5 shells** (shell radii 0.5403 vs
  0.2272, differ by 0.3131). Nested-shell flux: self = 0, nested = **1.9673**. Erase-nesting control:
  flux → 0 and interior resolution gone. **PASS.**
- **Meaning:** L5 refines L4's binary product/entangled bit into a *continuum* of Schmidt shells.

---

## The 7 axes (run in the owner's order 6 → 5 → 3 → 4 → 1 → 2 → 0)

Each axis is read as a **dynamical witness from the same running trajectory**, with a control that
collapses only that axis. Measured this run:

| Axis | What it measures | Measured value | Earned |
|---|---|---|---|
| **A6** signed precedence | b6 = −b0·b3 (exhaustive over 8 terrains) | 0 violations | ✓ |
| **A5** operator family | 4 generator archetypes give distinct Bloch norms | Se 0.106, Ne 0.287, Ni 0.636, Si 0.163 | ✓ (≥3 distinct) |
| **A3** inner/outer loop | fiber move vs base move (flux is geometry, not this axis) | fiber **0.0**, base **1.2073** | ✓ |
| **A4** deductive/inductive | composition order gap ‖UE−EU‖ (N01) | **0.0489** | ✓ |
| **A1** unitary/CPTP | purity preserved vs decreased | unitary 0.57, dissipative 0.505 | ✓ |
| **A2** frame | direct vs conjugated frame gap | **0.0159** | ✓ |
| **A0** feedback polarity | Ne/Ni:+ vs Se/Si:− split | **fails — see below** | ✗ |

A3 is the cleanest single fact: moving along the **fiber** (Hopf phase φ) leaves ρ *exactly* invariant
(0.0), while moving along the **base** (χ) moves it (1.2073). That is the fiber-bundle structure, measured.

---

## Axis-0 — the honest failure (this is the real open problem)

Doctrine wants: sensing terrains {Se,Si} homeostatic (−), intuition terrains {Ne,Ni} allostatic (+).
The ladder runs a **real perturb-evolve-classify loop** and tries six different state functionals as the
Axis-0 readout. **None realizes the doctrine split:**

- participation-ratio of Bloch deviation: all 8 terrains **+** (1 sign)
- norm of deviation: all 8 **−** (1 sign)
- purity: only Pit(Ni) flips **+**, rest **−** (2 signs, wrong partition)
- von Neumann entropy: only Pit/Source(Ni) flip **−**, rest **+** (2 signs, wrong partition)
- dD/dλ (owner definition): all **+**, family means Se 0.723, **Ne 1.076**, Ni 0.338, Si 0.800
- net entropy production dS: family means Se +0.026, Ne +0.050, **Ni −0.564**, Si +0.038 — only the two
  Ni (source-locked) terrains go negative, and via source-locking, not the intuition/sensing distinction.

**Verdict: Axis-0 is UNBUILT.** The doctrine polarity is not a density-level (ρ) readout — every functional
tried is blind to it, exactly as the project's own `axis0_readouts_density_blind` finding predicts. Axis-0
lives at the spinor/loop level (720° holonomy), or it is a genuinely open question. **I am not going to
paper over this: six honest functionals were tried and all six fail the doctrine target.**

---

## The entropic geometry — L6/L7/L8 (the "entropy = geometry" core)

## L6 — the shell metric IS the Hessian of relative entropy IS the BKM metric
This is the load-bearing identity of the whole model ("entropy and geometry as one tensor, not entropy
running on geometry"). **I re-derived it independently in this session, not from the stored result:**

- **BKM (Kubo–Mori) metric** g_BKM = ∫₀¹ Tr[(dρ) ρ^{−s} (dρ) ρ^{−(1−s)}] ds, computed in the eigenbasis
  with kernel c_ij = (log p_i − log p_j)/(p_i − p_j).
- **Hessian of relative entropy** ∂²/∂t² S(ρ(t)‖ρ₀) by finite difference.
- On a shell state (Bloch radius 0.8, tangent in the x–z plane) at θ₀=0.6:

  **g_BKM = 0.87888983,  Hessian = 0.87888984,  |difference| = 1.6×10⁻⁸.**

  They are the same tensor. The spine sim gets the same identity at another point
  (bkm 4.4915002223 vs rel-entropy-Hessian 4.4915002722, diff 5.0×10⁻⁸), with a wrong-direction control
  metric (4.3318) that genuinely differs.
- **Corrected fact (loop-back audit):** in the Schmidt-angle coordinate the metric is **exactly constant**
  g_ηη = 4.000000 (the earlier "curved" reading was a coordinate artifact of the r = 2cos²η − 1 reparam).
- **Monotonicity = DPI:** metric contracts under CPTP (4.4915 → 2.0695 depolarizing) and does **not** under a
  non-CPTP amplifier (→ 7.3358). This is the infinitesimal data-processing inequality — the pawl of the ratchet.
- **Prior art (honest):** this identity is established Tomita–Takesaki / Connes–Rovelli modular theory. The
  ownable claim is narrow: it renders *at the terrain level* as an application, not a rediscovery.

## L7 — the flux is Berry holonomy (geometry derives the entropy-shell flux)
- Berry connection A = i⟨ψ|dψ⟩ on the L3 Hopf chart; per-shell loop holonomy −2π cos²η, analytic match to
  9.7×10⁻⁷. Nested flux = **−3.141595**, ledger form −π(cos2η_i − cos2η_j) = −3.141593 — match.
- Closed-loop transport around a (φ,η) rectangle returns net phase −π (real curvature, non-integrable).
- Erase-nesting control kills the flux (−5.4×10⁻¹⁷). **PASS.**

## L8 — the total flux is quantized (Chern number), and its sign IS chirality
- Integrate Berry curvature over η∈[0,π/2]×φ-loop: **Chern = 0.99999800**, nearest int 1, error 2.0×10⁻⁶.
- Reverse loop orientation → Chern flips to **−0.99999800**. Trivial (flat) bundle control → **0.0**. **PASS.**
- **Meaning:** the Weyl chirality of L3 is topologically the sign of a Chern number — a quantized,
  orientation-defined integer, not a free label.

---

## Bottom line (honest)
- **Earned and independently checked:** L1–L5 (carrier → geometry → chirality → nesting → shells), the six
  non-Axis-0 axes, and the L6/L7/L8 entropic-geometry stack — with L6's entropy=geometry identity re-derived
  from scratch here (1.6×10⁻⁸).
- **Not earned:** Axis-0 feedback polarity — six functionals tried, all fail the doctrine target; it is a
  spinor-level or genuinely open object.
- **Ceiling:** all `scratch_diagnostic` — this is a *realization* under an installed complex-qubit carrier,
  not a proof the carrier is forced. That forcing question, and a non-tautological L5 re-audit, are the open digs.
