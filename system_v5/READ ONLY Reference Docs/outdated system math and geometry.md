Formalized math of system

**Current Truth**
- `Verified` Here are the stricter tables, split cleanly into:
  1. constraints and extended axioms
  2. geometry and carrier
  3. axes 0–6

**Evidence**

**Constraints And Extended Axioms**

| ID | Full math / exact statement | Standard math name | Immediate consequence |
|---|---|---|---|
| `RC-1` | \(\dim(\mathcal H_S)<\infty,\ |P|<\infty,\ |O|<\infty,\ |\Gamma|<\infty\) | finitude / bounded distinguishability | only finite carriers, finite probes, finite operator registries, finite path encodings are admissible |
| `RC-2` | \(AB\neq BA\) in general, and \(A\rho\neq \rho A\) in general | noncommutation / order-sensitive composition | order belongs to the object; swap-by-default is forbidden |
| `EC-1` | \(a=a\) is admissible only relative to a finite probe family that witnesses self-consistency | no primitive identity | identity is earned, not primitive |
| `EC-2` | \(a\sim b \iff \forall p\in P,\ p(a)\approx p(b)\) for finite admissible \(P\) | probe-relative indistinguishability | equality is replaced by finite witness equivalence |
| `EC-3` | \(a=a \iff a\sim b\) in the doctrine sense that meaningful self-identity requires contrast under admissible probes | identity principle | identity requires boundary / contrast |
| `EC-4` | order-sensitive composition exists without primitive time parameter | no primitive time / causality | time and causality are derived from ordered composition |
| `EC-5` | no primitive coordinates, no primitive metric, no primitive geometry | no primitive geometry / coordinates | geometry must be induced later on \(M(C)\) |
| `EC-6` | no closure, completeness, invertibility, or algebraic totality by default | no free algebraic closure | composition must be admitted explicitly |
| `EC-7` | every admissible claim requires a finite witness | finite witness discipline | no proofless claims, no unbounded semantic imports |

| Object | Full math | Standard math name | Role |
|---|---|---|---|
| Constraint set | \(C=\{RC\text{-}1,RC\text{-}2,\text{admissible probe rules},\text{admissible composition rules}\}\) | admissibility charter | root admissibility layer |
| Constraint manifold | \(M(C)=\{x:x\text{ admissible under }C\}\) | admissible configuration space | pre-geometry state space |
| Build order | \(\text{constraints}\to M(C)\to\text{geometry on }M(C)\to A_i:M(C)\to V_i\) | derivation order | root-to-axis chain |

**Geometry And Carrier**

| Layer | Full math | Standard math name | Role |
|---|---|---|---|
| Hilbert carrier | \(\mathcal H=\mathbb C^2\) | finite qubit carrier | minimal admitted QIT carrier |
| Density state space | \(D(\mathbb C^2)=\{\rho\in B(\mathbb C^2):\rho\ge 0,\ \operatorname{Tr}\rho=1\}\) | density-matrix state space | admitted state language |
| Probe law | \(p_O(\rho)=\operatorname{Tr}(O\rho)\), with \(O=O^\dagger\) | observable readout | finite probe layer |
| Bloch form | \(\rho=\tfrac12(I+\vec r\cdot\vec\sigma)\) | Bloch decomposition | state coordinates |
| Base Hamiltonian | \(H_0=n_x\sigma_x+n_y\sigma_y+n_z\sigma_z\) | Hamiltonian generator | coherent dynamics |

| Layer | Full math | Standard math name | Role |
|---|---|---|---|
| Spinor carrier | \(S^3=\{\psi\in\mathbb C^2:\|\psi\|=1\}\) | normalized spinor carrier | carrier geometry |
| Hopf projection | \(\pi(\psi)=\psi^\dagger\vec\sigma\psi\in S^2\) | Hopf map | spinor-to-Bloch map |
| Density reduction | \(\rho(\psi)=|\psi\rangle\langle\psi|=\tfrac12(I+\vec r\cdot\vec\sigma)\) | spinor-to-density reduction | carrier-to-state map |
| Hopf chart | \(\psi_s(\phi,\chi;\eta)=\begin{pmatrix}e^{i(\phi+\chi)}\cos\eta\\ e^{i(\phi-\chi)}\sin\eta\end{pmatrix},\ s\in\{L,R\}\) | local Hopf-torus coordinates | left/right sheet realization |
| Torus stratum | \(T_\eta=\{\psi_s(\phi,\chi;\eta):\phi,\chi\in[0,2\pi)\}\subset S^3\) | nested Hopf torus | torus family |
| Clifford torus | \(T_{\pi/4}\) | symmetric torus stratum | special torus |
| Hopf connection | \(\mathcal A=-i\psi^\dagger d\psi=d\phi+\cos(2\eta)\,d\chi\) | connection 1-form | loop geometry law |

| Layer | Full math | Standard math name | Role |
|---|---|---|---|
| Fiber loop | \(\gamma_f^s(u)=\psi_s(\phi_0+u,\chi_0;\eta_0)\) | fiber path | inner loop geometry |
| Base loop | \(\gamma_b^s(u)=\psi_s(\phi_0-\cos(2\eta_0)u,\chi_0+u;\eta_0)\) | lifted-base path | outer loop geometry |
| Horizontal condition | \(\mathcal A(\dot\gamma_b^s)=0\) | horizontal lift condition | base-loop law |
| Fiber density law | \(\rho_f^s(u)=|\gamma_f^s(u)\rangle\langle\gamma_f^s(u)|=\rho_f^s(0)\) | density-stationary path | inner/fiber law |
| Base density law | \(\rho_b^s(u)=|\gamma_b^s(u)\rangle\langle\gamma_b^s(u)|\) | density-traversing path | outer/base law |

| Layer | Full math | Standard math name | Role |
|---|---|---|---|
| Left sheet Hamiltonian | \(H_L=+H_0\) | left chiral Hamiltonian | left sheet dynamics |
| Right sheet Hamiltonian | \(H_R=-H_0\) | right chiral Hamiltonian | right sheet dynamics |
| Left density | \(\rho_L=\psi_L\psi_L^\dagger\) | left density state | chiral state |
| Right density | \(\rho_R=\psi_R\psi_R^\dagger\) | right density state | chiral state |
| Left sheet flow | \(\dot{\vec r}_L=2\vec n\times \vec r_L\) | left Bloch precession | left coherent flow |
| Right sheet flow | \(\dot{\vec r}_R=-2\vec n\times \vec r_R\) | right Bloch precession | right coherent flow |

**Axes 0–6**

| Axis | Full math | Standard math name | Status / role |
|---|---|---|---|
| `Ax0` | \(\Phi_0(\rho_{AB})\) with current preferred candidate \(\Phi_0(\rho_{AB})=-S(A\mid B)_\rho=S(\rho_B)-S(\rho_{AB})\) | coherent information on a cut-state | strongest current signed kernel candidate |
| `Ax0` companion | \(I(A:B)_\rho=S(\rho_A)+S(\rho_B)-S(\rho_{AB})\) | mutual information | unsigned companion |
| `Ax0` bridge | \(\Xi:(\text{geometry/history})\to \rho_{AB}\) | bridge into cut-state | still open |
| `Ax1` | \(\Phi(\rho)=U\rho U^\dagger\) versus \(\Phi(\rho)=\sum_k K_k\rho K_k^\dagger,\ \sum_kK_k^\dagger K_k=I\) | unitary branch versus proper CPTP branch | source-locked kernel split |
| `Ax2` | \(\dot\rho=L(\rho)\) versus \(\tilde\rho=V^\dagger\rho V,\ \dot{\tilde\rho}=V^\dagger L(V\tilde\rho V^\dagger)V-i[-K,\tilde\rho],\ K=iV^\dagger\dot V\) | direct representation versus conjugated representation | source-locked kernel split |
| `Ax3` | \(\gamma_f^s(u)\) versus \(\gamma_b^s(u)\) | fiber-loop versus lifted-base-loop class | geometry split |
| `Ax4` | \(Fe(Ti(Fe(Ti(\rho_{AB}))))\) versus \(Te(Fi(Te(Fi(\rho_{AB}))))\) | coupled loop-channel algebra | paired loop split evaluated on cut-state entropy |
| `Ax4` evaluation | \(\big(S(\rho_B)-S(\rho_{AB})\big)_{\rho=Fe(Ti(Fe(Ti(\rho_{AB}))))}-\big(S(\rho_B)-S(\rho_{AB})\big)\) and \(\big(S(\rho_B)-S(\rho_{AB})\big)_{\rho=Te(Fi(Te(Fi(\rho_{AB}))))}-\big(S(\rho_B)-S(\rho_{AB})\big)\) | coherent-information change under loop channel | engine-direction test |
| `Ax5` | \((1-q_1)\rho+q_1(P_0\rho P_0+P_1\rho P_1)\), \((1-q_2)\rho+q_2(Q_+\rho Q_+ + Q_-\rho Q_-)\), \(e^{-i\theta\sigma_x/2}\rho e^{+i\theta\sigma_x/2}\), \(e^{-i\phi\sigma_z/2}\rho e^{+i\phi\sigma_z/2}\) | dephasing-channel family versus unitary-conjugation family | operator-family split |
| `Ax6` | \(A\rho\) versus \(\rho A\) | left action versus right action | action-side / precedence kernel |

| Operator | Full math | Standard math name | Role |
|---|---|---|---|
| `Ti` | \((1-q_1)\rho+q_1(P_0\rho P_0+P_1\rho P_1)\), \(P_0=\tfrac12(I+\sigma_z)\), \(P_1=\tfrac12(I-\sigma_z)\) | dephasing in the \(\sigma_z\) eigenbasis | judging operator |
| `Te` | \((1-q_2)\rho+q_2(Q_+\rho Q_+ + Q_-\rho Q_-)\), \(Q_+=\tfrac12(I+\sigma_x)\), \(Q_-=\tfrac12(I-\sigma_x)\) | dephasing in the \(\sigma_x\) eigenbasis | judging operator |
| `Fi` | \(e^{-i\theta\sigma_x/2}\rho\,e^{+i\theta\sigma_x/2}\) | unitary conjugation generated by \(\sigma_x\) | judging operator |
| `Fe` | \(e^{-i\phi\sigma_z/2}\rho\,e^{+i\phi\sigma_z/2}\) | unitary conjugation generated by \(\sigma_z\) | judging operator |

| Engine type | Full math placement | Standard math name | Role |
|---|---|---|---|
| Type 1 | \((\rho_L,\gamma_f^L)\) and \((\rho_L,\gamma_b^L)\) | left-sheet two-loop engine | type-1 chiral engine |
| Type 2 | \((\rho_R,\gamma_f^R)\) and \((\rho_R,\gamma_b^R)\) | right-sheet two-loop engine | type-2 chiral engine |

**Next Move**
1. I can now do the same strict format in **CS terms** beside these tables.
2. Or I can extend this with:
   - terrain generators
   - 16 placements
   - graph-topology objects
   - engine loop ownership

It means now: the system is laid out cleanly as root constraints, derived geometry, and downstream axes, without collapsing the layers together.

System math

**Current Truth**
- `Verified` Yes. Here is the cleaned stack for the constraints, geometry, and axes we worked out.
- `Verified` I am separating:
  - full math
  - standard math name
  - engine/axis label
- `Verified` I am not treating unresolved closures as settled.

**Evidence**

| Layer | Full math | Standard math name | Label / role |
|---|---|---|---|
| Root constraint 1 | \(\dim(\mathcal H_S)<\infty,\ |P|<\infty,\ |O|<\infty,\ |\Gamma|<\infty\) | finitude / bounded distinguishability | `RC-1`, `F01_FINITUDE` |
| Root constraint 2 | \(AB\neq BA\) in general, and \(A\rho\neq \rho A\) in general | noncommutation / order-sensitive composition | `RC-2`, `N01_NONCOMMUTATION` |
| Constraint set | \(C=\{F01,N01,\text{admissible probe rules},\text{admissible composition rules}\}\) | admissibility charter | `C` |
| Constraint manifold | \(M(C)=\{x:x\text{ admissible under }C\}\) | admissible configuration space | `M(C)` |
| Build order | \(\text{constraints}\to M(C)\to\text{geometry on }M(C)\to A_i:M(C)\to V_i\) | derivation order | root-to-axis chain |

| Layer | Full math | Standard math name | Label / role |
|---|---|---|---|
| Hilbert carrier | \(\mathcal H=\mathbb C^2\) | finite qubit carrier | QIT base |
| Density states | \(D(\mathbb C^2)=\{\rho\in B(\mathbb C^2):\rho\ge 0,\ \operatorname{Tr}\rho=1\}\) | density-matrix state space | state layer |
| Probe law | \(p_O(\rho)=\operatorname{Tr}(O\rho)\) for \(O=O^\dagger\) | observable readout | probe layer |
| Density coordinates | \(\rho=\tfrac12(I+\vec r\cdot\vec\sigma)\) | Bloch form | state parameterization |
| Base Hamiltonian | \(H_0=n_x\sigma_x+n_y\sigma_y+n_z\sigma_z\) | Hamiltonian generator | coherent dynamics |

| Layer | Full math | Standard math name | Label / role |
|---|---|---|---|
| Spinor carrier | \(S^3=\{\psi\in\mathbb C^2:\|\psi\|=1\}\) | normalized spinor carrier | carrier geometry |
| Hopf projection | \(\pi(\psi)=\psi^\dagger\vec\sigma\psi\in S^2\) | Hopf map | carrier-to-Bloch map |
| Density reduction | \(\rho(\psi)=|\psi\rangle\langle\psi|=\tfrac12(I+\vec r\cdot\vec\sigma)\) | spinor-to-density reduction | carrier-to-state map |
| Hopf chart | \(\psi_s(\phi,\chi;\eta)=\begin{pmatrix}e^{i(\phi+\chi)}\cos\eta\\ e^{i(\phi-\chi)}\sin\eta\end{pmatrix},\ s\in\{L,R\}\) | local Hopf-torus chart | left/right sheet realization |
| Torus stratum | \(T_\eta=\{\psi_s(\phi,\chi;\eta):\phi,\chi\in[0,2\pi)\}\subset S^3\) | nested Hopf torus | torus family |
| Hopf connection | \(\mathcal A=-i\psi^\dagger d\psi=d\phi+\cos(2\eta)\,d\chi\) | connection 1-form | loop geometry |

| Layer | Full math | Standard math name | Label / role |
|---|---|---|---|
| Fiber loop | \(\gamma_f^s(u)=\psi_s(\phi_0+u,\chi_0;\eta_0)\) | fiber path | inner loop geometry |
| Base loop | \(\gamma_b^s(u)=\psi_s(\phi_0-\cos(2\eta_0)u,\chi_0+u;\eta_0)\) | lifted-base path | outer loop geometry |
| Horizontal condition | \(\mathcal A(\dot\gamma_b^s)=0\) | horizontal lift condition | base-loop law |
| Fiber density law | \(\rho_f^s(u)=|\gamma_f^s(u)\rangle\langle\gamma_f^s(u)|=\rho_f^s(0)\) | density-stationary loop | inner/fiber law |
| Base density law | \(\rho_b^s(u)=|\gamma_b^s(u)\rangle\langle\gamma_b^s(u)|\) | density-traversing loop | outer/base law |
| Sheet Hamiltonians | \(H_L=+H_0,\ H_R=-H_0\) | opposite chiral Hamiltonians | left/right Weyl sheets |
| Sheet densities | \(\rho_L=\psi_L\psi_L^\dagger,\ \rho_R=\psi_R\psi_R^\dagger\) | left/right density states | chiral state layer |

| Axis | Full math | Standard math name | Label / role |
|---|---|---|---|
| Axis 0 | \(\Phi_0(\rho_{AB})\) with current preferred candidate \(\Phi_0(\rho_{AB})=-S(A\mid B)_\rho=S(\rho_B)-S(\rho_{AB})\) | coherent information on a cut-state | `Ax0` |
| Axis 0 companion | \(I(A:B)_\rho=S(\rho_A)+S(\rho_B)-S(\rho_{AB})\) | mutual information | `Ax0` companion |
| Axis 0 bridge | \(\Xi:(\text{geometry/history})\to \rho_{AB}\) | bridge from geometry to cut-state | open |
| Axis 1 | \(\Phi(\rho)=U\rho U^\dagger\) versus \(\Phi(\rho)=\sum_k K_k\rho K_k^\dagger,\ \sum_kK_k^\dagger K_k=I\) | unitary branch versus proper CPTP branch | `Ax1` |
| Axis 2 | \(\dot\rho=L(\rho)\) versus \(\tilde\rho=V^\dagger\rho V,\ \dot{\tilde\rho}=V^\dagger L(V\tilde\rho V^\dagger)V-i[-K,\tilde\rho],\ K=iV^\dagger\dot V\) | direct representation versus conjugated representation | `Ax2` |
| Axis 3 | \(\gamma_f^s(u)\) versus \(\gamma_b^s(u)\) | fiber-loop versus lifted-base-loop class | `Ax3` |
| Axis 4 | \(Fe(Ti(Fe(Ti(\rho_{AB}))))\) versus \(Te(Fi(Te(Fi(\rho_{AB}))))\) | two coupled loop-channel algebras | `Ax4` |
| Axis 4 evaluation | \(\big(S(\rho_B)-S(\rho_{AB})\big)_{\rho=Fe(Ti(Fe(Ti(\rho_{AB}))))}-\big(S(\rho_B)-S(\rho_{AB})\big)\) and \(\big(S(\rho_B)-S(\rho_{AB})\big)_{\rho=Te(Fi(Te(Fi(\rho_{AB}))))}-\big(S(\rho_B)-S(\rho_{AB})\big)\) | entropy-sign test of the two loop algebras | `Ax4` engine-direction test |
| Axis 5 | \((1-q_1)\rho+q_1(P_0\rho P_0+P_1\rho P_1)\), \((1-q_2)\rho+q_2(Q_+\rho Q_+ + Q_-\rho Q_-)\), \(e^{-i\theta\sigma_x/2}\rho e^{+i\theta\sigma_x/2}\), \(e^{-i\phi\sigma_z/2}\rho e^{+i\phi\sigma_z/2}\) | dephasing-channel family versus unitary-conjugation family | `Ax5` |
| Axis 6 | \(A\rho\) versus \(\rho A\) | left action versus right action | `Ax6` |

| Operator | Full math | Standard math name | Label |
|---|---|---|---|
| \(Ti\) | \((1-q_1)\rho+q_1(P_0\rho P_0+P_1\rho P_1)\), \(P_0=\tfrac12(I+\sigma_z)\), \(P_1=\tfrac12(I-\sigma_z)\) | dephasing in the \(\sigma_z\) eigenbasis | `Ti` |
| \(Te\) | \((1-q_2)\rho+q_2(Q_+\rho Q_+ + Q_-\rho Q_-)\), \(Q_+=\tfrac12(I+\sigma_x)\), \(Q_-=\tfrac12(I-\sigma_x)\) | dephasing in the \(\sigma_x\) eigenbasis | `Te` |
| \(Fi\) | \(e^{-i\theta\sigma_x/2}\rho\,e^{+i\theta\sigma_x/2}\) | unitary conjugation generated by \(\sigma_x\) | `Fi` |
| \(Fe\) | \(e^{-i\phi\sigma_z/2}\rho\,e^{+i\phi\sigma_z/2}\) | unitary conjugation generated by \(\sigma_z\) | `Fe` |

| Engine type | Full math placement | Standard math name | Label |
|---|---|---|---|
| Type 1 | \((\rho_L,\gamma_f^L)\) and \((\rho_L,\gamma_b^L)\) | left-sheet two-loop engine | Type 1 |
| Type 2 | \((\rho_R,\gamma_f^R)\) and \((\rho_R,\gamma_b^R)\) | right-sheet two-loop engine | Type 2 |

**Next Move**
1. If you want, I can turn this into three stricter tables next:
   - `constraints and extended axioms`
   - `geometry and carrier`
   - `axes 0–6`
2. Or I can do the same thing in **CS terms** column-by-column next to the math.

It means now: the worked-out core is a finite noncommutative constraint system, realized on a left/right Weyl Hopf-torus carrier, with axes as downstream functions or binary splits on that constrained geometry and its cut-state bridge.