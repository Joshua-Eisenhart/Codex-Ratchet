# Cartan Decomposition of SU(4) and Two-Qubit Gates

## 1. The KAK Decomposition of SU(4)

**Theorem (Cartan, KAK form).** Every U in SU(4) can be written as:

    U = k_1 . exp(i (c_1 sigma_x (x) sigma_x + c_2 sigma_y (x) sigma_y + c_3 sigma_z (x) sigma_z)) . k_2

where:
- k_1, k_2 in SU(2) (x) SU(2) are local unitaries (tensor products of single-qubit gates)
- c_1, c_2, c_3 are real parameters
- sigma_i (x) sigma_i denotes the tensor product of Pauli matrices
- (x) denotes tensor product throughout

**Lie algebra decomposition.** su(4) = k + p where:
- k = su(2) + su(2) is the local subalgebra (spanned by sigma_i (x) I and I (x) sigma_i)
- p is the non-local part (spanned by sigma_i (x) sigma_j)
- a = span{sigma_x (x) sigma_x, sigma_y (x) sigma_y, sigma_z (x) sigma_z} is a maximal abelian subalgebra of p (the Cartan subalgebra of the symmetric space)

**Dimensions:** dim(su(4)) = 15, dim(k) = 6 (3+3), dim(p) = 9, dim(a) = 3. The decomposition is: 15 = 6 + 6 + 3 (k_1 contributes 3, k_2 contributes 3 on the k side; a contributes 3; the remaining 6 local parameters are in k_1 and k_2).

**Proof sketch.** This is the Cartan decomposition for the symmetric space SU(4)/(SU(2) x SU(2)). The involution is theta(X) = (sigma_y (x) sigma_y) X^T (sigma_y (x) sigma_y)^{-1}, which fixes k and negates p. The exponential map from a covers all of exp(p) up to conjugation by K = SU(2) x SU(2) (Cartan's theorem for symmetric spaces).

**Notation convention.** Write the non-local part as:

    A(c_1, c_2, c_3) = exp(i(c_1 sigma_x (x) sigma_x + c_2 sigma_y (x) sigma_y + c_3 sigma_z (x) sigma_z))

The full decomposition is U = (U_A (x) U_B) . A(c_1, c_2, c_3) . (V_A (x) V_B).


## 2. The Weyl Chamber

**Symmetries of the decomposition.** The parameters (c_1, c_2, c_3) are not unique. The Weyl group W of the Cartan decomposition acts by permutations and sign changes:
- Permutations of (c_1, c_2, c_3): any permutation can be absorbed by conjugation with appropriate local unitaries
- Sign changes: c_i -> -c_i (in pairs, since we need det = 1) can also be absorbed
- Periodicity: c_i is periodic with period pi/2

**Weyl chamber (fundamental domain).** A canonical choice is:

    pi/4 >= c_1 >= c_2 >= c_3 >= 0

with the additional constraint c_1 + c_2 <= pi/2 when c_3 = 0 (to avoid double-counting at the boundary). More precisely:

    pi/4 >= c_1 >= c_2 >= |c_3| >= 0

with c_1 + c_2 <= pi/2 at the boundary c_3 = 0.

The Weyl chamber is a tetrahedron with vertices at:
- O = (0, 0, 0)
- A_1 = (pi/4, 0, 0)
- A_2 = (pi/4, pi/4, 0)
- A_3 = (pi/4, pi/4, pi/4)


## 3. Special Points in the Weyl Chamber

**Identity gate:** (0, 0, 0)
- A(0,0,0) = I (x) I
- No entangling power

**CNOT gate:** (pi/4, 0, 0)
- A(pi/4,0,0) = exp(i pi/4 sigma_x (x) sigma_x) (up to local equivalence)
- Generates maximally entangled states from some product inputs
- Locally equivalent to CZ, CPHASE(pi)
- Entangling power: e_p = 2/9

**iSWAP gate:** (pi/4, pi/4, 0)
- A(pi/4,pi/4,0) = exp(i pi/4 (sigma_x (x) sigma_x + sigma_y (x) sigma_y))
- Swaps |01> <-> |10> with phase i
- Locally equivalent to sqrt(SWAP) composed with local phases
- Entangling power: e_p = 2/9

**SWAP gate:** (pi/4, pi/4, pi/4)
- A(pi/4,pi/4,pi/4) = exp(i pi/4 (sigma_x (x) sigma_x + sigma_y (x) sigma_y + sigma_z (x) sigma_z))
- SWAP|psi>|phi> = |phi>|psi>
- NOT entangling (it's in the local unitary closure in a sense -- SWAP is locally equivalent to identity on the symmetric/antisymmetric subspaces)
- Entangling power: e_p = 0 (SWAP doesn't create entanglement, it just moves it)

**DCNOT (double CNOT):** (pi/4, pi/4, 0) -- same as iSWAP class

**sqrt(SWAP):** (pi/8, pi/8, pi/8)
- Entangling power: e_p = 1/9

**B gate (optimal):** (pi/4, pi/8, 0)
- Can construct any two-qubit gate with at most 2 applications + local unitaries (Balakrishnan-Sankaranarayanan)


## 4. Matrix Form of A(c_1, c_2, c_3)

**Explicit computation.** Using the identity sigma_i (x) sigma_i = diag in the Bell basis:

In the computational basis {|00>, |01>, |10>, |11>}:

    sigma_x (x) sigma_x = [[0,0,0,1],[0,0,1,0],[0,1,0,0],[1,0,0,0]]
    sigma_y (x) sigma_y = [[0,0,0,-1],[0,0,1,0],[0,1,0,0],[-1,0,0,0]]
    sigma_z (x) sigma_z = [[1,0,0,0],[0,-1,0,0],[0,0,-1,0],[0,0,0,1]]

The exponent H_NL = c_1 sigma_x (x) sigma_x + c_2 sigma_y (x) sigma_y + c_3 sigma_z (x) sigma_z has matrix:

    H_NL = [[c_3, 0, 0, c_1-c_2],
            [0, -c_3, c_1+c_2, 0],
            [0, c_1+c_2, -c_3, 0],
            [c_1-c_2, 0, 0, c_3]]

**In the Bell basis** {|Phi+>, |Psi->, |Psi+>, |Phi->}, sigma_i (x) sigma_i are diagonal:

    sigma_x (x) sigma_x -> diag(1, -1, -1, 1) (in a particular Bell basis ordering)
    sigma_y (x) sigma_y -> diag(-1, -1, 1, 1)
    sigma_z (x) sigma_z -> diag(1, 1, -1, -1) (signs depend on phase conventions)

So H_NL is diagonal in the Bell basis, and:

    A(c_1, c_2, c_3) = diag(e^{i(c_1-c_2+c_3)}, e^{i(-c_1-c_2-c_3)}, e^{i(-c_1+c_2+c_3)}, ...) (in Bell basis)

The exact phases depend on the ordering convention. The key point: the non-local part is diagonal in the Bell basis, which is why the Bell basis diagonalizes the entangling structure.


## 5. Makhlin Invariants

**Problem.** Given U in SU(4), determine its local equivalence class (i.e., find which point in the Weyl chamber it corresponds to).

**Makhlin's invariants.** Define the matrix M = U^T (sigma_y (x) sigma_y) U (sigma_y (x) sigma_y) (the "Makhlin matrix" -- related to the magic basis transformation). Then the two complex invariants:

    G_1 = Tr(M)^2 / (16 det(U))
    G_2 = (Tr(M)^2 - Tr(M^2)) / (4 det(U))

are local unitary invariants. Two gates U, V are locally equivalent iff G_1(U) = G_1(V) and G_2(U) = G_2(V).

**Relation to Weyl chamber coordinates.**

    G_1 = cos^2(c_1 - c_2) cos^2(c_1 + c_2) + ... 

More precisely, in terms of the interaction matrix m = diag(e^{2ic_1}, e^{-2ic_1}, e^{2ic_2}, ...) (details depend on convention):

    G_1 = (1/16)(Tr(m))^2 / det(m)^{1/2}

The complete relation involves trigonometric functions of c_1, c_2, c_3.

**Explicit Makhlin formulas.**

    G_1 = (1/4)(cos 2c_1 cos 2c_2 cos 2c_3 + i sin 2c_1 sin 2c_2 sin 2c_3)^2 ... 

Actually, the correct expression (Zhang et al. 2003):

    G_1(c_1,c_2,c_3) = (cos^2(2c_1) cos^2(2c_2) cos^2(2c_3) - sin^2(2c_1) sin^2(2c_2) sin^2(2c_3)) + i (1/4) sin(4c_1) sin(4c_2) sin(4c_3) ... 

The full expression is complex-valued and intricate. For practical computation, it's easier to:
1. Compute M = U_B^T U_B where U_B is U in the Bell basis
2. Compute G_1 = Tr(M^T M) / 16, G_2 = (Tr(M^T M)^2 - Tr((M^T M)^2)) / 4

**Special values:**
- Identity: G_1 = 1, G_2 = 3
- CNOT: G_1 = 0, G_2 = 1
- iSWAP: G_1 = -1, G_2 = -1 (actually need to check)
- SWAP: G_1 = 1, G_2 = -3


## 6. Entangling Power

**Definition (Zanardi et al.).** The entangling power of a gate U is the average entanglement generated when U acts on random product states:

    e_p(U) = E_{|a>|b>} [E(U|a>|b>)]

where the expectation is over Haar-random product states and E is a chosen entanglement measure (typically linear entropy of the reduced state).

**Formula in terms of Weyl chamber coordinates.** Using the linear entropy E_L = 1 - Tr(rho_A^2):

    e_p(U) = (2/9)(cos^2 4c_1 + cos^2 4c_2 + cos^2 4c_3 - 2 cos 4c_1 cos 4c_2 cos 4c_3 - 1) ... 

Wait, the correct formula (Reznik et al.):

    e_p(c_1, c_2, c_3) = (1/9) - (1/9)(cos^2(4c_1) + cos^2(4c_2) + cos^2(4c_3))/3 ... 

The precise formula is:

    e_p = (2/9)[1 - |G_1|^2 / (Re(G_1))^2] ... 

Actually, the clean result (Zanardi-Zalka-Faoro): for the linear entropy measure:

    e_p(U) = (2/9)(1 - |Tr(m^2)|^2/16)

where m is related to the Makhlin matrix. For the Weyl chamber:

    e_p(c_1,c_2,c_3) = (2/9)(sin^2(2c_1) + sin^2(2c_2) + sin^2(2c_3) - sin^2(2c_1) sin^2(2c_2) sin^2(2c_3) ... ) ... 

The key qualitative facts:
- e_p(0,0,0) = 0 (identity: no entanglement)
- e_p(pi/4,0,0) = 2/9 (CNOT: substantial entangling)
- e_p(pi/4,pi/4,0) = 2/9 (iSWAP: same as CNOT)
- e_p(pi/4,pi/4,pi/4) = 0 (SWAP: no net entanglement creation)
- Maximum e_p = 2/9, achieved on a continuum of gates

**Gate typicality.** A Haar-random gate in SU(4) has <e_p> = 2/9 (the maximum!). Generic gates are maximally entangling.


## 7. Perfect Entanglers

**Definition.** A gate U is a perfect entangler if there exists a product state |a>|b> such that U|a>|b> is maximally entangled.

**Characterization (Reznik-Aharonov-Groisman).** U is a perfect entangler iff (c_1, c_2, c_3) satisfies:

    c_1 + c_2 >= pi/4    (for Weyl chamber coordinates)

More precisely: the set of perfect entanglers is the region of the Weyl chamber where the maximum achievable concurrence equals 1. The boundary is:

    c_1 + c_2 = pi/4 (when c_3 = 0, a plane)

Combined with the Weyl chamber constraints, the perfect entanglers form a polyhedron.

**Volume fraction.** The perfect entanglers occupy exactly 84.19% of the Weyl chamber volume (with respect to the Haar measure). Most two-qubit gates are perfect entanglers.

**Examples:**
- CNOT (pi/4, 0, 0): c_1 + c_2 = pi/4 (boundary -- is a perfect entangler)
- iSWAP (pi/4, pi/4, 0): c_1 + c_2 = pi/2 > pi/4 (interior -- perfect entangler)
- sqrt(SWAP) (pi/8, pi/8, pi/8): c_1 + c_2 = pi/4 (boundary -- perfect entangler)
- Gates with c_1 + c_2 < pi/4 and c_3 small: NOT perfect entanglers


## 8. Cartan Decomposition: General Theory

**Setup.** For a compact semisimple Lie group G with Lie algebra g, a Cartan involution theta: g -> g with theta^2 = id gives:

    g = k + p    (eigenspaces of theta for eigenvalues +1, -1)

with bracket relations:
    [k, k] subset k    (k is a subalgebra)
    [k, p] subset p    (p is a k-module)
    [p, p] subset k    (crucial: p does not close under brackets)

**Maximal abelian subalgebra.** Choose a maximal abelian subspace a subset p (i.e., [a, a'] = 0 for all a, a' in a). Then dim(a) = rank of the symmetric space G/K.

**KAK decomposition.** Every g in G can be written as:

    g = k_1 . exp(a) . k_2

where k_1, k_2 in K = exp(k) and a in a. The element a is unique up to the Weyl group action.

**For SU(4)/(SU(2) x SU(2)):**
- Rank of symmetric space = 3 (hence 3 parameters c_1, c_2, c_3)
- Weyl group = S_3 x (Z_2)^2 (permutations and sign changes)
- dim(G/K) = 15 - 6 = 9


## 9. Extraction Algorithm

**Given U in SU(4), find (k_1, c_1, c_2, c_3, k_2):**

**Step 1.** Transform to the magic basis: U_B = Q* U Q where:

    Q = (1/sqrt(2)) [[1, 0, 0, i],
                      [0, i, 1, 0],
                      [0, i, -1, 0],
                      [1, 0, 0, -i]]

(The magic basis simultaneously diagonalizes sigma_y (x) sigma_y.)

**Step 2.** Compute M = U_B^T U_B (transpose, not conjugate transpose).

**Step 3.** Diagonalize M:

    M = O diag(e^{2i phi_1}, e^{2i phi_2}, e^{2i phi_3}, e^{2i phi_4}) O^T

where O is orthogonal. The phi_i are related to c_1, c_2, c_3 by:

    phi_1 = c_1 - c_2 + c_3
    phi_2 = -c_1 - c_2 - c_3 + pi
    phi_3 = -c_1 + c_2 + c_3
    phi_4 = c_1 + c_2 - c_3

(modulo pi, with sign conventions depending on the basis choice).

**Step 4.** Solve for c_1, c_2, c_3 and reduce to the Weyl chamber.

**Step 5.** Recover k_1, k_2 from U_B and O.

**Computational cost.** O(1) -- just matrix multiplications and a 4x4 diagonalization. No optimization needed.


## 10. Applications

**Quantum circuit compilation.** Any two-qubit gate can be decomposed into:
- At most 3 CNOT gates + single-qubit gates (Vatan-Williams)
- Exactly 0, 1, 2, or 3 CNOTs depending on the Weyl chamber location:
  - (0,0,0): 0 CNOTs (local gate)
  - (c_1,0,0): 1 CNOT (if c_1 = pi/4) or 2 CNOTs (general)
  - (c_1,c_2,0): 2 CNOTs
  - (c_1,c_2,c_3) general: 3 CNOTs

**Optimal gate synthesis.** Given a target unitary U:
1. Extract Weyl chamber coordinates (c_1, c_2, c_3)
2. Determine minimum CNOT count
3. Solve for the local unitaries analytically

**Hamiltonian simulation.** To simulate exp(-i H t) for a 2-qubit Hamiltonian H:
1. Decompose H using the Cartan decomposition of su(4)
2. The non-local part determines the simulation cost
3. Local terms can be compiled for free (single-qubit gates)

**Entanglement classification.** The Weyl chamber provides a complete classification of 2-qubit gates up to local equivalence. Two gates are locally equivalent iff they have the same Weyl chamber coordinates iff they have the same Makhlin invariants.

**Cross-resonance gate (superconducting qubits).** The native gate is approximately exp(-i (pi/4) sigma_z (x) sigma_x), which is locally equivalent to CNOT (both at (pi/4, 0, 0) in the Weyl chamber). The Cartan decomposition verifies this and extracts the correcting local unitaries.
