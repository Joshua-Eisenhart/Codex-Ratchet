# Compression Mathematics and the Density Matrix

## Reference Note
This document covers the mathematical structures connecting data compression, dimensionality reduction, and density matrix formalism. Every section provides explicit formulas and identifies where the density matrix structure is exact versus approximate.

---

## 0. The Central Thesis

Compression = low-rank approximation of a density matrix. Every compression scheme can be written as:

    rho -> rho_k = sum_{i=1}^{k} lambda_i |e_i><e_i|    (keep top-k eigenstates)

The information retained is Tr(rho_k) = sum_{i=1}^{k} lambda_i. The information lost is 1 - Tr(rho_k) = sum_{i=k+1}^{d} lambda_i. The optimal k-rank approximation (Eckart-Young theorem) is the spectral truncation. All of rate-distortion theory, PCA, tensor networks, and compressed sensing are variations on this theme.

---

## 1. Classical Rate-Distortion Theory

### 1.1 Shannon's Rate-Distortion Function

For a source X with distribution p(x) and distortion measure d(x, x_hat):

    R(D) = min_{p(x_hat|x): E[d(X, X_hat)] <= D} I(X; X_hat)

R(D) gives the minimum bit rate needed to represent X with average distortion at most D.

**Key properties**:
- R(0) = H(X) for discrete sources (lossless requires full entropy)
- R(D_max) = 0 (enough distortion allows zero rate)
- R(D) is convex, non-increasing in D
- The minimizing p*(x_hat|x) defines the optimal encoding channel

### 1.2 Rate-Distortion as Density Matrix Optimization

Embed the source as a diagonal density matrix rho_X = diag(p(x_1), ..., p(x_d)). The encoding channel p(x_hat|x) is a CPTP map E. Then:

    R(D) = min_{E: CPTP, Tr(Delta * E(rho)) <= D} I(rho_X, E)

where I(rho, E) = S(E(rho)) - sum_x p(x) S(E(|x><x|)) is the Holevo information of the ensemble, and Delta is the distortion observable.

**Gaussian source** (X ~ N(0, sigma^2), squared-error distortion):

    R(D) = (1/2) log(sigma^2 / D)    for 0 < D < sigma^2

The optimal encoding: project onto the top eigenspace of the covariance matrix until the residual variance equals D. For a d-dimensional Gaussian source with covariance Sigma = U diag(lambda_1, ..., lambda_d) U^T:

    R(D) = sum_{i=1}^{d} max(0, (1/2) log(lambda_i / theta))

where theta is chosen so that sum_{i=1}^{d} min(lambda_i, theta) = D. This is the reverse water-filling solution. In density matrix terms: lambda_i / Tr(Sigma) are the eigenvalues of rho = Sigma / Tr(Sigma). The water-filling level theta / Tr(Sigma) determines which eigenstates to truncate.

### 1.3 Rate-Distortion for Parametric Families

For an exponential family p(x|theta) = exp(theta^T t(x) - A(theta)):

    R(D) = D_KL(p(x|theta*) || p(x|theta_0)) + O(D^2)

where theta* is the closest parameter (in KL divergence) with distortion D. The Fisher information matrix I(theta) determines the local rate-distortion tradeoff:

    R(D) ~ (1/2) delta_theta^T I(theta) delta_theta

This is the quantum Fisher information for diagonal density matrices.

---

## 2. Quantum Rate-Distortion Theory

### 2.1 The Quantum Rate-Distortion Function

For a quantum source rho^{tensor n} (n copies of density matrix rho in C^d):

    R_q(D) = min_{E: CPTP, E_d(rho, E(rho)) <= D} I_c(rho, E)

where:
- E is a CPTP map (the compression channel)
- E_d(rho, sigma) is a distortion measure (e.g., 1 - F(rho, sigma) where F is fidelity)
- I_c(rho, E) = S(E(rho)) - S(rho, E) is the coherent information

For the entanglement fidelity distortion:

    D = 1 - F_e(rho, E) = 1 - <psi| (id tensor E)(|psi><psi|) |psi>

where |psi> is a purification of rho.

### 2.2 Key Results

**Devetak-Berger (2005)**: The quantum rate-distortion function for i.i.d. quantum sources is:

    R_q(D) = min_{E: F_e(rho,E) >= 1-D} [S(rho) - S(rho, E)]

where S(rho, E) = S((id tensor E)(|psi><psi|)) is the entropy exchange.

**Datta-Renes-Renner-Wilde (2013)**: One-shot quantum rate-distortion:

    R_q^{(1)}(D, epsilon) = min_{E: F_e >= 1-D-epsilon} D_H^epsilon(rho_AE || rho_A tensor rho_E)

where D_H^epsilon is the epsilon-smooth hypothesis testing divergence.

**Comparison with classical**: For diagonal rho (classical source embedded in quantum):

    R_q(D) = R_classical(D)

But for genuine quantum sources (off-diagonal coherences):

    R_q(D) <= R_classical(D)

Quantum compression can be strictly more efficient because coherences enable Schumacher compression (projecting onto the typical subspace of the eigenvalue distribution of rho^{tensor n}).

### 2.3 Schumacher Compression

For n copies of a quantum source rho with eigendecomposition rho = sum lambda_i |i><i|:

    rho^{tensor n} = sum_{i_1,...,i_n} lambda_{i_1} ... lambda_{i_n} |i_1 ... i_n><i_1 ... i_n|

The typical subspace T_epsilon^n consists of basis states where:

    |-(1/n) sum_k log lambda_{i_k} - S(rho)| < epsilon

By the AEP (asymptotic equipartition property), dim(T_epsilon^n) ~ 2^{n S(rho)} and Tr(P_T rho^{tensor n}) -> 1 as n -> infinity.

**Compression protocol**:
1. Project rho^{tensor n} onto T_epsilon^n (this succeeds with probability -> 1)
2. Encode the projected state in nS(rho) qubits
3. Decode by embedding back into the full Hilbert space

**Rate**: S(rho) qubits per source copy. Compare with Shannon: H(X) bits per source symbol. Since S(rho) <= log d with equality iff rho = I/d, quantum compression can achieve rates below log d.

**Density matrix view**: Compression = spectral truncation of rho^{tensor n}. Keep the eigenvalues that contribute to the typical set, discard the atypical tails. This is PCA on the joint eigenvalue distribution.

---

## 3. PCA as Spectral Truncation of Density Matrices

### 3.1 Classical PCA

Given data matrix X in R^{n x d} (n samples, d features), centered (mean zero). The sample covariance:

    Sigma = (1/n) X^T X

has eigendecomposition Sigma = V Lambda V^T where Lambda = diag(lambda_1, ..., lambda_d), lambda_1 >= ... >= lambda_d >= 0.

**PCA-k**: Project onto the top-k eigenvectors:

    X_k = X V_k V_k^T

where V_k = [v_1, ..., v_k] are the top-k eigenvectors. The reconstruction error:

    ||X - X_k||_F^2 / ||X||_F^2 = sum_{i=k+1}^{d} lambda_i / sum_{i=1}^{d} lambda_i = 1 - sum_{i=1}^{k} lambda_i / Tr(Sigma)

### 3.2 PCA as Density Matrix Truncation

Define the normalized covariance density matrix:

    rho = Sigma / Tr(Sigma)

with eigenvalues p_i = lambda_i / Tr(Sigma) (probability distribution). PCA-k is:

    rho -> rho_k = sum_{i=1}^{k} p_i |v_i><v_i| / (sum_{i=1}^{k} p_i)

This is a rank-k density matrix. The compression corresponds to:

**Rate**: log k (bits to specify which of k components)
**Distortion**: 1 - sum_{i=1}^{k} p_i (fraction of variance lost)
**Fidelity**: F = sum_{i=1}^{k} p_i (fraction of variance retained)

The von Neumann entropy S(rho) = -sum p_i log p_i measures the effective dimensionality:

    S(rho) = 0:     rank-1, all variance in one direction (pure state, PCA-1 is lossless)
    S(rho) = log d:  all eigenvalues equal, no compression possible (maximally mixed)

### 3.3 Optimal Rank Selection via Entropy

**The scree criterion**: Choose k where the eigenvalue spectrum has an "elbow." In density matrix terms: choose k where the entropy of the truncated distribution changes behavior.

**Minimum description length (MDL)**: The optimal k minimizes:

    L(k) = n * D_KL(rho || rho_k) + (k/2) log n

where D_KL(rho || rho_k) = sum_{i=k+1}^{d} p_i log(p_i / (sum_{j>k} p_j / (d-k))) is the relative entropy from the full state to the k-rank approximation. The first term is distortion (fitting), the second is model complexity (coding).

### 3.4 Kernel PCA as Quantum State Truncation

For kernel PCA with kernel matrix K (n x n), define:

    rho_K = K / Tr(K)

Kernel PCA-k keeps the top-k eigenvalues/vectors of rho_K. This is density matrix truncation in feature space. The feature map phi: x -> phi(x) in Hilbert space H gives:

    rho = (1/n) sum_{i=1}^{n} |phi(x_i)><phi(x_i)|

Truncation to rank k projects each |phi(x_i)> onto the k-dimensional subspace spanned by the top eigenvectors of rho. The reconstruction error in feature space is:

    E = (1/n) sum_i ||phi(x_i) - P_k phi(x_i)||^2 = Tr(rho (I - P_k)) = sum_{i>k} p_i

exactly the discarded eigenvalue mass.

---

## 4. Quantum PCA

### 4.1 The Quantum PCA Algorithm (Lloyd, Mohseni, Rebentrost 2014)

**Problem**: Given many copies of an unknown density matrix rho, estimate its principal eigenvectors efficiently.

**Classical approach**: Measure rho in some basis, accumulate statistics, diagonalize (requires O(d^2) measurements for a d-dimensional system, plus O(d^3) classical computation for diagonalization).

**Quantum PCA**: Uses the quantum phase estimation algorithm to directly extract eigenvalues and eigenvectors of rho without full tomography.

**Protocol**:
1. Prepare two registers: the target state rho and an ancilla in |+> = (|0> + |1>)/sqrt(2)
2. Apply the controlled-swap (Fredkin) gate: C-SWAP|0>|psi>|phi> = |0>|psi>|phi>, C-SWAP|1>|psi>|phi> = |1>|phi>|psi>
3. Measure the ancilla in the X basis
4. The probability of outcome |+> is (1 + Tr(rho^2))/2

By iterating with multiple copies and quantum phase estimation:

    e^{-i rho t} |psi_j> = e^{-i lambda_j t} |psi_j>

where |psi_j> is an eigenvector of rho with eigenvalue lambda_j. Phase estimation extracts lambda_j to precision epsilon using O(1/epsilon) copies of rho.

**Exponential speedup**: For a d-dimensional density matrix, quantum PCA requires O(d * polylog(d) / epsilon) copies to extract the top eigenvalue/vector, versus O(d^2 / epsilon^2) for classical tomography.

### 4.2 Quantum Singular Value Transformation (QSVT)

A more general framework (Gilyen et al. 2019) that subsumes quantum PCA:

Given access to a block-encoding of a matrix A (i.e., a unitary U such that <0|U|0> = A/alpha for some normalization alpha), QSVT applies an arbitrary polynomial transformation to the singular values:

    A = sum_i sigma_i |u_i><v_i|  ->  f(A) = sum_i f(sigma_i) |u_i><v_i|

For density matrix compression: choose f to be a threshold function:

    f(sigma) = sigma    if sigma > threshold
    f(sigma) = 0        if sigma <= threshold

This implements spectral truncation (PCA) as a quantum circuit. The circuit depth is O(deg(f) * polylog(d)) where deg(f) is the polynomial degree needed to approximate the threshold function.

### 4.3 Density Matrix Exponentiation

Given n copies of rho, implement the unitary e^{-i rho t}:

**Technique** (Lloyd 2014): Use the identity:

    e^{-i rho Delta_t} approx SWAP^{rho Delta_t}

For small Delta_t, the partial swap with an ancilla copy of rho approximates the desired unitary. Specifically:

    Tr_ancilla(SWAP * (sigma tensor rho) * SWAP^dagger) = rho sigma rho + O(Delta_t^2)

By repeating t/Delta_t times with fresh copies of rho:

    sigma -> e^{-i rho t} sigma e^{i rho t} + O(t^2 Delta_t)

**Cost**: O(t^2 / epsilon) copies of rho for error epsilon. This enables simulation of rho as a Hamiltonian -- the density matrix itself generates unitary evolution.

---

## 5. Tensor Network Compression

### 5.1 Matrix Product States (MPS) / Tensor Trains

An n-site quantum state |psi> in (C^d)^{tensor n} has d^n amplitudes:

    |psi> = sum_{i_1,...,i_n} c_{i_1...i_n} |i_1 ... i_n>

The MPS decomposition:

    c_{i_1...i_n} = A_1^{i_1} A_2^{i_2} ... A_n^{i_n}

where A_k^{i_k} is a D_k x D_{k+1} matrix. The bond dimension D = max_k D_k controls the compression:

    Full state:     D = d^{n/2}    (no compression)
    Product state:  D = 1          (maximum compression, no entanglement)
    Area law state: D = poly(n)    (efficient compression)

### 5.2 Entanglement and Compression

For a bipartition of the n sites into A = {1,...,k} and B = {k+1,...,n}, the reduced density matrix:

    rho_A = Tr_B(|psi><psi|)

has rank at most D_k (the bond dimension at the cut). The entanglement entropy:

    S(rho_A) = -Tr(rho_A log rho_A) <= log D_k

**Compression rate**: An MPS with bond dimension D stores O(n d D^2) parameters versus d^n for the full state. The compression ratio is:

    R = n d D^2 / d^n ~ n D^2 / d^{n-1}

For D = poly(n), the compression is exponential. The entanglement entropy S ~ log D ~ log(poly(n)) = O(log n) -- these are states with logarithmic entanglement (area law in 1D).

### 5.3 Density Matrix Renormalization Group (DMRG)

DMRG (White 1992) finds the optimal MPS approximation to a ground state by iteratively optimizing each tensor A_k.

**Density matrix truncation at each step**: At site k, the system is bipartitioned into (1,...,k) and (k+1,...,n). The reduced density matrix rho_left = Tr_right(|psi><psi|) has eigenvalues lambda_i. DMRG keeps the top D eigenvalues and truncates:

    rho_left -> rho_left^{(D)} = sum_{i=1}^{D} lambda_i |i><i|

The truncation error is:

    epsilon = 1 - sum_{i=1}^{D} lambda_i = Tr(rho_left) - Tr(rho_left^{(D)})

This IS the infidelity of the compressed state. DMRG minimizes total truncation error across all cuts -- it finds the optimal spectral truncation of all reduced density matrices simultaneously.

### 5.4 MERA (Multi-scale Entanglement Renormalization Ansatz)

MERA (Vidal 2007) is a hierarchical tensor network with layers of:
- **Disentanglers**: Unitary gates that remove short-range entanglement
- **Isometries**: Coarse-graining maps that reduce the number of sites

Each layer compresses by removing entanglement at one length scale. The density matrix at scale s:

    rho^{(s)} = E_s(rho^{(s-1)})

where E_s is a CPTP map (disentangle + coarse-grain). The total compression:

    rho^{(0)} (fine) -> rho^{(1)} -> ... -> rho^{(S)} (coarse)

is a composition of CPTP maps = a CPTP map. The entanglement entropy at scale s:

    S(rho_A^{(s)}) ~ (Area of A) * log(chi) / s

where chi is the bond dimension and s is the scale. MERA can represent states with S ~ log(L) (critical systems), unlike MPS which requires S ~ const (gapped systems).

### 5.5 Tensor Network Compression of Classical Data

**Tensor train decomposition for data**: A dataset of n features, each taking d values, defines a tensor of size d^n. The tensor train (MPS) decomposition compresses this to O(n d D^2) parameters.

**Application to machine learning**: The weight tensor of a fully connected layer W in R^{d_out x d_in} can be reshaped and decomposed as a tensor train. If the effective rank (entanglement) is low, the compressed network has far fewer parameters.

**Density matrix of a tensor network**: The normalized tensor T / ||T||_F defines a probability distribution (amplitude squared) over the indices. The corresponding density matrix:

    rho_TN = T T^dagger / Tr(T T^dagger)

The von Neumann entropy of the bipartitioned rho_TN gives the "entanglement" of the data tensor -- how compressible the data is across that bipartition.

---

## 6. Random Matrix Theory

### 6.1 Marchenko-Pastur Law

For a random matrix X in R^{n x d} with i.i.d. entries X_{ij} ~ N(0, 1/n), the empirical spectral distribution of Sigma = X^T X converges (as n, d -> infinity with d/n -> gamma) to the Marchenko-Pastur distribution:

    f_MP(lambda) = (1/(2 pi sigma^2 gamma)) * sqrt((lambda_+ - lambda)(lambda - lambda_-)) / lambda

for lambda in [lambda_-, lambda_+], where:

    lambda_+/- = sigma^2 (1 +/- sqrt(gamma))^2

**Density matrix interpretation**: The normalized sample covariance rho = Sigma / Tr(Sigma) has eigenvalue distribution converging to:

    rho_MP(p) = f_MP(p * Tr(Sigma)) * Tr(Sigma)

The von Neumann entropy of a Marchenko-Pastur density matrix:

    S(rho_MP) = integral rho_MP(p) log(1/p) dp

depends only on the aspect ratio gamma = d/n. For gamma -> 0 (many samples, few features): S -> 0 (one dominant eigenvalue). For gamma -> infinity (few samples, many features): S -> log d (nearly uniform eigenvalues, maximally mixed).

### 6.2 Signal Detection: Spiked Covariance Model

The spiked covariance model (Johnstone 2001):

    Sigma = I + sum_{k=1}^{r} theta_k u_k u_k^T

where theta_k > 0 are the spike strengths and u_k are the spike directions. The sample covariance eigenvalues exhibit a phase transition:

**BBP transition** (Baik, Ben Arous, Peche 2005): For a single spike theta:

    theta > sqrt(gamma):  top eigenvalue separates from MP bulk (spike detectable)
    theta < sqrt(gamma):  top eigenvalue merges with MP bulk (spike undetectable)

**Density matrix interpretation**: The signal density matrix rho_signal = sum theta_k |u_k><u_k| / (d + sum theta_k) has rank r. The noise density matrix rho_noise = I/(d + sum theta_k) is near-maximally-mixed. The total rho = rho_signal + rho_noise is a signal+noise mixture.

The BBP transition says: the signal is detectable (the rank-r structure can be recovered by PCA) iff the signal-to-noise ratio exceeds sqrt(gamma). Below this threshold, the density matrix is indistinguishable from a maximally mixed state. This is the quantum analog: you cannot distinguish rho from I/d when the purity excess is too small.

### 6.3 Free Probability and Density Matrix Addition

When two density matrices rho_A, rho_B are "free" (algebraically independent in the sense of Voiculescu), the eigenvalue distribution of rho_A + rho_B is determined by the free convolution:

    mu_{rho_A + rho_B} = mu_{rho_A} boxplus mu_{rho_B}

The free convolution is computed via the R-transform:

    R_{rho_A + rho_B}(z) = R_{rho_A}(z) + R_{rho_B}(z)

For the product rho_A * rho_B (relevant for compression via sequential channels):

    mu_{rho_A rho_B} = mu_{rho_A} boxtimes mu_{rho_B}

computed via the S-transform:

    S_{rho_A rho_B}(z) = S_{rho_A}(z) * S_{rho_B}(z)

**Application to compression**: A compression channel E composed with a noise channel N gives:

    rho -> N(E(rho))

The eigenvalue distribution of the output is the free multiplicative convolution of the compression spectrum with the noise spectrum. The distortion is determined by the overlap of these free-convoluted spectra.

### 6.4 Wishart Ensembles and Random Density Matrices

A random density matrix drawn from the Wishart ensemble:

    rho = W / Tr(W),    W = X X^dagger,    X in C^{d x n}

with X having i.i.d. complex Gaussian entries. The eigenvalue distribution of rho is the (normalized) Marchenko-Pastur law.

**Purity**: E[Tr(rho^2)] = (d + n) / (dn + 1). For n >> d: Tr(rho^2) ~ 1/d (near-maximally-mixed). For n = 1: Tr(rho^2) = 1 (pure state).

**Page's theorem** (Page 1993): For a random pure state |psi> in C^{d_A} tensor C^{d_B} with d_A <= d_B:

    E[S(rho_A)] = sum_{k=d_B+1}^{d_A d_B} 1/k - (d_A - 1)/(2 d_B) ~ log d_A - d_A/(2 d_B)

Random states are nearly maximally entangled. Compression of a random state requires nearly log(d_A) qubits -- random states are incompressible (high entropy).

---

## 7. Matrix Completion and Low-Rank Recovery

### 7.1 The Matrix Completion Problem

**Given**: Partial observations {M_{ij} : (i,j) in Omega} of a matrix M in R^{d_1 x d_2}.
**Goal**: Recover M assuming it has low rank r.

For density matrices: M = rho, d_1 = d_2 = d, rank(rho) = r, with additional constraints rho >= 0, Tr(rho) = 1.

### 7.2 Nuclear Norm Minimization

    min ||X||_*    subject to    X_{ij} = M_{ij} for (i,j) in Omega

where ||X||_* = sum sigma_i(X) is the nuclear norm (sum of singular values). For density matrices, ||rho||_* = Tr(rho) = 1 (constant), so the relaxation becomes:

    min Tr(X)    subject to    X >= 0, X_{ij} = M_{ij} for (i,j) in Omega

This is a semidefinite program.

**Recovery guarantee** (Candes & Recht 2009, Gross 2011): If Omega is chosen uniformly at random with |Omega| >= C r d polylog(d), and M satisfies the incoherence condition:

    max_i ||P_U e_i||^2 <= mu r / d

where P_U is the projection onto the column space of M and mu is the incoherence parameter, then M is recovered exactly with high probability.

### 7.3 Quantum State Tomography as Matrix Completion

**Standard tomography**: Measure rho in d^2 linearly independent bases -> reconstruct rho from d^2 - 1 real parameters. Cost: O(d^2) measurements.

**Compressed tomography** (Gross et al. 2010): If rho has rank r, measure in O(r d polylog d) random Pauli bases and solve the SDP:

    min Tr(X)    subject to    X >= 0, Tr(P_i X) = p_i for measured Pauli operators P_i

Recovery is exact with high probability. This is matrix completion for density matrices.

**Measurement design**: Random Pauli measurements {P_i = sigma_{a1} tensor sigma_{a2} tensor ... tensor sigma_{an}} satisfy the RIP (restricted isometry property) for rank-r matrices with high probability when the number of measurements exceeds O(r d log^6 d).

### 7.4 Projected Gradient Descent for Density Matrices

Iterative algorithm for low-rank density matrix recovery:

    X_{t+1} = P_{rho}(X_t - eta nabla L(X_t))

where L(X) = sum_{(i,j) in Omega} (X_{ij} - M_{ij})^2 is the squared error, eta is the step size, and P_{rho} projects onto the set of valid density matrices:

    P_{rho}(X) = argmin_{Y >= 0, Tr(Y) = 1} ||Y - X||_F

The projection P_{rho} is computed by:
1. Symmetrize: X -> (X + X^T)/2
2. Eigendecompose: X = V Lambda V^T
3. Project eigenvalues onto the probability simplex: lambda -> lambda_+ / ||lambda_+||_1
4. Reconstruct: rho = V diag(lambda_projected) V^T

Convergence: O(d^2 / epsilon) iterations for epsilon accuracy when the rank is known.

---

## 8. Compressed Sensing for Density Matrices

### 8.1 Standard Compressed Sensing Review

For a sparse signal x in R^d with ||x||_0 = s (s-sparse):

    min ||x||_1    subject to    Ax = y

where A in R^{m x d} is the measurement matrix, y = Ax is the measurement vector. Recovery requires m >= C s log(d/s) measurements.

### 8.2 Low-Rank Matrix Compressed Sensing

For a rank-r matrix M in R^{d1 x d2}:

    min ||X||_*    subject to    A(X) = y

where A: R^{d1 x d2} -> R^m is a linear measurement map. Recovery requires m >= C r (d1 + d2) measurements.

**Connection to sparsity**: Rank is to matrices as sparsity is to vectors. Nuclear norm is to rank as l1-norm is to l0-norm. The matrix compressed sensing problem IS the vector compressed sensing problem lifted to matrices.

### 8.3 Density Matrix Compressed Sensing

**Measurement model**: m random measurements of a rank-r density matrix rho in C^{d x d}:

    y_i = Tr(A_i rho) + noise_i,    i = 1, ..., m

where A_i are measurement operators (Hermitian, trace-1 if they correspond to POVM elements).

**Recovery via SDP**:

    min Tr(X)    subject to    X >= 0, |Tr(A_i X) - y_i| <= epsilon for all i

**RIP for density matrices** (Gross et al. 2010, Liu 2011): Random Pauli measurements satisfy the rank-r RIP:

    (1-delta) ||rho||_F^2 <= (1/m) sum_i (Tr(A_i rho))^2 <= (1+delta) ||rho||_F^2

for all rank-r density matrices rho, when m >= C r d log^2(d) / delta^2.

**Information-theoretic lower bound**: A rank-r density matrix in C^{d x d} has 2rd - r^2 - 1 real parameters (accounting for Hermiticity, positive semidefiniteness, and trace-1). So m >= 2rd - r^2 - 1 measurements are necessary.

**Gap**: The achievable m ~ r d polylog(d) nearly matches the lower bound 2rd - r^2 up to log factors.

### 8.4 Adaptive Compressed Sensing

**Classical adaptive**: Measure, update, choose next measurement to maximize information gain. The information gain of measurement A on state rho is:

    IG(A, rho) = S(rho) - E_{outcome}[S(rho | outcome)]

For projective measurements A = |a><a|:

    IG = H_2(<a|rho|a>) - 0 = -<a|rho|a> log <a|rho|a> - (1-<a|rho|a>) log(1-<a|rho|a>)

The optimal adaptive strategy measures in the eigenbasis of the current estimate rho_hat, concentrating measurements where the eigenvalues are most uncertain.

**Connection to quantum state tomography**: Adaptive compressed sensing for density matrices IS adaptive quantum state tomography. The optimal measurement strategy minimizes the total number of measurements to achieve a target fidelity F(rho_hat, rho) >= 1 - epsilon.

---

## 9. Information-Geometric Compression

### 9.1 The Information Geometry of Density Matrices

The space of d-dimensional density matrices D_d is a (d^2 - 1)-dimensional manifold. The natural metric is the Bures metric (quantum Fisher information metric):

    ds_Bures^2 = (1/2) Tr(d rho * L)

where L is the symmetric logarithmic derivative: d rho = (rho L + L rho)/2.

For diagonal density matrices (probability simplex), the Bures metric reduces to the Fisher-Rao metric:

    ds_FR^2 = sum_i (dp_i)^2 / (4 p_i)

### 9.2 Geodesic Compression

The shortest path (geodesic) from rho to a rank-k approximation rho_k on the density matrix manifold:

    rho(t) = ((1-t) sqrt(rho) + t sqrt(rho_k))^2 / Tr(...)    (Bures geodesic, schematic)

The Bures distance from rho to the closest rank-k state:

    d_B(rho, D_k) = arccos(sum_{i=1}^{k} sqrt(lambda_i))

where lambda_i are eigenvalues of rho in decreasing order. For the trace distance:

    d_Tr(rho, rho_k) = sum_{i=k+1}^{d} lambda_i

For the fidelity:

    F(rho, rho_k) = (sum_{i=1}^{k} sqrt(lambda_i))^2 = (Tr(sqrt(sqrt(rho) rho_k sqrt(rho))))^2

### 9.3 Amari's alpha-Divergences and Compression

The alpha-divergence between density matrices:

    D_alpha(rho || sigma) = (4/(1-alpha^2)) (1 - Tr(rho^{(1+alpha)/2} sigma^{(1-alpha)/2}))

Special cases:
- alpha -> 1: quantum relative entropy S(rho || sigma)
- alpha -> -1: reverse relative entropy S(sigma || rho)
- alpha = 0: squared Hellinger distance

**Optimal compression at level k**: minimize D_alpha(rho || sigma) over rank-k density matrices sigma. For alpha = 1 (relative entropy):

    min_{rank(sigma)<=k} S(rho || sigma) = -S(rho) + sum_{i=1}^{k} lambda_i log lambda_i + (sum_{i=k+1}^d lambda_i) log(sum_{i=k+1}^d lambda_i / (d-k))

The minimizer distributes the discarded eigenvalue mass uniformly across the discarded subspace.

---

## 10. Compression Inequalities and Bounds

### 10.1 Fannes-Audenaert Inequality

For density matrices rho, sigma in C^{d x d} with T = (1/2)||rho - sigma||_1 <= 1/e:

    |S(rho) - S(sigma)| <= T log(d-1) + H_2(T)

where H_2(T) = -T log T - (1-T) log(1-T).

**Compression implication**: If a compression channel E produces output E(rho) with trace distance T from the ideal output, the entropy error is bounded by T log d. Small distortion => small entropy change.

### 10.2 Quantum Data Processing Inequality

For any CPTP map E (including compression channels):

    S(E(rho) || E(sigma)) <= S(rho || sigma)

Channels cannot increase distinguishability. Compression necessarily loses information:

    I(A;B)_{E(rho)} <= I(A;B)_rho

The mutual information between the original and compressed representations is bounded by the mutual information in the original state.

### 10.3 Holevo Bound

For an ensemble {p_i, rho_i} sent through a channel E, the accessible classical information is bounded by:

    I_acc <= chi = S(sum p_i E(rho_i)) - sum p_i S(E(rho_i))

The Holevo quantity chi upper bounds how much classical information can be extracted from a quantum state. For compression: the number of distinguishable messages after compression is at most 2^chi.

### 10.4 Entropy Power Inequality (Quantum Version)

For density matrices rho, sigma (representing quantum states of continuous-variable systems):

    exp(2 S(rho * sigma) / d) >= exp(2 S(rho) / d) + exp(2 S(sigma) / d)

where * denotes the beam-splitter combination. This bounds how entropy grows under mixing -- the quantum generalization of Shannon's entropy power inequality.

**Compression implication**: Mixing two compressed representations always increases entropy at least as fast as the sum of exponentials. Compression followed by mixing is less efficient than mixing followed by compression.

---

## 11. Connections and Synthesis

### 11.1 The Compression Hierarchy

    Full state rho (d^2 - 1 parameters)
        |
        | Spectral truncation (PCA)
        v
    Rank-k approximation (2kd - k^2 - 1 parameters)
        |
        | Tensor network decomposition
        v
    MPS/MERA representation (n d D^2 parameters)
        |
        | Compressed sensing recovery
        v
    O(rd polylog d) measurements suffice
        |
        | Rate-distortion optimal coding
        v
    R(D) bits per source copy

Each level is a different formalization of the same operation: spectral truncation of a density matrix.

### 11.2 Universality of Spectral Truncation

Every compression scheme discussed in this document is, at its core, the following operation:

1. Represent the data/state as a density matrix rho
2. Compute (or estimate) the eigendecomposition rho = sum lambda_i |i><i|
3. Keep the top-k eigenvalues/vectors, discard the rest
4. Renormalize: rho_k = (sum_{i=1}^{k} lambda_i |i><i|) / (sum_{i=1}^{k} lambda_i)

The differences between PCA, Schumacher compression, DMRG, rate-distortion coding, and compressed sensing are differences in:
- How rho is constructed from the data
- How the eigendecomposition is computed (exact vs. approximate vs. randomized)
- How k is chosen (fixed rank, rate-distortion tradeoff, error threshold)
- What distortion measure is used (Frobenius, trace, fidelity, relative entropy)
- What additional structure is exploited (tensor product, sparsity, symmetry)

The mathematical core is universal: spectral truncation of a positive semidefinite trace-1 operator.

---

## References

- Baik, Ben Arous, Peche, "Phase transition of the largest eigenvalue for non-null complex sample covariance matrices" Ann. Prob. 33 (2005)
- Candes & Recht, "Exact Matrix Completion via Convex Optimization" Found. Comp. Math. 9 (2009)
- Datta, Renes, Renner, Wilde, "One-shot lossy quantum data compression" IEEE Trans. IT 59 (2013)
- Devetak & Berger, "Quantum Rate-Distortion Theory" arXiv:quant-ph/0501088 (2005)
- Gilyen, Su, Low, Wiebe, "Quantum singular value transformation and beyond" STOC (2019)
- Gross, Liu, Flammia, Becker, Eisert, "Quantum State Tomography via Compressed Sensing" PRL 105 (2010)
- Johnstone, "On the distribution of the largest eigenvalue in principal components analysis" Ann. Stat. 29 (2001)
- Lloyd, Mohseni, Rebentrost, "Quantum principal component analysis" Nature Phys. 10 (2014)
- Marchenko & Pastur, "Distribution of eigenvalues for some sets of random matrices" Math. USSR Sb. 1 (1967)
- Nielsen & Chuang, "Quantum Computation and Quantum Information" (2000)
- Page, "Average entropy of a subsystem" PRL 71 (1993)
- Recht, Fazel, Parrilo, "Guaranteed minimum-rank solutions of linear matrix equations" SIAM Review 52 (2010)
- Schumacher, "Quantum coding" PRA 51 (1995)
- Vidal, "Entanglement Renormalization" PRL 99 (2007)
- Voiculescu, "Free Probability Theory" Fields Inst. Comm. 12 (1997)
- White, "Density matrix formulation for quantum renormalization groups" PRL 69 (1992)
- Wilde, "Quantum Information Theory" 2nd ed. (2017)
