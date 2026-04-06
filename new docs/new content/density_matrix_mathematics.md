# Density Matrix Mathematics: Complete Theory on C^2 and C^4

## Reference: Bengtsson & Zyczkowski "Geometry of Quantum States" (2006, 2nd ed. 2017)

---

## 1. Foundations

A density matrix rho on Hilbert space H of dimension d is a linear operator satisfying:

1. **Hermiticity**: rho = rho^dagger
2. **Positivity**: <psi|rho|psi> >= 0 for all |psi> in H (equivalently, all eigenvalues >= 0)
3. **Unit trace**: Tr(rho) = 1

The set of all density matrices on C^d is denoted D(C^d). It is a convex body of real dimension d^2 - 1.

**Pure states**: rho^2 = rho (rank-1 projectors). These are the extreme points of D(C^d).
**Mixed states**: rho^2 =/= rho, equivalently Tr(rho^2) < 1.

**Purity**: gamma = Tr(rho^2), satisfying 1/d <= gamma <= 1. gamma = 1 iff pure, gamma = 1/d iff maximally mixed.

---

## 2. Spectral Decomposition

Every density matrix admits:

    rho = sum_{i=1}^{d} lambda_i |i><i|

where {|i>} is an orthonormal eigenbasis, lambda_i >= 0, sum lambda_i = 1.

The spectrum (lambda_1, ..., lambda_d) lives in the probability simplex Delta_{d-1}.

For **C^2**: rho = lambda_1 |1><1| + lambda_2 |2><2| with lambda_1 + lambda_2 = 1, lambda_i >= 0.
One free parameter: lambda_1 in [0,1].

For **C^4**: rho = sum_{i=1}^{4} lambda_i |i><i| with three independent eigenvalues (constraint: sum = 1).
Spectrum in the tetrahedron Delta_3.

**Key property**: The unitary orbit of rho (all U rho U^dagger for unitary U) is determined entirely by the spectrum. Two density matrices are unitarily equivalent iff they have the same spectrum.

**Majorization**: For spectra lambda, mu (sorted decreasingly), lambda majorizes mu (written lambda >- mu) iff sum_{i=1}^{k} lambda_i >= sum_{i=1}^{k} mu_i for all k. This gives a partial order on the set of spectra. The maximally mixed state (1/d, ..., 1/d) is majorized by all others.

---

## 3. Bloch Decomposition: Single Qubit (C^2)

Any 2x2 density matrix can be written:

    rho = (I + r . sigma) / 2

where:
- sigma = (sigma_x, sigma_y, sigma_z) are the Pauli matrices
- r = (r_x, r_y, r_z) in R^3 is the **Bloch vector**
- r_i = Tr(rho sigma_i)

**Pauli matrices** (explicit):

    sigma_x = [[0, 1], [1, 0]]
    sigma_y = [[0, -i], [i, 0]]
    sigma_z = [[1, 0], [0, -1]]

Properties: sigma_i^dagger = sigma_i, Tr(sigma_i) = 0, sigma_i^2 = I, sigma_i sigma_j = delta_{ij} I + i epsilon_{ijk} sigma_k.

**Eigenvalues of rho**: lambda_pm = (1 +/- |r|) / 2

**Positivity constraint**: lambda_pm >= 0 implies |r| <= 1.

The Bloch ball B^3 = {r in R^3 : |r| <= 1} is the full state space.
- **Surface** |r| = 1: pure states. rho = |psi><psi| iff rho^2 = rho iff |r| = 1.
- **Interior** |r| < 1: mixed states.
- **Center** r = 0: maximally mixed state rho = I/2.

**Purity**: Tr(rho^2) = (1 + |r|^2) / 2

**Von Neumann entropy**: S(rho) = -lambda_+ log lambda_+ - lambda_- log lambda_-
    = h((1 + |r|)/2) where h is the binary entropy h(x) = -x log x - (1-x) log(1-x)

**Explicit matrix form**:

    rho = (1/2) [[1 + r_z, r_x - i r_y], [r_x + i r_y, 1 - r_z]]

**Parametrization by (theta, phi, r)**:
For r = r(sin theta cos phi, sin theta sin phi, cos theta):

    rho = (1/2) [[1 + r cos theta, r sin theta e^{-i phi}], [r sin theta e^{i phi}, 1 - r cos theta]]

Pure state (r = 1): rho = |psi><psi| with |psi> = cos(theta/2)|0> + e^{i phi} sin(theta/2)|1>.

---

## 4. Two-Qubit Decomposition (C^2 tensor C^2 = C^4)

General 2-qubit density matrix in the Pauli product basis:

    rho = (1/4)(I_4 + a . sigma tensor I + I tensor b . sigma + sum_{i,j=1}^{3} T_{ij} sigma_i tensor sigma_j)

where:
- a in R^3: local Bloch vector of subsystem A, a_i = Tr(rho (sigma_i tensor I))
- b in R^3: local Bloch vector of subsystem B, b_j = Tr(rho (I tensor sigma_j))
- T in R^{3x3}: correlation tensor, T_{ij} = Tr(rho (sigma_i tensor sigma_j))

This gives 3 + 3 + 9 = 15 real parameters, which combined with the trace-1 constraint accounts for 4^2 - 1 = 15 degrees of freedom.

**Reduced states**:
    rho_A = Tr_B(rho) = (I + a . sigma) / 2
    rho_B = Tr_A(rho) = (I + b . sigma) / 2

### 4.1 Correlation Tensor Properties

The correlation tensor T captures all correlations between A and B.

**SVD of T**: T = U diag(t_1, t_2, t_3) V^T where U, V in SO(3) and t_i >= 0 are the singular values.

By local unitary equivalence (rho -> (U_A tensor U_B) rho (U_A tensor U_B)^dagger), one can always bring rho to a form where T is diagonal:

    T_canonical = diag(t_1, t_2, t_3)

(This corresponds to choosing local Bloch bases aligned with the SVD.)

**Product states**: rho = rho_A tensor rho_B implies T_{ij} = a_i b_j, i.e., T = a b^T (rank-1).

**Bell states**: a = b = 0 and T = diag(+/-1, +/-1, +/-1) with det(T) = -1.
Explicitly for |Phi+> = (|00> + |11>)/sqrt(2): T = diag(1, -1, 1), a = b = 0.

**Werner states**: rho_W = (1-p) I/4 + p |Phi+><Phi+|: a = b = 0, T = p diag(1, -1, 1).
Entangled iff p > 1/3. Violates Bell inequality iff p > 1/sqrt(2).

### 4.2 Positivity Constraints on (a, b, T)

The constraint rho >= 0 translates to nonlinear inequalities on (a, b, T). For the general case, the complete set of constraints is:

**Necessary conditions**:
- |a| <= 1, |b| <= 1
- Tr(T^T T) + |a|^2 + |b|^2 <= 3
- |T_{ij}| <= 1 for all i,j

**Sufficient condition for separability (much stronger)**:
For T diagonal with entries t_i, and a = b = 0 (Bell-diagonal states):
rho >= 0 iff 1 +/- t_1 +/- t_2 +/- t_3 >= 0 (for all 4 sign choices matching even parity).

The complete positivity condition requires computing the eigenvalues of the 4x4 matrix explicitly.

**Eigenvalues of rho** (Bell-diagonal case, a = b = 0, T diagonal):

    lambda_1 = (1 + t_1 - t_2 + t_3)/4
    lambda_2 = (1 + t_1 + t_2 - t_3)/4
    lambda_3 = (1 - t_1 + t_2 + t_3)/4
    lambda_4 = (1 - t_1 - t_2 - t_3)/4

(These correspond to the four Bell state populations.)

---

## 5. Quantum Steering Ellipsoid

**Theorem (Jevtic, Pusey, Rudolph, Jennings 2014)**: For a 2-qubit state rho with decomposition (a, b, T), the set of all Bloch vectors that Bob's qubit can be steered to by Alice's measurements forms an ellipsoid (or degenerate ellipsoid) in Bob's Bloch ball.

**Construction**: Alice performs a general POVM element E_alpha on her qubit. Bob's unnormalized conditional state is:

    rho_B|alpha = Tr_A((E_alpha tensor I) rho)

The set of all normalized Bloch vectors for Bob, as E_alpha ranges over all rank-1 POVMs, traces out an ellipsoid.

**Ellipsoid parameters**:
- Center: c = (b - T^T a) / (1 - |a|^2)  [when |a| < 1]
- Shape matrix: Q = (T^T - b a^T)(I - a a^T)^{-1}(T - a b^T) / (1 - |a|^2)

For the canonical form (a along z-axis, T diagonal):
The ellipsoid has semi-axes:

    s_i = t_i / sqrt(1 - a_z^2)  [for i = 1, 2 corresponding to x, y]

**Separability criterion**: rho is separable iff the steering ellipsoid fits inside the Bloch ball AND the ellipsoid is centered at the origin for the canonical form (after accounting for local shifts).

**Volume**: V = (4 pi / 3) |det(Q)|^{1/2} / (1 - |a|^2)^{3/2}

Entanglement increases the ellipsoid volume. Maximal for Bell states (full Bloch sphere).

---

## 6. Purification Theorem

**Theorem**: Every mixed state rho_A on H_A can be realized as the partial trace of a pure state |Psi> on H_A tensor H_B for some auxiliary system B with dim(H_B) >= rank(rho_A).

**Proof**:
Let rho_A = sum_{i=1}^{r} lambda_i |a_i><a_i| be the spectral decomposition with r = rank(rho_A).

Define |Psi> = sum_{i=1}^{r} sqrt(lambda_i) |a_i> tensor |b_i>

where {|b_i>} is any orthonormal set in H_B (dim H_B >= r).

Then:
Tr_B(|Psi><Psi|) = sum_{i,j} sqrt(lambda_i lambda_j) |a_i><a_j| Tr(|b_i><b_j|)
                  = sum_{i,j} sqrt(lambda_i lambda_j) |a_i><a_j| delta_{ij}
                  = sum_i lambda_i |a_i><a_i|
                  = rho_A.  QED.

**Non-uniqueness**: If |Psi> and |Phi> are two purifications of the same rho_A with the same B, then |Phi> = (I_A tensor U_B) |Psi> for some unitary U_B on H_B. (This is the **unitary freedom in purifications**.)

**Proof of non-uniqueness**:
Write |Psi> = sum_i sqrt(lambda_i) |a_i>|b_i> and |Phi> = sum_i sqrt(lambda_i) |a_i>|b'_i>.
Both purify rho_A, so both have the same Schmidt coefficients sqrt(lambda_i).
Define U_B: |b_i> -> |b'_i>, extended unitarily. Then |Phi> = (I tensor U_B)|Psi>.

**Consequence for C^2**: Any qubit mixed state has a purification in C^4 (2-qubit pure state). The purification is unique up to a unitary on the purifying qubit.

**For C^4**: A general 2-qubit mixed state requires purification in C^4 tensor C^r where r = rank(rho), so up to C^4 tensor C^4 = C^{16} in the worst case. But if we only need to purify one subsystem, a 2-qubit mixed state rho on C^4 can be purified by appending C^4, giving a pure state on C^{16}.

---

## 7. Matrix Representations and Computational Forms

### 7.1 Explicit Pauli tensor basis for C^4

The 16 basis operators for 2-qubit density matrices:

    {sigma_mu tensor sigma_nu : mu, nu in {0, 1, 2, 3}}

where sigma_0 = I. These satisfy:

    Tr((sigma_mu tensor sigma_nu)(sigma_alpha tensor sigma_beta)) = 4 delta_{mu alpha} delta_{nu beta}

So rho = (1/4) sum_{mu,nu} r_{mu nu} sigma_mu tensor sigma_nu with r_{mu nu} = Tr(rho sigma_mu tensor sigma_nu).

The matrix r_{mu nu} is a real 4x4 matrix with r_{00} = 1. The (0,i) components give a, the (i,0) components give b, and the (i,j) block gives T.

### 7.2 Partial Transpose

For rho on C^2 tensor C^2 written in the computational basis:

    rho = [[rho_{00,00}, rho_{00,01}, rho_{00,10}, rho_{00,11}],
           [rho_{01,00}, rho_{01,01}, rho_{01,10}, rho_{01,11}],
           [rho_{10,00}, rho_{10,01}, rho_{10,10}, rho_{10,11}],
           [rho_{11,00}, rho_{11,01}, rho_{11,10}, rho_{11,11}]]

The partial transpose w.r.t. B (transposing the second index pair):

    rho^{T_B}_{ij,kl} = rho_{ij,lk}  (swap k <-> l)

Equivalently, within each 2x2 block (indexed by i,k), transpose the block.

In terms of (a, b, T): partial transpose maps T -> T', where T' = diag(t_1, -t_2, t_3) for diagonal T. More generally: T_2 -> -T_2 (the sigma_y component flips sign).

---

## 8. Higher Dimensional Generalization: Generalized Bloch Decomposition

For C^d, the density matrix decomposes in the generalized Gell-Mann basis:

    rho = (1/d)(I + sqrt(d(d-1)/2) n . lambda)

where lambda = (lambda_1, ..., lambda_{d^2-1}) are the generalized Gell-Mann matrices (traceless Hermitian generators of SU(d)), and n in R^{d^2-1} is the generalized Bloch vector.

**Key difference from d=2**: For d >= 3, the state space is NOT the full ball. The positivity constraint rho >= 0 carves out a complicated convex body strictly inside the ball |n| <= 1.

For d = 4 (2-qubit): the generalized Bloch vector has 15 components, decomposing as described in section 4 into (a, b, T).

---

## 9. Functional Calculus on Density Matrices

For any function f: R -> R and rho = sum lambda_i |i><i|:

    f(rho) = sum f(lambda_i) |i><i|

Key instances:
- rho^alpha = sum lambda_i^alpha |i><i| (matrix power, used in Renyi entropy)
- log(rho) = sum log(lambda_i) |i><i| (used in von Neumann entropy)
- sqrt(rho) = sum sqrt(lambda_i) |i><i| (used in fidelity)

**Caution**: log(rho) is defined only on the support of rho. For rank-deficient rho, the convention is 0 log 0 = 0 in entropy calculations.

---

## 10. Convex Structure and Extremal Decompositions

D(C^d) is a convex set. Its extreme points are the pure states (rank-1 projectors).

**Caratheodory's theorem**: Every rho in D(C^d) can be written as a convex combination of at most d^2 pure states (though d suffices by the spectral decomposition).

**Non-uniqueness of decompositions**: A mixed state rho generally has infinitely many decompositions into pure states. The spectral decomposition is unique only when all eigenvalues are distinct. More generally:

    rho = sum_i p_i |psi_i><psi_i|  and  rho = sum_j q_j |phi_j><phi_j|

are two decompositions of the same rho iff there exists a unitary matrix u_{ij} such that sqrt(p_i) |psi_i> = sum_j u_{ij} sqrt(q_j) |phi_j>. (Hughston-Jozsa-Wootters / Schrodinger mixture theorem.)

This is the density matrix analog of the unitary freedom in purifications, and is in fact equivalent to it via the purification-ensemble correspondence.
