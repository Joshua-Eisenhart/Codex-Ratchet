# Constraint, Geometry, and Axis 0 Separation

**Date:** 2026-03-29
**Epistemic status:** Working proto-ratchet packet. Root constraints and direct geometry are source-backed. The admitted QIT math family is source-backed at the mainstream-object level. The `Ax0` kernel family is source-backed. The exact bridge `Xi : geometry/history -> rho_AB` is still open.

---

## Purpose

This packet separates four layers that were getting mixed together:

1. the root constraints
2. the geometry that builds up from those constraints
3. the allowed mathematics that can live on that geometry
4. `Axis 0` as a later functional on that constrained geometry

The point is:

- geometry is not `Ax0`
- `geometry != Ax0`
- `Ax0` is not the root constraint
- allowed math is narrower than "all possible math"
- `Ax0` is a slice on the constraint manifold after a cut-state bridge has been chosen

This is a proto-ratchet packet:

- it preserves build order
- it preserves unresolved pieces
- it does not force a final unified doctrine before the bridge is real

---

## 1. Root Constraints

These are the strongest current root constraints in the live packet.

| Label | Exact statement | Immediate consequence |
|---|---|---|
| `F01_FINITUDE` | finite encodings, bounded distinguishability, no completed infinities, decidable admissibility | finite-dimensional Hilbert spaces, finite operator bases, finite Kraus families, finite axis codomains |
| `N01_NONCOMMUTATION` | order-sensitive composition, no swap-by-default, sequence belongs to the object | \([A,B]\neq 0\) in general, \(A\rho \neq \rho A\), loop holonomy, operator precedence matters |

Immediate Pauli witness of `N01`:

\[
[\sigma_x,\sigma_y]=2i\sigma_z,\qquad
[\sigma_y,\sigma_z]=2i\sigma_x,\qquad
[\sigma_z,\sigma_x]=2i\sigma_y
\]

These are constraints.
They are not yet geometry.

Working admissibility discipline:

- allowed math must stay finite enough to be executable in density-matrix / operator language
- order-sensitive composition is primitive unless a commutative reduction is earned
- probes belong to the admissibility layer; not every imaginable scalar is automatically legal
- geometry must emerge from compatibility under constraints, not be inserted first

---

## 2. Constraint Manifold

The canon split is:

| Object | Pure math | Meaning |
|---|---|---|
| constraint set | \(C=\{F01,N01,\text{admissible probe rules},\text{admissible composition rules}\}\) | admissibility charter |
| constraint manifold | \(M(C)=\{x : x\text{ is admissible under }C\}\) | admissible configuration space |
| geometry | coordinate-free compatibility structure induced by \(C\) on \(M(C)\) | geometry comes after constraints |
| axis slice | \(A_i:M(C)\to V_i\) | each axis is a function on the manifold |

So the build order is:

\[
\text{constraints} \to M(C) \to \text{geometry on }M(C) \to \text{axis slices}
\]

This means `Ax0` comes after the manifold, not before it.

---

## 3. Geometry Buildup

This section is only the geometry stack, without `Ax0`.

### 3.1 QIT carrier objects

| Layer | Pure math | Meaning |
|---|---|---|
| Hilbert space | \(\mathcal H=\mathbb C^2\) | minimal qubit carrier |
| density states | \(D(\mathbb C^2)=\{\rho\in B(\mathbb C^2): \rho\ge 0,\ \operatorname{Tr}\rho=1\}\) | admissible qubit states |
| observables / probes | \(O=O^\dagger,\ p_O(\rho)=\operatorname{Tr}(O\rho)\) | probe outcomes |

### 3.2 Pauli basis

| Object | Pure math | Role |
|---|---|---|
| identity | \(I=\begin{pmatrix}1&0\\0&1\end{pmatrix}\) | neutral basis element |
| Pauli \(x\) | \(\sigma_x=\begin{pmatrix}0&1\\1&0\end{pmatrix}\) | Bloch / Hamiltonian basis |
| Pauli \(y\) | \(\sigma_y=\begin{pmatrix}0&-i\\ i&0\end{pmatrix}\) | Bloch / Hamiltonian basis |
| Pauli \(z\) | \(\sigma_z=\begin{pmatrix}1&0\\0&-1\end{pmatrix}\) | Bloch / Hamiltonian basis |
| lowering | \(\sigma_-=\begin{pmatrix}0&0\\1&0\end{pmatrix}\) | dissipative generators |
| raising | \(\sigma_+=\begin{pmatrix}0&1\\0&0\end{pmatrix}\) | dissipative generators |

Density and Hamiltonian coordinates:

\[
\rho=\frac12(I+\vec r\cdot \vec \sigma)
\]

\[
H_0=n_x\sigma_x+n_y\sigma_y+n_z\sigma_z
\]

### 3.3 Spinor carrier

| Layer | Pure math | Meaning |
|---|---|---|
| normalized spinor carrier | \(S^3=\{\psi\in\mathbb C^2:\|\psi\|=1\}\) | unit spinor carrier |
| Hopf projection | \(\pi(\psi)=\psi^\dagger \vec \sigma \psi \in S^2\) | map from spinor carrier to Bloch sphere |
| density reduction | \(\rho(\psi)=|\psi\rangle\langle\psi|=\frac12(I+\vec r\cdot\vec \sigma)\) | spinor to density matrix |

So the first geometry ladder is:

\[
\psi\in S^3 \to \pi(\psi)\in S^2 \to \rho(\psi)\in D(\mathbb C^2)
\]

### 3.4 Hopf chart and nested tori

Local chart:

\[
\psi_s(\phi,\chi;\eta)=
\begin{pmatrix}
e^{i(\phi+\chi)}\cos\eta\\
e^{i(\phi-\chi)}\sin\eta
\end{pmatrix},
\qquad s\in\{L,R\}
\]

Torus foliation:

\[
T_\eta=\{\psi_s(\phi,\chi;\eta):\phi,\chi\in[0,2\pi)\}\subset S^3
\]

Special torus:

\[
\eta=\frac{\pi}{4}
\]

gives the Clifford torus.

So:

| Layer | Pure math | Meaning |
|---|---|---|
| torus stratum | \(T_\eta\subset S^3\) | one nested Hopf torus |
| Clifford torus | \(T_{\pi/4}\) | symmetric special torus |
| nested Hopf tori | \(\{T_\eta\}_{\eta\in[0,\pi/2]}\) | torus family inside \(S^3\) |

### 3.5 Fiber/base loop geometry

Hopf connection:

\[
\mathcal A=-i\psi^\dagger d\psi=d\phi+\cos(2\eta)\,d\chi
\]

Fiber loop:

\[
\gamma_{\mathrm{fiber}}^s(u)=\psi_s(\phi_0+u,\chi_0;\eta_0)
\]

Base loop:

\[
\gamma_{\mathrm{base}}^s(u)=\psi_s(\phi_0-\cos(2\eta_0)u,\chi_0+u;\eta_0)
\]

Horizontal condition:

\[
\mathcal A(\dot\gamma_{\mathrm{base}}^s)=0
\]

Density behavior:

\[
\rho_{\mathrm{fiber}}^s(u)=|\gamma_{\mathrm{fiber}}^s(u)\rangle\langle\gamma_{\mathrm{fiber}}^s(u)|
=\rho_{\mathrm{fiber}}^s(0)
\]

\[
\rho_{\mathrm{base}}^s(u)=|\gamma_{\mathrm{base}}^s(u)\rangle\langle\gamma_{\mathrm{base}}^s(u)|
\]

So the strongest geometry packet is:

\[
S^3 \to T_\eta \to \{\gamma_{\mathrm{fiber}},\gamma_{\mathrm{base}}\} \to \rho(\psi)
\]

This is geometry.
It is still not `Ax0`.

### 3.6 Weyl working layer

This is the strongest current working layer above the direct carrier geometry:

| Layer | Pure math | Meaning |
|---|---|---|
| left spinor | \(\psi_L\in S^3\subset \mathbb C^2\) | left Weyl sheet |
| right spinor | \(\psi_R\in S^3\subset \mathbb C^2\) | right Weyl sheet |
| left density | \(\rho_L=\psi_L\psi_L^\dagger\) | left sheet density |
| right density | \(\rho_R=\psi_R\psi_R^\dagger\) | right sheet density |
| left Hamiltonian | \(H_L=+H_0\) | coherent sign |
| right Hamiltonian | \(H_R=-H_0\) | opposite coherent sign |

So the working stack is:

\[
\text{constraints} \to M(C) \to S^3 \to T_\eta \to \gamma_{\mathrm{fiber/base}} \to (\psi_L,\psi_R,\rho_L,\rho_R)
\]

That gives you the geometry and Weyl layer.

---

## 4. Allowed Mathematics On The Manifold

This section lists the strongest currently admitted math objects that live on top of the constraint-built geometry.

### 4.1 Admitted base mathematics

| Layer | Pure math | Role |
|---|---|---|
| density language | \(\rho\in D(\mathbb C^2)\) | admissible state language |
| observables / probes | \(O=O^\dagger,\ p_O(\rho)=\operatorname{Tr}(O\rho)\) | admissible scalar readout |
| operator basis | \(I,\sigma_x,\sigma_y,\sigma_z,\sigma_\pm\) | minimal local operator algebra |
| Hamiltonian form | \(H_0=n_x\sigma_x+n_y\sigma_y+n_z\sigma_z\) | coherent generator coordinates |
| bipartite state space | \(D(H_A\otimes H_B)\) | minimum QIT domain for `Ax0` |
| entropy primitive | \(S(\rho)=-\operatorname{Tr}(\rho\log\rho)\) | single-state mixedness |
| cut correlation | \(I(A:B)_\rho\) | unsigned total correlation |
| cut conditional entropy | \(S(A|B)_\rho\) | signed cut entropy |
| coherent information | \(I_c(A\rangle B)_\rho=-S(A|B)_\rho\) | strongest simple signed `Ax0` candidate |

### 4.2 What is admitted but not yet finished

| Object | Status | Why it matters |
|---|---|---|
| pointwise pullback \(\phi_0(x)=\Phi_0(\rho_{AB}(x))\) | admitted shape, unfinished bridge | gives the manifold-local `Ax0` form |
| history form \(\phi_0[h]\) | admitted shape, unfinished cut family | lets `Ax0` live on trajectories |
| shell-cut family \(\sum_r w_r I_c(A_r\rangle B_r)\) | admitted global form, unfinished shell algebra | strongest current global read |
| Weyl-sheet layer \((\psi_L,\psi_R,\rho_L,\rho_R)\) | compiled working layer | useful runtime realization, not a final bridge by itself |

### 4.3 What is not enough by itself

| Object | Why it is insufficient |
|---|---|
| one isolated spinor \(\psi\) | not bipartite |
| one reduced density \(\rho(\psi)\) | not a cut state |
| raw torus latitude \(\eta\) | geometry coordinate only |
| raw fiber/base transport | geometry only, not `Ax0` by itself |
| mutual information alone | useful diagnostic, but cannot express the signed negative-entropy side |

So the current build order is:

\[
\text{constraints} \to M(C) \to \text{geometry} \to \text{admitted math on that geometry} \to Ax0
\]

---

## 5. What Axis 0 Is

Now `Ax0` can be stated separately.

### 5.1 Formal role

`Ax0` is not a piece of the carrier geometry.

It is a slice on the manifold:

\[
A_0:M(C)\to V_0
\]

But in QIT form it acts through a cut-state functional:

\[
\Phi_0(\rho_{AB})
\]

So the minimum honest form is:

\[
\phi_0(x)=\Phi_0(\rho_{AB}(x))
\]

or, in history form,

\[
\phi_0[h]=\frac1T\int_0^T \sum_{c\in\mathcal C} w_c\, I_c(c;\rho_h(t))\,dt
\]

### 5.2 Why von Neumann entropy alone was close but not enough

Your original instinct was reasonable:

- von Neumann entropy
\[
S(\rho)=-\operatorname{Tr}(\rho\log\rho)
\]
is the clean QIT entropy primitive
- it does measure mixedness / information loss / coarse-graining pressure

But by itself it is usually not the right final `Ax0` object because:

- it is a one-state scalar
- it does not directly tell you about correlation across a cut
- it does not naturally give the “negative entropy” effect you were looking for

So it is a good primitive, but not the finished `Ax0` kernel.

### 5.3 Why mutual information felt more aligned

Mutual information is:

\[
I(A:B)_\rho = S(\rho_A)+S(\rho_B)-S(\rho_{AB})
\]

This is much closer to what you were after because it is explicitly about:

- correlation
- information shared across a cut
- bookkeeping between two domains

So it matches your “information rather than just raw mixedness” intuition.

But it also has a limit:

- \(I(A:B)\ge 0\)

So it cannot itself be the signed “negative entropy” quantity.

### 5.4 The strongest simple signed candidate

Conditional entropy:

\[
S(A|B)_\rho = S(\rho_{AB})-S(\rho_B)
\]

Coherent information:

\[
I_c(A\rangle B)_\rho = -S(A|B)_\rho
\]

This is the strongest current simple candidate because:

- it is fully QIT-native
- it is directly about a cut
- it can be negative on the conditional-entropy side
- it fits your search for “negative entropy that is really about information”

So the clean current kernel ranking is:

| Candidate | Pure math | Role |
|---|---|---|
| von Neumann entropy | \(S(\rho)\) | primitive entropy, good base measure, not enough by itself |
| mutual information | \(I(A:B)\) | best total-correlation companion diagnostic |
| conditional entropy | \(S(A|B)\) | gives the negative-entropy side directly |
| coherent information | \(I_c(A\rangle B)=-S(A|B)\) | strongest simple working `Ax0` kernel |

### 5.5 Bridge-family relation

The bridge side is now narrowed enough that the family relation should stay explicit.

Current differentiated read:

- `Xi_hist` remains the strongest live executable bridge family
- shell/interior-boundary remains the strongest doctrine-facing cut family
- point-reference remains the strongest live pointwise discriminator

Those are not three ways of saying the same thing.

They are three different strengths:

| Family | Current strength | What it does not earn by itself |
|---|---|---|
| `Xi_hist` | strongest executable bridge family | final canon `Xi` |
| shell/interior-boundary / strict shell replacement | strongest doctrine-facing cut route | strongest executable bridge family |
| point-reference | strongest live pointwise discriminator | finished bridge theorem or final cut theorem |

So the safe combined read is:

\[
\text{history} = \text{best executable bridge}
\]

\[
\text{shell} = \text{best doctrine-facing cut route}
\]

\[
\text{point-reference} = \text{best pointwise discriminator}
\]

and not one fake closure where all three are silently identified.

Bridge relation owner packet:

- [AXIS0_BRIDGE_RELATION_PACKET.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_BRIDGE_RELATION_PACKET.md)
| shell-cut coherent family | \(\sum_r w_r I_c(A_r\rangle B_r)\) | strongest current global form |

So the clean sentence is:

`Ax0` is best understood as a negative-entropy correlation functional on a cut state, not as plain von Neumann entropy on one density matrix.

---

## 6. The Bridge Problem

This is the missing step:

\[
\Xi:\text{geometry sample or history window}\to \rho_{AB}
\]

Without `\Xi`, you only have:

- geometry
- spinors
- densities
- loops

But you do not yet have the bipartite cut-state that `Ax0` measures.

So the full stack is:

\[
\text{constraints} \to M(C) \to \text{geometry} \to \Xi \to \rho_{AB} \to \Phi_0(\rho_{AB})
\]

That is the separation you were asking for.

---

## 7. Best Current Lock

### Constraints and geometry

| Layer | Current lock |
|---|---|
| root constraints | `F01_FINITUDE`, `N01_NONCOMMUTATION` |
| geometry | constraint manifold `M(C)` and its induced compatibility structure |
| concrete realization | \(S^3 \to S^2\), Hopf chart, \(T_\eta\), Clifford torus, nested Hopf tori, fiber/base loops |
| Weyl working layer | left/right Weyl spinors and sign-flipped Hamiltonians |

### Axis 0

| Layer | Current lock |
|---|---|
| what it is | a cut-state correlation functional on the manifold |
| strongest simple kernel | \(I_c(A\rangle B)=-S(A|B)\) |
| strongest companion | \(I(A:B)\) |
| strongest global form | \(\sum_r w_r I_c(A_r\rangle B_r)\) |
| unresolved core | the bridge \(\Xi\) and the exact cut \(A|B\) |

### Working summary

\[
\text{geometry} \neq Ax0
\]

\[
Ax0 = \Phi_0(\rho_{AB})\ \text{after a bridge } \Xi
\]

\[
\Phi_0 \text{ is most likely a coherent-information / negative-conditional-entropy family}
\]

---

## 8. Do Not Smooth

- Do not collapse root constraints into geometry.
- Do not collapse geometry into the later `Ax0` functional.
- Do not treat every runtime proxy as the final kernel.
- Do not treat every bridge candidate as doctrine.
- Do not confuse Weyl-sheet realization with the exact `Ax0` cut.
- Do not confuse mutual information with the full signed primitive.
- Do not confuse torus transport with `Ax0` itself.
- Do not force one final `Xi` before the executable bridge is actually stable.

---

## 9. Practical Reading

If you want the short practical read:

- the root of the system is **constraint**
- the next layer is **geometry**
- the next layer is **allowed mathematics on that constrained geometry**
- the next layer is **spinor / Weyl / torus realization**
- only after that do you define **Axis 0**
- `Axis 0` is not “the manifold itself”
- `Axis 0` is the negative-entropy / correlation-gradient functional living on a cut-state attached to that manifold
