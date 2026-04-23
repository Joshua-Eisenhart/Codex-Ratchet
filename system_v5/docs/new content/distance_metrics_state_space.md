# Distance Metrics on Quantum State Space

## Reference: Watrous "Theory of Quantum Information" Ch. 3, Wilde "QIT" Ch. 9, Fuchs & van de Graaf (1999)

---

## 1. Trace Distance

### 1.1 Definition

For Hermitian operators A, the trace norm is:

    ||A||_1 = Tr|A| = Tr(sqrt(A^dagger A)) = sum_i |lambda_i|

where lambda_i are eigenvalues.

The **trace distance** between density matrices rho and sigma:

    D(rho, sigma) = (1/2) ||rho - sigma||_1 = (1/2) sum_i |lambda_i|

where lambda_i are eigenvalues of (rho - sigma).

### 1.2 Properties

**(D1) Metric**: D satisfies non-negativity, symmetry, and triangle inequality. D(rho, sigma) = 0 iff rho = sigma.

**(D2) Bounded**: 0 <= D(rho, sigma) <= 1. D = 1 iff rho and sigma have orthogonal supports.

**(D3) Operational interpretation**: 

    D(rho, sigma) = max_{0 <= E <= I} Tr(E(rho - sigma))

This is the maximum probability of correctly distinguishing rho from sigma in a single measurement, minus 1/2, times 2. Specifically, the optimal success probability for distinguishing equal-prior rho vs sigma is:

    p_success = (1 + D(rho, sigma)) / 2

**(D4) Contractivity under CPTP**: For any quantum channel E:

    D(E(rho), E(sigma)) <= D(rho, sigma)

This is the data processing inequality for trace distance.

**Proof of contractivity**: D(rho, sigma) = max_{E} Tr(E(rho-sigma)). For E(rho), D(E(rho), E(sigma)) = max_{E'} Tr(E'(E(rho)-E(sigma))) = max_{E'} Tr(E'(E(rho-sigma))). But E' . E is a specific POVM element in the original optimization, so the max is at most D(rho, sigma). QED.

**(D5) Convexity**: D(sum p_i rho_i, sum p_i sigma_i) <= sum p_i D(rho_i, sigma_i).

**(D6) Unitary invariance**: D(U rho U^dagger, U sigma U^dagger) = D(rho, sigma).

### 1.3 For Qubits

If rho = (I + r . sigma)/2 and sigma = (I + s . sigma)/2:

    D(rho, sigma) = (1/2)|r - s|

(Half the Euclidean distance between Bloch vectors.) This is because rho - sigma = ((r-s) . sigma)/2 has eigenvalues +/- |r-s|/2.

### 1.4 Variational Characterization

    D(rho, sigma) = max_{P} Tr(P(rho - sigma))

where the max is over all projectors P (rank-unconstrained). The optimal P is the projector onto the positive part of (rho - sigma).

**Proof**: Write rho - sigma = Q_+ - Q_- (Jordan decomposition into positive and negative parts). Then Tr(P(rho-sigma)) = Tr(P Q_+) - Tr(P Q_-) <= Tr(Q_+) = (1/2)||rho - sigma||_1. Equality when P is the support projector of Q_+. QED.

---

## 2. Fidelity

### 2.1 Definition

For density matrices rho, sigma:

    F(rho, sigma) = (Tr sqrt(sqrt(rho) sigma sqrt(rho)))^2

Some references use F = Tr sqrt(sqrt(rho) sigma sqrt(rho)) (the square root of our F). We use the squared convention (Jozsa).

### 2.2 Equivalent Forms

**(a) Uhlmann's formula**: 

    F(rho, sigma) = (max_{|psi>, |phi>} |<psi|phi>|)^2

where the max is over all purifications |psi> of rho and |phi> of sigma.

**(b) For one pure state**: F(|psi><psi|, sigma) = <psi|sigma|psi>.

**(c) SDP form**: F(rho, sigma) = (max Re Tr(X))^2 subject to [[rho, X], [X^dagger, sigma]] >= 0.

### 2.3 Properties

**(F1) Symmetry**: F(rho, sigma) = F(sigma, rho). (Non-obvious from definition; follows from Uhlmann.)

**Proof of symmetry**: sqrt(rho) sigma sqrt(rho) and sigma^{1/2} rho sigma^{1/2} have the same nonzero eigenvalues (since AB and BA have the same nonzero eigenvalues for A = sqrt(rho) sqrt(sigma) and B = sqrt(sigma) sqrt(rho)). QED.

**(F2) Bounded**: 0 <= F <= 1. F = 1 iff rho = sigma. F = 0 iff rho and sigma have orthogonal supports.

**(F3) Multiplicativity**: F(rho_1 tensor rho_2, sigma_1 tensor sigma_2) = F(rho_1, sigma_1) F(rho_2, sigma_2).

**(F4) Monotonicity under CPTP**: F(E(rho), E(sigma)) >= F(rho, sigma). (Fidelity can only increase under channels — dual to trace distance decreasing.)

**(F5) Concavity**: F(rho, sum p_i sigma_i) >= sum p_i F(rho, sigma_i). (Concave in the second argument for fixed first argument.)

**(F6) Jozsa axioms**: F is the UNIQUE function satisfying:
1. F(rho, sigma) = F(sigma, rho)
2. F(U rho U^dagger, U sigma U^dagger) = F(rho, sigma)
3. F(|0><0|, rho) = <0|rho|0>
4. F(rho_1 tensor rho_2, sigma_1 tensor sigma_2) = F(rho_1, sigma_1) F(rho_2, sigma_2)

### 2.4 For Qubits

For rho = (I + r . sigma)/2, sigma = (I + s . sigma)/2:

    F = (1/2)(1 + r . s + sqrt((1 - |r|^2)(1 - |s|^2)))

For pure states (|r| = |s| = 1): F = (1 + r . s)/2 = cos^2(theta/2) where theta is the angle between Bloch vectors.

For one pure, one mixed (|r| = 1): F = (1 + r . s)/2 = <psi|sigma|psi>.

### 2.5 Fidelity and Bures Distance

    d_B(rho, sigma) = sqrt(2(1 - sqrt(F(rho, sigma))))

(Bures distance is a true metric on state space.)

Also: d_A(rho, sigma) = arccos(sqrt(F(rho, sigma))) (the angle/arc distance, also a metric).

---

## 3. Fuchs-van de Graaf Inequalities

### 3.1 The Relations

    1 - sqrt(F(rho, sigma)) <= D(rho, sigma) <= sqrt(1 - F(rho, sigma))

Both bounds are tight.

**Lower bound is tight**: For rho = |0><0|, sigma = cos^2(epsilon)|0><0| + sin^2(epsilon)|1><1| with small epsilon. F -> 1, D -> 0.

**Upper bound is tight**: For rho = |0><0|, sigma = |1><1|. F = 0, D = 1.

### 3.2 Proof of Lower Bound

D(rho, sigma) >= 1 - sqrt(F).

Use Uhlmann: sqrt(F) = max |<psi|phi>| over purifications. Choose optimal purifications |psi>, |phi>.

D(rho, sigma) = D(Tr_E |psi><psi|, Tr_E |phi><phi|)
             >= D(|psi><psi|, |phi><phi|) ... NO, wrong direction (partial trace can decrease D).

Actually: D(rho, sigma) >= 1 - F^{1/2} follows from:

For ANY measurement {E_x}, the classical distance sum_x |p_x - q_x|/2 <= D(rho, sigma) where p_x = Tr(E_x rho). And:

F(rho, sigma) <= F_classical(p, q) = (sum sqrt(p_x q_x))^2

So 1 - sqrt(F) <= 1 - sum sqrt(p_x q_x) <= (1/2) sum |p_x - q_x| <= D. (Using 1 - sum sqrt(p_x q_x) <= TV distance for classical distributions.)

### 3.3 Proof of Upper Bound

D(rho, sigma) <= sqrt(1 - F).

Choose purifications |psi>, |phi> with |<psi|phi>| = sqrt(F) (Uhlmann). Then:

D(rho, sigma) = D(Tr_E |psi><psi|, Tr_E |phi><phi|)
             <= D(|psi><psi|, |phi><phi|)  (partial trace is CPTP, contractivity)
             = sqrt(1 - |<psi|phi>|^2)     (trace distance for pure states)
             = sqrt(1 - F).  QED.

**Pure state trace distance**: D(|psi><psi|, |phi><phi|) = sqrt(1 - |<psi|phi>|^2).

Proof: |psi><psi| - |phi><phi| has eigenvalues +/- sqrt(1 - |<psi|phi>|^2) and 0 (in the 2D subspace spanned by |psi>, |phi>). So D = sqrt(1 - |<psi|phi>|^2).

---

## 4. Relative Entropy

### 4.1 Definition

    S(rho || sigma) = Tr(rho log rho - rho log sigma)

Defined when supp(rho) subset supp(sigma); otherwise S(rho || sigma) = +infinity.

### 4.2 Properties

**(R1) Non-negative**: S(rho || sigma) >= 0. Equality iff rho = sigma. (Klein's inequality.)

**Proof of Klein's inequality**: Uses the operator concavity of log.

Tr(rho log rho - rho log sigma) = Tr(rho(log rho - log sigma))

By the Golden-Thompson inequality and operator monotonicity, this is >= 0. The rigorous proof uses the spectral theorem:

Write rho = sum p_i |i><i|, sigma = sum q_j |j><j|. Then:

S(rho || sigma) = sum_i p_i log p_i - sum_{i,j} p_i |<i|j>|^2 log q_j
                = sum_i p_i log p_i - sum_i p_i sum_j |<i|j>|^2 log q_j
                = sum_i p_i (log p_i - log(sum_j |<i|j>|^2 q_j)) + sum_i p_i D_KL(|<i|.|>|^2 || something)

Actually the clean proof: define r_j = sum_i p_i |<i|j>|^2. Then r_j >= 0, sum r_j = 1. By log-sum inequality:

S(rho || sigma) >= sum_j r_j log(r_j / q_j) = S_classical(r || q) >= 0.

Equality iff r_j = q_j for all j AND |<i|j>|^2 = delta_{ij} (rho and sigma commute and are equal). QED.

**(R2) Not symmetric**: S(rho || sigma) =/= S(sigma || rho) in general.

**(R3) Not bounded**: S(rho || sigma) can be infinite.

**(R4) Monotonicity (data processing)**: For CPTP map E:

    S(rho || sigma) >= S(E(rho) || E(sigma))

**(R5) Joint convexity**: 

    S(sum p_i rho_i || sum p_i sigma_i) <= sum p_i S(rho_i || sigma_i)

**(R6) Relation to other quantities**:

    S(rho_A || I_A/d) = log d - S(rho_A)  (relative entropy to maximally mixed)
    I(A:B) = S(rho_{AB} || rho_A tensor rho_B)
    chi = S(rho || sum p_x rho_x) ... (Holevo information is a relative entropy)

### 4.3 Pinsker's Inequality

    D(rho, sigma)^2 <= (1/2) S(rho || sigma)

(Sometimes written as D^2 <= (1/(2 ln 2)) S for natural log convention.)

This connects trace distance and relative entropy. Relative entropy is always at least as strong as trace distance (up to a factor).

### 4.4 Operational Meaning

In quantum hypothesis testing (Stein's lemma): given n copies of either rho or sigma:

    -log beta_n / n -> S(rho || sigma) as n -> infinity

where beta_n is the type-II error probability at fixed type-I error rate. S(rho || sigma) is the optimal asymptotic rate of distinguishing rho from sigma.

---

## 5. Diamond Norm for Channels

### 5.1 Definition

For a superoperator (linear map on operators) Phi:

    ||Phi||_diamond = max_{rho on H tensor H} ||(Phi tensor id)(rho)||_1

where the max is over all bipartite states (using an ancilla of the same dimension).

### 5.2 Diamond Distance Between Channels

    D_diamond(E_1, E_2) = (1/2) ||E_1 - E_2||_diamond

### 5.3 Properties

- True metric on the space of channels.
- Operational: D_diamond = max probability of distinguishing E_1 from E_2 using a single use with arbitrary ancilla and input state.
- Multiplicative: ||Phi_1 tensor Phi_2||_diamond = ||Phi_1||_diamond ||Phi_2||_diamond.
- Computable via semidefinite programming (Watrous 2009).

### 5.4 Relation to Choi Matrix

    ||Phi||_diamond = max ||J(Phi) . (rho^T tensor I)||_1

where J(Phi) is the Choi matrix and the max is over states rho.

For qubit channels, the diamond norm can often be computed analytically.

### 5.5 SDP Formulation

    ||Phi||_diamond = max { Tr(J(Phi) W) : W >= 0, Tr_2(W) <= I }

(primal SDP). Dual:

    ||Phi||_diamond = min { ||Tr_1(Z)||_inf : Z >= J(Phi), Z >= 0 }

This allows efficient computation for any finite-dimensional channel.

---

## 6. Schatten Norms and Generalizations

### 6.1 Schatten p-Norms

    ||A||_p = (Tr(|A|^p))^{1/p} = (sum_i s_i^p)^{1/p}

where s_i are the singular values.

Special cases:
- p = 1: trace norm ||A||_1 = sum s_i (used in trace distance)
- p = 2: Hilbert-Schmidt norm ||A||_2 = sqrt(Tr(A^dagger A)) = sqrt(sum s_i^2)
- p = infinity: operator norm ||A||_inf = max s_i = largest singular value

### 6.2 Hilbert-Schmidt Distance

    D_{HS}(rho, sigma) = ||rho - sigma||_2 = sqrt(Tr((rho - sigma)^2))

Properties:
- Easy to compute (no diagonalization needed).
- NOT contractive under general CPTP maps (not operationally motivated).
- For qubits: D_{HS} = |r - s| / sqrt(2) (proportional to Euclidean Bloch distance).

### 6.3 Norm Inequalities

For d-dimensional operators:

    ||A||_inf <= ||A||_2 <= ||A||_1

    ||A||_1 <= sqrt(d) ||A||_2 <= d ||A||_inf

So trace distance and HS distance are related by:

    D_{HS} / sqrt(d) <= D_{trace} <= D_{HS}  (up to factors of 2 from different normalizations)

---

## 7. Quantum Fidelity: Computational Methods

### 7.1 For Commuting States

If [rho, sigma] = 0 (simultaneously diagonalizable):

    F(rho, sigma) = (sum_i sqrt(p_i q_i))^2

where p_i, q_i are eigenvalues in the common eigenbasis.

### 7.2 For One Pure State

    F(|psi><psi|, sigma) = <psi|sigma|psi>

(No square root needed.)

### 7.3 For Qubit States

Using the Bloch decomposition (formula from Section 2.4 above):

    sqrt(F) = sqrt((1 + r.s)/2 + sqrt((1-|r|^2)(1-|s|^2))/2)

Hmm actually let me state the correct qubit formula.

For rho = (I + r.sigma)/2, sigma = (I + s.sigma)/2:

    F = Tr(rho sigma) + 2 sqrt(det(rho) det(sigma)) + ... 

Actually the correct formula (derivable by direct computation of the 2x2 case):

    sqrt(F) = Tr sqrt(sqrt(rho) sigma sqrt(rho))

For 2x2 matrices with eigenvalues (lambda_+, lambda_-) of sqrt(rho) sigma sqrt(rho):

    sqrt(F) = sqrt(lambda_+) + sqrt(lambda_-)

Using the identity for 2x2 matrices: for a positive matrix M with eigenvalues mu_1, mu_2:
Tr(sqrt(M)) = sqrt(mu_1) + sqrt(mu_2) = sqrt(Tr(M) + 2 sqrt(det(M))).

So: sqrt(F) = sqrt(Tr(rho sigma) + 2 sqrt(det(rho) det(sigma)))

For qubits:
    Tr(rho sigma) = (1 + r.s)/2
    det(rho) = (1 - |r|^2)/4
    det(sigma) = (1 - |s|^2)/4

Therefore:
    F = (1 + r.s)/2 + sqrt((1 - |r|^2)(1 - |s|^2))/2

    = (1 + r.s + sqrt((1 - |r|^2)(1 - |s|^2))) / 2

This is exact and is the correct qubit fidelity formula.

### 7.4 Numerical Computation (General d)

For general d-dimensional states, compute:
1. R = sqrt(rho) (matrix square root via eigendecomposition)
2. M = R sigma R (matrix product)
3. Eigenvalues {mu_i} of M (all non-negative since M is PSD)
4. F = (sum sqrt(mu_i))^2

Complexity: O(d^3) for eigendecomposition.

---

## 8. Metric Hierarchy and Relations

### 8.1 Summary of Distances

From weakest to strongest distinguishability:

    Hilbert-Schmidt <= Trace distance <= Bures <= Angular (Fubini-Study)

More precisely, the relations:

    d_B^2 / 2 <= D <= d_B sqrt(1 - d_B^2/4)  (Bures vs trace)
    1 - sqrt(F) <= D <= sqrt(1-F)              (Fuchs-van de Graaf)
    d_B = sqrt(2 - 2 sqrt(F))                  (Bures = f(fidelity))
    d_A = arccos(sqrt(F))                       (angular = f(fidelity))

### 8.2 Relative Entropy vs Metric Distances

S(rho || sigma) is NOT a metric (asymmetric, no triangle inequality) but:

    D^2 <= S/2  (Pinsker)
    D <= sqrt(S/2)  (Pinsker, rearranged)
    S <= -2 log(1-D)  (reverse Pinsker, sometimes)

### 8.3 Contractivity Summary

All operationally motivated distances are contractive under CPTP:
- D(E(rho), E(sigma)) <= D(rho, sigma)  (trace)
- F(E(rho), E(sigma)) >= F(rho, sigma)  (fidelity increases)
- d_B(E(rho), E(sigma)) <= d_B(rho, sigma)  (Bures)
- S(E(rho) || E(sigma)) <= S(rho || sigma)  (relative entropy)

Hilbert-Schmidt distance is NOT contractive in general (counterexample exists for d >= 3).

---

## 9. Operational Distinctions

### 9.1 Single-Shot vs Asymptotic

- **Trace distance**: Single-shot optimal discrimination probability.
- **Fidelity**: Single-shot state transfer quality (worst-case over inputs for channels).
- **Relative entropy**: Asymptotic discrimination rate (Stein's lemma).
- **Diamond norm**: Single-shot channel discrimination with ancilla.

### 9.2 When to Use Which

- **Trace distance**: When you need operational discrimination probability.
- **Fidelity**: When you need state preparation quality or gate error.
- **Relative entropy**: When you need asymptotic rates (capacities, thermodynamics).
- **Diamond norm**: When comparing quantum channels (process tomography, error bounds).
- **Bures**: When you need a Riemannian geometry on state space (geodesics, curvature, volumes).
