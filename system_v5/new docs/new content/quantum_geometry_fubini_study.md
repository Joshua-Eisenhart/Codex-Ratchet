# Quantum Geometry: Fubini-Study Metric, Quantum Geometric Tensor, and Bures Metric

## References: Provost & Vallee (1980), Bengtsson & Zyczkowski (2006), Braunstein & Caves (1994)

---

## 1. Projective Hilbert Space and the Fubini-Study Metric

Quantum states are rays in Hilbert space, not vectors. The space of rays in C^{d+1} is complex projective space CP^d. For a qubit (d=1), CP^1 = S^2 (the Bloch sphere).

**Definition**: For |psi>, |psi + d psi> in H, the Fubini-Study line element is:

    ds^2_{FS} = (<d psi|d psi><psi|psi> - |<psi|d psi>|^2) / <psi|psi>^2

For normalized states (<psi|psi> = 1):

    ds^2_{FS} = <d psi|d psi> - |<psi|d psi>|^2

### 1.1 Derivation from Distinguishability

The FS distance between |psi> and |phi> (both normalized) is:

    d_{FS}(|psi>, |phi>) = arccos(|<psi|phi>|)

This is a proper geodesic distance on CP^d. The infinitesimal form:

|<psi|psi + d psi>|^2 = |1 + <psi|d psi>|^2 = 1 + 2 Re(<psi|d psi>) + |<psi|d psi>|^2

Since we can choose <psi|d psi> to be purely imaginary (gauge choice d(<psi|psi>) = 0), we get:

cos^2(ds) = 1 - ds^2_{FS} to leading order, confirming ds_{FS} = arccos|<psi|phi>|.

### 1.2 Qubit Case: CP^1 = S^2

Parametrize |psi> = cos(theta/2)|0> + e^{i phi} sin(theta/2)|1>. Then:

    |d psi> = (-sin(theta/2)/2 d theta)|0> + e^{i phi}(cos(theta/2)/2 d theta + i sin(theta/2) d phi)|1>

Computing:
    <d psi|d psi> = (1/4) d theta^2 + sin^2(theta/2) cos^2(theta/2) d phi^2 + sin^2(theta/2) d phi^2
    
Wait, let me be precise:

    <d psi|d psi> = sin^2(theta/2)/4 d theta^2 + cos^2(theta/2)/4 d theta^2 + sin^2(theta/2) d phi^2
                  = (1/4) d theta^2 + sin^2(theta/2) d phi^2

Hmm, that includes gauge terms. Let me use the gauge-invariant form directly.

    <psi|d psi> = i sin^2(theta/2) d phi   (purely imaginary for real d theta)

    |<psi|d psi>|^2 = sin^4(theta/2) d phi^2

So:
    ds^2_{FS} = (1/4) d theta^2 + sin^2(theta/2) d phi^2 - sin^4(theta/2) d phi^2
              = (1/4) d theta^2 + sin^2(theta/2) cos^2(theta/2) d phi^2
              = (1/4)(d theta^2 + sin^2 theta d phi^2)

This is **(1/4) times the round metric on S^2**. The total area of CP^1 under FS is 4 pi * (1/4) = pi.

**Gaussian curvature**: K = 4 (constant positive curvature). The Bloch sphere has radius 1/2 in the FS metric.

---

## 2. Quantum Geometric Tensor

**Definition** (Provost & Vallee 1980): For a family of states |psi(lambda)> parametrized by lambda = (lambda^1, ..., lambda^n):

    Q_{mu nu} = <partial_mu psi|(1 - |psi><psi|)|partial_nu psi>

where partial_mu = partial/partial lambda^mu and |psi> is normalized.

Equivalently:

    Q_{mu nu} = <partial_mu psi|partial_nu psi> - <partial_mu psi|psi><psi|partial_nu psi>

### 2.1 Decomposition into Symmetric and Antisymmetric Parts

Q_{mu nu} is complex in general. Decompose:

    Q_{mu nu} = g_{mu nu} + (i/2) F_{mu nu}

where:

**Symmetric (real) part**: g_{mu nu} = Re(Q_{mu nu}) = (1/2)(Q_{mu nu} + Q_{nu mu})

This is the **Fubini-Study metric tensor** (Riemannian metric on parameter space, pulled back from CP^d).

**Antisymmetric (imaginary) part**: F_{mu nu} = -2 Im(Q_{mu nu}) = i(Q_{mu nu} - Q_{nu mu})

This is the **Berry curvature 2-form**.

### 2.2 Berry Curvature

    F_{mu nu} = -2 Im(<partial_mu psi|partial_nu psi> - <partial_mu psi|psi><psi|partial_nu psi>)
              = -2 Im(<partial_mu psi|partial_nu psi>) + 2 Im(<partial_mu psi|psi><psi|partial_nu psi>)

The **Berry connection** (gauge potential):

    A_mu = i<psi|partial_mu psi>

is real-valued (since d<psi|psi> = 0 implies <partial_mu psi|psi> + <psi|partial_mu psi> = 0, so <psi|partial_mu psi> is purely imaginary).

**Berry curvature as curl of connection**:

    F_{mu nu} = partial_mu A_nu - partial_nu A_mu

This is gauge-invariant even though A_mu transforms as A_mu -> A_mu + partial_mu chi under |psi> -> e^{i chi} |psi>.

### 2.3 Berry Phase

For a closed loop C in parameter space:

    gamma_Berry = integral_C A . d lambda = integral_S F . dS   (by Stokes)

where S is any surface bounded by C.

For a qubit with |psi(theta, phi)> on the Bloch sphere:

    A_theta = 0,  A_phi = -sin^2(theta/2)  (in standard gauge)

    F_{theta phi} = -(1/2) sin theta

    gamma_Berry = -(1/2) integral sin theta d theta d phi = -Omega/2

where Omega is the solid angle subtended by the loop on the Bloch sphere.

---

## 3. Kahler Structure

CP^d is a Kahler manifold. The three structures (Riemannian metric g, symplectic form omega, complex structure J) satisfy:

    g(u, v) = omega(u, Jv)

In the quantum context:
- g = Fubini-Study metric (real part of Q)
- omega = Berry curvature form (imaginary part of Q)
- J = complex structure of projective Hilbert space

**Kahler potential**: For CP^d in homogeneous coordinates [z_0 : ... : z_d]:

    K = log(sum_i |z_i|^2)

The FS metric in terms of the Kahler potential:

    g_{a b*} = partial^2 K / (partial z^a partial z*^b) - (partial K / partial z^a)(partial K / partial z*^b)

For CP^1 with affine coordinate w = z_1/z_0:

    K = log(1 + |w|^2)

    g_{w w*} = 1/(1 + |w|^2)^2

    ds^2 = g_{w w*} dw dw* = (dw dw*) / (1 + |w|^2)^2

Setting w = tan(theta/2) e^{i phi}, this reproduces ds^2 = (1/4)(d theta^2 + sin^2 theta d phi^2).

---

## 4. Bures Metric for Mixed States

The Fubini-Study metric applies to pure states. For mixed states, the natural generalization is the **Bures metric**.

### 4.1 Definition via Fidelity

**Fidelity**: F(rho, sigma) = (Tr sqrt(sqrt(rho) sigma sqrt(rho)))^2

**Bures distance**:

    d_B(rho, sigma) = sqrt(2(1 - sqrt(F(rho, sigma))))

**Bures metric** (infinitesimal):

    ds^2_B = (1/2)(1 - F(rho, rho + d rho)) ≈ (1/4) Tr(d rho G^{-1}(d rho))

where G is the symmetric logarithmic derivative (SLD) superoperator.

### 4.2 SLD Fisher Information

The SLD L_mu is defined implicitly by:

    partial_mu rho = (1/2)(L_mu rho + rho L_mu)

The Bures metric tensor is then:

    g^B_{mu nu} = (1/2) Re Tr(rho L_mu L_nu) = (1/4) Tr(rho {L_mu, L_nu})

This is the **quantum Fisher information matrix** (divided by 4):

    [J_Q]_{mu nu} = (1/2) Tr(rho {L_mu, L_nu})

So g^B = J_Q / 4.

### 4.3 Explicit SLD for Spectral Decomposition

Given rho = sum_i lambda_i |i><i|, the matrix elements of L_mu are:

    <i|L_mu|j> = (2 <i|partial_mu rho|j>) / (lambda_i + lambda_j)

provided lambda_i + lambda_j > 0. If both lambda_i = lambda_j = 0, the matrix element is undefined (but irrelevant as it's outside the support).

### 4.4 Bures Metric for Qubits

For rho = (I + r . sigma)/2 with |r| = r:

    ds^2_B = (1/4) ((dr . dr) / (1 - r^2) + ... )

More explicitly, in spherical coordinates r = r(sin theta cos phi, sin theta sin phi, cos theta):

    ds^2_B = (1/4) (dr^2 / (1 - r^2) + r^2(d theta^2 + sin^2 theta d phi^2))

Note the (1 - r^2)^{-1} divergence as r -> 1 (approaching pure states): the Bures metric becomes singular at the boundary of the Bloch ball, reflecting the fact that pure states are "infinitely far" from nearby mixed states in an information-geometric sense.

**At the center** (r = 0): ds^2_B = (1/4)(dr^2 + 0) — the angular part vanishes because the maximally mixed state has full rotational symmetry.

**At the boundary** (r = 1): ds^2_B agrees with ds^2_{FS} = (1/4)(d theta^2 + sin^2 theta d phi^2) in the angular directions, recovering the Fubini-Study metric for pure states.

### 4.5 Scalar Curvature

The Bures metric on the qubit state space (3D Bloch ball) has scalar curvature:

    R_scalar = (3/4)(3 - r^2) / (1 - r^2)^2

which diverges as r -> 1 and equals R = 9/4 at the center.

---

## 5. Relation to Classical Fisher Information

### 5.1 Classical Fisher Information

For a probability distribution p(x|theta) depending on parameter theta:

    J_C(theta) = sum_x p(x|theta) (partial_theta log p(x|theta))^2
               = sum_x (partial_theta p(x|theta))^2 / p(x|theta)

### 5.2 Quantum-Classical Connection

For a quantum state rho(theta) and measurement POVM {E_x}:

    J_C(theta; {E_x}) <= J_Q(theta) = Tr(rho L^2)

where J_C depends on the measurement choice but J_Q is measurement-independent.

**Quantum Cramer-Rao bound**:

    Var(theta_hat) >= 1 / (n J_Q(theta))

for any unbiased estimator theta_hat from n copies.

### 5.3 Optimal Measurement

The quantum CRB is achievable: there exists a POVM (the eigenstates of L) that saturates J_C = J_Q. For multiple parameters, simultaneous saturation requires [L_mu, L_nu] = 0 (not always possible).

---

## 6. Geodesics on State Space

### 6.1 Geodesics on CP^d (Fubini-Study)

Great circles: |psi(t)> = cos(t)|psi_0> + sin(t)|psi_perp>

where <psi_0|psi_perp> = 0. These are geodesics with constant speed ||d psi/dt||_{FS} = 1.

The geodesic distance is d_{FS} = arccos|<psi_0|psi_1>|.

### 6.2 Geodesics on D(C^d) (Bures)

The Bures geodesic from rho_0 to rho_1 is:

    rho(t) = ((1-t) sqrt(rho_0) + t M)((1-t) sqrt(rho_0) + t M)^dagger / N(t)^2

where M = sqrt(rho_0)^{-1} sqrt(sqrt(rho_0) rho_1 sqrt(rho_0)) (when rho_0 is full rank) and N(t) ensures trace normalization.

For qubits (full rank), the geodesic in Bloch coordinates traces a curve that is generally NOT a straight line through the ball (it curves outward due to the non-Euclidean metric).

### 6.3 Geodesics for Quantum Channels

On the space of CPTP maps, one can define a Bures-like metric via the Choi isomorphism. The geodesic structure is much more complex and generally requires numerical computation.

---

## 7. Quantum Speed Limits

The Fubini-Study and Bures metrics give fundamental bounds on how fast quantum states can evolve.

### 7.1 Mandelstam-Tamm Bound

For unitary evolution under Hamiltonian H:

    t >= d_{FS}(|psi_0>, |psi_t>) / Delta_E

where Delta_E = sqrt(<H^2> - <H>^2) is the energy uncertainty.

For orthogonal states (d_{FS} = pi/2):

    t_perp >= pi / (2 Delta_E)

### 7.2 Margolus-Levitin Bound

    t >= d_{FS} / (<H> - E_0)

where E_0 is the ground state energy.

### 7.3 Unified Bound (mixed states, Bures)

    t >= d_B(rho_0, rho_t) / sqrt(J_Q / 4)

where J_Q is the quantum Fisher information with respect to the evolution parameter.

---

## 8. Wigner-Yanase Skew Information

**Definition**: I(rho, K) = -(1/2) Tr([sqrt(rho), K]^2) where K is an observable.

Properties:
- 0 <= I(rho, K) <= Var(K)
- I(rho, K) = 0 iff [rho, K] = 0
- I(rho, K) = Var(K) for pure states
- Convex in rho: I(sum p_i rho_i, K) <= sum p_i I(rho_i, K)

**Connection to metric**: The Wigner-Yanase information defines another Riemannian metric on state space (different from Bures). It belongs to the Petz family of monotone metrics, all of which satisfy:

    g^f_{mu nu} = (1/2) Tr(partial_mu rho . c_f(L_rho, R_rho)^{-1}(partial_nu rho))

where L_rho(X) = rho X, R_rho(X) = X rho, and c_f is a function satisfying certain monotonicity conditions (Petz 1996). The Bures metric corresponds to c_f(x,y) = (x+y)/2 and the Wigner-Yanase metric to c_f(x,y) = (sqrt(x) + sqrt(y))^2 / 4.
