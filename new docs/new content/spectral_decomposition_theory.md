# Spectral Decomposition Theory for Density Matrices

## 1. Spectral Theorem for Normal Operators on C^n

**Theorem (Spectral Theorem, finite-dimensional).** Let A be a normal operator on C^n (i.e., A*A = AA*). Then there exists a unitary U and a diagonal matrix D such that:

    A = U D U*

Equivalently, A = sum_{i=1}^{n} lambda_i |e_i><e_i|

where {|e_i>} is an orthonormal eigenbasis and lambda_i in C are eigenvalues.

**Proof sketch.** A normal implies A is diagonalizable. Take any eigenvalue lambda_1 (guaranteed by fundamental theorem of algebra over C). The eigenspace E_1 = ker(A - lambda_1 I) is nonzero. For normal A, A* also preserves E_1^perp (since A*A = AA* implies A maps E_1^perp to itself). Induct on E_1^perp. QED.

**Key specializations:**
- Hermitian (A = A*): all lambda_i real
- Unitary (A*A = I): all |lambda_i| = 1
- Positive semidefinite (Hermitian + lambda_i >= 0): density matrices live here
- Projectors (A^2 = A, A = A*): lambda_i in {0, 1}

**Functional calculus.** For any function f: C -> C, define:

    f(A) = sum_i f(lambda_i) |e_i><e_i|

This is the foundation for computing log(rho), sqrt(rho), rho^alpha, etc.


## 2. Density Matrix Spectral Decomposition

A density matrix rho on C^n satisfies:
1. rho = rho* (Hermitian)
2. rho >= 0 (positive semidefinite)
3. Tr(rho) = 1

Its spectral decomposition is:

    rho = sum_{i=1}^{n} lambda_i |i><i|

with constraints:
- lambda_i >= 0 for all i
- sum_i lambda_i = 1
- {|i>} orthonormal

**The eigenvalues form a probability distribution** over the eigenstates. This is the unique convex decomposition into mutually orthogonal pure states.

**Rank and purity:**
- rank(rho) = number of nonzero lambda_i = dimension of support
- Pure state: rank 1, rho = |psi><psi|, one eigenvalue = 1
- Maximally mixed: rho = I/n, all eigenvalues = 1/n
- Purity: Tr(rho^2) = sum_i lambda_i^2, ranges from 1/n to 1

**Non-uniqueness of convex decompositions.** While the spectral decomposition is unique (up to degeneracy), rho has infinitely many decompositions as convex combinations of pure states:

    rho = sum_j p_j |psi_j><psi_j|

These are related by Schrodinger's mixture theorem (Hughston-Jozsa-Wootters): all decompositions of rho into m >= n pure states are related by partial isometries.


## 3. Eigenvalue Interlacing for Partial Traces (Thompson's Theorem)

**Setup.** Let rho_AB be a density matrix on C^m tensor C^n with eigenvalues mu_1 >= mu_2 >= ... >= mu_{mn}. Let rho_A = Tr_B(rho_AB) with eigenvalues lambda_1 >= ... >= lambda_m.

**Thompson's interlacing inequalities.** The eigenvalues of rho_A are constrained by those of rho_AB:

    sum_{i=1}^{k} lambda_i <= sum_{i=1}^{kn} mu_i,    for k = 1, ..., m

    sum_{i=m-k+1}^{m} lambda_i >= sum_{i=mn-kn+1}^{mn} mu_i,    for k = 1, ..., m

**More refined statement.** For any index set I subset {1,...,mn} with |I| = m, the eigenvalues satisfy Horn-type inequalities. The complete set of inequalities characterizing the relationship lambda(rho_A) vs mu(rho_AB) is given by the solution to the Horn conjecture (Klyachko, Knutson-Tao).

**Key special case (pure state).** If rho_AB = |psi><psi| (rank 1), then:
- rho_A and rho_B have the SAME nonzero eigenvalues (Schmidt decomposition)
- lambda_i(rho_A) = lambda_i(rho_B) for all i (with zero-padding)

**Araki-Lieb inequality (entropy version).**

    |S(rho_A) - S(rho_B)| <= S(rho_AB) <= S(rho_A) + S(rho_B)

This is the entropy consequence of eigenvalue interlacing.


## 4. Weyl's Inequalities for Eigenvalue Perturbation

**Theorem (Weyl, 1912).** Let A, B be n x n Hermitian matrices with eigenvalues alpha_1 >= ... >= alpha_n and beta_1 >= ... >= beta_n respectively. Let C = A + B with eigenvalues gamma_1 >= ... >= gamma_n. Then:

    alpha_i + beta_n <= gamma_i <= alpha_i + beta_1

More precisely, for i + j - n <= k <= i + j - 1 (when indices are valid):

    gamma_k <= alpha_i + beta_j

and for i + j <= k + 1 (when valid):

    gamma_k >= alpha_i + beta_j

**Corollary (perturbation bound).** If B is a perturbation with ||B||_op = epsilon, then:

    |gamma_i - alpha_i| <= epsilon    for all i

**Application to density matrices.** If rho and sigma are density matrices with ||rho - sigma||_op <= epsilon, their eigenvalues satisfy:

    |lambda_i(rho) - lambda_i(sigma)| <= epsilon

This gives continuity of all spectral functions.

**Lidskii's theorem (refinement).** The vector of eigenvalue differences gamma - alpha is majorized by the vector of eigenvalues of B:

    gamma - alpha is majorized by eigenvalues(B)

**Hoffman-Wielandt inequality (Frobenius norm version).**

    sum_i (gamma_i - alpha_i)^2 <= ||B||_F^2 = Tr(B*B)

**Fan's inequality.** For k = 1, ..., n:

    sum_{i=1}^{k} gamma_i <= sum_{i=1}^{k} alpha_i + sum_{i=1}^{k} beta_i


## 5. Majorization Theory

**Definition.** For vectors x, y in R^n with components sorted in decreasing order (x_1^down >= x_2^down >= ...), x is majorized by y (written x <| y) if:

    sum_{i=1}^{k} x_i^down <= sum_{i=1}^{k} y_i^down    for k = 1, ..., n-1
    sum_{i=1}^{n} x_i^down = sum_{i=1}^{n} y_i^down        (equality for k = n)

**Equivalent characterizations (Hardy-Littlewood-Polya):**
1. x <| y iff x = Dy for some doubly stochastic matrix D
2. x <| y iff x is in the convex hull of all permutations of y
3. x <| y iff sum_i f(x_i) <= sum_i f(y_i) for all convex functions f

**Birkhoff's theorem.** The set of doubly stochastic matrices is the convex hull of permutation matrices. This connects majorization to the symmetric group.

**Partial order structure.** Majorization defines a partial order on probability vectors. The extremes are:
- Most majorized: (1/n, ..., 1/n) (uniform)
- Least majorized: (1, 0, ..., 0) (pure)

**Lorenz curve.** Plot (k/n, sum_{i=1}^k x_i^down) for k = 0, ..., n. Then x <| y iff the Lorenz curve of x lies nowhere above that of y.


## 6. Nielsen's Theorem (LOCC Convertibility)

**Theorem (Nielsen, 1999).** For bipartite pure states |psi> and |phi> on C^d tensor C^d, the transformation |psi> -> |phi> is achievable by Local Operations and Classical Communication (LOCC) if and only if:

    lambda(rho_A^psi) <| lambda(rho_A^phi)

where lambda(rho) denotes the vector of eigenvalues of rho sorted in decreasing order.

**Proof sketch.**

(=>) LOCC operations have the form sum_k (A_k tensor B_k) rho (A_k tensor B_k)* with sum_k A_k* A_k = I. For pure-to-pure, this imposes that the Schmidt coefficients transform by a doubly stochastic matrix. By Birkhoff, this is equivalent to majorization.

(<=) If lambda^psi <| lambda^phi, construct an explicit LOCC protocol: Alice measures in the Schmidt basis of |psi>, applies a random unitary conditioned on outcome to steer Schmidt coefficients of the post-measurement state to match those of |phi>. The majorization condition guarantees the required probability distribution is achievable.

**Consequences:**
- Entanglement is a resource that can only decrease under LOCC
- Maximally entangled state |Phi+> = (1/sqrt(d)) sum_i |ii> has lambda = (1/d, ..., 1/d), which is majorized by all other lambda vectors => can be converted to ANY state by LOCC
- GHZ and W states are LOCC-incomparable for 3+ qubits (neither majorizes the other)

**Catalytic LOCC (Jonathan-Plenio).** There exist states |psi>, |phi> where |psi> -/-> |phi> by LOCC but |psi> tensor |chi> -> |phi> tensor |chi> for some catalyst |chi>. The catalysis condition uses a refined majorization criterion called trumping.


## 7. Schur-Horn Theorem

**Theorem (Schur, 1923; Horn, 1954).** Let A be an n x n Hermitian matrix with eigenvalues lambda = (lambda_1, ..., lambda_n). Let d = (d_1, ..., d_n) be its diagonal entries d_i = A_{ii} = <e_i|A|e_i> in the standard basis. Then:

    d <| lambda    (Schur's inequality)

Conversely, for any d <| lambda, there exists a Hermitian matrix with eigenvalues lambda and diagonal d (Horn's result).

**Proof of Schur's inequality.** Write A = U diag(lambda) U*. Then:

    d_i = sum_j |U_{ij}|^2 lambda_j

The matrix (|U_{ij}|^2)_{ij} is doubly stochastic (rows and columns sum to 1 by unitarity). Therefore d = D lambda with D doubly stochastic, so d <| lambda.

**Physical meaning for density matrices.**

The diagonal of rho in any basis gives the measurement probabilities in that basis. The eigenvalues give the intrinsic probability distribution. Schur-Horn says:

    Measurement probabilities in any basis are majorized by the eigenvalues.

The eigenvalue distribution is the "most informative" -- it has the least entropy.

**Kostant's generalization.** The Schur-Horn theorem generalizes to arbitrary compact Lie groups: the image of a coadjoint orbit under projection to the Cartan subalgebra is a convex polytope (the Weyl group orbit convex hull). For U(n), this recovers Schur-Horn.

**Relation to quantum tomography.** Knowing the diagonal of rho in sufficiently many bases (an informationally complete set) determines rho uniquely. Schur-Horn constrains what diagonals are consistent with a given spectrum.


## 8. Entropy as Schur-Concave Function

**Definition.** A function f: R^n -> R is Schur-concave if x <| y implies f(x) >= f(y). (Mixing increases the value.)

**Theorem.** The von Neumann entropy S(rho) = -Tr(rho log rho) = -sum_i lambda_i log lambda_i is a Schur-concave function of the eigenvalue vector lambda.

**Proof.** S(lambda) = sum_i eta(lambda_i) where eta(x) = -x log x is a concave function. For any Schur-convex function g(lambda) = sum_i phi(lambda_i) with phi convex, x <| y implies g(x) <= g(y) (by Hardy-Littlewood-Polya). Since eta is concave, S = sum eta is Schur-concave.

**Consequences:**
- LOCC cannot increase entanglement entropy (by Nielsen + Schur-concavity)
- lambda^psi <| lambda^phi implies S(rho_A^psi) >= S(rho_A^phi)
- Maximum entropy state = maximally mixed = (1/n, ..., 1/n)
- Minimum entropy state = pure = (1, 0, ..., 0)

**Other Schur-concave functions on density matrices:**
- Renyi entropy: S_alpha(rho) = (1/(1-alpha)) log(sum_i lambda_i^alpha), alpha > 0
- min-entropy: S_inf(rho) = -log(lambda_max)
- All unitarily invariant concave functions of eigenvalues

**Schur-convex functions (opposite direction):**
- Purity: Tr(rho^2) = sum lambda_i^2
- All Renyi entropies with negative coefficient
- lambda_max (largest eigenvalue)


## 9. Spectral Decomposition and Quantum Channels

**Kraus representation.** A quantum channel E has Kraus operators {K_i}:

    E(rho) = sum_i K_i rho K_i*,    sum_i K_i* K_i = I

**Effect on spectrum.** In general, eigenvalues of E(rho) depend on both eigenvalues AND eigenvectors of rho. Exception: unital channels E(I) = I preserve the maximally mixed state.

**Schur's theorem for channels.** For a unital channel E:

    lambda(E(rho)) <| lambda(rho)

i.e., unital channels always increase the "mixedness" of the state.

**Proof.** A unital channel can be written as E(rho) = sum_i p_i U_i rho U_i* (mixture of unitaries, by Choi's theorem in finite dimensions for unital CPTP maps -- note this is exact only in dimensions 2 and 3; in general unital != mixed unitary, but majorization still holds via the doubly stochastic structure of the channel's action on eigenvalues).

**Spectral decomposition of the Choi matrix.** The Choi matrix J(E) = sum_{ij} E(|i><j|) tensor |i><j| is positive semidefinite iff E is completely positive. Its spectral decomposition:

    J(E) = sum_k mu_k |phi_k><phi_k|

gives Kraus operators via reshaping: K_k = sqrt(mu_k) * reshape(|phi_k>). The rank of J(E) is the minimum number of Kraus operators (Choi rank).


## 10. Key Identities and Computation

**Computing eigenvalues of 2x2 density matrix.**

    rho = [[a, b], [b*, 1-a]]

    lambda_+/- = (1 +/- sqrt((2a-1)^2 + 4|b|^2)) / 2

    Bloch vector: r = (2 Re(b), -2 Im(b), 2a-1)
    |r|^2 = (2a-1)^2 + 4|b|^2
    lambda_+/- = (1 +/- |r|) / 2

**Entropy of a qubit:**

    S(rho) = H_2((1+|r|)/2) = -((1+|r|)/2) log((1+|r|)/2) - ((1-|r|)/2) log((1-|r|)/2)

where H_2 is the binary entropy function.

**Eigenvalues of tensor products:**

    lambda(rho_A tensor rho_B) = {lambda_i^A * lambda_j^B}_{i,j}

sorted in decreasing order, these are the products of the individual eigenvalues.

**Eigenvalues of partial trace.** No closed form in general. For rho_AB = |psi><psi| (pure), the nonzero eigenvalues of Tr_B(|psi><psi|) equal the squared Schmidt coefficients.

**Perturbation theory for eigenvalues (non-degenerate).**

    lambda_i(rho + epsilon V) = lambda_i(rho) + epsilon <i|V|i> + epsilon^2 sum_{j != i} |<j|V|i>|^2 / (lambda_i - lambda_j) + O(epsilon^3)

This fails at degeneracies, where degenerate perturbation theory (diagonalize V in the degenerate subspace) is required.
