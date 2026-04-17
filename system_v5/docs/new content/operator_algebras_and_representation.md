# Operator Algebras and Representation Theory for Quantum Information

## 1. su(2) Algebra: Complete Treatment

**Generators and commutation relations.**

    [J_x, J_y] = i J_z
    [J_y, J_z] = i J_x
    [J_z, J_x] = i J_y

Compact form: [J_i, J_j] = i epsilon_{ijk} J_k, where epsilon is the Levi-Civita symbol.

**Raising/lowering operators.**

    J_+ = J_x + i J_y,    J_- = J_x - i J_y = (J_+)*

    [J_z, J_+] = J_+      (J_+ raises eigenvalue of J_z by 1)
    [J_z, J_-] = -J_-     (J_- lowers eigenvalue of J_z by 1)
    [J_+, J_-] = 2 J_z

**Casimir operator.**

    J^2 = J_x^2 + J_y^2 + J_z^2 = J_z^2 + J_z + J_- J_+ = J_z^2 - J_z + J_+ J_-

    [J^2, J_i] = 0    for all i (J^2 commutes with all generators)

**Eigenvalues.**

    J^2 |j, m> = j(j+1) |j, m>
    J_z |j, m> = m |j, m>

with j = 0, 1/2, 1, 3/2, ... and m = -j, -j+1, ..., j-1, j.

    J_+ |j, m> = sqrt(j(j+1) - m(m+1)) |j, m+1> = sqrt((j-m)(j+m+1)) |j, m+1>
    J_- |j, m> = sqrt(j(j+1) - m(m-1)) |j, m-1> = sqrt((j+m)(j-m+1)) |j, m-1>


## 2. Representations of su(2)

**Spin-j representation.** Dimension d = 2j + 1. The representation space is spanned by {|j, m>}_{m=-j}^{j}.

**Explicit matrices for small j:**

**j = 1/2 (qubit):**

    J_x = (1/2) sigma_x = (1/2)[[0,1],[1,0]]
    J_y = (1/2) sigma_y = (1/2)[[0,-i],[i,0]]
    J_z = (1/2) sigma_z = (1/2)[[1,0],[0,-1]]

    J^2 = (3/4) I

**j = 1 (qutrit):**

    J_x = (1/sqrt(2)) [[0,1,0],[1,0,1],[0,1,0]]
    J_y = (1/sqrt(2)) [[0,-i,0],[i,0,-i],[0,i,0]]
    J_z = [[1,0,0],[0,0,0],[0,0,-1]]

    J^2 = 2 I

**j = 3/2:**

    J_z = diag(3/2, 1/2, -1/2, -3/2)
    J_+ = [[0, sqrt(3), 0, 0],
            [0, 0, 2, 0],
            [0, 0, 0, sqrt(3)],
            [0, 0, 0, 0]]

    J^2 = (15/4) I

**Irreducibility.** Each spin-j representation is irreducible: no proper invariant subspace. Every finite-dimensional irreducible representation of su(2) is isomorphic to exactly one spin-j representation.

**Complete reducibility.** Every finite-dimensional representation of su(2) decomposes as a direct sum of irreducible representations. (This is because SU(2) is compact, so all representations are unitarizable.)


## 3. Clebsch-Gordan Decomposition

**Tensor product decomposition.**

    j_1 (x) j_2 = |j_1 - j_2| (+) |j_1 - j_2| + 1 (+) ... (+) (j_1 + j_2)

As vector spaces:

    C^{2j_1 + 1} (x) C^{2j_2 + 1} = C^{2|j_1-j_2|+1} (+) C^{2|j_1-j_2|+3} (+) ... (+) C^{2(j_1+j_2)+1}

Dimension check: (2j_1+1)(2j_2+1) = sum_{j=|j_1-j_2|}^{j_1+j_2} (2j+1). This is verified by the identity for arithmetic sums.

**Clebsch-Gordan coefficients.** The change of basis:

    |j, m> = sum_{m_1 + m_2 = m} <j_1, m_1; j_2, m_2 | j, m> |j_1, m_1> |j_2, m_2>

The coefficients <j_1, m_1; j_2, m_2 | j, m> are the Clebsch-Gordan (CG) coefficients.

**Properties of CG coefficients:**
- Real (with Condon-Shortley phase convention)
- Nonzero only when m = m_1 + m_2 and |j_1 - j_2| <= j <= j_1 + j_2
- Orthogonality: sum_{m_1 m_2} <j_1,m_1;j_2,m_2|j,m> <j_1,m_1;j_2,m_2|j',m'> = delta_{jj'} delta_{mm'}
- Symmetry: <j_1,m_1;j_2,m_2|j,m> = (-1)^{j_1+j_2-j} <j_2,m_2;j_1,m_1|j,m>

**Wigner 3j-symbols (symmetric form).**

    (j_1  j_2  j_3)   = (-1)^{j_1-j_2-m_3} / sqrt(2j_3+1) * <j_1,m_1;j_2,m_2|j_3,-m_3>
    (m_1  m_2  m_3)

More symmetric under permutations. Selection rules: m_1 + m_2 + m_3 = 0 and triangle inequality |j_1 - j_2| <= j_3 <= j_1 + j_2.


## 4. Two-Qubit System: 1/2 (x) 1/2

**Decomposition.** 1/2 (x) 1/2 = 0 (+) 1 (singlet + triplet).

**Explicit basis change:**

Triplet (j = 1, symmetric):

    |1, 1> = |up up> = |00>
    |1, 0> = (|up down> + |down up>)/sqrt(2) = (|01> + |10>)/sqrt(2)
    |1, -1> = |down down> = |11>

Singlet (j = 0, antisymmetric):

    |0, 0> = (|up down> - |down up>)/sqrt(2) = (|01> - |10>)/sqrt(2)

**CG coefficients for 1/2 (x) 1/2:**

    <1/2,1/2; 1/2,1/2 | 1,1> = 1
    <1/2,1/2; 1/2,-1/2 | 1,0> = 1/sqrt(2)
    <1/2,-1/2; 1/2,1/2 | 1,0> = 1/sqrt(2)
    <1/2,1/2; 1/2,-1/2 | 0,0> = 1/sqrt(2)
    <1/2,-1/2; 1/2,1/2 | 0,0> = -1/sqrt(2)
    <1/2,-1/2; 1/2,-1/2 | 1,-1> = 1

**Relation to Bell states.** The singlet is (up to phase) the Bell state |Psi->. The triplet states are related to the other Bell states by local unitaries:

    |Phi+> = (|00> + |11>)/sqrt(2) = (|1,1> + |1,-1>)/sqrt(2)    (superposition of triplet)
    |Phi-> = (|00> - |11>)/sqrt(2) = (|1,1> - |1,-1>)/sqrt(2)    (superposition of triplet)
    |Psi+> = (|01> + |10>)/sqrt(2) = |1,0>                        (triplet)
    |Psi-> = (|01> - |10>)/sqrt(2) = |0,0>                        (singlet)

**Total spin.** For the singlet: J^2_total = 0, J_total = 0. For the triplet: J^2_total = 2, J_total = 1.

**Singlet as maximally entangled.** The singlet has maximum entanglement entropy S = log 2. It is the unique state (up to phase) that is invariant under simultaneous rotations U (x) U for all U in SU(2). This is the representation-theoretic origin of its special role in entanglement theory.

**Exchange symmetry.** The SWAP operator P_{12} has eigenvalue +1 on the triplet (symmetric) and -1 on the singlet (antisymmetric):

    P_{12} = (1/2)(I (x) I + sigma_x (x) sigma_x + sigma_y (x) sigma_y + sigma_z (x) sigma_z)

    P_{12} = 2 P_{sym} - I = I - 2 P_{antisym}

where P_{sym/antisym} are projectors onto symmetric/antisymmetric subspaces.


## 5. su(4): Structure and Generators

**Generators.** su(4) has dimension 15. A natural basis for the 2-qubit system:

Type I (local on A): sigma_x (x) I, sigma_y (x) I, sigma_z (x) I (3 generators)
Type II (local on B): I (x) sigma_x, I (x) sigma_y, I (x) sigma_z (3 generators)
Type III (non-local): sigma_i (x) sigma_j for i,j in {x,y,z} (9 generators)

Total: 3 + 3 + 9 = 15 = dim(su(4)).

**Subalgebra structure.** su(2)_A (+) su(2)_B is a subalgebra (Type I + Type II generators close under commutation). The non-local generators (Type III) form the complement p in the Cartan decomposition.

**Commutation relations.**

    [sigma_i (x) I, I (x) sigma_j] = 0                        (local algebras commute)
    [sigma_i (x) I, sigma_j (x) sigma_k] = 2i epsilon_{ijl} sigma_l (x) sigma_k    (k acts on Type III)
    [sigma_i (x) sigma_j, sigma_k (x) sigma_l] = ...          (produces both local and non-local)

The last type: [sigma_i (x) sigma_j, sigma_k (x) sigma_l] = (delta_{ik} epsilon_{jlm} I (x) sigma_m + epsilon_{ikm} delta_{jl} sigma_m (x) I + ...) -- this is the [p,p] subset k relation of the Cartan decomposition.

**Generalized Gell-Mann matrices.** For su(n), the generalized Gell-Mann matrices provide a standard basis. For n = 4, there are 15 traceless Hermitian 4x4 matrices, organized into:
- 6 symmetric off-diagonal (like sigma_x)
- 6 antisymmetric off-diagonal (like sigma_y)
- 3 diagonal traceless (like sigma_z, plus higher Cartan elements)


## 6. Killing Form and Structure Constants

**Structure constants.** For a basis {T_a} of a Lie algebra g:

    [T_a, T_b] = sum_c f_{abc} T_c

The f_{abc} are the structure constants. For su(2): f_{123} = 1 (and cyclic permutations), all others zero (with T_i = J_i).

**Killing form.** For any Lie algebra g:

    K(X, Y) = Tr(ad_X . ad_Y)

where (ad_X)(Z) = [X, Z] is the adjoint representation.

**Explicit.** In terms of structure constants:

    K_{ab} = sum_{c,d} f_{acd} f_{bdc}

**For su(2):**

    K_{ij} = -2 delta_{ij}

(The factor depends on normalization. With generators J_i satisfying [J_i, J_j] = i epsilon_{ijk} J_k, we get K_{ij} = -2 delta_{ij}.)

**Properties:**
- K is bilinear, symmetric, ad-invariant: K([X,Y], Z) = K(X, [Y,Z])
- For semisimple g: K is non-degenerate (Cartan's criterion)
- For compact g: K is negative definite (equivalently, -K is a positive definite inner product)
- For su(n): K(X, Y) = 2n Tr(X Y) (up to normalization, where X, Y are in the fundamental representation)

**Negative definiteness for compact algebras.** K < 0 implies the group is compact. This is because the Killing form controls the curvature of the group manifold: negative K means positive sectional curvature (compact manifold).

**Application to quantum information.** The Killing form provides the natural inner product on the space of Hamiltonians. For su(4), it gives the metric on the 15-dimensional parameter space of 2-qubit Hamiltonians, which is used in optimal control theory.


## 7. Casimir Operators

**Definition.** A Casimir operator C is an element of the universal enveloping algebra that commutes with all generators: [C, T_a] = 0 for all a.

**Construction.** Using the Killing form to raise indices:

    C = sum_{a,b} K^{ab} T_a T_b

where K^{ab} is the inverse of the Killing metric.

**For su(2):**

    C_2 = J_x^2 + J_y^2 + J_z^2 = J^2

Eigenvalue on spin-j representation: C_2 = j(j+1).

**For su(n):** There are n-1 independent Casimir operators (= rank of su(n)).

**For su(4):** Three Casimir operators: C_2 (quadratic), C_3 (cubic), C_4 (quartic).

    C_2 = sum_a T_a^2    (quadratic Casimir)

On the fundamental representation (4-dimensional): C_2 = (n^2 - 1)/(2n) I = 15/8 I.

**Casimir eigenvalues for su(2) representations appearing in 2-qubit system:**

Decomposition as su(2)_total: 1/2 (x) 1/2 = 0 (+) 1.
- On j = 0 (singlet): C_2 = 0
- On j = 1 (triplet): C_2 = 2

**Casimir and entanglement.** The total spin Casimir J^2_total = (J_A + J_B)^2 = J_A^2 + J_B^2 + 2 J_A . J_B. Since J_A^2 = J_B^2 = 3/4 for two qubits:

    J_A . J_B = (J^2_total - J_A^2 - J_B^2) / 2 = (J^2_total - 3/2) / 2

For the singlet: J_A . J_B = -3/4 (maximally anti-correlated, maximally entangled).
For the triplet: J_A . J_B = 1/4 (correlated).

The expectation value of the exchange interaction J_A . J_B is thus an entanglement witness.


## 8. Jordan Algebra Perspective

**Jordan product.** For two observables (Hermitian operators) A, B:

    A o B = (AB + BA) / 2

This is the symmetrized (anti-commutator) product, stripping out the Lie bracket part.

**Jordan algebra properties:**
- A o B = B o A (commutative)
- A o (B o A^2) = (A o B) o A^2 (Jordan identity, NOT associative in general)
- A o B is Hermitian when A, B are Hermitian (unlike AB which may not be)

**Decomposition of operator product.** The full product of Hermitian operators splits:

    AB = (A o B) + (i/2)[A, B] / i = (A o B) + (1/2)[A, B]

- Jordan part A o B: symmetric, Hermitian, commutative
- Lie part [A, B]/2: antisymmetric, anti-Hermitian (times i is Hermitian)

**Physical meaning:**
- The Jordan product governs measurement statistics: <A o B> = Re(<AB>) relates to sequential measurement correlations
- The Lie bracket governs dynamics: d/dt A = (i/hbar)[H, A]
- Quantum mechanics requires BOTH structures (unlike classical mechanics, which only needs the Poisson bracket)

**JBW algebra of density matrices.** The set of density matrices on C^n forms a JBW (Jordan-Banach-Wigner) algebra under the Jordan product. The state space (density matrices) is the "positive cone" of this algebra.

**Special Jordan algebras.** The Jordan algebra of n x n Hermitian matrices over C is a special Jordan algebra (embeddable in an associative algebra). The exceptional Jordan algebra (3 x 3 Hermitian matrices over octonions, 27-dimensional) is not embeddable and has deep connections to string theory and exceptional groups.

**Spectral theory in Jordan algebras.** An element A of a Jordan algebra has a spectral decomposition A = sum lambda_i e_i where e_i are orthogonal idempotents (e_i o e_j = delta_{ij} e_i). For the matrix Jordan algebra, this reduces to the usual spectral decomposition. The Jordan algebraic framework provides an axiomatization of quantum mechanics without assuming the full associative matrix structure.


## 9. Representation Theory and Quantum Information

**Schur-Weyl duality.** For n copies of C^d (d-dimensional system):

    (C^d)^{(x) n} = sum_lambda V_lambda (x) S_lambda

where:
- lambda ranges over Young diagrams with n boxes and at most d rows
- V_lambda is an irreducible representation of GL(d) (or U(d))
- S_lambda is an irreducible representation of the symmetric group S_n
- The sum is a direct sum, and the decomposition is multiplicity-free

**Application to quantum information:**
- Permutation-invariant states live in the symmetric subspace (lambda = (n), one row)
- The symmetric subspace of n qubits has dimension n+1 (spin-j = n/2 representation)
- Quantum de Finetti theorem: permutation-invariant states on many copies are approximately mixtures of tensor products (connects to the symmetric subspace)

**Representation-theoretic entanglement measures.** For a bipartite state |psi> in C^d (x) C^d, the Schmidt decomposition corresponds to the decomposition of the fundamental representation of U(d) x U(d) acting on C^d (x) C^d.

**Weyl's unitary trick.** Representations of the compact group SU(n) are in bijection with polynomial representations of GL(n, C). This allows using algebraic (highest weight) methods for compact group representation theory.

**Highest weight theory.** Irreducible representations of su(n) are classified by their highest weight lambda = (lambda_1, ..., lambda_{n-1}) with lambda_1 >= lambda_2 >= ... >= lambda_{n-1} >= 0 (integers). The dimension is given by the Weyl dimension formula. For su(2): highest weight = 2j, dimension = 2j+1.


## 10. Tensor Network Notation and Algebra

**Graphical calculus for tensor products.** Represent:
- State |psi> as a triangle with one leg (the Hilbert space index)
- Operator A as a box with two legs (input and output)
- Tensor product: place diagrams side by side (legs don't connect)
- Contraction (trace): connect legs

**Key identities in graphical notation:**

    Tr(AB) = loop connecting A and B
    |psi><phi| = triangle-triangle connection
    Tr_B(rho_AB) = partial loop (connect only B-legs of rho)

**Tensor network states:**
- MPS: chain of tensors, bond dimension = Schmidt rank across each cut
- PEPS: 2D grid of tensors
- MERA: hierarchical tensor network with disentanglers

**Algebraic structure.** The space of linear operators on H_A (x) H_B is:

    End(H_A (x) H_B) = End(H_A) (x) End(H_B)

This is an algebra isomorphism. The Pauli matrices {I, sigma_x, sigma_y, sigma_z} form a basis of End(C^2), so {sigma_mu (x) sigma_nu}_{mu, nu = 0}^{3} form a basis of End(C^2 (x) C^2) = End(C^4).

**Operator algebra decomposition.** Any 4x4 matrix M can be uniquely written as:

    M = sum_{mu, nu = 0}^{3} m_{mu nu} (sigma_mu (x) sigma_nu) / 4

where sigma_0 = I and m_{mu nu} = Tr(M (sigma_mu (x) sigma_nu)). This is the "Pauli transfer matrix" representation, fundamental to quantum process tomography.
