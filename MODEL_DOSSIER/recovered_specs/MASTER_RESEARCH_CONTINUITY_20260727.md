# Constraint–Geometry Research Continuity

**Preservation date:** 2026-07-27  
**Document type:** cumulative continuity record  
**Scope:** the finite mathematics model, Ratchet, ordered-deformation manifold, ring/checkerboard geometry, engine degrees of freedom, engine fields, ConstraintBox/ClaimGate, simulation architecture, and the bounded program for major mathematics and science problems  
**Authority:** this document preserves and organizes work; it does not canonize model-generated prose or promote bounded simulations into proofs

## 1. Reading rules

This research has repeatedly been damaged by flattening distinct objects into one smooth story. The following labels are mandatory:

| Label | Meaning |
|---|---|
| **OWNER STATEMENT** | A current statement or correction made by Joshua Eisenhart. |
| **FORMALIZATION** | A precise mathematical representation proposed for an owner statement. It remains replaceable. |
| **EXECUTED — BOUNDED** | Code ran on the declared finite carrier and supports only the stated result. |
| **DERIVED CANDIDATE** | A mathematical consequence conditional on the chosen formalization. |
| **OPEN RIVAL** | A serious alternative retained for comparison. |
| **NEGATIVE RESULT** | An attempted implication or mechanism that failed a declared test. |
| **UNTESTED** | Described but not executed. |
| **SUPERSEDED** | Preserved for provenance but not current. |

The authority order is:

1. current owner correction;
2. attributable owner text;
3. freshly executed code and independently inspectable evidence, within its claim ceiling;
4. current repository material consistent with 1–3;
5. older repository versions and prior continuity packs;
6. LLM output as proposals, rivals, and test fuel.

### 1.1 Current owner supersessions

The following corrections govern this pack even where preserved older
documents disagree.

#### Engine loops

The current cyclic traversal classes are:

\[
[\ell_{\mathrm{ind}}]_{\mathrm{cyc}}
=
[(S_e,S_i,N_i,N_e)]_{\mathrm{cyc}},
\]

\[
[\ell_{\mathrm{ded}}]_{\mathrm{cyc}}
=
[(N_e,N_i,S_i,S_e)]_{\mathrm{cyc}}.
\]

A cyclic rotation changes only the chosen entry point:

\[
(x_0,x_1,x_2,x_3)
\sim_{\mathrm{cyc}}
(x_k,x_{k+1},x_{k+2},x_{k+3}).
\]

The loops therefore have no intrinsic first stage. Observation-first and
theory-first scientific procedures may select convenient entry points without
changing the underlying loop.

Older schedules such as
`Ne → Si → Se → Ni`, `Ne → Ni → Se → Si`,
`Se → Ne → Ni → Si`, and `Se → Si → Ni → Ne` remain in preserved source
documents as provenance. They are not current authority.

#### Four topologies, eight terrains, sixteen placements

The current structural requirement is:

\[
4\text{ local flow topologies}
\times
2\text{ flux orientations}
=
8\text{ flux-bearing terrains},
\]

followed by

\[
8\text{ terrains}
\times
2\text{ precedence/sign states}
=
16\text{ engine placements}.
\]

The four candidate formal flow classes are:

1. dissipative outward transport;
2. attracting relaxation;
3. Hamiltonian orbit circulation;
4. invariant-subspace stratification.

Write them as

\[
\mathfrak T
=
\{\mathcal G_{\mathrm{out}},
\mathcal G_{\mathrm{sink}},
\mathcal G_{\mathrm{orb}},
\mathcal G_{\mathrm{strat}}\}.
\]

The eight flux-bearing terrains are indexed by

\[
\mathcal T_{a,\chi},
\qquad
a\in\{1,2,3,4\},
\quad
\chi\in\{-1,+1\},
\]

with an orientation-sensitive record

\[
\Phi_{a,\chi}
=
\chi\int_{\Sigma_a}F_a.
\]

This indexing preserves the current structural statement. The unique
generator and physical realization of every class remain open to tournament.

#### Axis 6

Axis 6 is not composition order alone. It specifies:

1. operator-first versus terrain-first composition; and
2. a corresponding operator-sign reversal.

A sign-neutral formal placeholder is:

\[
\Psi^{\uparrow}_{a,\chi}
=
\Phi_{a,\chi}\circ
\mathcal O^{\sigma_\uparrow}_{a,\chi},
\]

\[
\Psi^{\downarrow}_{a,\chi}
=
\mathcal O^{\sigma_\downarrow}_{a,\chi}
\circ\Phi_{a,\chi},
\]

subject to

\[
\sigma_\uparrow=-\sigma_\downarrow.
\]

The owner correction establishes the reversal. It does not, in the sources
available to this pack, uniquely establish which arrow receives the positive
sign for every operator family. That binding must be stated explicitly and
tested rather than guessed.

The user’s informal labels may appear in explanatory crosswalks. Formal object names and equations do not depend on those labels.

---

## 2. The central object

### 2.1 Three views of one finite process

**OWNER STATEMENT**

1. The flat, recursively nested checkerboard is the Ratchet view.
2. The checkerboard curving upward is the manifold view.
3. When the curvature closes into a sphere, that closed geometry is the spinning-ring realization. The rings are the operational engine view.
4. These are positions along one geometric–entropic gradient, not three unrelated metaphors.

The model begins with a finite possibility carrier. Ordered constraints deform it. The deformations create new admissible structures, new invariants, new geometries, and new entropies. At sufficient depth, residual cyclic degrees of freedom may support engine dynamics. Those dynamics may then create records, histories, fields, and further constraint material.

The dependency is:

\[
\boxed{
\text{finite possibility carrier}
\xrightarrow{\text{ordered constraints}}
\text{nested deformed carrier}
\xrightarrow{\text{residual cyclic degrees}}
\text{engine dynamics}
\xrightarrow{\text{records and coupling}}
\text{new effective geometry and entropy}
}
\]

This is a research program, not an already-established theorem.

### 2.2 What “geometry and entropy are one” means here

At the base, the same finite structure has two readings:

- geometrically: which alternatives, adjacencies, identifications, boundaries, and extensions exist;
- entropically: how many alternatives remain available at the declared resolution.

An ordered deformation changes both at once. Removing a face from a finite cell complex, for example, can create a new homology class and increase the Hartley capacity of that homology group. The geometry and the capacity are not two unrelated outputs; they are two invariants of the same finite deformation.

Later layers license different entropy functionals. They must remain typed. Hartley capacity, Shannon entropy, von Neumann entropy, relative entropy, conditional entropy, coherent information, entropy production, and path entropy are not interchangeable scalars.

---

## 3. Finite numerical frames

### 3.1 Numbers require a declared finite carrier

**OWNER STATEMENT**

A number is not used before the finite field of representable possibilities has been specified. A computation requires:

- a finite number of possible encodings;
- an origin;
- a resolution;
- a scale or span;
- a representation rule;
- explicit maps when the carrier grows or when values move between carriers.

There is no operational infinity inside a completed computation. A continuum may be a limiting construction or an external mathematical ideal, but every actual run occupies a finite declared frame.

### 3.2 Formal numerical frame

**FORMALIZATION**

Define a finite numerical frame

\[
\mathfrak F
=
(X,o,\delta,\nu),
\qquad
|X|=2^n<\infty,
\]

where:

- \(X\) is the finite set of encodings;
- \(o\in X\) is the chosen origin;
- \(\delta>0\) is the resolution;
- \(\nu:X\to\mathbb R\) is an interpretation map used only after the frame is declared.

One common signed fixed-point interpretation is

\[
\nu(x)=a+\delta\,q(x),
\]

where \(q:X\to\mathbb Z\) is a chosen integer code and \(a\) fixes the interpreted origin.

The possibility count and its bit scale are

\[
N(\mathfrak F)=|X|=2^n,
\qquad
S_0(\mathfrak F)=\log_2|X|=n.
\]

Here \(N\) is the count of encodings and \(S_0\) is its Hartley/Rényi-0 capacity in bits.

### 3.3 Frame growth

A larger carrier does not appear without a map. Growth is:

\[
\iota_{n,m}:\mathfrak F_n\hookrightarrow\mathfrak F_m,
\qquad
m>n,
\]

with explicit obligations:

\[
\iota_{n,m}(o_n)=o_m,
\]

\[
\nu_m\!\left(\iota_{n,m}(x)\right)=\nu_n(x)
\quad\text{or an explicitly declared approximation},
\]

and a stated treatment of resolution, overflow, rounding, and unused encodings.

Cross-frame arithmetic is undefined until an embedding or reconciliation map is declared.

### 3.4 Magnitude of zero

**OWNER DIRECTION; FORMALIZATION OPEN**

Zero is not treated as a universally context-free atom. A zero result can encode the magnitude and structure of what was collapsed by a map.

For a finite map

\[
q:X\to Y,
\]

define the fibre over \(y\in Y\):

\[
q^{-1}(y)=\{x\in X:q(x)=y\}.
\]

A candidate finite “magnitude of zero” descriptor at \(y\) is the fibre-capacity vector

\[
\mathbf z_q(y)
=
\left(
|q^{-1}(y)|,\,
\log_2|q^{-1}(y)|,\,
\operatorname{rank}D_y,\,
\beta_\bullet(K_y),\,
\ldots
\right),
\]

where \(D_y\) and \(K_y\) are declared history and geometric structures on that fibre. This is not ordinary division by zero. It is a set- or structure-valued release operation describing what a quotient or singular map merged.

Any proposed arithmetic such as “\(1/0\) returns a field” must therefore be expressed as a new typed operation:

\[
\mathcal R_q(y)=q^{-1}(y)
\quad\text{or}\quad
\mathcal R_q(y)=\text{an invariant object constructed from }q^{-1}(y),
\]

not as a claim that ordinary field division has changed its standard meaning.

---

## 4. The finite Ratchet

### 4.1 Input contract

At round \(r\), let:

\[
\mathcal K_r
=
\left(
D_r,\,
P_r,\,
\mathcal C_r,\,
\{\preceq_{r,a}\}_{a\in A_r},\,
\mathcal H_r
\right),
\]

where:

- \(D_r\) is a finite set of demanded distinctions;
- \(P_r\) is a finite probe family;
- \(\mathcal C_r\) is a finite candidate family;
- \(\preceq_{r,a}\) are declared partial orders of presumption;
- \(\mathcal H_r\) is the retained history and obstruction record.

A candidate \(c\) induces an observational partition

\[
\pi_c
=
\{[x]_{c,P_r}:x\in X_r\},
\]

where

\[
x\sim_{c,P_r}y
\iff
\forall p\in P_r,\;p(c,x)=p(c,y).
\]

### 4.2 Demand loss

For demanded pairs \(D_r\subseteq X_r\times X_r\), define

\[
L_{D_r}(\pi_c)
=
\sum_{(x,y)\in D_r}
\mathbf 1\!\left([x]_{\pi_c}=[y]_{\pi_c}\right).
\]

The admissible survivors are

\[
\mathcal S_r
=
\{c\in\mathcal C_r:L_{D_r}(\pi_c)=0\}.
\]

No demand means no discrimination:

\[
D_r=\varnothing
\quad\Longrightarrow\quad
\text{HOLD},
\]

not an invented preference.

### 4.3 Minimal sufficient structure

Under partition refinement,

\[
\pi_a\preceq\pi_b
\iff
\forall B\in\pi_a\;\exists C\in\pi_b\text{ such that }B\subseteq C.
\]

The desired frontier is the set of coarsest demand-preserving survivors:

\[
\mathcal F_r
=
\left\{
c\in\mathcal S_r:
\nexists c'\in\mathcal S_r
\text{ with }
\pi_c\prec\pi_{c'}
\right\}.
\]

When survivors are incomparable under one or more declared orders, they remain plural. The Ratchet does not invent a scalar score to force a winner.

MSS is relative to the candidate packet, demand, probes, and partial order. It is not an unrestricted proof of an absolutely minimal ontology.

### 4.4 Nested comparison

A manifold candidate is a compatible tower:

\[
\mathcal T
=
(X_0,X_1,\ldots,X_R;
\rho_{1,0},\rho_{2,1},\ldots,\rho_{R,R-1}),
\]

with

\[
\rho_{r+1,r}:X_{r+1}\to X_r
\]

and compatibility constraints

\[
C_r(X_{\le r})=1.
\]

A layer is not compared in isolation when its meaning depends on the tower. Its observable content is a projection:

\[
X_r^\ast=\Pi_r(\mathcal T).
\]

Flat comparison of two isolated layers is invalid unless a declared forgetful functor makes it valid.

### 4.5 Ratchet output

Each round returns a vector, not a story:

\[
\Delta_r
=
(\text{survivors},\,
\text{defeats},\,
\text{incomparables},\,
\text{obstructions},\,
\text{unmet demands},\,
\text{next finite obligations}).
\]

If no new finite obligation is earned, the correct transition is HOLD.

---

## 5. The ordered-deformation manifold

### 5.1 Core thesis

**OWNER STATEMENT**

The nested manifold is generated by ordered deformations of a finite maximum-capacity Hartley/Rényi-0 base. Each earned deformation constrains the carrier and licenses a new class of mathematics, geometry, and entropy. The order of deformations is content.

### 5.2 Formal deformation chain

Let

\[
\mathcal M_0=\mathfrak F_n
\]

be the finite base. A candidate tower is

\[
\mathcal M_r
=
\mathcal D_r\circ\mathcal D_{r-1}\circ\cdots\circ\mathcal D_1(\mathcal M_0).
\]

Two orderings are equivalent only if an explicit natural equivalence or conjugacy is exhibited:

\[
\mathcal D_i\circ\mathcal D_j
\cong
\mathcal D_j\circ\mathcal D_i.
\]

Order is load-bearing when

\[
[\mathcal D_i,\mathcal D_j](\mathcal M)
:=
\mathcal D_i\!\circ\mathcal D_j(\mathcal M)
-
\mathcal D_j\!\circ\mathcal D_i(\mathcal M)
\ne0
\]

under an admitted finite discriminator.

Grouping is load-bearing when the associator

\[
\alpha(\mathcal D_i,\mathcal D_j,\mathcal D_k)
=
(\mathcal D_i\circ\mathcal D_j)\circ\mathcal D_k
-
\mathcal D_i\circ(\mathcal D_j\circ\mathcal D_k)
\]

is nonzero after the effective reductions actually used by the model.

Noncommutation does not imply nonassociativity.

### 5.3 Earned layer criterion

A deformation earns a layer only if:

1. it is well-defined on the previous layer;
2. its compatibility map is explicit;
3. at least one new invariant becomes computable;
4. deleting it changes a demanded invariant after all allowed refits;
5. no declared redundancy map reproduces the same change;
6. relevant rival orderings have been retained or killed by finite witnesses.

Coordinate changes, relabelings, and conjugations that create no new invariant are gauge, not new layers.

### 5.4 Candidate deformation ladder

This is a likely ordering and a test plan, not a settled canon.

| Rung | Formal deformation | New mathematical carrier | Newly licensed geometry | Newly licensed entropy/information | Required negative |
|---:|---|---|---|---|---|
| 0 | none | finite set \(X\), \(|X|=2^n\) | finite incidence without metric | \(S_0(X)=\log_2|X|\) | no probabilities or continuum imported |
| 1 | probe quotient | \(X/{\sim_P}\) | partition lattice, quotient incidence, fibre geometry | class and fibre capacities | change labels while preserving probes; result must not change |
| 2 | extension structure | fibres \(\operatorname{Ext}(y)\) and restriction maps | presheaf-like finite extension geometry | \(\log_2|\operatorname{Ext}(y)|\) | no holonomy unless transition maps are invertible |
| 3 | weighting | probability simplex \(\Delta^{d-1}\) | Fisher information geometry | Shannon, classical Rényi, KL divergence | unweighted carrier must not gain Shannon entropy |
| 4 | complex linear carrier | finite-dimensional Hilbert space and density cone | convex state geometry, rank strata | rank Rényi-0, von Neumann, Umegaki relative entropy | basis relabeling must be gauge |
| 5 | projectivization and phase quotient | rays in \(\mathbb{CP}^{d-1}\) | Fubini–Study metric and quantum geometric tensor | pure-state spectral and geometric-phase invariants | global phase must be unobservable |
| 6 | tensor factorization and cuts | \(\mathcal H_A\otimes\mathcal H_B\) | cut lattice, Schmidt strata, entropy cone | mutual, conditional, coherent information; negativity as a monotone | no cut entropy before a cut exists |
| 7 | grading or double cover | graded Clifford module / spin representation | orientation and chirality bundle candidates | graded coherence and orientation-sensitive records | conjugate copies that add no discriminator are demoted |
| 8 | connection | principal or vector bundle with \(A\) and \(F=dA+A\wedge A\) | holonomy and curvature; nested-leaf relative flux | phase records; distributions over records only after readout | contractible-loop control must show the boundary of “flux requires nesting” |
| 9 | process | finite channels or semigroups | flow, fixed points, basins, currents | data-processing contraction and entropy production | a topological cycle with zero affinity must carry no current |
| 10 | history | path register \(D(j,k)\) | path-space and cycle-space geometry | path entropy, coherent-history distinguishability, full-counting statistics | dephasing must erase orientation information when it is coherence-only |
| 11 | effective reduction | Schur complement, coarse-graining, projection | effective nested geometry | information loss and retained sufficient statistics | exact unreduced composition must remain associative |
| 12 | bracketing-sensitive reduction | nonassociative effective composition if earned | associator geometry; exceptional algebra only as a rival | distribution of associator defects; spectral entropy if licensed | lossy projection must compete against octonionic explanations |
| 13 | field coupling | spatially indexed local generators \(x\mapsto G_x\) | bundle/graph field, defects, domains, transport | local production, transfer, path and field entropies | uncoupled and scrambled-topology controls |

The ladder is a directed acyclic candidate system, not necessarily one forced linear chain. Some deformations may commute; others may branch; some may be incomparable.

### 5.5 Entropy ordering without flattening

The universal support ordering on one declared density operator is:

\[
S_0(\rho)
\ge
S_\alpha(\rho)
\ge
S_\beta(\rho)
\ge
S_\infty(\rho),
\qquad
0\le\alpha\le\beta\le\infty.
\]

For the standard named members:

\[
S_0(\rho)=\log\operatorname{rank}\rho,
\]

\[
S_1(\rho)=-\operatorname{Tr}(\rho\log\rho),
\]

\[
S_2(\rho)=-\log\operatorname{Tr}(\rho^2),
\]

\[
S_\infty(\rho)=-\log\lambda_{\max}(\rho).
\]

This is not the nesting order of the whole manifold. It is an inequality family licensed after the density carrier exists. Earlier finite-set capacity and later cut, path, production, and record functionals occupy different types.

---

## 6. The checkerboard, curvature, sphere, and ring realization

### 6.1 The finite checkerboard

The checkerboard is a visual carrier for a finite recursively nested possibility system. Each cell at resolution \(r\) carries a finite fibre:

\[
\pi_r:E_r\to B_r,
\qquad
\pi_r^{-1}(x)\cong X_{r,x},
\qquad
|X_{r,x}|=2^{n_{r,x}}.
\]

The fibre may carry a history-pair matrix

\[
D_x(j,k)
=
\operatorname{Tr}
\left(
K_j\rho_xK_k^\dagger
\right).
\]

The diagonal terms encode history weights. The off-diagonal terms encode retained coherence between histories. A \(2^n\)-element history set gives a \(2^n\times2^n\) history-pair field, not merely a list of \(2^n\) probabilities.

### 6.2 Curvature as ordered constraint

The “board curving upward” is the visual representation of ordered deformation. It is not an extra sphere placed around a still-flat board.

A discrete version can use weighted cochains:

\[
d_k:C^k(K)\to C^{k+1}(K),
\]

\[
\mathcal D=d+d^\dagger,
\qquad
\Delta=\mathcal D^2.
\]

Changes in faces, identifications, weights, and transition maps change the Hodge decomposition:

\[
C^1
=
\operatorname{im}d_0
\oplus
\operatorname{im}d_1^\dagger
\oplus
\ker\Delta_1.
\]

The exact, coexact, and harmonic components provide finite discriminators for gradient settlement, local circulation, and global cycle degrees of freedom.

### 6.3 Closure

**OWNER STATEMENT**

When the upward curvature closes into a sphere, the closed sphere is equal to the ring model with spinning rings. The rings do not independently “become” a sphere; the sphere is the closed realization of the curved checkerboard, and spinning rings are its dynamic representation.

A candidate mathematical chart is the Hopf fibration:

\[
\pi:S^3\to S^2,
\]

\[
(z_1,z_2)
=
(\cos\eta\,e^{i\phi_1},
\sin\eta\,e^{i\phi_2}),
\]

whose regular leaves

\[
T_\eta
=
\{|z_1|=\cos\eta,\;|z_2|=\sin\eta\}
\]

are Clifford tori. This chart is a formal candidate for the ring realization; it does not by itself prove that the physical model must use Hopf geometry.

For a connection \(A\) with curvature \(F=dA\), a relative flux through an inter-leaf strip \(\Sigma_{\eta_1,\eta_2}\) is

\[
\Phi(\eta_1,\eta_2)
=
\int_{\Sigma_{\eta_1,\eta_2}}F
=
\oint_{C_{\eta_2}}A
-
\oint_{C_{\eta_1}}A.
\]

On the tested Hopf chart this becomes

\[
\Phi
=
2\pi
\left(
\sin^2\eta_{\mathrm{out}}
-
\sin^2\eta_{\mathrm{in}}
\right)
=
\pi
\left(
\cos2\eta_{\mathrm{in}}
-
\cos2\eta_{\mathrm{out}}
\right).
\]

The qualified statement is:

- noncontractible leaf loops need relative inter-leaf geometry for this flux;
- a contractible loop can bound a disk and carry flux without a second nested leaf;
- therefore “flux requires nesting” is true for the selected noncontractible leaf class, not universally.

---

## 7. Engine degrees of freedom

### 7.1 Loops have no intrinsic first stroke

**OWNER STATEMENT**

Engine traversals are loops. A scientific procedure may choose a preferred entry point, but the engine itself can be entered at any stage. The invariant content is cyclic order, orientation, composition order, and continuous state handoff.

For a cyclic word

\[
w=(G_0,G_1,\ldots,G_{m-1}),
\]

the \(k\)-shift

\[
\tau_k w
=
(G_k,G_{k+1},\ldots,G_{m-1},G_0,\ldots,G_{k-1})
\]

is the same unbased loop when only cyclic structure is observed. Reversal

\[
w^{-1}
=
(G_{m-1},\ldots,G_1,G_0)
\]

is generally different.

For the current four-stage classes:

\[
[\ell_{\mathrm{ind}}]_{\mathrm{cyc}}
=[(S_e,S_i,N_i,N_e)]_{\mathrm{cyc}},
\qquad
[\ell_{\mathrm{ded}}]_{\mathrm{cyc}}
=[(N_e,N_i,S_i,S_e)]_{\mathrm{cyc}}.
\]

The two classes traverse the same four labels in opposite cyclic direction.
The preferred beginning of a scientific procedure is an entry convention,
not a fifth engine degree of freedom.

### 7.2 Complete affine generator coordinates

For a qubit state

\[
\rho=\frac12(I+r\cdot\sigma),
\]

every trace-preserving, Hermiticity-preserving generator has

\[
\dot r=b+Ar.
\]

The matrix \(A\in\mathbb R^{3\times3}\) has the unique decomposition

\[
A=\Omega+\lambda I+S,
\]

\[
\Omega^\mathsf T=-\Omega,
\qquad
S^\mathsf T=S,
\qquad
\operatorname{tr}S=0.
\]

The full real parameter count is

\[
\underbrace{3}_{b}
+
\underbrace{3}_{\Omega}
+
\underbrace{1}_{\lambda}
+
\underbrace{5}_{S}
=12.
\]

These are formal local degrees of freedom:

| Component | Formal name | Geometric effect | Entropic effect |
|---|---|---|---|
| \(b\) | affine translation | displaces the stationary point | permits relaxation toward a noncentral state |
| \(\Omega\) | antisymmetric generator | tangent rotation | isospectral; von Neumann entropy preserved |
| \(\lambda I\) | scalar symmetric generator | isotropic radial contraction or dilation | direction-independent purity change |
| \(S\) | traceless symmetric generator | anisotropic contraction, shear, axis selection | direction-dependent production or contraction |

This decomposition exhausts the local affine generator space. It does not prove that four previously named flow families are uniquely selected. The bounded census found many valid mixtures and additional normal forms.

### 7.3 Minimum engine conditions

A cycle is only capacity. An engine requires:

\[
\boxed{
\text{cycle capacity}
+
\text{nonzero affinity}
+
\text{stationary current}
+
\text{load or task coupling}
}
\]

For a finite Markov network with stationary distribution \(\pi\) and rates \(k_{ij}\):

\[
J_{ij}=\pi_i k_{ij}-\pi_j k_{ji},
\]

\[
BJ=0,
\]

\[
J=\sum_\gamma j_\gamma c_\gamma,
\]

\[
\mathcal A_\gamma
=
\sum_{(i,j)\in\gamma}
\log\frac{k_{ij}}{k_{ji}},
\]

\[
\dot\Sigma
=
\sum_\gamma j_\gamma\mathcal A_\gamma
\ge0.
\]

Useful output requires an explicitly declared relation such as

\[
\sum_a\dot Q_a+\dot W=0.
\]

Without a load or task, the system is a driven circulating process, not yet a heat, work, or information engine.

### 7.4 How engine degrees can emerge

The currently defensible mechanism is:

1. ordered constraints create a finite residual cycle class;
2. a non-exact affinity cochain drives that class;
3. dynamics supplies nonzero current weights;
4. retained histories preserve order and orientation information;
5. a load turns circulation into an operational engine;
6. records feed new constraints into later Ratchet rounds.

The finite topology test established:

\[
\beta_1:0\to1\to0
\]

under filled-disk, puncture, and slit deformations, and

\[
S_0(H_1):0\to1\to0\text{ bit}.
\]

It also established the necessary negative:

\[
\text{cycle capacity}\not\Rightarrow\text{current}.
\]

The 512-candidate face tournament then found that the coarsest constraint system preserving one specifically demanded central circulation had:

\[
\dim H_1=1.
\]

With the weaker demand \(\beta_1\ge1\), nine incomparable one-hole survivors remained. The demand selected a cycle; the algorithm did not invent one.

### 7.5 Autonomous history cycles

For a primitive stationary quantum semigroup, the density operator may converge while quantum-jump histories retain nonzero cycle currents. Therefore an autonomous engine’s cyclic address can live in history space even when

\[
\dot\rho_{\mathrm{ss}}=0.
\]

The executed three-qubit absorption-machine scout used:

\[
H_0=\sum_{i=1}^{3}E_i n_i,
\]

\[
H_{\mathrm{int}}
=
g
\left(
|010\rangle\langle101|
+
|101\rangle\langle010|
\right),
\]

with

\[
E_2=E_1+E_3.
\]

Its history graph had eight vertices, twelve reservoir edges, and one coherent chord:

\[
\dim\ker B=13-7=6.
\]

The six reservoir orderings formed a cycle basis:

\[
J=\sum_{\pi\in S_3}j_\pi c_\pi.
\]

All six coefficients were positive in the productive regime. Equal temperatures, zero coherent coupling, and reversed gradients behaved as required controls.

This supports autonomous weighted cycle currents. It does not yet establish an explicit work load, an autonomous derivation of the proposed holonomy record, or survival of all sixteen sectors in the fully coupled model.

### 7.6 Cohomological affinity

The thermal cube alone had

\[
\beta_1=5
\]

but zero cycle affinity because the edge-affinity cochain was exact:

\[
a_{\mathrm{thermal}}=B^\mathsf T\phi.
\]

The coherent chord raised the cycle dimension to six and made the full cochain non-exact. The six cycle coordinates split into:

\[
\boxed{
\text{one driven chord-winding coordinate}
\oplus
\text{five zero-affinity ordering coordinates}.
}
\]

Entropy production detects the driven coordinate. Unequal cycle weights also contain kinetic information in the five ordering coordinates.

### 7.7 Sixteen conditional sectors

The local crossing

\[
4\text{ flow exemplars}
\times
2\text{ composition signs}
\times
2\text{ orientations}
\]

creates sixteen labels but only ten distinguishable local channels in the tested construction.

Adding a coherent two-history record:

\[
D_\chi
=
\frac12
\begin{pmatrix}
1&e^{i(-1)^\chi\Phi}\\
e^{-i(-1)^\chi\Phi}&1
\end{pmatrix}
\]

restored sixteen distinguishable sectors. Dephasing:

\[
D_\chi\mapsto\frac12I
\]

returned the count to ten. Opposite orientations differed only in off-diagonal terms.

Thus the current bounded result is:

\[
\text{local channel}
+
\text{ordered placement}
+
\text{coherent relative-history record}
\Longrightarrow
16\text{ distinguishable sectors}.
\]

The history record remains load-bearing and must be generated autonomously in the decisive experiment.

### 7.8 Thermodynamic analogues

Carnot, Otto, and Szilard engines are comparison structures, not literal identifications.

The useful shared grammar is:

- a finite cyclic word;
- alternating approximately isospectral and dissipative processes;
- at least two distinct potentials, reservoirs, or information stores;
- entropy/information accounting;
- a declared load or task;
- no intrinsic first stroke.

A literal temperature interpretation is unlicensed until a probability weighting and a Gibbs state are defined. At earlier layers, capacity gradients may play the analogous role, but they are not temperatures.

---

## 8. Engine fields

### 8.1 Definition

An engine field is a spatial or graph-indexed family of local finite generators:

\[
x\longmapsto G_x
=
\left(
b_x,\Omega_x,\lambda_x,S_x
\right),
\qquad x\in V(K),
\]

with coupling operators

\[
C_{xy}:\mathcal H_x\otimes\mathcal H_y
\to
\mathcal H_x\otimes\mathcal H_y
\]

on edges \((x,y)\in E(K)\).

A discrete field evolution can be written:

\[
\dot\rho_x
=
\mathcal L_x(\rho_x)
+
\sum_{y\sim x}
\mathcal C_{xy}(\rho_x,\rho_y).
\]

The field is not created by placing names on a grid. It requires:

- local physical generators;
- explicit coupling;
- boundary conditions;
- stability and complete-positivity checks where applicable;
- transport, defect, domain, and correlation observables;
- topology-scramble and uncoupled controls.

### 8.2 Candidate normal forms

Near a Hopf bifurcation, a complex amplitude field is often reduced to the complex Ginzburg–Landau equation:

\[
\partial_t A
=
\mu A
+
(1+ic_1)\nabla^2A
-
(1+ic_3)|A|^2A.
\]

This is a leading candidate normal form for collective engine-field phases, defects, and traveling structures. It assumes smooth amplitude, spatial scale separation, and continuum derivatives; those assumptions are not licensed at the finite base and must be earned by coarse-graining tests.

A finite graph alternative is:

\[
\dot A_x
=
\mu_x A_x
-
\sum_y L_{xy}A_y
-
\gamma_x|A_x|^2A_x,
\]

where \(L\) is a declared graph Laplacian.

### 8.3 Tape and machine

A finite computational layer may use:

- a finite tape carrier \(T\);
- a finite head state set \(Q\);
- a local transition map

\[
\delta:Q\times\Sigma\to Q\times\Sigma\times\{-1,+1\};
\]

- explicit periodic or twisted boundary conditions.

The transition system may be encoded in reversible Hamiltonian dynamics, stochastic channels, or finite state updates.

For a twisted cyclic tape:

\[
\psi(x+L)=U_{\mathrm{twist}}\psi(x).
\]

Candidate boundary classes include trivial periodic, exchange, conjugation, orientation-reversing, and antiperiodic twists. “Möbius-like” is a visual label; the formal object is the specified bundle holonomy \(U_{\mathrm{twist}}\).

The proposed tape–machine equivalence becomes a finite fixed-point problem only after the transition rule is itself represented as tape content:

\[
\Theta(M)=M.
\]

No mechanism has yet established that manifold depth forces this fixed point.

### 8.4 Oracles and demons

An oracle-like lookup over a precomputed fibre

\[
\operatorname{Ext}(y)
\]

is amortized computation, not free computation. The cost has moved into construction and maintenance of the fibre.

A demon-like selective instrument has:

\[
p(y|\rho)=\operatorname{Tr}(M_y\rho),
\qquad
\rho_y
=
\frac{K_y\rho K_y^\dagger}{p(y|\rho)}.
\]

Feedback may use \(y\), but record formation and erasure must be accounted separately. The typed entropy ledger prevents an information gain from being silently canceled by an unrelated entropy term.

---

## 9. ConstraintBox and ClaimGate

### 9.1 Purpose

ConstraintBox is the lean standalone system being extracted from:

- useful LevOS contracts and orchestration ideas;
- existing ClaimGate intake, evidence, and ledger work;
- finite Ratchet comparison machinery;
- a small resource-efficient subset of the simulation and formal-tool stack;
- CodexRatchet’s constraint and evidence discipline.

It must work independently. It may also act as a patch or adapter for LevOS and as a controller for selected CodexRatchet and simulation tasks.

It is not the whole LevOS repository, the whole CodexRatchet estate, or the full simulation fleet.

### 9.2 Intended containment model

LLMs generate branches inside a deterministic finite box:

\[
\text{proposal}
\to
\text{strict intake}
\to
\text{finite obligations}
\to
\text{tool execution}
\to
\text{independent checks}
\to
\text{plural survivors or rejection}.
\]

The goal is not to make hallucination impossible. It is to:

- contain exploration;
- prevent fluent prose from self-promoting;
- preserve live alternatives;
- require executable consequences;
- stop unsupported claims at the boundary;
- make branch pruning and merging earned.

### 9.3 What existing ClaimGate work established

The prior campaign improved:

- strict JSON intake;
- duplicate-key and non-finite-number rejection;
- frozen path-and-digest debt baselines;
- hostile regression fixtures;
- orphan receipt detection;
- durable local ledgers;
- claim-typed tool dispatch;
- basic recomputation and severance tests;
- resource bake-offs for NumPy, SciPy, Z3, cvc5, PyDMD, PySINDy, JAX, and related tools.

It also established a decisive limitation:

\[
\boxed{
\text{receipt shape}\ne\text{execution truth}.
}
\]

Six syntactic or producer-controlled relieving surfaces failed. The two techniques that repeatedly discriminated were:

1. **severance:** break the claimed dependency and require the verdict to change;
2. **independent re-derivation:** recompute the claim from independent inputs and logic.

Therefore the standalone system should be called a constraint/evidence box, not a universal truth verifier.

### 9.4 Lean core

The practical core is:

| Function | Default implementation | Resource policy |
|---|---|---|
| strict intake and schemas | Python standard library + JSON Schema when available | always on |
| finite arithmetic and arrays | NumPy | always on for numeric profiles |
| scientific reference functions | SciPy | claim-typed dispatch |
| finite logical obligations | Z3; cvc5 as independent rival for selected obligations | claim-typed dispatch |
| state-machine and orchestration properties | TLA+/TLC or Apalache when installed | scheduled or release checks |
| law discovery proposals | PySINDy | only when feature library, variables, sampling, and residual budget are declared |
| spectral/rate proposals | PyDMD/Koopman tools | only for declared dynamic claims |
| scalable differentiable computation | JAX | maturity layer after NumPy reference and controls |
| durable evidence | content-addressed artifacts + append-only ledger | every run |

PySINDy proposes candidate laws. It never chooses its own feature library and never certifies the law it fits.

### 9.5 Simulation installation validation

The system should validate the larger simulation estate in layers:

1. **Core constraint layer:** Python, NumPy, SciPy, Z3, cvc5, schemas, test runner.
2. **Manifold and engine layer:** JAX, Diffrax, QuTiP, Julia, QuantumOptics, graph/topology and symbolic packages.
3. **Science-field layer:** tensor networks, active-inference and field tools selected per experiment.
4. **Cloud layer:** PyTorch/JAX/Julia GPU execution, graph mutation, large contractions, and batch search.

Each layer needs:

- version and interpreter fingerprint;
- genuine import and operation witness;
- known-answer positive and negative controls;
- dependency severance;
- output mutation sensitivity;
- cross-backend or analytic witness where warranted;
- peak time and memory;
- maintenance/freshness timestamp.

One heavy runtime should own a constrained local machine at a time. Immutable artifacts and process exit separate runtime lanes.

---

## 10. Mathematics and science problem program

### 10.1 Bounded-computation rule

Every campaign follows:

\[
\text{native statement}
\to
\text{finite challenge}
\to
\text{candidate search}
\to
\text{deterministic replay}
\to
\text{independent certificate}
\to
\text{explicit lift obligation}.
\]

The finite challenge never silently becomes the unrestricted theorem.

### 10.2 Singularity-to-field hypothesis

**OWNER DIRECTION; OPEN**

The model proposes that approaching a singular quotient need not produce an operational infinity. It may release a finite unresolved field of alternatives.

Let

\[
f_\epsilon:X_\epsilon\to Y_\epsilon
\]

be a family of finite maps. If distinct states collapse toward \(y_0\) as \(\epsilon\to0\), define:

\[
\mathcal F_{\epsilon}(y_0)
=
f_\epsilon^{-1}(B_\epsilon(y_0)).
\]

Candidate observables include:

\[
N_\epsilon
=
|\mathcal F_\epsilon(y_0)|,
\]

\[
S_{0,\epsilon}
=
\log_2N_\epsilon,
\]

\[
D_\epsilon(j,k),
\]

\[
\beta_\bullet(K_\epsilon),
\]

and distributions of finite renormalized residues. An empirically useful claim requires a measurable prediction that distinguishes this finite-field release from ordinary noise, unresolved instrumentation, standard critical fluctuations, and known regularization effects.

### 10.3 Special seams

A special seam is the exact missing statement connecting a finite certified result to a broader claim.

Every campaign must state:

- the native claim and quantifiers;
- the bounded carrier and bounds;
- the discretization or projection;
- information lost by that projection;
- the independently checkable certificate;
- the missing lift lemma;
- the maximum claim tier.

Special seams may be searched for, but a small residual or stable plot is not itself a lift lemma.

### 10.4 Major-problem tracks

The project has considered tracks touching:

- complexity and satisfiability;
- Navier–Stokes and nonlinear PDE regularity;
- Yang–Mills and lattice-to-continuum gaps;
- the Riemann hypothesis and finite zero searches;
- algebraic and arithmetic geometry;
- quantum gravity, cosmology, and finite singular behavior;
- object formation, perception, and machine intelligence.

These are research tracks. None is claimed solved.

The model’s possible contribution is methodological:

1. make the finite representational carrier explicit;
2. enumerate hidden frame assumptions;
3. preserve rival discretizations and orderings;
4. use topology, entropy, and history as typed invariants;
5. identify a seam where a finite structure could support a new lemma;
6. use GPUs for candidate discovery and falsification;
7. use exact checkers, formal proof, interval methods, or analytic arguments for bounded certification.

### 10.5 Proposed GPU experiment

The most valuable unified experiment is not “run every possibility.” It is:

1. generate rival finite deformation towers from the same \(2^n\) carrier;
2. vary ordering, quotient rules, cuts, connection, and history retention;
3. compute homology, Hodge components, affinities, stationary currents, and entropy vectors;
4. select coarsest candidates preserving declared distinctions and circulation;
5. couple the surviving cycle to an explicit finite load;
6. derive rather than prescribe the history/holonomy record;
7. test whether sixteen sectors remain distinguishable;
8. scale across carrier size and precision;
9. preserve incomparables and negative controls;
10. emit independent artifacts for NumPy, JAX, Julia, and selected GPU lanes.

This experiment can deepen the manifold and engine proposal without claiming that the proposal is already true.

---

## 11. Current bounded evidence

The preserved engine-emergence suite reports 20/20 isolated jobs passing under one subprocess per probe with Python isolation. The source, results, verifiers, and suite receipt are included in this pack.

### 11.1 Supported within tested carriers

| Result | Current bounded support |
|---|---|
| ordered topological deformation changes capacity | finite cell-complex sequence with \(\beta_1:0\to1\to0\) and matching Hartley capacity |
| topology does not generate current | same one-skeleton and rates retained the same current; zero affinity gave zero current |
| coarsest sufficient cycle can be isolated | exact 512-candidate face tournament; one demanded central cycle gave unique \(\beta_1=1\) survivor |
| weak demand preserves plurality | nine incomparable one-hole survivors under \(\beta_1\ge1\) |
| complete affine qubit generator coordinates | \(3+3+1+5=12\), reconstruction and rotation covariance near machine precision |
| four named flow examples are not exhaustive | finite census contains mixtures, saddles, and spiral flows outside four examples |
| autonomous currents can live in histories | three-qubit stationary absorption-machine scout with six cycle currents and control reversals |
| affinity has a cohomological obstruction form | thermal edge cochain exact; added coherent chord makes enlarged cochain non-exact |
| order affects kinetics | six cycle orders share affinity but carry different current weights |
| coherent history can make orientation observable | local count 10; coherent history count 16; dephased count 10 |
| projection can create effective nonassociativity | exact composition associative; lossy intermediate projection produced a nonzero effective associator |
| noncommutation is not nonassociativity | explicit controls keep the two obligations separate |

### 11.2 Not established

- the manifold ladder is uniquely selected;
- the Hopf chart is the required physical geometry;
- the sixteen-sector construction emerges autonomously end to end;
- a useful work load has been coupled to the autonomous machine;
- the holonomy record is generated by the jump cycles rather than supplied;
- exceptional Lie algebras or octonions are required;
- the engine field has been derived from the finite base;
- singularities empirically release the proposed finite field;
- gravity and entropy have been unified by this model;
- a Millennium problem or other unrestricted problem has been solved;
- ConstraintBox/ClaimGate verifies intentional honesty;
- the full simulation fleet is installed, integrated, and sealed in one current environment.

### 11.3 Decisive next experiment

The next high-value build is:

\[
\boxed{
\text{demand-protected finite cycle}
\to
\text{autonomous quantum-jump current}
\to
\text{explicit finite load}
\to
\text{derived history holonomy}
\to
\text{16-sector discrimination}
}
\]

Required controls:

- fill or slit the cycle;
- set affinity to zero;
- remove the coherent chord;
- equalize reservoirs;
- reverse the gradient;
- dephase history;
- identify inner and outer leaves;
- erase orientation;
- scramble order while preserving multiset;
- replace authored holonomy with derived cycle statistics;
- delete the load;
- run independent analytic, NumPy, JAX, and Julia witnesses.

---

## 12. Preservation map

| Pack directory | Contents |
|---|---|
| `00_START_HERE` | this master record, status rules, and navigation |
| `01_CORE_MODEL` | high-level system orientation and grounded continuity documents |
| `02_RATCHET_AND_MANIFOLD` | formal manifold/Ratchet sources and ordered-layer work |
| `03_ENGINES_AND_ENGINE_FIELDS` | engine-emergence reports, scripts, results, and independent audits |
| `04_CONSTRAINTBOX_AND_CLAIMGATE` | standalone ConstraintBox design/runtime and ClaimGate lessons |
| `05_SIM_AND_FORMAL_TOOLING` | sim-engine audit, lean package slice, and implementation plan |
| `06_MATH_AND_SCIENCE_PROGRAM` | GPU, special-seam, and major-problem program documents |
| `07_EXECUTABLE_EVIDENCE` | bounded probes, receipts, and verifiers |
| `08_USER_SOURCE_DOCUMENTS` | attached source transcripts, audits, PDFs, and preserved raw inputs |
| `09_PRIOR_CONTINUITY_PACKS` | earlier curated packs, not entire repositories |
| `10_MANIFEST` | hashes, inventory, build receipt, source status |

The repository checkouts are intentionally not embedded. Another system with repository access should use the preserved repository pointers and hashes to inspect them directly.
