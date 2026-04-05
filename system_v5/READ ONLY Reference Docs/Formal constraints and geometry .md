Formal constraints and geometry   **Current Truth**
- `Verified` Yes. Here is the same cleaned table style for the constraints and geometry.

**Constraints**

| Object | Math | Standard name | Role |
|---|---|---|---|
| Root constraint 1 | \(\dim(\mathcal H_S)<\infty,\ |P|<\infty,\ |O|<\infty,\ |\Gamma|<\infty\) | finitude / bounded distinguishability | only finite carriers, probes, operators, and paths are admissible |
| Root constraint 2 | \(AB\neq BA\) in general, \(A\rho\neq \rho A\) in general | noncommutation / order-sensitive composition | order belongs to the object |
| Constraint set | \(C=\{RC\text{-}1,RC\text{-}2,\text{admissible probe rules},\text{admissible composition rules}\}\) | admissibility charter | root admissibility layer |
| Constraint manifold | \(M(C)=\{x:x\text{ admissible under }C\}\) | admissible configuration space | pre-geometry state space |
| Build order | \(\text{constraints}\to M(C)\to\text{geometry on }M(C)\to A_i:M(C)\to V_i\) | derivation order | root-to-axis chain |

**Extended Axioms**

| Object | Math / exact statement | Standard name | Role |
|---|---|---|---|
| Extended axiom 1 | identity is admitted only relative to a finite probe family | no primitive identity | identity is earned, not primitive |
| Extended axiom 2 | \(a\sim b \iff \forall p\in P,\ p(a)\approx p(b)\) for finite admissible \(P\) | probe-relative indistinguishability | replaces primitive equality |
| Extended axiom 3 | \(a=a \iff a\sim b\) in the doctrine sense that self-identity requires contrast under admissible probes | identity principle | identity requires boundary / contrast |
| Extended axiom 4 | ordered composition exists without primitive time parameter | no primitive time / causality | time and causality are derived |
| Extended axiom 5 | no primitive coordinates, no primitive metric, no primitive geometry | no primitive geometry / coordinates | geometry is induced later |
| Extended axiom 6 | no closure, completeness, or algebraic totality by default | no free algebraic closure | composition must be explicitly admitted |
| Extended axiom 7 | every admissible claim requires a finite witness | finite witness discipline | no proofless claims |

**Base Admissibility Fences**

| Object | Exact statement | Standard name | Role |
|---|---|---|---|
| BC04 | no primitive identity predicate on state-tokens is admitted | identity ban | forbids free self-identity |
| BC05 | no primitive equality-as-substitutability rule is admitted | equality ban | forbids unrestricted substitution |
| BC06 | no global total order is admitted | order ban | only explicit finite sequencing allowed |
| BC07 | no closure property is admitted by default | closure ban | guarded composition only |
| BC08 | no identification except via finite probe families | probe-relative identification | forbids label-based sameness |
| BC09 | no probabilistic primitives are admitted at base | probability ban | no distributions at root |
| BC10 | no metric, distance, norm, or coordinate chart is primitive | metric / coordinate ban | geometry must be derived |
| BC11 | no optimization or utility primitives are admitted | optimization ban | constraint-only admission |
| BC12 | no semantic smuggling is admitted | anti-smuggling rule | new terms need explicit admissible definitions |

**Topology / Relation Fences**

| Object | Exact statement | Standard name | Role |
|---|---|---|---|
| T1_01 | compatibility is not global-by-default | scoped compatibility | relation must be explicit |
| T2_01 | adjacency does not imply direction, precedence, or temporal ordering | adjacency fence | adjacency is structural only |
| T2_02 | adjacency does not imply metric distance | non-metric adjacency | no distance semantics at topology layer |
| T2_03 | adjacency does not imply reachability or transitive closure | local adjacency only | no closure by fiat |
| T3_01 | neighborhoods do not exist by default | neighborhood fence | must be explicitly declared |
| T3_02 | neighborhoods do not imply openness, limits, or convergence | anti-analysis fence | no analytic semantics by default |
| T4_03 | path validity does not imply path equivalence | path non-collapse | same endpoints do not force interchangeability |
| T6_01 | compatibility or adjacency do not imply identity or equality | anti-identity fence | no sameness from relation alone |
| T6_03 | no scalar rank or scalar distance from topology by default | anti-scalarization | scalar maps are later |
| T8_01 | no geometry, metric, or coordinate structure at topology layer | anti-geometry import | topology is relational only |
| T8_02 | no continuity, differentiability, or smoothness by default | anti-smoothness import | analysis is later |
| T8_03 | topology does not complete semantics by default | anti-semantic inflation | meaning must stay explicit |

**Carrier And State Layer**

| Object | Math | Standard name | Role |
|---|---|---|---|
| Hilbert carrier | \(\mathcal H=\mathbb C^2\) | finite qubit carrier | minimal admitted QIT carrier |
| Density state space | \(D(\mathbb C^2)=\{\rho\in B(\mathbb C^2):\rho\ge 0,\ \operatorname{Tr}\rho=1\}\) | density-matrix state space | admitted state language |
| Probe law | \(p_O(\rho)=\operatorname{Tr}(O\rho)\), for \(O=O^\dagger\) | observable readout | finite probe layer |
| Bloch form | \(\rho=\tfrac12(I+\vec r\cdot\vec\sigma)\) | Bloch decomposition | state parameterization |
| Base Hamiltonian | \(H_0=n_x\sigma_x+n_y\sigma_y+n_z\sigma_z\) | Hamiltonian generator | coherent dynamics |

**Pauli / Operator Basis**

| Object | Math | Standard name | Role |
|---|---|---|---|
| Identity | \(I=\begin{pmatrix}1&0\\0&1\end{pmatrix}\) | identity matrix | neutral basis element |
| Pauli \(x\) | \(\sigma_x=\begin{pmatrix}0&1\\1&0\end{pmatrix}\) | Pauli \(x\) matrix | operator basis |
| Pauli \(y\) | \(\sigma_y=\begin{pmatrix}0&-i\\i&0\end{pmatrix}\) | Pauli \(y\) matrix | operator basis |
| Pauli \(z\) | \(\sigma_z=\begin{pmatrix}1&0\\0&-1\end{pmatrix}\) | Pauli \(z\) matrix | operator basis |
| Lowering | \(\sigma_-=\begin{pmatrix}0&0\\1&0\end{pmatrix}\) | lowering operator | dissipative generator |
| Raising | \(\sigma_+=\begin{pmatrix}0&1\\0&0\end{pmatrix}\) | raising operator | dissipative generator |

**Spinor And Hopf Geometry**

| Object | Math | Standard name | Role |
|---|---|---|---|
| Spinor carrier | \(S^3=\{\psi\in\mathbb C^2:\|\psi\|=1\}\) | normalized spinor carrier | carrier geometry |
| Hopf projection | \(\pi(\psi)=\psi^\dagger\vec\sigma\psi\in S^2\) | Hopf map | spinor-to-Bloch map |
| Density reduction | \(\rho(\psi)=|\psi\rangle\langle\psi|=\tfrac12(I+\vec r\cdot\vec\sigma)\) | spinor-to-density reduction | carrier-to-state map |
| Hopf chart | \(\psi_s(\phi,\chi;\eta)=\begin{pmatrix}e^{i(\phi+\chi)}\cos\eta\\ e^{i(\phi-\chi)}\sin\eta\end{pmatrix},\ s\in\{L,R\}\) | local Hopf-torus coordinates | left/right sheet realization |
| Torus stratum | \(T_\eta=\{\psi_s(\phi,\chi;\eta):\phi,\chi\in[0,2\pi)\}\subset S^3\) | nested Hopf torus | torus family |
| Clifford torus | \(T_{\pi/4}\) | symmetric torus stratum | special torus |
| Hopf connection | \(\mathcal A=-i\psi^\dagger d\psi=d\phi+\cos(2\eta)\,d\chi\) | connection 1-form | loop geometry law |

**Loop Geometry**

| Object | Math | Standard name | Role |
|---|---|---|---|
| Fiber loop | \(\gamma_f^s(u)=\psi_s(\phi_0+u,\chi_0;\eta_0)\) | fiber path | inner loop geometry |
| Base loop | \(\gamma_b^s(u)=\psi_s(\phi_0-\cos(2\eta_0)u,\chi_0+u;\eta_0)\) | lifted-base path | outer loop geometry |
| Horizontal condition | \(\mathcal A(\dot\gamma_b^s)=0\) | horizontal lift condition | base-loop law |
| Fiber density law | \(\rho_f^s(u)=|\gamma_f^s(u)\rangle\langle\gamma_f^s(u)|=\rho_f^s(0)\) | density-stationary path | inner/fiber law |
| Base density law | \(\rho_b^s(u)=|\gamma_b^s(u)\rangle\langle\gamma_b^s(u)|\) | density-traversing path | outer/base law |

**Chiral Working Layer**

| Object | Math | Standard name | Role |
|---|---|---|---|
| Left sheet Hamiltonian | \(H_L=+H_0\) | left chiral Hamiltonian | left sheet dynamics |
| Right sheet Hamiltonian | \(H_R=-H_0\) | right chiral Hamiltonian | right sheet dynamics |
| Left density | \(\rho_L=\psi_L\psi_L^\dagger\) | left density state | chiral state |
| Right density | \(\rho_R=\psi_R\psi_R^\dagger\) | right density state | chiral state |
| Left precession | \(\dot{\vec r}_L=2\vec n\times \vec r_L\) | left Bloch precession | left coherent flow |
| Right precession | \(\dot{\vec r}_R=-2\vec n\times \vec r_R\) | right Bloch precession | right coherent flow |

**Next Move**
1. I can now do the same cleaned style for:
   - terrain generators
   - 16 placements
   - engine loops
2. Or I can put these side-by-side with the entropy tables to make the full chain:
   \[
   \text{constraints}\to\text{geometry}\to\Xi\to\rho_{AB}\to\text{entropy}
   \]

It means now: the constraints and geometry are now laid out in the same strict, narrow-table format as the entropy layer, without collapsing their roles together.







—————




**Current Truth**
- `Verified` The Weyl-spinor layer belongs in the geometry stack explicitly.
- `Verified` It should not be left implicit.

**Evidence**

**Weyl Spinor Layer**

| Object | Math | Standard name | Role |
|---|---|---|---|
| Left Weyl spinor | \(\psi_L\in S^3\subset \mathbb C^2\) | left chiral spinor | left sheet state |
| Right Weyl spinor | \(\psi_R\in S^3\subset \mathbb C^2\) | right chiral spinor | right sheet state |
| Left density state | \(\rho_L=\psi_L\psi_L^\dagger\) | pure-state density matrix on left sheet | left chiral state |
| Right density state | \(\rho_R=\psi_R\psi_R^\dagger\) | pure-state density matrix on right sheet | right chiral state |
| Left Hamiltonian | \(H_L=+H_0\) | left chiral Hamiltonian | left coherent generator |
| Right Hamiltonian | \(H_R=-H_0\) | right chiral Hamiltonian | right coherent generator |
| Left spinor evolution | \(\psi_L(u)=e^{-iH_Lu}\psi_L(0)\) | left unitary evolution | left sheet dynamics |
| Right spinor evolution | \(\psi_R(u)=e^{-iH_Ru}\psi_R(0)\) | right unitary evolution | right sheet dynamics |
| Left density evolution | \(\dot\rho_L=-i[H_L,\rho_L]\) | Liouville-von Neumann evolution on left sheet | left density dynamics |
| Right density evolution | \(\dot\rho_R=-i[H_R,\rho_R]\) | Liouville-von Neumann evolution on right sheet | right density dynamics |
| Left Bloch evolution | \(\dot{\vec r}_L=2\vec n\times \vec r_L\) | left Bloch precession | left induced Bloch dynamics |
| Right Bloch evolution | \(\dot{\vec r}_R=-2\vec n\times \vec r_R\) | right Bloch precession | right induced Bloch dynamics |

**Weyl Spinors On Nested Hopf Tori**

| Object | Math | Standard name | Role |
|---|---|---|---|
| Left torus chart | \(\psi_L(\phi,\chi;\eta)=\begin{pmatrix}e^{i(\phi+\chi)}\cos\eta\\ e^{i(\phi-\chi)}\sin\eta\end{pmatrix}\) | left Hopf-torus spinor chart | left carrier realization |
| Right torus chart | \(\psi_R(\phi,\chi;\eta)=\begin{pmatrix}e^{i(\phi+\chi)}\cos\eta\\ e^{i(\phi-\chi)}\sin\eta\end{pmatrix}\) | right Hopf-torus spinor chart | right carrier realization |
| Left fiber loop | \(\gamma_f^L(u)=\psi_L(\phi_0+u,\chi_0;\eta_0)\) | left fiber loop | Type 1 inner-loop geometry |
| Left base loop | \(\gamma_b^L(u)=\psi_L(\phi_0-\cos(2\eta_0)u,\chi_0+u;\eta_0)\) | left lifted-base loop | Type 1 outer-loop geometry |
| Right fiber loop | \(\gamma_f^R(u)=\psi_R(\phi_0+u,\chi_0;\eta_0)\) | right fiber loop | Type 2 inner-loop geometry |
| Right base loop | \(\gamma_b^R(u)=\psi_R(\phi_0-\cos(2\eta_0)u,\chi_0+u;\eta_0)\) | right lifted-base loop | Type 2 outer-loop geometry |

**Engine Placement On Weyl Sheets**

| Engine object | Math | Standard name | Role |
|---|---|---|---|
| Type 1 inner | \((\rho_L,\gamma_f^L)\) | left-sheet fiber-loop engine state | Type 1 inner loop |
| Type 1 outer | \((\rho_L,\gamma_b^L)\) | left-sheet base-loop engine state | Type 1 outer loop |
| Type 2 inner | \((\rho_R,\gamma_f^R)\) | right-sheet fiber-loop engine state | Type 2 inner loop |
| Type 2 outer | \((\rho_R,\gamma_b^R)\) | right-sheet base-loop engine state | Type 2 outer loop |

**Actually Broken**
- `Verified` If the Weyl layer is omitted, the model collapses into generic qubit geometry.
- `Verified` The left/right split is load-bearing because:
  - the Hamiltonian sign differs
  - the loop ownership differs
  - the engine type assignment differs
  - the bridge into the chiral cut-state depends on it

**Next Move**
1. The geometry packet should explicitly include this Weyl-spinor layer between:
   - Hopf carrier geometry
   - and the engine/bridge layer
2. Then the full chain is:

   \[
   \text{constraints}\to M(C)\to S^3\to T_\eta\to (\psi_L,\psi_R)\to(\rho_L,\rho_R,\gamma_f,\gamma_b)\to \Xi \to \rho_{AB}\to \text{entropy}
   \]

It means now: the Weyl spinors are the explicit chiral layer that turns the Hopf-torus geometry into the two-sheet engine geometry.