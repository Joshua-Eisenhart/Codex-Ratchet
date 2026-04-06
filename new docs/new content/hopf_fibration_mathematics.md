# Hopf Fibration Mathematics and Quantum Information

## References: Mosseri & Dandoloff (2001), Urbantke (2003), Bernevig & Chen (2003)

---

## 1. The First Hopf Map: S^1 -> S^3 -> S^2

### 1.1 Construction

S^3 sits in C^2 as {(z_1, z_2) : |z_1|^2 + |z_2|^2 = 1}.

The Hopf map pi: S^3 -> S^2 is:

    pi(z_1, z_2) = (2 Re(z_1 z_2*), 2 Im(z_1 z_2*), |z_1|^2 - |z_2|^2)

Let x = 2 Re(z_1 z_2*), y = 2 Im(z_1 z_2*), z = |z_1|^2 - |z_2|^2. Then:

    x^2 + y^2 + z^2 = (2 Re(z_1 z_2*))^2 + (2 Im(z_1 z_2*))^2 + (|z_1|^2 - |z_2|^2)^2
                     = 4|z_1|^2|z_2|^2 + |z_1|^4 - 2|z_1|^2|z_2|^2 + |z_2|^4
                     = (|z_1|^2 + |z_2|^2)^2
                     = 1

So the image is indeed on S^2.

### 1.2 Quantum Mechanical Meaning

The Hopf map IS the qubit state map. Given |psi> = z_1|0> + z_2|1> (normalized), the Hopf image is the Bloch vector:

    n = <psi|sigma|psi> = (2 Re(z_1 z_2*), 2 Im(z_1 z_2*), |z_1|^2 - |z_2|^2)

The fiber over each point n in S^2 is the set of all state vectors mapping to the same physical state:

    pi^{-1}(n) = {e^{i alpha} |psi_n> : alpha in [0, 2pi)} = S^1

This S^1 is the global phase.

### 1.3 Explicit Fiber Description

Over the point (theta, phi) on S^2 (in spherical coordinates):

    pi^{-1}(theta, phi) = {e^{i alpha} (cos(theta/2), e^{i phi} sin(theta/2)) : alpha in [0, 2pi)}

Over the north pole (theta = 0): fiber = {e^{i alpha} (1, 0)}.
Over the south pole (theta = pi): fiber = {e^{i alpha} (0, e^{i phi})}.
Over the equator (theta = pi/2): fiber = {e^{i alpha} (1/sqrt(2), e^{i phi}/sqrt(2))}.

---

## 2. Connection and Curvature

### 2.1 Connection 1-Form

The natural connection on the Hopf bundle is:

    A = Im(z_1* dz_1 + z_2* dz_2) = (i/2)(z_1* dz_1 - z_1 dz_1* + z_2* dz_2 - z_2 dz_2*)

This is the Berry connection. In the qubit parametrization:

    A = -sin^2(theta/2) d phi + (1/2) d alpha

where alpha is the fiber coordinate (global phase).

The horizontal component (projected to the base S^2):

    A_hor = -sin^2(theta/2) d phi = -(1/2)(1 - cos theta) d phi

This is exactly the gauge potential of a magnetic monopole of charge 1/2 at the center of S^2.

### 2.2 Curvature

    F = dA = (1/2) sin theta d theta wedge d phi

This is the area form on S^2 (divided by 2), proportional to the Berry curvature.

**First Chern number**:

    c_1 = (1/(2 pi)) integral_{S^2} F = (1/(2 pi)) . (1/2) . 4 pi = 1

This topological invariant classifies the Hopf bundle as non-trivial. It cannot be continuously deformed to a product S^2 x S^1.

### 2.3 Holonomy = Berry Phase

For a closed curve C on S^2 enclosing solid angle Omega:

    gamma = integral_C A = -(1/2) integral_C (1 - cos theta) d phi = -Omega/2

This is the Berry phase. Under transport around a loop, the fiber phase shifts by -Omega/2.

---

## 3. Nested Tori Structure

### 3.1 Inverse Images of Latitude Circles

Consider a circle at latitude eta on S^2 (where eta in [-pi/2, pi/2], eta = 0 is equator). Its inverse image under pi is a torus T_eta in S^3.

**Parametrization of T_eta**:
The circle at latitude eta on S^2 has:
    z = sin(eta), sqrt(x^2 + y^2) = cos(eta)

The fiber over this circle is:

    (z_1, z_2) = (cos(eta/2 + pi/4) e^{i alpha}, sin(eta/2 + pi/4) e^{i(alpha + phi)})

Wait, let me be more careful. At colatitude theta (where sin eta = cos theta, so theta = pi/2 - eta):

    z_1 = cos(theta/2) e^{i alpha} = cos((pi/4 - eta/2)) e^{i alpha}
    z_2 = sin(theta/2) e^{i(phi + alpha)} = sin((pi/4 - eta/2)) e^{i(phi + alpha)}

As alpha and phi range over [0, 2pi), this traces out a torus T^2 in S^3.

### 3.2 Torus Radii

Embedding S^3 in R^4 via (x_1, y_1, x_2, y_2) where z_k = x_k + i y_k:

The torus at latitude eta (colatitude theta) has:
- |z_1| = cos(theta/2) = major circle in the (x_1, y_1) plane
- |z_2| = sin(theta/2) = major circle in the (x_2, y_2) plane

So:
    R_1 = cos(theta/2)  (radius in z_1 plane)
    R_2 = sin(theta/2)  (radius in z_2 plane)

with R_1^2 + R_2^2 = 1.

### 3.3 Clifford Torus

At theta = pi/2 (equator of S^2, eta = 0):

    R_1 = R_2 = 1/sqrt(2)

This is the **Clifford torus**: the unique flat torus in S^3 that divides S^3 into two congruent solid tori.

Properties:
- Zero extrinsic curvature in S^3 (flat embedding)
- Minimal surface in S^3 (area = 2 pi^2)
- Self-dual under the Hopf map symmetry
- The two solid tori correspond to the "northern" and "southern" hemispheres of the base S^2

**Quantum significance**: The Clifford torus is where |z_1|^2 = |z_2|^2 = 1/2, meaning both basis states have equal probability. It is the equator of the Bloch sphere — maximally superposed states.

### 3.4 Decomposition of S^3

S^3 is foliated by the family of tori {T_theta : theta in (0, pi)} plus two degenerate circles:
- theta = 0: T_0 degenerates to a circle (|z_2| = 0)
- theta = pi: T_pi degenerates to a circle (|z_1| = 0)

These two circles are the fibers over the north and south poles of S^2. They are linked once in S^3 (Hopf link). The linking number of ANY two fibers is 1 — this is a topological invariant of the Hopf fibration.

---

## 4. Stereographic Projection and Visualization

### 4.1 Stereographic Projection of S^3 to R^3

Projecting from the point (0,0,0,-1) in S^3 subset R^4:

    (x_1, y_1, x_2, y_2) -> (x_1, y_1, x_2) / (1 + y_2)

Under this projection:
- The degenerate fiber at theta = 0 maps to a circle in the (x_1, y_1) plane.
- The degenerate fiber at theta = pi maps to the y_2 axis (a line through infinity, i.e., a circle through the point at infinity).
- Each torus T_theta maps to a torus in R^3.
- The Clifford torus maps to a standard-looking torus.

All fibers (circles in S^3) project to circles in R^3 (stereographic projection preserves circles).

### 4.2 Linked Fibers

Any two fibers (circles) of the Hopf fibration are linked exactly once. This linking number is the first Chern number c_1 = 1.

**Proof**: Consider two fibers over points p, q in S^2. They bound disks in S^3 (the preimages of arcs from p and q to the south pole). The linking number equals the intersection number of one fiber with the disk bounded by the other, which equals the degree of the Hopf map = 1.

---

## 5. S^7 -> S^4: The Second Hopf Fibration and 2-Qubit States

### 5.1 Construction

S^7 sits in C^4 = H^2 (H = quaternions) as {(q_1, q_2) : |q_1|^2 + |q_2|^2 = 1}.

The second Hopf map pi_2: S^7 -> S^4 is the quaternionic analog:

    pi_2(q_1, q_2) = (2 Re(q_1 q_2*), 2j_1(q_1 q_2*), 2j_2(q_1 q_2*), 2j_3(q_1 q_2*), |q_1|^2 - |q_2|^2)

where j_1, j_2, j_3 are the imaginary quaternion components.

Fiber: S^3 (unit quaternions acting on the right: (q_1, q_2) -> (q_1 u, q_2 u) for |u| = 1).

### 5.2 Two-Qubit States and the 7-Sphere

A normalized 2-qubit state |Psi> = a|00> + b|01> + c|10> + d|11> lives on S^7 subset C^4 (with the overall phase giving S^7/S^1 = CP^3).

The entanglement structure creates a more refined fibration:

    S^7 -> S^4 (second Hopf map, via quaternionic structure)

but the physically relevant fibration for 2 qubits is:

    S^1 -> S^7 -> CP^3 (first Hopf-like, removing overall phase)

with CP^3 further decomposing based on entanglement.

### 5.3 Entanglement-Sensitive Fibration (Mosseri & Dandoloff)

For a 2-qubit pure state, write:

    |Psi> = (z_1, z_2, z_3, z_4) in S^7

Define two quaternions:
    q_A = z_1 + z_2 j,  q_B = z_3 + z_4 j

The concurrence is:
    C = 2|z_1 z_4 - z_2 z_3| = 2|det(Z)|

where Z = [[z_1, z_2], [z_3, z_4]].

**Key result (Mosseri & Dandoloff 2001)**: The second Hopf map naturally encodes the entanglement. The base point in S^4 determines the entanglement class, while the fiber (S^3) determines the local unitary equivalence class.

Specifically, the S^4 base decomposes as:
- North pole: product states (C = 0)
- South pole: maximally entangled (C = 1)
- Latitude determines concurrence

### 5.4 Fibration Structure by Entanglement

The full picture:

    S^1 --> S^7 --> CP^3
                     |
                     | (entanglement map)
                     v
                  [0, 1] (concurrence)

The preimage of C = 0 in CP^3 is the Segre embedding CP^1 x CP^1 subset CP^3 (product states).
The preimage of C = 1 is a single CP^1 (maximally entangled states, up to local unitaries).

---

## 6. Higher Hopf Maps

### 6.1 The Three Hopf Fibrations

    S^0 -> S^1 -> S^1  (real, trivial)
    S^1 -> S^3 -> S^2  (complex, 1-qubit)
    S^3 -> S^7 -> S^4  (quaternionic, 2-qubit)
    S^7 -> S^15 -> S^8 (octonionic, beyond standard QM)

These correspond to the four normed division algebras: R, C, H, O.

The first three are the ONLY fiber bundles with spheres as total space, fiber, and base (Adams theorem 1960).

### 6.2 Connection to Entanglement Classification

The hierarchy of Hopf maps provides a natural framework for entanglement classification:
- 1 qubit: S^1 -> S^3 -> S^2 (Bloch sphere)
- 2 qubits: Uses S^3 -> S^7 -> S^4 structure
- 3 qubits: No Hopf map available; entanglement classification becomes much more complex (GHZ vs W classes, continuous invariants)

---

## 7. Berry Phase from Hopf Geometry

### 7.1 Geometric Phase as Holonomy

The Berry phase acquired by a qubit state under adiabatic transport around a loop C on the Bloch sphere:

    gamma_B = -Omega(C)/2

where Omega is the solid angle. This follows directly from the Hopf fibration:

The connection 1-form A = -(1/2)(1 - cos theta) d phi has curvature F = (1/2) sin theta d theta wedge d phi.

By Stokes: gamma = integral_C A = integral_S F = (1/2) integral_S sin theta d theta d phi = Omega/2.

(Sign depends on orientation convention.)

### 7.2 Non-Abelian Berry Phase for Multi-Level Systems

For degenerate subspaces (n-fold degeneracy), the Berry connection becomes a U(n) gauge field:

    [A_mu]_{ab} = <psi_a|partial_mu|psi_b>

The holonomy is a unitary matrix (not just a phase):

    U = P exp(integral_C A . d lambda)

where P denotes path-ordering. This is a non-abelian generalization.

For 2-qubit systems, the relevant gauge group is U(2) acting on the entanglement fiber.

---

## 8. Stereographic and Hopf Coordinates for Computation

### 8.1 Hopf Coordinates on S^3

    (z_1, z_2) = (cos(xi) e^{i eta_1}, sin(xi) e^{i eta_2})

where xi in [0, pi/2], eta_1, eta_2 in [0, 2pi).

The Hopf map in these coordinates:
    theta = 2 xi  (colatitude on S^2)
    phi = eta_2 - eta_1  (azimuth on S^2)
    alpha = eta_1  (fiber coordinate)

Round metric on S^3:
    ds^2_{S^3} = d xi^2 + cos^2(xi) d eta_1^2 + sin^2(xi) d eta_2^2

In Hopf coordinates (theta, phi, alpha):
    ds^2_{S^3} = (1/4)(d theta^2 + sin^2 theta d phi^2 + (d alpha + cos theta d phi)^2)

The first two terms = (1/4) ds^2_{S^2} (the base metric).
The third term = (d alpha + A)^2 (the fiber + connection piece).

This is the canonical form of a principal U(1) bundle metric.

### 8.2 Volume Forms

    Vol(S^3) = 2 pi^2  (total volume)

Decomposed via the fibration:
    Vol(S^3) = Vol(S^1) x Vol(S^2) x (twist factor)
             = 2 pi x 4 pi x (1/(4 pi))  ... 

Actually the decomposition is: integrating the fiber direction gives 2pi, and the base volume is pi (the FS area of CP^1), giving 2pi x pi = 2pi^2. Correct.

---

## 9. Topological Invariants

### 9.1 Homotopy Groups

    pi_3(S^2) = Z  (generated by the Hopf map)
    pi_7(S^4) = Z  (generated by the second Hopf map)
    pi_15(S^8) = Z  (generated by the third Hopf map)

These are the only cases where pi_{2n-1}(S^n) = Z.

### 9.2 Hopf Invariant

For a map f: S^{2n-1} -> S^n, the Hopf invariant H(f) in Z is defined by:

If alpha = f*(omega) where omega generates H^n(S^n), then alpha wedge alpha = H(f) . vol_{S^{2n-1}}.

For the Hopf maps: H = 1. By Adams' theorem (1960), maps with H = 1 exist only for n = 1, 2, 4, 8.

### 9.3 Linking Number Interpretation

The Hopf invariant of pi: S^3 -> S^2 equals the linking number of pi^{-1}(p) and pi^{-1}(q) for any two regular values p, q in S^2. This linking number is 1 for the Hopf map.
