# Quantum Fisher Information and Information Geometry

## 1. Classical Fisher Information

**Setup.** A probability distribution p(x; theta) parameterized by theta. The Fisher information measures the sensitivity of the distribution to changes in theta.

**Definition.**

    F(theta) = E[(d/d theta log p(x; theta))^2]
             = sum_x (1/p(x;theta)) (dp(x;theta)/d theta)^2
             = -E[d^2/d theta^2 log p(x;theta)]

(The last equality holds under regularity conditions allowing exchange of differentiation and integration.)

**Score function.** s(x; theta) = d/d theta log p(x; theta). Then F(theta) = Var(s) (since E[s] = 0).

**Multi-parameter case.** For parameter vector theta = (theta_1, ..., theta_d):

    F_{ij}(theta) = E[(d/d theta_i log p) (d/d theta_j log p)]

This is the Fisher information matrix (FIM), a d x d positive semidefinite matrix.

**Cramer-Rao bound.**

    Cov(hat{theta}) >= F(theta)^{-1}

For any unbiased estimator hat{theta}. The variance of any single parameter estimate satisfies:

    Var(hat{theta}_i) >= [F^{-1}]_{ii} >= 1/F_{ii}

**Fisher-Rao metric.** F_{ij} defines a Riemannian metric on the parameter space (the statistical manifold). The geodesic distance is:

    d(theta_1, theta_2) = inf_{gamma: theta_1 -> theta_2} integral sqrt(sum_{ij} F_{ij} d theta_i/dt d theta_j/dt) dt

This is the unique metric (up to scaling) invariant under sufficient statistics (Chentsov's theorem, classical case).


## 2. Quantum Fisher Information (QFI)

**Setup.** A quantum state rho(theta) depending on parameter theta. We want the maximum classical Fisher information achievable by any measurement.

**Definition via Symmetric Logarithmic Derivative (SLD).**

The SLD L_theta is the Hermitian operator satisfying:

    d rho/d theta = (rho L_theta + L_theta rho) / 2

The QFI is:

    F_Q(theta) = Tr(rho L_theta^2) = Tr((d rho/d theta) L_theta)

**Explicit formula in eigenbasis.** Let rho = sum_i lambda_i |i><i|. Then:

    F_Q = 2 sum_{i,j: lambda_i + lambda_j > 0} (lambda_i - lambda_j)^2 / (lambda_i + lambda_j) * |<i|d rho/d theta|j>|^2 / (lambda_i - lambda_j)^2

Simplifying:

    F_Q = sum_{i,j: lambda_i + lambda_j > 0} 2/(lambda_i + lambda_j) * |<i|d rho/d theta|j>|^2 * ... 

**Correct explicit form.** Writing rho_dot = d rho/d theta:

    F_Q = 2 sum_{i,j: lambda_i + lambda_j > 0} |<i|rho_dot|j>|^2 / (lambda_i + lambda_j)

**Note on the sum.** Terms with lambda_i + lambda_j = 0 (both eigenvalues zero) are excluded. The matrix element <i|rho_dot|j> for such terms is automatically zero if rho_dot is consistent (the support of rho cannot grow under smooth perturbation).

**SLD explicit form.**

    L_theta = 2 sum_{i,j: lambda_i + lambda_j > 0} <i|rho_dot|j> / (lambda_i + lambda_j) * |i><j|


## 3. QFI for Pure States

For rho(theta) = |psi(theta)><psi(theta)|:

    F_Q = 4 (< psi_dot | psi_dot > - |< psi_dot | psi >|^2)

where |psi_dot> = d/d theta |psi(theta)>.

**Proof.** For pure states, rho_dot = |psi_dot><psi| + |psi><psi_dot|. The eigenvalues of rho are (1, 0, 0, ...). The SLD formula gives:

    F_Q = 2/(1+0) * ... + contributions from support

Working through: F_Q = 4 Var(H) where the "generator" H is defined by i d/d theta |psi> = H|psi> (up to phase).

**Alternative form.** If the parameter is encoded by a unitary: |psi(theta)> = e^{-i H theta} |psi_0>, then:

    F_Q = 4 Var_psi(H) = 4 (<psi|H^2|psi> - <psi|H|psi>^2)

This connects QFI directly to the variance of the generator.

**Saturation.** For pure states, QFI = 4 Var(H) is always achievable by a projective measurement in the eigenbasis of the SLD. The optimal measurement is the one that distinguishes |psi(theta)> from |psi(theta + d theta)> most efficiently.


## 4. Quantum Cramer-Rao Bound

**Theorem.** For any unbiased estimator hat{theta} based on n independent measurements on rho(theta):

    Var(hat{theta}) >= 1 / (n F_Q(theta))

**Saturation.** The bound is asymptotically achievable (for large n) by:
1. Measuring in the eigenbasis of the SLD L_theta
2. Using maximum likelihood estimation on the outcomes

**Multi-parameter quantum Cramer-Rao bound.** For theta = (theta_1, ..., theta_d):

    Cov(hat{theta}) >= F_Q^{-1}

where (F_Q)_{ij} = Re Tr(rho L_i L_j) / 2 + Re Tr(rho L_j L_i) / 2 (symmetrized).

**Non-commutativity obstruction.** Unlike classical statistics, [L_i, L_j] != 0 in general. This means the multi-parameter quantum CRB cannot always be saturated simultaneously. The Holevo bound provides a tighter (attainable) bound:

    Cov(hat{theta}) >= C_H(theta) >= F_Q^{-1}

where C_H is the Holevo Cramer-Rao bound, which accounts for measurement incompatibility.

**Condition for simultaneous saturation.** The multi-parameter QCR bound is saturable iff:

    Tr(rho [L_i, L_j]) = 0    for all i, j

i.e., the SLDs are "weakly commuting" on the state.


## 5. QFI as Metric on State Space

**Bures metric.** The Bures distance between density matrices:

    d_B(rho, sigma)^2 = 2(1 - sqrt(F(rho, sigma)))

where F(rho, sigma) = (Tr sqrt(sqrt(rho) sigma sqrt(rho)))^2 is the Uhlmann fidelity.

**Infinitesimal Bures metric.** For rho(theta) and rho(theta + d theta):

    d_B^2 = (1/4) F_Q d theta^2

So:

    ds_B^2 = (1/4) F_Q(theta) d theta^2

The QFI is (up to a factor of 4) the Bures metric on the space of density matrices.

**Multi-parameter version.**

    ds_B^2 = (1/4) sum_{ij} (F_Q)_{ij} d theta_i d theta_j

**For pure states (Fubini-Study metric).** The Bures metric reduces to the Fubini-Study metric:

    ds_{FS}^2 = <d psi|d psi> - |<psi|d psi>|^2 = (1/4) F_Q d theta^2

For a qubit |psi> = cos(theta/2)|0> + e^{i phi} sin(theta/2)|1>:

    ds_{FS}^2 = (1/4)(d theta^2 + sin^2 theta d phi^2)

This is the round metric on S^2 with radius 1/2 (the Bloch sphere).

**Monotonicity.** The Bures metric (equivalently QFI) is monotonically non-increasing under CPTP maps:

    F_Q(E(rho(theta))) <= F_Q(rho(theta))

for any quantum channel E. This is the quantum analogue of the data processing inequality.


## 6. QFI as Entanglement Witness

**Theorem (Pezze-Smerzi, Toth).** For an N-particle state rho and a linear observable H = sum_{i=1}^N h_i (sum of single-particle observables with ||h_i||_op <= 1):

    If rho is k-producible (no genuine (k+1)-partite entanglement), then:

    F_Q(rho, H) <= s k^2 + (N - sk)^2

where s = floor(N/k). In particular:

    F_Q > N  implies entanglement (not fully separable)
    F_Q > N k  implies genuine (k+1)-partite entanglement (rough bound)

**Shot noise limit vs Heisenberg limit.**

- Separable states (k=1): F_Q <= N (shot noise limit, SQL)
- General states: F_Q <= N^2 (Heisenberg limit)
- GHZ state achieves F_Q = N^2 for H = sum sigma_z

**Spin squeezing parameter.** xi^2 = N Var(J_perp) / <J>^2 < 1 implies entanglement and:

    F_Q >= N / xi^2

**Metrological usefulness.** A state rho is metrologically useful (beats SQL) iff there exists H such that F_Q(rho, H) > N. This is a sufficient condition for entanglement.


## 7. Wigner-Yanase Skew Information

**Definition.** For a density matrix rho and an observable K:

    I(rho, K) = -(1/2) Tr([sqrt(rho), K]^2)

**Expanded form:**

    I(rho, K) = Tr(rho K^2) - Tr(sqrt(rho) K sqrt(rho) K)

**Properties:**
- I(rho, K) >= 0
- I(rho, K) = 0 iff [rho, K] = 0 (K is a constant of the motion)
- I(|psi><psi|, K) = Var_psi(K) (reduces to variance for pure states)
- I(rho, K) <= Var_rho(K) (always less than or equal to variance)
- I(rho, K) is convex in rho: I(sum p_i rho_i, K) <= sum p_i I(rho_i, K)

**Relation to QFI.** For the unitary encoding rho(theta) = e^{-iKtheta} rho e^{iKtheta}:

    F_Q(rho, K) = 2 sum_{i,j: lambda_i + lambda_j > 0} (lambda_i - lambda_j)^2/(lambda_i + lambda_j) |<i|K|j>|^2

    I(rho, K) = sum_{i,j} (sqrt(lambda_i) - sqrt(lambda_j))^2 |<i|K|j>|^2

**Inequality chain:**

    I(rho, K) <= (1/4) F_Q(rho, K) <= Var_rho(K)

The first inequality follows from (sqrt(a) - sqrt(b))^2 <= (a-b)^2/(a+b) for a,b > 0 (AM-GM type). The second from (a-b)^2/(a+b) <= a + b - 2 sqrt(ab) ... actually:

Correct ordering: I(rho, K) <= (1/4) F_Q(rho, K) <= Var(K). Both equalities hold for pure states.

**Wigner-Yanase-Dyson information (generalization).**

    I_alpha(rho, K) = -(1/2) Tr([rho^alpha, K][rho^{1-alpha}, K])

for 0 < alpha < 1. The case alpha = 1/2 is the standard Wigner-Yanase skew information.


## 8. Relation to Coherence and Asymmetry

**Coherence as skew information.** With respect to a reference basis {|i>}, coherence of rho is related to:

    C_I(rho) = sum_k I(rho, |k><k|)

(sum of skew informations for the basis projectors).

**Asymmetry.** A state rho has asymmetry with respect to a group G acting as U(g) if rho != U(g) rho U(g)* for some g. The QFI quantifies asymmetry:

    For G = U(1) generated by K: F_Q(rho, K) = 0 iff rho is symmetric (commutes with K)

**Resource theory of asymmetry.** The QFI is an asymmetry monotone: non-increasing under G-covariant channels. States with higher QFI are more "asymmetric" (more useful as reference frames).

**Coherence-entanglement duality.** For a bipartite system, local coherence (in a product basis) and entanglement are related:

    C_l(rho_AB) >= sum_i C_l(rho_i)    (coherence can be distributed as entanglement)

where C_l is a coherence measure and the inequality captures the coherence-entanglement interconversion.


## 9. Fisher Information for Specific Quantum States

**Qubit (Bloch vector r, |r| <= 1).**

For rho = (I + r . sigma)/2 and generator H = n . sigma/2:

    F_Q = |n|^2 * (r . n_hat)^2 * 1/(1-|r|^2) + |n - (n.r_hat) r_hat|^2 * ... 

Simplified: for the unitary generated by H = sigma_z/2 acting on rho with Bloch vector (r sin theta_r cos phi_r, r sin theta_r sin phi_r, r cos theta_r):

    F_Q = (sin theta_r)^2 / (1 - r^2 cos^2 theta_r)  ... 

**Correct qubit formula.** For rho = (I + r.sigma)/2 and unitary exp(-i theta H), H = n.sigma/2:

    F_Q = (n x r)^2 / (1 - r^2) + (n . r_hat)^2

Wait -- let me give the clean result. For generator K (not halved):

    F_Q(rho, K) = Tr(rho_dot L) where rho_dot = -i[K, rho]

For qubit with rho = (I + r.sigma)/2 and K = (1/2) n . sigma:

    F_Q = |n|^2 - (n . r)^2/(1 - |r|^2)    ... 

**Correct formula (Braunstein-Caves).** For a qubit:

    F_Q = |dr/d theta|^2 + (r . dr/d theta)^2 / (1 - |r|^2)

For unitary rotation by angle theta about axis n: dr/d theta = n x r, so:

    F_Q = |n x r|^2 + (r . (n x r))^2/(1 - |r|^2) = |n x r|^2 (pure since r . (n x r) = 0)

    F_Q = |n x r|^2 / (1 - |r|^2 + (r . n_hat)^2 (1 - |r|^2)/(1-|r|^2))

For a pure state (|r| = 1): F_Q = |n x r|^2 = |n|^2 - (n.r_hat)^2 = |n|^2 sin^2(angle(n,r)).

For maximally mixed (|r| = 0): F_Q = 0 (no information extractable).

**N-qubit GHZ state.** |GHZ> = (|00...0> + |11...1>)/sqrt(2), generator H = (1/2) sum_i sigma_z^{(i)}:

    F_Q = N^2    (Heisenberg scaling)

**Thermal state.** rho = e^{-beta H} / Z, estimating beta:

    F_Q(beta) = Var_rho(H) = sum_i lambda_i E_i^2 - (sum_i lambda_i E_i)^2


## 10. Computational Methods

**Computing QFI numerically.** Given rho(theta) as a matrix:

1. Diagonalize rho = U D U*
2. Compute rho_dot = d rho/d theta (finite difference or analytic)
3. Transform: rho_dot_eig = U* rho_dot U
4. Compute: F_Q = sum_{i,j: d_i + d_j > 0} 2 |rho_dot_eig_{ij}|^2 / (d_i + d_j)

**Cost:** O(n^3) for diagonalization, O(n^2) for the sum. Dominated by diagonalization.

**SLD computation.** The SLD solves the Lyapunov equation:

    rho L + L rho = 2 rho_dot

This is a linear system in n^2 unknowns. In the eigenbasis of rho:

    L_{ij} = 2 (rho_dot)_{ij} / (lambda_i + lambda_j)

**Numerical stability.** When lambda_i + lambda_j is very small, the SLD element L_{ij} can be numerically unstable. Regularize by thresholding: if lambda_i + lambda_j < epsilon, set L_{ij} = 0 (these terms are in the kernel of rho and don't contribute to F_Q since the numerator also vanishes).

**Automatic differentiation.** For parameterized quantum circuits, rho_dot can be computed via:
- Parameter shift rule: d/d theta <O> = (1/2)(<O>_{theta+pi/2} - <O>_{theta-pi/2})
- This gives access to F_Q without explicit matrix differentiation
