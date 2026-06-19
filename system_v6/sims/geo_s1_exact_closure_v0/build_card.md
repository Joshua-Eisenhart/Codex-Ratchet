# BUILD CARD v2 (REBUILD after REJECT AS CLAIMED): geo_s1_exact_closure_v0 — earn the exactness claim

The v1 was REJECTED AS CLAIMED (`audit_verdict.md` in this sim folder). Read that verdict first before rebuilding; E1/E2/E3/E6 failed. Rebuild the failing receipts so the claim is earned. Rebuild in place: keep `audit_verdict.md` untouched as append-only history, replace leg/envelope sources, regenerate results, and preserve the v1 card below under `SUPERSEDED v1`.

The v1 claim values were partly fixture artifacts; v2 values come from the genuine routes.

## The six repairs

V1. EXPLICIT CONVENTION PIN: a structured PIN field naming `sigma_y_standard`, the Bloch basis, `r_i = Tr(rho sigma_i)`, and `Hopf_y = +2 Im(z1 conj(z2))` — with the derived consequence stated in the PIN. Chosen story: `sigma_y_standard = [[0,-i],[i,0]]`, pinned Bloch basis is `(sigma_x, -sigma_y_standard, sigma_z)`, and `r_i = Tr(rho basis_i)`. Under these choices standard `r_y = -2 Im(z1 conj(z2))`, pinned `r_y = +2 Im(z1 conj(z2))`, so `Bloch_pinned(rho) = (x,y,z)` while standard Bloch would be `(x,-y,z)` relative to the Hopf convention.

V2. JULIA X1 DERIVES: from `rho = psi psi^dagger` and the pinned Pauli basis, expand symbolically with `Symbolics.jl` to the components and emit the expanded difference polynomial `= 0`. No predeclared component equality. The SymPy leg independently does the same from its own construction.

V3. CROSSING SIGNS COMPUTED: each crossing's sign comes from exact projected geometry: orientation of the tangent pair plus z-order at the crossing, exact arithmetic; no assigned constants. Emit per crossing: segment pair, computed orientation determinant, z-delta, and sign.

V4. CLOSED-FORM ORIENTATION CONTROL: rerun the symbolic Gauss route with one fiber orientation reversed and emit exactly `-1`.

V5. GENUINE INTERVALS: use `IntervalArithmetic.jl` from interval-valued inputs through the integrand to the final bound; the claim-path comparison is interval-contains-1, never a float tail. The coarse-quadrature control emits a wide interval honestly.

V6. HONEST TABLE: re-emit the classification table with every row's strength matching its actual computation; recompute `bare_float_rows`; if any row remains float-tolerance, list it. Zero is a result, not a target.

Unchanged X-receipts (`X2`, `X3`, `X5`, `X6`, `X7`) may be retained if their code paths are untouched; rerun everything fresh regardless.

## Engines / files / ceiling

As v1 card: three-engine, identical PIN, `source_sha256`; same folder; `scratch_diagnostic`, no promotion; lineage `geo_s1_spinor_hopf_free_v0@013fb0fa1`.

## Acceptance

Legs exit 0 fresh; validator `--require-pytorch --strict-source-backed` returns `ok:true`; V1-V6 receipt fields exist; the audit's E1/E2/E3/E6 fail conditions are demonstrably closed; solver flips are genuine.

## SUPERSEDED v1 BUILD CARD

# BUILD CARD: geo_s1_exact_closure_v0 — S1 made strong: symbolic proofs, closed forms, interval bounds (no claim left at float tolerance)

One object, one claim, one card. CLAIM UNDER TEST: every S1 claim of the committed geo_s1_spinor_hopf_free_v0 packet upgrades to one of three exact strengths — (i) SYMBOLIC: proven identically for all points by computer algebra; (ii) CLOSED-FORM: the exact value derived analytically and matched; (iii) RIGOROUS-BOUND: interval-arithmetic enclosure — with an explicit classification table showing NO claim remains at bare float tolerance (statistical-only rows, e.g. Monte Carlo, explicitly labeled redundant-by-exact-route).

Ceiling: scratch_diagnostic, promotion_allowed=false, formal_admission_allowed=false (process-level promotion is a separate repo gate; this packet upgrades MATH strength, not status). Cite the committed S1 packet by lineage; do not modify it.

## The exact upgrades (each = a computed receipt)
X1. KEYSTONE IDENTITY, symbolic: with psi=(z1,z2), |z1|^2+|z2|^2=1 as a side relation, prove Bloch(psi psi^dagger) = (2Re(z1 conj(z2)), 2Im(z1 conj(z2)), |z1|^2-|z2|^2) component-wise by symbolic expansion (Symbolics.jl on the Julia leg, sympy on the JAX leg — TWO independent CAS). Emit the expanded polynomial difference = 0 exactly.
X2. PHASE INVARIANCE + UNIT IMAGE, symbolic: pi(e^{i alpha} psi) = pi(psi) and x^2+y^2+z^2 = (|z1|^2+|z2|^2)^2 as exact CAS identities.
X3. METRIC + INTEGRALS, closed-form: derive ds^2 = d eta^2 + d phi^2 + d chi^2 + 2cos(2eta) dphi dchi symbolically from the chart; compute Vol(S^3) = 2pi^2, Area(S^2) = 4pi, Area(T_eta) = 2pi^2 sin(2eta) (WITH the double-cover division shown symbolically: chart integral 4pi^2 sin2eta / 2) as exact symbolic integrals.
X4. LINKING = 1, three exact routes: (a) crossing-count route re-derived as exact integers from exact rational/algebraic sample points (no float): signed sum / 2 = 1 exactly; (b) the Gauss linking integral for two explicit Hopf fibers (great circles over distinct base points) — derive the closed form symbolically and evaluate = 1 exactly; (c) interval-arithmetic enclosure of the numerical Gauss integral (e.g. IntervalArithmetic.jl) proving |I - 1| < bound with the bound emitted. All three must agree on exactly 1.
X5. DOUBLE COVER, exact algebra: exp(-i pi n.sigma) = -(I) computed symbolically (2pi rotation: U(2pi) = -I exactly), U(4pi) = +I; the path statement as exact matrix exponentials at rational multiples of pi.
X6. HAAR UPGRADE (closes the audit's gap-5 note): replace/augment the marginal chi-square with a rotation-invariant joint statistic (e.g. pairwise-angle distribution vs the exact known density, or spherical-harmonic moments vanishing) — computed with its exact expected values derived symbolically.
X7. P2 UPGRADE (closes gap-6 note): bind the commuting-square identity SYMBOLICALLY — prove U(n) action commutes with the quotient map as a CAS identity (all points), superseding the four-residual float binding.
X8. CLASSIFICATION TABLE: every S1 claim listed with its achieved strength (symbolic / closed-form / rigorous-bound / statistical-redundant); any claim that cannot be upgraded gets an honest reason field.

## Proofs (z3 AND cvc5 over exact arithmetic)
P1: the keystone polynomial identity verified by the solvers over the reals (nlsat/nra: assert the expanded difference nonzero -> UNSAT; a corrupted-formula control -> SAT).
P2: the crossing-count exact-integer linking: assert signed_sum != 2 from the exact combinatorial data -> UNSAT; scrambled control -> SAT.

## Controls (can-fail)
corrupted-identity control (a wrong Hopf formula must fail X1 symbolically); broken-chart metric control; interval-blowup control (a deliberately coarse quadrature must produce a WIDE interval that still contains 1 or honestly fails the bound); non-Haar sample control fails X6.

## Engines (three-engine; identical PIN; source_sha256; R3-v2 + S1-audit lessons binding — no hardcoded receipts, exact-by-algebra rows labeled as such BY DESIGN here)
Julia = canon (Symbolics.jl + IntervalArithmetic.jl + Z3.jl). JAX leg = sympy symbolic route (the second independent CAS) + z3/cvc5. PyTorch = honest scoped role (e.g. independent exact-rational crossing-count recomputation via integer tensors) or explicit pytorch_role demotion. NumPy control-lane only.

## Files (one folder, atomic)
system_v6/sims/geo_s1_exact_closure_v0/ — legs + envelope + build_card.md (verbatim) + results/. No audit_verdict.md. No edits to existing files.

## Acceptance (re-run mechanically)
Legs exit 0 fresh; validator --require-pytorch ok:true; X1-X8 receipts with the exact values; the classification table complete with zero bare-float rows; both solver proofs flip; ceiling exact.
