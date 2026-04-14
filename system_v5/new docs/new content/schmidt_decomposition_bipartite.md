# Schmidt Decomposition for Bipartite Systems

## 1. Statement and Construction

**Theorem (Schmidt Decomposition).** Any pure state |psi> in H_A tensor H_B (with dim H_A = m, dim H_B = n, m <= n) can be written as:

    |psi>_AB = sum_{i=1}^{r} alpha_i |i_A> |i_B>

where:
- r <= m = min(m, n) is the Schmidt rank
- alpha_i > 0 are Schmidt coefficients, sum_i alpha_i^2 = 1
- {|i_A>} are orthonormal in H_A
- {|i_B>} are orthonormal in H_B

The Schmidt coefficients are unique (up to ordering). The Schmidt bases {|i_A>}, {|i_B>} are unique when all alpha_i are distinct; degenerate coefficients allow unitary freedom within the degenerate subspace.


## 2. Construction via SVD of Coefficient Matrix

**Step 1.** Expand |psi> in computational bases:

    |psi> = sum_{j=1}^{m} sum_{k=1}^{n} C_{jk} |j> |k>

where C is an m x n complex matrix.

**Step 2.** Compute the SVD of C:

    C = U Sigma V*

where U is m x m unitary, V is n x n unitary, Sigma is m x n with diagonal entries sigma_1 >= sigma_2 >= ... >= sigma_m >= 0.

**Step 3.** Define Schmidt bases:

    |i_A> = sum_j U_{ji} |j>    (columns of U)
    |i_B> = sum_k V_{ki}^* |k>  (columns of V, conjugated)

**Step 4.** Then alpha_i = sigma_i and:

    |psi> = sum_i sigma_i |i_A> |i_B>

**Normalization check.** ||psi||^2 = Tr(C* C) = sum_i sigma_i^2 = 1.


## 3. Schmidt Rank as Entanglement Witness

**Definition.** The Schmidt rank (or Schmidt number for pure states) is r = number of nonzero Schmidt coefficients = rank(C).

**Classification:**
- r = 1: |psi> = |phi_A> tensor |phi_B> is a product state (separable)
- r > 1: |psi> is entangled
- r = min(m,n): |psi> is full Schmidt rank

**Examples (2-qubit):**

Product state: |00> has Schmidt coefficients (1, 0), rank 1.

Bell state: |Phi+> = (|00> + |11>)/sqrt(2) has C = (1/sqrt(2)) [[1,0],[0,1]], SVD gives sigma_1 = sigma_2 = 1/sqrt(2), rank 2.

General: |psi> = a|00> + b|01> + c|10> + d|11> has C = [[a,b],[c,d]]. Schmidt rank = rank(C).

**Schmidt rank is invariant under local unitaries.** If |psi'> = (U_A tensor U_B)|psi>, then C' = U_A C U_B^T, and SVD of C' has the same singular values as C.

**Schmidt rank as entanglement monotone.** Under LOCC, the Schmidt rank can only decrease (it is an entanglement monotone). More precisely, it equals the minimum number of product states needed to express |psi>.


## 4. Two-Qubit Case: Detailed Analysis

For m = n = 2, |psi> = a|00> + b|01> + c|10> + d|11>.

**Coefficient matrix:**

    C = [[a, b],
         [c, d]]

**SVD:** C = U diag(alpha_1, alpha_2) V* with alpha_1 >= alpha_2 >= 0, alpha_1^2 + alpha_2^2 = 1.

**Singular values:**

    alpha_1^2 + alpha_2^2 = 1
    alpha_1^2 * alpha_2^2 = |det(C)|^2 = |ad - bc|^2

So:
    alpha_1^2 = (1 + sqrt(1 - 4|det C|^2)) / 2
    alpha_2^2 = (1 - sqrt(1 - 4|det C|^2)) / 2

**Concurrence.** C(psi) = 2|det C| = 2 alpha_1 alpha_2. This ranges from 0 (product) to 1 (maximally entangled).

**Parametrization.** Set alpha_1 = cos(theta), alpha_2 = sin(theta) for theta in [0, pi/4]. Then:
- theta = 0: product state
- theta = pi/4: maximally entangled (Bell state)
- Concurrence = sin(2 theta)

**Entanglement entropy:**

    S = -cos^2(theta) log cos^2(theta) - sin^2(theta) log sin^2(theta) = H_2(cos^2(theta))

Monotonically increasing with theta from 0 to log 2.


## 5. Relation to Reduced Density Matrices

**Fundamental connection.** The Schmidt coefficients are the square roots of the eigenvalues of the reduced density matrices:

    rho_A = Tr_B(|psi><psi|) = sum_i alpha_i^2 |i_A><i_A|

    rho_B = Tr_A(|psi><psi|) = sum_i alpha_i^2 |i_B><i_B|

**Proof.**

    rho_A = Tr_B(sum_{i,j} alpha_i alpha_j |i_A><j_A| tensor |i_B><j_B|)
          = sum_{i,j} alpha_i alpha_j |i_A><j_A| Tr(|i_B><j_B|)
          = sum_{i,j} alpha_i alpha_j |i_A><j_A| delta_{ij}
          = sum_i alpha_i^2 |i_A><i_A|

**Key consequence.** rho_A and rho_B have the same nonzero eigenvalues, namely {alpha_i^2}. This is true even when dim(H_A) != dim(H_B); the extra eigenvalues are zero.

**Eigenvalue decomposition of rho_A via C:**

    rho_A = C C*    (eigenvalues = singular values of C squared)
    rho_B = C* C    (same nonzero eigenvalues)

This is exactly the SVD relationship: if C = U Sigma V*, then C C* = U Sigma^2 U* and C* C = V Sigma^2 V*.


## 6. Entanglement Entropy from Schmidt Coefficients

**Von Neumann entropy of entanglement:**

    S(rho_A) = S(rho_B) = -sum_i alpha_i^2 log(alpha_i^2)

This is the Shannon entropy of the probability distribution {alpha_i^2}.

**Renyi entanglement entropy:**

    S_alpha(rho_A) = 1/(1-alpha) * log(sum_i alpha_i^{2 alpha})

**Special cases:**
- S_0 = log(Schmidt rank) (Hartley entropy, counts number of nonzero coefficients)
- S_1 = von Neumann entropy (limit as alpha -> 1)
- S_2 = -log(sum alpha_i^4) = -log(Tr(rho_A^2)) = -log(purity)
- S_inf = -log(alpha_max^2) = -log(lambda_max) (min-entropy)

**Bounds:**
- 0 <= S <= log(min(m,n))
- S = 0 iff product state (one alpha_i = 1)
- S = log(min(m,n)) iff maximally entangled (all alpha_i = 1/sqrt(min(m,n)))

**Relation to majorization.** For two pure bipartite states |psi> and |phi>:

    |psi> can be converted to |phi> by LOCC
    iff alpha^2(psi) <| alpha^2(phi)    (eigenvalues of rho_A)
    implies S(rho_A^psi) >= S(rho_A^phi)  (by Schur-concavity)

LOCC can only decrease entanglement entropy.


## 7. Operator-Schmidt Decomposition

**Extension to operators.** Any operator M on H_A tensor H_B can be decomposed as:

    M = sum_{i=1}^{r} s_i A_i tensor B_i

where:
- s_i > 0 are operator-Schmidt coefficients
- {A_i} are orthonormal in H_A under the Hilbert-Schmidt inner product: Tr(A_i* A_j) = delta_{ij}
- {B_i} are orthonormal in H_B: Tr(B_i* B_j) = delta_{ij}
- r is the operator-Schmidt rank

**Construction.** Expand M in a product basis {sigma_mu tensor tau_nu}:

    M = sum_{mu, nu} T_{mu nu} sigma_mu tensor tau_nu

Compute SVD of T: T = U Sigma V*. Then A_i = sum_mu U_{mu i} sigma_mu, B_i = sum_nu V_{nu i}^* tau_nu, s_i = Sigma_{ii}.

**For density matrices (2-qubit).** Using Pauli basis {I, sigma_x, sigma_y, sigma_z} / sqrt(2):

    rho = (1/4)(I tensor I + sum_i a_i sigma_i tensor I + sum_j b_j I tensor sigma_j + sum_{ij} T_{ij} sigma_i tensor sigma_j)

The operator-Schmidt decomposition of the correlated part involves SVD of T_{ij}. The operator-Schmidt rank determines the entanglement structure.

**Operator-Schmidt rank properties:**
- rank 1: M = A tensor B is a product operator
- For unitary gates: operator-Schmidt rank is related to entangling power
- For density matrices: rank 1 iff separable (for pure states); for mixed states, separability is a stricter condition


## 8. Schmidt Number for Mixed States

**Definition (Terhal-Horodecki).** The Schmidt number of a mixed state rho is:

    SN(rho) = min_{decompositions} max_{|psi_k> in decomposition} (Schmidt rank of |psi_k>)

where the minimum is over all pure-state decompositions rho = sum_k p_k |psi_k><psi_k|.

**Properties:**
- SN(rho) = 1 iff rho is separable
- SN(rho) = k means rho requires at least one pure state with Schmidt rank >= k in every decomposition
- SN is an entanglement monotone (non-increasing under LOCC)
- 1 <= SN(rho) <= min(m, n)

**Schmidt number witnesses.** An operator W is a Schmidt-number-k witness if:
- Tr(W sigma) >= 0 for all states sigma with SN(sigma) <= k
- Tr(W rho) < 0 for some state rho with SN(rho) > k

**Construction of witnesses.** For k-positive maps Phi (positive on operators of Schmidt rank <= k but not on Schmidt rank k+1):

    W = (id tensor Phi)(|Phi+><Phi+|)

is a Schmidt-number-k witness. Here |Phi+> = (1/sqrt(d)) sum_i |ii> is the maximally entangled state.

**Relation to entanglement dimensionality.** The Schmidt number quantifies the "effective dimensionality" of entanglement. A state with SN = k requires at least k-dimensional local Hilbert spaces to exhibit its entanglement structure.


## 9. Multi-partite Generalizations

**No Schmidt decomposition for 3+ parties.** For |psi> in H_A tensor H_B tensor H_C, a Schmidt-like decomposition:

    |psi> = sum_i alpha_i |i_A> |i_B> |i_C>

does NOT always exist. Counterexample: the W state |W> = (|100> + |010> + |001>)/sqrt(3).

**SLOCC classification replaces Schmidt.** Two states are SLOCC-equivalent if connected by invertible local operations (not necessarily unitary). For 3 qubits, there are exactly 6 SLOCC classes (Dur-Vidal-Cirac):
1. Fully separable: |000>
2. Three biseparable classes: |0> tensor |Phi+>_BC (and permutations)
3. W class: |W>
4. GHZ class: |GHZ>

**Higher-order SVD (HOSVD, Tucker decomposition).** For a tensor T_{ijk}, decompose:

    T = S x_1 U^(1) x_2 U^(2) x_3 U^(3)

where S is the core tensor and U^(k) are unitary matrices from SVD of the k-th unfolding. This is not a true Schmidt decomposition but provides a canonical form.

**Tensor rank.** The minimum r such that:

    T = sum_{i=1}^{r} a_i tensor b_i tensor c_i

Computing tensor rank is NP-hard in general. This is a fundamental obstacle to multipartite entanglement theory.


## 10. Computational Aspects

**Algorithm for Schmidt decomposition:**

1. Form the m x n coefficient matrix C from the state vector
2. Compute SVD: C = U Sigma V* (cost: O(m^2 n) for m <= n)
3. Read off alpha_i = sigma_i, |i_A> from columns of U, |i_B> from columns of V

**Numerical stability.** The SVD is backward stable (Golub-Van Loan). Small singular values (near machine epsilon) should be treated as zero for rank determination. Use a threshold: sigma_i < epsilon * sigma_1 * sqrt(min(m,n)).

**Truncated Schmidt decomposition.** Keep only the k largest Schmidt coefficients:

    |psi> approx |psi_k> = (1/N) sum_{i=1}^{k} alpha_i |i_A> |i_B>

where N = sqrt(sum_{i=1}^k alpha_i^2) renormalizes. Error in trace distance:

    D(|psi><psi|, |psi_k><psi_k|) <= 2 sqrt(1 - sum_{i=1}^k alpha_i^2)

This is the foundation of MPS/DMRG truncation in many-body physics.

**Matrix Product States (MPS).** For an n-site system, repeated Schmidt decompositions across each bipartition give the MPS form:

    C_{i_1 i_2 ... i_n} = A^{[1] i_1} A^{[2] i_2} ... A^{[n] i_n}

where A^{[k] i_k} are chi x chi matrices (chi = bond dimension = max Schmidt rank across all bipartitions). This is the most efficient representation for states with bounded entanglement.
