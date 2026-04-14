# SVD and Low-Rank Approximation for Quantum States

## 1. Singular Value Decomposition: Full Statement

**Theorem (SVD).** Every m x n complex matrix A admits a decomposition:

    A = U Sigma V*

where:
- U is m x m unitary (columns are left singular vectors)
- V is n x n unitary (columns are right singular vectors)
- Sigma is m x n diagonal with real non-negative entries sigma_1 >= sigma_2 >= ... >= sigma_p >= 0, p = min(m,n)

**Compact (thin) SVD.** If rank(A) = r:

    A = sum_{i=1}^{r} sigma_i |u_i><v_i|

where |u_i> are columns of U, |v_i> are columns of V corresponding to nonzero singular values.

**Relation to eigendecomposition:**
- A*A = V Sigma^2 V* (eigenvalues = sigma_i^2, eigenvectors = right singular vectors)
- AA* = U Sigma^2 U* (eigenvalues = sigma_i^2, eigenvectors = left singular vectors)
- For Hermitian A: singular values = |eigenvalues|, and SVD reduces to spectral decomposition with signs absorbed

**For density matrices (rho = rho*, rho >= 0):** SVD = spectral decomposition:
    sigma_i = lambda_i (singular values = eigenvalues since all eigenvalues are non-negative)


## 2. Matrix Norms from SVD

**Operator (spectral) norm:**

    ||A||_op = sigma_1 = max_{|x|=1} |Ax|

**Frobenius norm:**

    ||A||_F = sqrt(sum_i sigma_i^2) = sqrt(Tr(A*A))

**Nuclear (trace) norm:**

    ||A||_1 = sum_i sigma_i

For positive semidefinite matrices: ||A||_1 = Tr(A).

**Schatten p-norms (unified family):**

    ||A||_p = (sum_i sigma_i^p)^{1/p}

- p = 1: nuclear norm
- p = 2: Frobenius norm
- p = infinity: operator norm

**Relationships for density matrices:**
- ||rho||_1 = Tr(rho) = 1 (always)
- ||rho||_F = sqrt(Tr(rho^2)) = sqrt(purity)
- ||rho||_op = lambda_max (largest eigenvalue)

**Trace distance between density matrices:**

    D(rho, sigma) = (1/2)||rho - sigma||_1 = (1/2) sum_i |mu_i|

where mu_i are eigenvalues of (rho - sigma). Note rho - sigma is Hermitian but not PSD, so this requires the singular values (= absolute eigenvalues) of the difference.


## 3. Eckart-Young-Mirsky Theorem

**Theorem (Eckart-Young, 1936; Mirsky, 1960).** The best rank-k approximation to A in both operator norm and Frobenius norm is given by truncated SVD:

    A_k = sum_{i=1}^{k} sigma_i |u_i><v_i|

**Frobenius norm version:**

    min_{rank(B) <= k} ||A - B||_F = ||A - A_k||_F = sqrt(sum_{i=k+1}^{r} sigma_i^2)

**Operator norm version:**

    min_{rank(B) <= k} ||A - B||_op = ||A - A_k||_op = sigma_{k+1}

**Proof sketch (Frobenius).** Any rank-k matrix B has at most k nonzero singular values. By the interlacing inequalities and the variational characterization of singular values, the error sum_{i=k+1}^r sigma_i^2 is minimized when B captures the top-k singular value components. The formal proof uses the Courant-Fischer min-max principle.

**Uniqueness.** The best rank-k approximation is unique iff sigma_k > sigma_{k+1}. If sigma_k = sigma_{k+1}, there is a continuous family of optimal approximations.

**Nuclear norm version.** For the nuclear norm, the best rank-k approximation is also the truncated SVD:

    min_{rank(B) <= k} ||A - B||_1 = sum_{i=k+1}^{r} sigma_i


## 4. Low-Rank Approximation of Density Matrices

**Problem.** Given rho (rank r, dimension n), find the best rank-k density matrix approximation (k < r).

**Naive truncation.** The Eckart-Young truncation gives:

    rho_k^{raw} = sum_{i=1}^{k} lambda_i |i><i|

This is PSD but has Tr(rho_k^{raw}) = sum_{i=1}^k lambda_i < 1. It is NOT a valid density matrix.

**Trace renormalization.** Define:

    rho_k = rho_k^{raw} / Tr(rho_k^{raw}) = sum_{i=1}^{k} (lambda_i / sum_{j=1}^k lambda_j) |i><i|

This IS a valid density matrix but is NOT the best rank-k approximation in trace distance.

**Best rank-k density matrix approximation (trace distance).** The optimization:

    min_{sigma: rank(sigma) <= k, Tr(sigma) = 1, sigma >= 0} D(rho, sigma)

has the solution (Ky Fan):

    sigma_opt = sum_{i=1}^{k-1} lambda_i |i><i| + (1 - sum_{i=1}^{k-1} lambda_i) |k><k|

i.e., keep the top k-1 eigenvalues and lump all remaining probability into the k-th eigenvector. The trace distance is:

    D(rho, sigma_opt) = sum_{i=k+1}^{r} lambda_i

**Fidelity-based approximation.** For fidelity F(rho, sigma) = (Tr sqrt(sqrt(rho) sigma sqrt(rho)))^2, the optimal rank-k approximation differs from the trace-distance optimal. For pure-state fidelity with mixed states, the truncated + renormalized form often suffices.

**Information loss.** The entropy of the discarded part:

    Delta S = -sum_{i=k+1}^{r} lambda_i log lambda_i

quantifies the information lost in truncation.


## 5. Nuclear Norm and Trace Norm

**Nuclear norm.** For any matrix A:

    ||A||_* = ||A||_1 = sum_i sigma_i = Tr(sqrt(A*A))

**Dual norm relationship:**

    ||A||_* = max_{||B||_op <= 1} |Tr(B*A)|    (nuclear norm is dual to operator norm)
    ||A||_op = max_{||B||_* <= 1} |Tr(B*A)|    (operator norm is dual to nuclear norm)

**For PSD matrices:** ||A||_* = Tr(A) (trivially, since singular values = eigenvalues >= 0).

**For Hermitian matrices:** ||A||_* = sum_i |lambda_i| = Tr(|A|) where |A| = sqrt(A^2).

**Nuclear norm minimization.** The convex relaxation of rank minimization:

    min rank(X) subject to constraints  -->  min ||X||_* subject to constraints

This is the basis of compressed sensing / matrix completion algorithms.

**Application to quantum state tomography.** Reconstructing rho from partial measurements can use nuclear norm minimization:

    min ||X||_* subject to Tr(M_i X) = m_i, X >= 0

The nuclear norm penalty encourages low-rank solutions (since physical density matrices are often low-rank or approximately low-rank).


## 6. Correlation Tensor SVD for 2-Qubit States

**Bloch representation of 2-qubit state.** Any 2-qubit density matrix:

    rho = (1/4)(I tensor I + a . sigma tensor I + I tensor b . sigma + sum_{ij} T_{ij} sigma_i tensor sigma_j)

where:
- a = (a_1, a_2, a_3) is the Bloch vector of subsystem A: a_i = Tr(rho (sigma_i tensor I))
- b = (b_1, b_2, b_3) is the Bloch vector of subsystem B: b_i = Tr(rho (I tensor sigma_i))
- T is the 3x3 real correlation tensor: T_{ij} = Tr(rho (sigma_i tensor sigma_j))

**SVD of the correlation tensor.**

    T = O_1 diag(t_1, t_2, t_3) O_2^T

where O_1, O_2 are 3x3 real orthogonal matrices (in SO(3) if we absorb signs into the singular values, allowing t_i to be negative) and t_1 >= t_2 >= |t_3| (with convention that we allow signed "singular values" to maintain proper orientations).

**Proper convention.** More precisely, take the standard SVD T = O_1 diag(|t_1|, |t_2|, |t_3|) O_2^T with all entries non-negative, then absorb signs: t_i = sign * |t_i| where sign is determined by det(O_1) det(O_2).

**Physical meaning of T-SVD components:**

- **t_1, t_2, t_3 (principal correlations):** The singular values measure the strength of correlations along the principal axes. For a product state: all t_i = a_i * b_j type factored form, not independent.

- **O_1, O_2 (rotations):** Correspond to local unitary operations on each qubit. Specifically, U_A = exp(-i theta_A n_A . sigma/2) acts as a rotation O_1 on the Bloch sphere of A. So O_1 and O_2 encode the local unitary freedom.

- **Local unitary invariants:** The values (t_1, t_2, t_3) along with (|a|, |b|, a . T b, ...) form a complete set of local unitary invariants.

**Entanglement conditions on (t_1, t_2, t_3).**

For Bell-diagonal states (a = b = 0):

    rho_BD = (1/4)(I tensor I + sum_i t_i sigma_i tensor sigma_i)

Eigenvalues of rho_BD:

    lambda_1 = (1 + t_1 - t_2 + t_3)/4
    lambda_2 = (1 + t_1 + t_2 - t_3)/4
    lambda_3 = (1 - t_1 + t_2 + t_3)/4
    lambda_4 = (1 - t_1 - t_2 - t_3)/4

Positivity requires all lambda_i >= 0, giving:

    |t_1 - t_2| <= 1 - |t_3 + t_1|  (and permutations -- the tetrahedron condition)

The set of valid (t_1, t_2, t_3) is a tetrahedron with vertices at:
- (1, 1, 1): |Phi+>
- (1, -1, -1): |Psi+>
- (-1, 1, -1): |Phi->
- (-1, -1, 1): |Psi->

**Separability of Bell-diagonal states.** rho_BD is separable iff:

    |t_1| + |t_2| + |t_3| <= 1

This is the octahedron inscribed in the tetrahedron. The entangled Bell-diagonal states are the four "corner" regions between the octahedron and tetrahedron.

**Concurrence of Bell-diagonal states:**

    C(rho_BD) = max(0, 2 max_i |lambda_i| - 1)

where lambda_i are the eigenvalues above.

**General entanglement criterion (Horodecki).** For any 2-qubit state, the Peres-Horodecki criterion (PPT) is necessary and sufficient. In terms of T: the partial transpose flips the sign of t_2 (for transpose on B with respect to sigma_y), and the state is entangled iff the partially transposed matrix has a negative eigenvalue.


## 7. Singular Values and Entanglement Measures

**Negativity from singular values.** The negativity is:

    N(rho) = (||rho^{T_B}||_1 - 1) / 2 = sum_{sigma_i < 0 in spectrum of rho^{T_B}} |sigma_i|

where rho^{T_B} is the partial transpose (Hermitian, so eigenvalues = signed singular values).

**Realignment criterion.** Define the realignment R(rho) by R_{(ij),(kl)} = rho_{ik,jl}. Then:

    ||R(rho)||_1 > 1 implies rho is entangled

The singular values of R(rho) thus provide an entanglement witness.

**Cross-norm criterion.** Equivalent to realignment: for any decomposition rho = sum_k A_k tensor B_k:

    sum_k ||A_k||_1 * ||B_k||_1 >= 1 for separable states

Violation implies entanglement.

**Correlation matrix criterion.** For the 3x3 correlation tensor T and Bloch vectors a, b, define the 4x4 matrix:

    M = [[1, b^T], [a, T]]

The singular values of M constrain separability.


## 8. Low-Rank Structure in Quantum Channels

**Choi matrix rank = Kraus rank.** A quantum channel E with Choi matrix J(E) has:

    Kraus rank = rank(J(E)) = number of nonzero singular values of J(E)

since J(E) is PSD, singular values = eigenvalues.

**Low-rank channels.** A channel with Kraus rank k has:

    E(rho) = sum_{i=1}^{k} K_i rho K_i*

The minimum k is the Choi rank. Examples:
- Unitary channel: k = 1 (E(rho) = U rho U*)
- Depolarizing channel: k = 4 in dimension 2
- Amplitude damping: k = 2

**Low-rank approximation of channels.** Truncate the Choi matrix SVD:

    J(E) approx J_k(E) = sum_{i=1}^{k} mu_i |phi_i><phi_i|

This gives an approximate channel with k Kraus operators. BUT: the approximate channel may not be trace-preserving. Enforcing Tr_output(J_k) = I requires a constrained optimization.

**Stinespring dilation and rank.** The Stinespring representation E(rho) = Tr_E(V rho V*) has the environment dimension = Choi rank. Low Choi rank means the channel's interaction with the environment is "simple."


## 9. Randomized SVD for Large Density Matrices

**Problem.** Computing full SVD of an n x n matrix costs O(n^3). For large quantum systems (n = 2^N for N qubits), this is intractable.

**Randomized SVD algorithm (Halko-Martinsson-Tropp):**

1. Draw random Gaussian matrix Omega (n x (k+p)), where k = target rank, p = oversampling (p ~ 5-10)
2. Form Y = A Omega (n x (k+p) matrix)
3. Compute QR: Y = QR
4. Form B = Q* A (small (k+p) x n matrix)
5. Compute SVD of B: B = U_B Sigma V*
6. Recover: A approx (Q U_B) Sigma V*

**Cost:** O(n^2 (k+p)) instead of O(n^3). For k << n, this is a massive speedup.

**Error bound:**

    E[||A - A_k||_F] <= (1 + k/(p-1))^{1/2} * (sum_{i=k+1}^{min(m,n)} sigma_i^2)^{1/2}

For p >= 2, the expectation is within a small constant factor of optimal.

**Application to quantum state tomography.** When rho is approximately rank-k with k << n = 2^N, randomized SVD enables efficient estimation from measurement data.


## 10. Connections Between SVD Concepts

**Unified view.** The SVD sits at the center of a web connecting:

    Schmidt decomposition (SVD of coefficient matrix C)
          |
          v
    Reduced density matrices (rho_A = CC*, rho_B = C*C)
          |
          v
    Entanglement measures (functions of singular values of C)
          |
          v
    Low-rank approximation (truncated SVD = MPS truncation)
          |
          v
    Channel decomposition (SVD of Choi matrix -> Kraus operators)

**Key identity chain.** For a bipartite pure state |psi> with coefficient matrix C:

    Singular values of C = Schmidt coefficients alpha_i
    alpha_i^2 = eigenvalues of rho_A = eigenvalues of rho_B
    S(rho_A) = -sum alpha_i^2 log alpha_i^2 = H(alpha^2)
    ||C||_F = 1 (normalization)
    ||C||_1 = sum alpha_i (related to concurrence for 2-qubit)
    rank(C) = Schmidt rank = entanglement dimensionality
    ||C||_op = alpha_max = sqrt(lambda_max(rho_A)) = sqrt(max overlap with product state)
