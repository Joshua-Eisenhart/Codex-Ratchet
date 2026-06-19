# BUILD CARD: geo_s1_three_qubit_floor_exact_v0 — the minimum carrier, made exact (3 qubits minimum)

One object, one claim, one card. CLAIM UNDER TEST (owner doctrine: 3 qubits minimum — the floor where irreducible chirality and the three-slot bracket both first exist): the three-spinor carrier (C^2)^{x3} ~= C^8 admits the same exact-strength treatment as single-qubit S1 — every claim symbolic, closed-form, or rigorously bounded; nothing at bare float tolerance.

Ceiling: scratch_diagnostic, promotion_allowed=false, formal_admission_allowed=false. DO NOT conflate the two S^15 structures: the 3-qubit global-phase quotient is S^15 -> CP^7 (complex projective, the density quotient); the octonionic fibration S^15 -> S^8 is a DIFFERENT decomposition (O^2 structure) — both may be mentioned, never merged (a known conflation trap; emit an explicit non-conflation field).

## Exact computations (each = a receipt)
Y1. CARRIER: (C^2)^{x3} ~= C^8 exact (basis dictionary); normalized states S^15 subset C^8; global-phase quotient psi psi^dagger with the phase-erasure identity proven symbolically (the X2 analogue at 8 dims).
Y2. REDUCED DENSITIES, exact on symbolic states: for GHZ = (|000>+|111>)/sqrt2, W = (|001>+|010>+|100>)/sqrt3, and a product state — compute rho_A, rho_B, rho_C symbolically; exact entanglement entropies: GHZ rho_A = I/2 -> S = ln 2 exactly; W rho_A eigenvalues {1/3, 2/3} -> S = ln 3 - (2/3) ln 2 exactly; product -> 0 exactly. CAS-exact (two independent CAS: Symbolics.jl + sympy), no float.
Y3. ENTANGLEMENT CLASSES, exact witnesses: the 3-tangle tau (Coffman-Kundu-Wootters): tau(GHZ)=1, tau(W)=0, tau(product)=0 — computed exactly via the hyperdeterminant route; biseparable controls.
Y4. Cl(6) FLOOR, exact integer arithmetic: construct the six gamma generators as Pauli strings (Jordan-Wigner: gamma_1 = X⊗I⊗I, gamma_2 = Y⊗I⊗I, gamma_3 = Z⊗X⊗I, gamma_4 = Z⊗Y⊗I, gamma_5 = Z⊗Z⊗X, gamma_6 = Z⊗Z⊗Y or a pinned equivalent — PIN the convention); verify {gamma_i, gamma_j} = 2 delta_ij over EXACT integer/Gaussian-integer 8x8 matrices (all 36 pairs, exact); the algebra they generate has dimension 64 -> Cl_6(C) ~= M_8(C) verified by exact rank/span computation; the chirality element gamma_7 = -i gamma_1...gamma_6 (convention pinned): gamma_7^2 = I exact, eigenspaces split 4+4 (the Weyl split at the floor).
Y5. THE THREE-SLOT FLOOR: binary vs ternary order made exact at the minimum carrier — commutators [A,B] of Pauli strings exact; matrix multiplication is associative ((AB)C - A(BC) = 0 exact, ALL sampled triples — the associative-representation fact), with the explicit statement: nonassociativity CANNOT live in the matrix representation; it requires the algebra-extension nesting (octonion table) — the floor provides three SLOTS (sites/tensor factors), bracketing-sensitivity of STATES under site-grouped operations: compute ((A⊗B)⊗C-grouped vs A⊗(B⊗C)-grouped action receipts where grouping = operation-application order on sites — pinned definition, exact.
Y6. CHIRALITY IRREDUCIBILITY (the floor's reason for existing): the gamma_7 Weyl split exists at 3 qubits; verify by exact computation that the analogous construction at 2 qubits (Cl(4), gamma_5) gives spinor halves of dim 2+2 while 3 qubits gives 4+4 — and emit the committed-doctrine cross-reference (Cl(6)/3-qubit floor = where >= 7 anticommuting units first fit: count the maximal anticommuting family at 1/2/3 qubits exactly: 3/5/7).
Y7. CLASSIFICATION TABLE: every claim with achieved strength (symbolic / exact-integer / closed-form); zero bare-float rows.

## Proofs (z3 AND cvc5 over exact arithmetic)
P1: the anticommutation table as exact integer matrix constraints — assert some {gamma_i,gamma_j} != 2 delta_ij -> UNSAT; corrupted-generator control -> SAT.
P2: tau(GHZ)=1 and tau(W)=0 as exact polynomial evaluations — assert tau(W) != 0 -> UNSAT; a GHZ/W-swapped control -> SAT.

## Controls (can-fail)
corrupted gamma (one sign flipped) fails Y4 exactly; wrong-state control (W labeled GHZ) fails Y3; 2-qubit comparison rows (Y6) computed not asserted; conflation control: the non-conflation field present and the S^15->S^8 octonionic structure NOT used anywhere in the quotient computations.

## Engines (three-engine; identical PIN; source_sha256; all prior lessons binding)
Julia = canon (Symbolics.jl exact + Z3.jl). JAX leg = sympy (second CAS) + z3/cvc5. PyTorch = exact integer tensor route for the anticommutation table (honest role). NumPy control-lane only.

## Files: system_v6/sims/geo_s1_three_qubit_floor_exact_v0/ (atomic; card verbatim; no audit_verdict.md; no edits elsewhere)
## Acceptance: validator --require-pytorch ok:true; Y1-Y7 with exact values (ln2, ln3-(2/3)ln2, tau 1/0, counts 3/5/7, splits 2+2/4+4); proofs flip; non-conflation field present; ceiling exact.
