# BUILD CARD: geo_s1_quaternion_model_v0 — SAME S1 geometry, DIFFERENT MODEL (quaternion representation) + multi-method invariants

Foundation-breadth lane (owner directive: same sims with different models; simming in different ways). Stays at Stage 1 — no higher-layer content. CLAIM UNDER TEST: the S1 geometry computed through the QUATERNION model agrees pointwise with the complex-pair model, and the key invariants agree across MULTIPLE independent computation methods.

Ceiling: scratch_diagnostic, promotion_allowed=false, formal_admission_allowed=false.

## The alternative model
Unit quaternions q = a + bi + cj + dk, |q| = 1 (S^3 as the quaternion group manifold). Identification with the complex model: q = z1 + z2 j. Hopf map, quaternion form: q -> q i q-bar (a pure-imaginary unit quaternion = a point of S^2). PIN the sign/orientation convention and emit the explicit dictionary to the complex-model map (x,y,z) = (2Re(z1 z2bar), 2Im(z1 z2bar), |z1|^2-|z2|^2) — agreement must be computed POINTWISE over a shared Haar sample, with any constant rotation between conventions identified explicitly (a fixed R in SO(3), emitted), not absorbed silently.

## What to compute
Q1. Model dictionary: q <-> (z1,z2) round trip exact; group law agreement (quaternion product vs SU(2) matrix product) pointwise.
Q2. Hopf agreement: quaternion-form image vs complex-form image over >=1e4 shared samples; the fixed conversion rotation R emitted; max pointwise deviation after R.
Q3. MULTI-METHOD LINKING (simming the same invariant different ways): linking number of two distinct fibers via (a) the Gauss linking integral, (b) the Hopf-invariant integral form (int A ^ F normalized), (c) discrete crossing-count on a projected diagram. All three must give 1; report each method's convergence/resolution behavior.
Q4. MULTI-METHOD VOLUME: Vol(S^3) = 2pi^2 via (a) Monte Carlo, (b) metric-determinant lattice integration over the (eta,phi,chi) chart WITH the 2:1 cover correction applied explicitly (the naive chart integral must be shown = 4pi^2 then corrected — emit both numbers), (c) the quaternion-measure route.
Q5. Double-cover check in the quaternion model: the 2pi rotation path q(t) = exp(t i/2)... gives q(2pi) = -q(0) computed along the path; 4pi returns.

## Controls (can-fail)
wrong-convention control (skip the R identification: pointwise agreement must FAIL with the measured deviation); single-method control flagged (any invariant with only one method is reported as single-sourced); broken-dictionary control (q -> z mapping with conjugation error fails Q1).

## Proofs (z3+cvc5, raw values)
Bind the computed multi-method linking values: UNSAT that the three methods disagree beyond tolerance; scrambled-fiber control -> SAT.

## Engines (three-engine; identical PIN; source_sha256)
Julia canon; JAX batched sweeps; PyTorch independent path for one method per multi-method family (honest role labels). NumPy control-lane.

## Files: system_v6/sims/geo_s1_quaternion_model_v0/ (atomic, card copied verbatim, no audit_verdict.md, no edits elsewhere)
## Acceptance: legs exit 0; validator --require-pytorch ok:true; Q1-Q5 receipts; all controls fired; multi-method tables complete; ceiling exact.
