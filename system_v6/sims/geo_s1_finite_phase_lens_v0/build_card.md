# BUILD CARD: geo_s1_finite_phase_lens_v0 — the F01-aligned ALTERNATIVE quotient (lens-space tower)

Foundation-breadth lane (owner directive: testing alternatives). Stays at Stage 1 (quotient layer). CLAIM UNDER TEST: the finite-phase quotients of S^3 — quotient by the cyclic group Z_N acting psi -> e^{2pi i/N} psi, giving the lens spaces L(N,1) — form the F01-admissible approximation TOWER of the Hopf quotient: each L(N,1) is a finite-phase-resolution alternative to full phase erasure, with computed invariants, and the tower converges to the Hopf/density quotient as N grows. This tests the ALTERNATIVE to the continuous S^1 quotient: finite phase groups, which is what finite probe families can actually resolve (F01).

Ceiling: scratch_diagnostic, promotion_allowed=false, formal_admission_allowed=false. No claim that the lens tower replaces the Hopf quotient — it is the finite-resolution alternative family, tested.

## What to compute (N in {1, 2, 3, 4, 8, 16, 64})
L1. The quotient computed: Haar samples of S^3 with the Z_N orbit identification (orbit representatives, orbit size exactly N for N>1 away from fixed-point-free everywhere — verify the action is free: no psi with e^{2pi i/N}psi = psi).
L2. Volume tower: Vol(L(N,1)) = 2pi^2/N by Monte Carlo per N — the exact known values, convergence rows.
L3. Fundamental group order: count distinct loop lifts — a loop closing in L(N,1) lifts to a path in S^3 connecting psi to e^{2pi i k/N}psi; the lift classes = Z_N (computed order N), vs S^3 simply connected (N=1 control) and the full Hopf quotient S^2 simply connected (the phase-erasure endpoint).
L4. The factoring chain computed pointwise: S^3 -> L(N,1) -> S^2: the density map rho = psi psi-dagger is invariant under the FULL S^1, hence under every Z_N — verify the chain commutes over all samples; what each rung erases: L(N,1) keeps phase mod 2pi/N (compute a phase-residue observable that distinguishes Z_N orbits but not finer), S^2 erases all of it.
L5. F01 reading, computed: a finite probe family with phase resolution 2pi/N separates exactly the L(N,1) classes and not finer — emit the probe family, its quotient class structure, and the statement as computed class counts (matching L(N,1) orbit counts), N-ladder.
L6. Convergence: the L(N,1) class structure -> the Hopf quotient as N -> 64 (distance between the N-resolution quotient classes and the density classes, decreasing curve).

## Controls (can-fail)
non-free-action control (quotient by a non-free action candidate must be caught by the L1 freeness check); wrong-volume control (unidentified sample set gives 2pi^2, ratio N emitted); probe-resolution mismatch control (a probe family at resolution 2pi/M, M != N, must NOT reproduce the L(N,1) classes — compute the mismatch).

## Proofs (z3+cvc5, raw values)
Bind the computed orbit/class counts: UNSAT that the Z_N orbit count differs from sample_count/N (free action, exact integers); non-free control -> SAT. Bind the L4 commuting-chain deviations: UNSAT nonzero beyond tolerance.

## Engines (three-engine; identical PIN; source_sha256); R3-v2 lessons binding.
## Files: system_v6/sims/geo_s1_finite_phase_lens_v0/ (atomic). No audit_verdict.md. No edits elsewhere.
## Acceptance: validator --require-pytorch ok:true; L1-L6 receipts with the exact known values (2pi^2/N, group order N); controls fired; proofs flip; ceiling exact.
