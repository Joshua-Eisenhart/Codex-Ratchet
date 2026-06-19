# BUILD CARD: geo_s1_spinor_hopf_free_v0 — Stage 1 free-mode geometry sim (the foundation, simmed fully)

One object, one claim, one card. CLAIM UNDER TEST: the Stage-1 geometry of the canonical program (system_v6/receipts/geometry_sim_program_canonical_20260610.md) — normalized spinors, S^3, the Hopf map, fibers and linking, the density quotient, S^2 — simmed DENSELY in free mode with every exact known invariant reproduced to stated tolerance and resolution-convergence demonstrated. This is a GEOMETRY sim: the object is the geometry itself, not a claim gadget.

Ceiling: scratch_diagnostic, promotion_allowed=false, formal_admission_allowed=false. No manifold/axis/physics claims; pure standard mathematics with committed-program provenance.

## What to sim (each item = dense computation + exact-invariant check + convergence row)
G1. SPINORS: Haar-dense samples of normalized psi in C^2 (normalized complex Gaussian pairs), N in {1e3, 1e4, 1e5}; check ||psi||=1; coordinate chart psi(phi,chi,eta) consistency (chart->vector->chart round trip).
G2. S^3 METRIC/VOLUME: verify ds^2 = d eta^2 + d phi^2 + d chi^2 + 2cos(2eta) dphi dchi by finite-difference lengths of sampled curves vs exact arc lengths; Monte-Carlo volume -> 2pi^2 with convergence curve vs N; geodesic check: great-circle distance d(psi1,psi2)=arccos|<psi1,psi2>|... NOTE: arccos(Re<psi1,psi2>) is the S^3 geodesic distance (real inner product on R^4) — distinguish it from the Fubini-Study distance arccos|<psi1,psi2>| of the BASE; compute both, label both, never conflate.
G3. SU(2) STRUCTURE: sampled pairs compose (matrix product of the corresponding SU(2) elements stays in SU(2): det=1, unitary); quaternion correspondence; DOUBLE COVER: a continuous 2pi rotation path returns rho but flips psi -> -psi; 4pi returns psi (computed along the path, not asserted).
G4. HOPF MAP: x=2Re(z1 z2bar), y=2Im(z1 z2bar), z=|z1|^2-|z2|^2; check x^2+y^2+z^2=1 over all samples; coordinate form (sin2eta cos2chi, sin2eta sin2chi, cos2eta) agreement; phase invariance pi(e^{i alpha}psi)=pi(psi) over a dense alpha sweep; SURJECTIVITY: pushforward of Haar covers S^2 uniformly (binned chi-square or covering-radius receipt).
G5. FIBERS + LINKING: compute whole fibers (parametrized circles) over >=2 base points; verify each fiber maps to one base point to tolerance; fiber length 2pi; LINKING NUMBER of two distinct fibers = 1 via the Gauss linking integral computed numerically (this is the named load-bearing computation of the packet).
G6. DENSITY QUOTIENT: rho=psi psi^dagger explicit; (e^{i alpha}psi) gives identical rho (max deviation over sweep); the quotient map S^3 -> S^2 equals the Hopf map (rho's Bloch vector == G4's image, pointwise over all samples) — the keystone identity, computed.
G7. S^2 BASE: area 4pi by Monte Carlo with convergence; SO(3) rotation action consistency with the lifted SU(2) action (U psi vs R applied to the Bloch image — commuting square computed pointwise).

## Proofs (z3 AND cvc5, raw computed values)
P1: bind sampled computed values of x^2+y^2+z^2 (scaled ints) — UNSAT that any sampled image point lies off the unit sphere beyond tolerance; scrambled control (break the Hopf formula) -> SAT.
P2: bind the computed commuting-square deviations of G7 — UNSAT nonzero beyond tolerance; control: a deliberately wrong rotation pairing -> SAT.

## Controls (can-fail, failure semantics shown)
broken-chart control (wrong chart formula fails G1 round trip); non-Haar sampling control (clustered sampling fails G4 uniformity); wrong-linking control (two fibers of the SAME base point: linking integral must NOT give 1 — compute what it gives and label); phase-sweep granularity sweep; convergence rows mandatory (each invariant vs N) — a flat or diverging curve is a finding, not a pass.

## Tripwires from the program receipt (binding)
The S^3-vs-FS distance conflation (G2 note); convention pins recorded for orientation choices; no Bloch-ball content here (that is S3 of the program); no torus content here (S2 of the program).

## Engines (three-engine claim-bearing; identical PIN; source_sha256)
Julia = canon. JAX = the dense sweeps (vmap over samples; genuinely batched). PyTorch = independent path for the linking integral + commuting-square checks (torch-native; honest role labels). NumPy control-lane only. R3-v2 lessons binding (no fixture isolation, no tautological controls, raw-value SMT).

## Files (one folder, atomic)
system_v6/sims/geo_s1_spinor_hopf_free_v0/
  *_julia.jl / _jax.py / _pytorch.py / _envelope.py / build_card.md (verbatim) / results/*.json
No audit_verdict.md. No edits to existing files.

## Acceptance (re-run mechanically)
Legs exit 0 fresh; validator --require-pytorch ok:true; every G-item has dense-computation receipts + exact-invariant deviations + convergence rows; linking number 1 computed by Gauss integral; the keystone identity G6 pointwise; both proofs flip; ceiling exact.
