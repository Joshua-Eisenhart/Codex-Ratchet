# CPTP Maps and Quantum Channels: Complete Reference

## References: Wilde "Quantum Information Theory" Ch. 4-5, Nielsen & Chuang "QCQI" Ch. 8, Watrous "TQI" Ch. 2

---

## 1. Definitions and Equivalences

### 1.1 Linear Maps on Density Matrices

A quantum channel is a linear map E: L(H_A) -> L(H_B) between spaces of linear operators on Hilbert spaces H_A and H_B.

**Positive**: E(X) >= 0 whenever X >= 0.

**Completely Positive (CP)**: (E tensor id_k)(X) >= 0 for all X >= 0 on H_A tensor C^k, for ALL k >= 1.

**Important**: Positive does NOT imply completely positive. The transpose map T(rho) = rho^T is positive but not CP. (This is why partial transpose can detect entanglement.)

**Trace-Preserving (TP)**: Tr(E(X)) = Tr(X) for all X.

**CPTP = Quantum Channel**: Completely positive AND trace-preserving.

### 1.2 CP vs Positive: The Transpose Example

T: M_2(C) -> M_2(C) defined by T([[a,b],[c,d]]) = [[a,c],[b,d]].

T is positive: if rho >= 0, then rho^T >= 0 (eigenvalues are preserved).

But (T tensor id)(|Phi+><Phi+|) has a negative eigenvalue. Here |Phi+> = (|00> + |11>)/sqrt(2).

Compute: |Phi+><Phi+| = (1/2)[[1,0,0,1],[0,0,0,0],[0,0,0,0],[1,0,0,1]].

(T tensor id)(|Phi+><Phi+|) = (1/2)[[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]].

Eigenvalues: 1/2, 1/2, 1/2, -1/2. NOT positive semidefinite. So T is not CP.

---

## 2. Kraus Representation

### 2.1 Theorem (Kraus/Choi)

E: L(H_A) -> L(H_B) is CP iff there exist operators A_k: H_A -> H_B (Kraus operators) such that:

    E(rho) = sum_{k=1}^{r} A_k rho A_k^dagger

The number r of Kraus operators satisfies r <= d_A d_B.

E is additionally TP iff:

    sum_k A_k^dagger A_k = I_A

E is trace non-increasing (quantum operation / CP map) iff:

    sum_k A_k^dagger A_k <= I_A

### 2.2 Non-Uniqueness

Two sets {A_k}_{k=1}^{r} and {B_l}_{l=1}^{s} define the same channel iff there exists a (partial) unitary matrix u_{kl} such that:

    A_k = sum_l u_{kl} B_l

(with zero-padding if r =/= s).

### 2.3 Minimal Kraus Rank

The minimum number of Kraus operators = rank of the Choi matrix = Choi rank.

For a d-dimensional system, the Choi rank r satisfies 1 <= r <= d^2.
- r = 1: unitary channel (E(rho) = U rho U^dagger)
- r = d^2: "generic" channel (maximally noisy)

### 2.4 Examples: Qubit Channels

**Depolarizing channel**: E(rho) = (1-p) rho + p I/2 = (1 - 3p/4) rho + (p/4)(sigma_x rho sigma_x + sigma_y rho sigma_y + sigma_z rho sigma_z)

Kraus operators: A_0 = sqrt(1-3p/4) I, A_1 = sqrt(p/4) sigma_x, A_2 = sqrt(p/4) sigma_y, A_3 = sqrt(p/4) sigma_z.

**Amplitude damping**: Models energy dissipation (T1 decay).

    A_0 = [[1, 0], [0, sqrt(1-gamma)]]
    A_1 = [[0, sqrt(gamma)], [0, 0]]

Check: A_0^dagger A_0 + A_1^dagger A_1 = [[1,0],[0,1-gamma]] + [[0,0],[0,gamma]] = I. TP confirmed.

Effect on Bloch vector:
    r_x -> sqrt(1-gamma) r_x
    r_y -> sqrt(1-gamma) r_y
    r_z -> (1-gamma) r_z + gamma

The Bloch ball is compressed and shifted toward |0>.

**Phase damping (dephasing)**: Models T2 decay.

    A_0 = sqrt(1-p/2) I = [[sqrt(1-p/2), 0], [0, sqrt(1-p/2)]]
    A_1 = sqrt(p/2) sigma_z = [[sqrt(p/2), 0], [0, -sqrt(p/2)]]

Effect: r_x -> (1-p) r_x, r_y -> (1-p) r_y, r_z -> r_z. Shrinks equatorial plane, preserves z.

---

## 3. Stinespring Dilation

### 3.1 Theorem

Every CPTP map E: L(H_A) -> L(H_B) can be written as:

    E(rho) = Tr_E(V rho V^dagger)

where:
- H_E is an "environment" Hilbert space with dim(H_E) = Choi rank
- V: H_A -> H_B tensor H_E is an isometry (V^dagger V = I_A)
- Tr_E is the partial trace over the environment

### 3.2 Relation to Kraus

Given Kraus operators {A_k}, construct:

    V|psi> = sum_k (A_k|psi>) tensor |k>

where {|k>} is an orthonormal basis for H_E. Then:

    Tr_E(V|psi><psi|V^dagger) = sum_k A_k|psi><psi|A_k^dagger

Check V is isometric: <psi|V^dagger V|psi> = sum_k <psi|A_k^dagger A_k|psi> = <psi|I|psi> = <psi|psi>.

### 3.3 Complementary Channel

The complementary (or conjugate) channel E^c maps:

    E^c(rho) = Tr_B(V rho V^dagger)

(Trace over the output instead of the environment.)

E^c captures the information leaked to the environment. For the amplitude damping channel:

    E^c(rho) = [[<0|rho|0> + (1-gamma)<1|rho|1>, sqrt(gamma)<1|rho|0>],
                [sqrt(gamma)<0|rho|1>, gamma<1|rho|1>]]

**Degradable channel**: E^c = D . E for some CPTP map D.
(The environment can simulate itself from the output.) Amplitude damping is degradable.

**Anti-degradable**: E = D . E^c for some CPTP map D.
(The output can be simulated from the environment leakage.)

**Neither**: Most channels. The depolarizing channel is degradable for small p, anti-degradable for large p, neither in between.

---

## 4. Choi-Jamiolkowski Isomorphism

### 4.1 Definition

For E: L(H_A) -> L(H_B), define the Choi matrix:

    J(E) = (E tensor id_A)(|Omega><Omega|)

where |Omega> = sum_{i=1}^{d_A} |i>|i> is the (unnormalized) maximally entangled state on H_A tensor H_A.

Equivalently: [J(E)]_{ij,kl} = <i|E(|j><l|)|k>.

### 4.2 Fundamental Correspondence

    E is CP      <=>  J(E) >= 0  (positive semidefinite)
    E is TP      <=>  Tr_B(J(E)) = I_A
    E is unital  <=>  Tr_A(J(E)) = I_B  (E(I) = I)

So CPTP channels correspond to bipartite density matrices (up to normalization) satisfying a marginal constraint.

### 4.3 Recovery of the Channel from J(E)

    E(rho) = d_A Tr_A((rho^T tensor I_B) J(E))

### 4.4 Properties of the Choi Matrix

- dim(J(E)) = d_A d_B x d_A d_B
- rank(J(E)) = Choi rank = minimum number of Kraus operators
- For unitary channels: J(U . U^dagger) = |U_vec><U_vec| where |U_vec> = (U tensor I)|Omega> (rank 1)
- Eigenvalues of J(E): non-negative, related to singular values of Kraus operators

### 4.5 Channel-State Duality

The Choi-Jamiolkowski isomorphism establishes a bijection between:
- CPTP maps E: L(C^d) -> L(C^d)
- Density matrices rho on C^d tensor C^d with Tr_2(rho) = I/d

This is profound: studying quantum channels IS studying certain bipartite quantum states, and vice versa.

---

## 5. Lindblad Master Equation

### 5.1 Derivation Context

For a system coupled to a Markovian environment, the most general time-local, CPTP-preserving evolution is:

    d rho/dt = L(rho) = -i[H, rho] + sum_{k=1}^{d^2-1} gamma_k (L_k rho L_k^dagger - (1/2){L_k^dagger L_k, rho})

where:
- H is the effective Hamiltonian (Hermitian)
- L_k are Lindblad (jump) operators
- gamma_k >= 0 are decay rates
- {A, B} = AB + BA is the anticommutator

### 5.2 GKSL Form (Gorini-Kossakowski-Sudarshan-Lindblad)

The most general generator of a quantum dynamical semigroup (E_t = exp(tL) for t >= 0):

    L(rho) = -i[H, rho] + sum_{j,k} h_{jk} (F_j rho F_k^dagger - (1/2){F_k^dagger F_j, rho})

where h_{jk} is a positive semidefinite matrix (Kossakowski matrix) and {F_j} is any basis for the traceless operators on H.

Diagonalizing h_{jk} = sum gamma_l u_{jl} u_{kl}* and defining L_l = sum_j u_{jl} F_j gives the diagonal Lindblad form above.

### 5.3 Properties

- L is a superoperator (linear map on operators).
- E_t = exp(tL) is CPTP for all t >= 0 iff L has the Lindblad form (GKSL theorem, 1976).
- The steady state: L(rho_ss) = 0. May be unique or not.
- Detailed balance: L satisfies detailed balance w.r.t. rho_ss if it models thermal relaxation.

### 5.4 Qubit Lindblad Operators

For a single qubit with general Markovian dynamics:

**T1 decay** (amplitude damping):
    L_1 = sqrt(gamma) sigma_- = sqrt(gamma) [[0,1],[0,0]]
    
    L(rho) = gamma(sigma_- rho sigma_+ - (1/2){sigma_+ sigma_-, rho})
    
    In components: d<rho_{00}>/dt = gamma rho_{11}, d<rho_{11}>/dt = -gamma rho_{11},
                   d<rho_{01}>/dt = -(gamma/2) rho_{01}.

**T2 dephasing** (pure dephasing):
    L_2 = sqrt(gamma_phi) sigma_z / 2
    
    Effect: d<rho_{01}>/dt = -gamma_phi rho_{01} (off-diagonals decay).
    
    Total decoherence rate: 1/T2 = 1/(2 T1) + 1/T_phi.

### 5.5 Vectorization and Liouvillian

Vectorize the density matrix: rho -> |rho>> (stack columns). Then:

    d|rho>>/dt = L_super |rho>>

where L_super is the Liouvillian superoperator matrix:

    L_super = -i(H tensor I - I tensor H^T) + sum_k gamma_k (L_k tensor L_k* - (1/2)(L_k^dagger L_k tensor I + I tensor L_k^T L_k*))

Dimension of L_super: d^2 x d^2.

The eigenvalues of L_super determine the relaxation spectrum. All eigenvalues have Re(lambda) <= 0 (stability). The zero eigenvalue(s) correspond to steady states.

---

## 6. Affine Map on the Bloch Sphere

### 6.1 General Qubit Channel

Any qubit CPTP map acts on the Bloch vector as:

    r -> M r + t

where M is a 3x3 real matrix and t is a 3-vector (translation).

Constraints from CPTP:
- The image of the Bloch ball must lie inside the Bloch ball.
- The full constraint is: for all |r| <= 1, |M r + t| <= 1.
- More precisely: singular values of M plus |t| must satisfy specific inequalities (Ruskai, Szarek, Werner 2002).

### 6.2 Unital Channels (t = 0)

A channel is unital iff E(I) = I, i.e., the maximally mixed state maps to itself.

For qubit unital channels: t = 0, so r -> M r.

The image of the Bloch ball is an ellipsoid (possibly degenerate) centered at the origin.

**Pauli channels**: M = diag(lambda_1, lambda_2, lambda_3) where:

    E(rho) = p_0 rho + p_1 sigma_x rho sigma_x + p_2 sigma_y rho sigma_y + p_3 sigma_z rho sigma_z

with p_i >= 0, sum p_i = 1, and:
    lambda_1 = p_0 + p_1 - p_2 - p_3
    lambda_2 = p_0 - p_1 + p_2 - p_3
    lambda_3 = p_0 - p_1 - p_2 + p_3

CP constraint (Fujiwara & Algoet 1999): the Pauli channel is CP iff the eigenvalues satisfy:

    1 + lambda_k >= |lambda_i + lambda_j|  for all permutations {i,j,k} of {1,2,3}

Geometrically, (lambda_1, lambda_2, lambda_3) must lie in a tetrahedron with vertices at (1,1,1), (1,-1,-1), (-1,1,-1), (-1,-1,1).

### 6.3 Non-Unital Channels

For non-unital channels (t =/= 0), the image ellipsoid is shifted from the origin.

Example: Amplitude damping has M = diag(sqrt(1-gamma), sqrt(1-gamma), 1-gamma) and t = (0, 0, gamma).

### 6.4 Complete Parameterization of Qubit Channels

By the singular value decomposition of M = U diag(s_1, s_2, s_3) V^T with U, V in O(3), any qubit channel can be brought to canonical form (by pre- and post-composition with unitaries):

    r -> diag(s_1, s_2, s_3) r + (0, 0, t_3)

with s_1 >= s_2 >= s_3 >= 0 and t_3 >= 0 (after appropriate rotations).

CPTP constraints on (s_1, s_2, s_3, t_3) are given by the Fujiwara-Algoet conditions (generalized for non-unital case).

---

## 7. Channel Capacities

### 7.1 Classical Capacity

    C(N) = lim_{n->inf} (1/n) chi(N^{tensor n})

where chi is the Holevo information of the channel:

    chi(N) = max_{ensemble} [S(sum p_x N(rho_x)) - sum p_x S(N(rho_x))]

For degradable channels: C(N) = max_{rho} [S(N(rho)) - S(N^c(rho))].

**Additivity**: C(N) = chi(N) was conjectured (and would mean no entanglement needed in encoding), but DISPROVED (Hastings 2009). There exist channels where entangled inputs increase the Holevo information.

### 7.2 Quantum Capacity

    Q(N) = lim_{n->inf} (1/n) max_{rho^{(n)}} I_c(N^{tensor n}, rho^{(n)})

where I_c is the coherent information.

For degradable channels: Q(N) = max_rho I_c(N, rho) (single-letter).
For anti-degradable channels: Q(N) = 0.

**Superadditivity**: Q can be superadditive (Cubitt et al. 2015 showed "superactivation": two channels with Q = 0 individually can have Q > 0 jointly).

### 7.3 Private Classical Capacity

    P(N) = lim_{n->inf} (1/n) max [I(X:B) - I(X:E)]

where B is the receiver and E is the eavesdropper (environment).

P(N) >= Q(N) always. Equality for degradable channels.

### 7.4 Entanglement-Assisted Classical Capacity

    C_E(N) = max_rho I(A:B)_sigma

where sigma_{AB} = (id tensor N)(|phi><phi|) and |phi> is a purification of rho. This equals:

    C_E(N) = max_rho [S(rho) + S(N(rho)) - S((id tensor N)(|phi><phi|))]

Bennett-Shor-Smolin-Thapliyal (2002): C_E is additive (single-letter formula always works).

---

## 8. Channel Composition and Concatenation

### 8.1 Serial Composition

(E_2 . E_1)(rho) = E_2(E_1(rho)).

Kraus: if E_1 has Kraus {A_k} and E_2 has Kraus {B_l}, then E_2 . E_1 has Kraus {B_l A_k}.

Choi: J(E_2 . E_1) = Tr_2((I_1 tensor J(E_2)) . (J(E_1)^{T_2} tensor I_3)) [Schur product/link product].

### 8.2 Parallel Composition (Tensor Product)

(E_1 tensor E_2)(rho_{AB}) applies E_1 to A and E_2 to B.

Kraus: {A_k tensor B_l}.
Choi: J(E_1 tensor E_2) = J(E_1) tensor J(E_2) (up to reordering subsystems).

### 8.3 Twirling

The depolarizing channel is the result of "twirling" any channel:

    integral dU (U . E . U^dagger) = Delta_{depol}

where the integral is over the Haar measure on SU(d) and Delta_{depol}(rho) = p rho + (1-p) I/d.

Similarly, Pauli twirling (averaging over random Pauli applications) converts any channel into a Pauli channel.

---

## 9. Quantum Error Correction

### 9.1 Knill-Laflamme Conditions

A code with projector P corrects the errors {E_a} iff:

    P E_a^dagger E_b P = alpha_{ab} P

for some Hermitian matrix alpha_{ab}.

Interpretation: all errors look the same on the code space (up to a scalar), so they can be reversed.

### 9.2 Recovery Channel

Given a correctable error channel E with Kraus {A_k} and code projector P, the recovery channel R exists such that:

    R . E(rho) = rho  for all rho in the code space

R can be constructed explicitly from the syndrome measurement and conditional unitaries.

### 9.3 Approximate Error Correction

For approximate correction (Barnum & Knill 2002):

    F(rho, R . E(rho)) >= 1 - epsilon

The necessary condition weakens to: P E_a^dagger E_b P approx alpha_{ab} P.

The Petz recovery map provides a near-optimal recovery for approximate correction.
