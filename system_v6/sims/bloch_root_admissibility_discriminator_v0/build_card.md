# BUILD CARD: bloch_root_admissibility_discriminator_v0 — is the Bloch sphere admitted by F01/N01/non-associativity, and what are the alternatives

One object, one claim, one card. CLAIM UNDER TEST: (T1) under F01 the Bloch sphere is admissible only as the measured refinement LIMIT of finite probe quotients, never primitive; (T2) under N01 the solid Bloch ball is the reconstructed state space of a noncommuting probe family while a commuting family reconstructs only a simplex (interval); (T3) the Bloch construction (normalized 2-vector over a normed division algebra -> psi psi-dagger -> projective base) runs at exactly four rungs R/C/H/O giving bases S^1/S^2/S^4/S^8 with fibers S^0/S^1/S^3/S^7; (T4) the sedenion rung FAILS measurably (norm law breaks, image leaves the sphere, fiber-constancy breaks) — the ladder terminates; (T5) the octonion rung survives ONLY by alternativity: two-slot association holds on sampled 2-generated sets, three-slot fails on the 168 nonassociating triples.

Ceiling: scratch_diagnostic, promotion_allowed=false, formal_admission_allowed=false. Language: the roots ADMIT the four-member family {S^1,S^2,S^4,S^8}; the C^2 carrier INSTALLS S^2 (installed-not-forced pattern); no carrier admission, no physics.

## The five tests (each = computed receipt + control that can fail)
T1 (F01 limit-shape): for probe families of size k (binned spin directions), compute the finite quotient point sets; compute Hausdorff distance d_H(quotient_k, S^2) for a refinement ladder k = 6, 14, 30, 62 directions x bin refinements; receipt = monotone convergence curve d_H -> 0; control: a NON-refining family (repeated probes) must NOT converge. Every quotient cardinality finite and emitted.
T2 (N01 ball-vs-simplex): generate states; reconstruct the accessible state space from probe statistics alone: (a) commuting family {sigma_z binned} -> reconstructed object is 1-dimensional (interval; emit affine dimension + extreme points 2); (b) full Pauli family -> 3-dimensional ball (emit affine dimension 3, boundary sphericity ||r||<=1 saturation, extreme points = pure states). Receipt = reconstructed dimensions 1 vs 3; control: adding only commuting probes to (a) never raises the dimension.
T3 (four-rung ladder): implement the division algebras R, C, H (quaternion multiplication table), O (octonion table imported from system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json under the committed hash/orientation reconciliation — cite the weld-2 precedent). For each rung, sample unit 2-vectors (x,y), compute h(x,y) = (|x|^2-|y|^2, 2*x*conj(y)); receipts per rung: (i) image norm = 1 to tolerance over the full sample (the composition-norm law), (ii) fiber-constancy: h(x*q, y*q) = h(x,y) for sampled unit q in the algebra (uses alternativity at O — emit the max deviation), (iii) base dimension by local PCA/rank of the image samples = 1/2/4/8, (iv) fiber dimension = 0/1/3/7 by sampling the preimage orbit.
T4 (sedenion termination — the kill control): same construction with the sedenion table (Cayley-Dickson double of the octonion table, computed in-packet): find and emit explicit unit sedenions with ||x*y|| != ||x||*||y|| (norm-law violation magnitude), show the image leaves S^16 (max |norm-1| large), show fiber-constancy breaks (max deviation), and exhibit a zero-divisor pair from the committed 84. This must FAIL — if the sedenion rung passes, the packet emits kill_condition_met and the claim dies.
T5 (alternativity two-vs-three): on the octonion table: associator [a,b,c]=(ab)c-a(bc) computed for (i) sampled pairs' 2-generated sets -> all zero (alternativity), (ii) the 210 ordered distinct imaginary triples -> exactly 168 nonzero (committed count; recompute, don't import), with the 42 Fano-line triples zero.

## Load-bearing proofs (z3 AND cvc5, raw computed values, no booleans)
P1: from the computed T4 rows — UNSAT that the sedenion norm-violation equals zero (bind the computed violation value); octonion control rows -> SAT for zero (the flip).
P2: from T2 — bind the reconstructed affine-dimension witnesses (the computed rank evidence): UNSAT that the noncommuting family's reconstruction fits in dimension <= 2; commuting control -> SAT.

## Controls
non-refining probe family (T1), commuting-only additions (T2), sedenion rung (T4 = the designed failure), label shuffle (algebra basis relabel leaves all dimension/count receipts invariant), orientation-flip of the octonion table (T3/T5 counts invariant — the convention-independence check).

## Engines (three-engine claim-bearing; identical PIN; source_sha256 fields)
Julia = canon (algebra tables + ladder + proofs via Z3.jl). JAX = the sampling sweeps (Haar via normalized Gaussians; batched fiber/base sampling) + z3/cvc5. PyTorch = independent computation of the reconstruction ranks/PCA dimensions (torch-native SVD path; honest role labels per the R3-v2 precedent). NumPy control-lane only. R3-v2 lessons binding: no fixture isolation, no label echo, all controls can-fail with failure semantics, raw-value SMT only.

## Files (one folder, atomic)
system_v6/sims/bloch_root_admissibility_discriminator_v0/
  *_julia.jl / _jax.py / _pytorch.py / _envelope.py / build_card.md (verbatim) / results/*.json
No audit_verdict.md. No edits to existing files.

## Acceptance (re-run mechanically)
Legs exit 0 fresh; validator --require-pytorch ok:true (+ source-backed recorded); T1-T5 receipts present with the exact expected values where exact (dims 1/2/4/8, fibers 0/1/3/7, count 168/42, simplex 1 vs ball 3); the sedenion kill fires with magnitudes; both proofs flip; ceiling exact.
