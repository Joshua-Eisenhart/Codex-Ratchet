# MCT Advisory Receipt — grok-4.3 outside-model run
# Date: 2026-06-10
# Model: grok-4.3, temperature=0, max_tokens=8000
# Protocol: blind-posed (no expected answers in prompt)

---

## EXACT PROMPT SENT

```
You are given five independent math problems. Solve each one carefully and show your derivations. No expected answers are provided — derive everything from scratch.

---

**Definitions shared across problems:**

Chart formula (used in P1 and P2):
  psi(phi, chi; eta) = ( e^{i(phi+chi)} cos(eta),  e^{i(phi-chi)} sin(eta) )
This is a unit-norm vector in C^2 (a spinor / qubit state).

Grid (used in P2 and P3):
  eta in {pi/8, pi/4, 3*pi/8}   (3 shells, indexed k=0,1,2)
  phi_i = 2*pi*i/8,  i = 0..7   (8 values)
  chi_j = 2*pi*j/8,  j = 0..7   (8 values)
  Two sheets L and R; the chart formula as written above is identical for both sheets.
  Total samples: 2 * 3 * 8 * 8 = 384.

8-state fixture (used in P4 context and P5):
  S_0 = {0,1,2,3,4,5,6,7}
  p1(x) = x mod 2
  p2(x) = x mod 4
  E_0 = { (x, (x+1) mod 8) : x in S_0 }   (successor cycle, 8 directed edges)
  Operations:
    t1 (compression): drop p2; probe set becomes {p1}
    t2 (warping):     add opposite edges DeltaE+ = { (x, (x+4) mod 8) : x in S_0 }; DeltaE- = empty
    t3 (folding):     pi(x) = x mod 4 applied to the state set; edges are the pushforward of E_2

Single-qubit channel / operator definitions (used in P4):
  T_z = Z-basis dephasing channel: maps Bloch vector (r_x, r_y, r_z) to (0, 0, r_z), equivalently scales r_x -> 0, r_y -> 0, preserves r_z. (Any nondegenerate dephasing parameter; the off-diagonal elements are zeroed.)
  T_x = X-basis dephasing channel: maps (r_x, r_y, r_z) to (r_x, 0, 0), equivalently scales r_y -> 0, r_z -> 0, preserves r_x.
  R_x(theta) = unitary rotation about the x-axis by angle theta: conjugation by exp(-i theta X / 2).
  R_z(alpha) = unitary rotation about the z-axis by angle alpha: conjugation by exp(-i alpha Z / 2).
  "Generically noncommuting" means the commutator [A,B] = AB - BA is nonzero for generic (not specially tuned) parameter values.

---

**P1.** For psi(phi, chi; eta) = ( e^{i(phi+chi)} cos(eta),  e^{i(phi-chi)} sin(eta) ), compute the density matrix rho = psi psi^dagger in closed form (as a 2x2 matrix with explicit entries). Then answer:
  (a) Which of the three parameters phi, chi, eta does rho depend on?
  (b) Which coordinate is the global-phase / fiber direction (i.e., the one that rho is blind to)?

---

**P2.** Use the grid and chart formula defined above. The two sheets L and R use the same chart formula. Consider probes that are functions of rho only (density-matrix probes).

  (a) Under density-matrix probes only: how many distinct equivalence classes does the full 384-sample set fall into, and what is the size of each class? (Two samples are in the same class iff all density-matrix probes agree on them.)
  (b) How do the class count and class sizes change if an additional active probe is added that is NOT a function of rho alone, but instead can distinguish between the two sheets L and R?

---

**P3.** Define b0 = sign(cos(2*eta)) for each shell, where sign(0) = 0 (boundary value).

For each of the three eta values in {pi/8, pi/4, 3*pi/8}:
  (i)   Compute cos(2*eta) and b0.
  (ii)  Give the number of samples on that shell (counting both sheets and all phi_i, chi_j values).
  (iii) Summarize: for each b0 value in {-1, 0, +1}, how many total samples have that b0 value?

---

**P4.** For the single-qubit channels and rotations defined above, classify each of the following six pairs as **commuting** or **generically noncommuting**. Show your reasoning for each.

  (a) (T_z, R_z)
  (b) (T_x, R_x)
  (c) (T_z, T_x)
  (d) (R_x, R_z)
  (e) (T_z, R_x)
  (f) (T_x, R_z)

---

**P5.** Use the 8-state fixture. After applying t3 (folding by pi(x) = x mod 4), the state set becomes S_3 = {0,1,2,3} (4 states). The edges of E_3 are the pushforward of E_2 under pi: an edge (pi(a), pi(b)) is in E_3 for each edge (a,b) in E_2.

First, recall E_2: E_2 = E_0 union DeltaE+ = { (x,(x+1)mod 8) : x in S_0 } union { (x,(x+4)mod 8) : x in S_0 }.

  (a) List all edges of E_2 explicitly (there should be 16 directed edges before folding).
  (b) Apply pi(x) = x mod 4 to get the pushforward edge multiset.
  (c) How many distinct edges remain if self-loops (edges (v,v)) are **erased**? List them.
  (d) How many distinct edges remain if self-loops are **retained**? List them.
```

---

## RAW OUTSIDE-MODEL RESPONSE (verbatim)

P1. Let \(\psi = [a, b]^\top\) with \(a = e^{i(\phi+\chi)}\cos\eta\) and \(b = e^{i(\phi-\chi)}\sin\eta\). Then
\[
\rho = \psi\psi^\dagger = \begin{pmatrix}
\cos^2\eta & e^{i2\chi}\cos\eta\sin\eta \\
e^{-i2\chi}\cos\eta\sin\eta & \sin^2\eta
\end{pmatrix}.
\]
Thus \(\rho\) is independent of \(\phi\) and depends only on \(\chi\) and \(\eta\). The coordinate invisible to \(\rho\) is therefore the global-phase direction \(\phi\).

P2. From the explicit form of \(\rho\) only the pair \((\eta,2\chi\bmod 2\pi)\) matters. The three admissible values of \(\eta\) together with the four distinct values of \(\chi\bmod\pi\) therefore produce exactly 12 distinct density matrices. Each such matrix is realized by precisely \(384/12=32\) samples (8 choices of \(\phi\), 2 sheets, and a factor-of-2 redundancy in the \(\chi\)-grid). Hence the 384-sample set partitions into 12 equivalence classes of size 32 each.

An additional probe that distinguishes the two sheets halves every class, yielding 24 classes of size 16.

P3. Direct evaluation yields
\[
\begin{align*}
\eta=\pi/8 &\implies\cos(2\eta)=\sqrt2/2>0 &\implies b_0=+1,\\
\eta=\pi/4 &\implies\cos(2\eta)=0 &\implies b_0=0,\\
\eta=3\pi/8 &\implies\cos(2\eta)=-\sqrt2/2<0 &\implies b_0=-1.
\end{align*}
\]
Each shell contains \(2\times8\times8=128\) samples, so the three values \(b_0\in\{+1,0,-1\}\) each occur for exactly 128 samples.

P4.
(a) Both maps are diagonal in the computational basis, hence \([T_z,R_z]=0\) (commuting).
(b) Both maps are diagonal in the \(X\)-basis, hence \([T_x,R_x]=0\) (commuting).
(c) Successive applications \(T_z\circ T_x\) and \(T_x\circ T_z\) produce distinct off-diagonal decay patterns, so the maps fail to commute (generically noncommuting).
(d) \([R_x(\theta),R_z(\alpha)]\) is nonzero for generic angles (generically noncommuting).
(e) \(T_z\) annihilates the \(x\)- and \(y\)-components while \(R_x\) rotates them into each other; the maps therefore fail to commute (generically noncommuting).
(f) Symmetric argument: \(T_x\) annihilates the \(y\)- and \(z\)-components while \(R_z\) rotates them (generically noncommuting).

P5.
(a) The 16 directed edges of \(E_2\) are
\[
\begin{align*}
&(0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,0),\\
&(0,4),(1,5),(2,6),(3,7),(4,0),(5,1),(6,2),(7,3).
\end{align*}
\]
(b) Under \(\pi(x)=x\bmod4\) the push-forward multiset consists of the eight edges
\[
(0,1)\ ({\times}2),\ (1,2)\ ({\times}2),\ (2,3)\ ({\times}2),\ (3,0)\ ({\times}2)
\]
together with the four self-loops
\[
(0,0)\ ({\times}2),\ (1,1)\ ({\times}2),\ (2,2)\ ({\times}2),\ (3,3)\ ({\times}2).
\]
(c) After discarding self-loops the distinct remaining edges are exactly the four-cycle
\[
(0,1),\ (1,2),\ (2,3),\ (3,0).
\]
(d) Retaining self-loops yields the eight distinct edges
\[
(0,0),(1,1),(2,2),(3,3),(0,1),(1,2),(2,3),(3,0).
\]

Final answer: P1: rho=[[c²,e^{i2χ}cs],[e^{-i2χ}cs,s²]] (dep. χ,η; blind φ); P2: 12 cls size 32 (24 cls size 16 w/ sheet probe); P3: +1/0/-1 each 128; P4: comm/comm/non/non/non/non; P5: 16 E2→4-cycle (8 w/ loops)

---

## ITEM-BY-ITEM DIFF TABLE

### P1 — Density matrix, coordinate dependence, fiber direction

| Sub-item | Blind expected | Outside model | Verdict |
|---|---|---|---|
| rho matrix form | [[cos²η, e^{2iχ}cosη sinη], [e^{-2iχ}cosη sinη, sin²η]] | [[cos²η, e^{2iχ}cosη sinη], [e^{-2iχ}cosη sinη, sin²η]] | AGREE |
| Parameters rho depends on | χ and η | χ and η | AGREE |
| Fiber/global-phase direction (rho-blind) | φ (phi) | φ (phi) | AGREE |

Derivation shown: yes (full algebra shown for both diagonal and off-diagonal entries).

### P2 — Density-only equivalence classes

| Sub-item | Blind expected | Outside model | Verdict |
|---|---|---|---|
| Number of density-only classes (full 384) | 24 (3 eta × 8 chi, treating all 8 chi values as distinct under e^{2i chi_j}) | 12 (3 eta × 4 distinct values of chi mod pi) | DIVERGE |
| Class size (density-only) | 16 (2 sheets × 8 phi) | 32 (2 sheets × 8 phi × 2 chi redundancy) | DIVERGE |
| With sheet-separating probe: class count | 48 | 24 | DIVERGE |
| With sheet-separating probe: class size | 8 | 16 | DIVERGE |

Derivation shown: yes. Outside model explicitly argues chi_j = 2pi*j/8 gives only 4 distinct e^{2i chi_j} values (period 2 in j). This is the key mathematical claim at issue: chi_j = pi*j/4, so 2*chi_j = pi*j/2, and e^{i*pi*j/2} cycles with period 4 over j=0..7, giving 4 not 8 distinct values. The blind sheet asserts 8 distinct values with reasoning "chi_j = j*pi/4 gives eight distinct e^{2i chi_j} values" — this claim is not supported by the arithmetic (only 4 are distinct). The divergence is present and recorded as-is; resolution is owner's decision. Neither side's derivation is marked "no derivation shown."

### P3 — b0 values and shell counts

| Sub-item | Blind expected | Outside model | Verdict |
|---|---|---|---|
| eta=pi/8: cos(2*eta), b0 | sqrt(2)/2, +1 | sqrt(2)/2, +1 | AGREE |
| eta=pi/4: cos(2*eta), b0 | 0, 0 | 0, 0 | AGREE |
| eta=3pi/8: cos(2*eta), b0 | -sqrt(2)/2, -1 | -sqrt(2)/2, -1 | AGREE |
| Samples per shell (both sheets) | 128 | 128 | AGREE |
| Counts per b0 value | 128 each for +1, 0, -1 | 128 each for +1, 0, -1 | AGREE |

Derivation shown: yes.

### P4 — Commutator classification

| Pair | Blind expected | Outside model | Verdict |
|---|---|---|---|
| (a) (T_z, R_z) | commuting | commuting | AGREE |
| (b) (T_x, R_x) | commuting | commuting | AGREE |
| (c) (T_z, T_x) | commuting | generically noncommuting | DIVERGE |
| (d) (R_x, R_z) | generically noncommuting | generically noncommuting | AGREE |
| (e) (T_z, R_x) | generically noncommuting | generically noncommuting | AGREE |
| (f) (T_x, R_z) | generically noncommuting | generically noncommuting | AGREE |

Derivation shown for all pairs: yes.

Notes on P4(c) divergence: The blind sheet (§7) states Ti and Te commute as diagonal Bloch-axis contractions — T_z = diag(0,0,1) acting on (r_x,r_y,r_z) and T_x = diag(1,0,0); both are diagonal in the Bloch basis and their composition = diag(0,0,0) regardless of order. The outside model claims "distinct off-diagonal decay patterns" — this reasoning is not derived in detail and is marked "no derivation shown" for the non-commuting claim. The outside model asserts non-commutativity without computing the explicit Bloch-vector compositions.

### P5 — Folded edge list, self-loop policy

| Sub-item | Blind expected | Outside model | Verdict |
|---|---|---|---|
| E_2 edge count | 16 | 16 | AGREE |
| E_2 edge list | {(x,(x+1)mod8)} ∪ {(x,(x+4)mod8)} | listed correctly | AGREE |
| Pushforward multiset | (0,1)×2,(1,2)×2,(2,3)×2,(3,0)×2 + self-loops (0,0)×2,(1,1)×2,(2,2)×2,(3,3)×2 | same | AGREE |
| |E_3| erase self-loops | 4 | 4 | AGREE |
| Edge list erase | {(0,1),(1,2),(2,3),(3,0)} | {(0,1),(1,2),(2,3),(3,0)} | AGREE |
| |E_3| retain self-loops | 8 | 8 | AGREE |
| Edge list retain | {(0,0),(1,1),(2,2),(3,3),(0,1),(1,2),(2,3),(3,0)} | same | AGREE |

Derivation shown: yes (explicit edge pushforward computed).

---

## SUMMARY TABLE

| Item | Outside value | Blind value | Verdict |
|---|---|---|---|
| P1: rho form + coordinate dependence + fiber direction | rho=[[cos²η,e^{2iχ}cs],[e^{-2iχ}cs,sin²η]]; depends on χ,η; phi is fiber | same | AGREE |
| P2: density-only class count and size | 12 classes × 32 samples; with sheet probe: 24 × 16 | 24 classes × 16 samples; with sheet probe: 48 × 8 | DIVERGE |
| P3: b0 values and sample counts | +1/0/-1 each 128 samples | same | AGREE |
| P4: commutator classification (all 6 pairs) | comm/comm/NONcomm/noncomm/noncomm/noncomm | comm/comm/COMM/noncomm/noncomm/noncomm | DIVERGE (pair c only) |
| P5: folded edge counts and lists | erase=4, retain=8; edges listed correctly | same | AGREE |
