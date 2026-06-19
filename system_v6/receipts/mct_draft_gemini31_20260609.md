### 1. State Space Definition
Let $t \in \mathbb{N}$ be the discrete update step. The Finite Dynamic Admissibility Object is a tuple $M(C,t) = (S_t, V_t, P_t, \sim_t, E_t, Adm_t)$ where:
*   $S_t$: A finite set of states.
*   $V_t$: A finite set of probe values.
*   $P_t$: A finite family of probe functions $p: S_t \to V_t$.
*   $\sim_t$: An equivalence relation where $x \sim_t y \iff \forall p \in P_t, p(x) = p(y)$. The quotient space is $Q_t = S_t / \sim_t$.
*   $E_t \subseteq S_t \times S_t$: A directed adjacency relation.
*   $C$: A fixed, finite set of boolean constraints $c: V_t^{|P_t|} \to \{0,1\}$.
*   $Adm_t \subseteq S_t$: The admissibility predicate, defined as $Adm_t = \{x \in S_t \mid \forall c \in C, c(\{p(x)\}_{p \in P_t}) = 1\}$.

### 2. The UPDATE Map ($U_t$)
The transition $U_t: M(C,t) \to M(C,t+1)$ is a composition of five primitive finite operations. 
*[Choice point: Operations can be applied simultaneously or as a strict sequence. We define them as independent sequential transformations.]*

1.  **COMPRESSION** ($U_{comp}$): Quotient refinement collapse.
    *   $P_{t+1} = P_t \setminus P_{drop}$ for some $P_{drop} \subset P_t$.
    *   $S_{t+1} = S_t$, $E_{t+1} = E_t$.
2.  **EXPANSION** ($U_{exp}$): New distinctions.
    *   $P_{t+1} = P_t \cup P_{new}$ for a finite set of new functions $P_{new} \subset V_t^{S_t}$.
    *   $S_{t+1} = S_t$, $E_{t+1} = E_t$.
3.  **WARPING** ($U_{warp}$): Relation modification.
    *   $E_{t+1} = (E_t \cup \Delta E^+) \setminus \Delta E^-$ for finite sets $\Delta E^+, \Delta E^- \subseteq S_t \times S_t$.
    *   $S_{t+1} = S_t$, $P_{t+1} = P_t$.
4.  **FOLDING** ($U_{fold}$): Partial surjection gluing.
    *   Given a surjection $\pi: S_t \to S_{t+1}$ where $\ker(\pi) \subseteq \sim_t$ *[Choice point: If $\ker(\pi) \not\subseteq \sim_t$, an aggregation function like $\max$ over $\pi^{-1}$ is required]*.
    *   $E_{t+1} = \{(\pi(u), \pi(v)) \mid (u,v) \in E_t\}$.
    *   $P_{t+1} = \{p' \mid p'(\pi(x)) = p(x), p \in P_t\}$.
5.  **REINDEXING** ($U_{reidx}$): Content-preserving relabeling.
    *   Given a bijection $\phi: S_t \to S_{t+1}$.
    *   $E_{t+1} = \{(\phi(u), \phi(v)) \mid (u,v) \in E_t\}$.
    *   $P_{t+1} = \{p \circ \phi^{-1} \mid p \in P_t\}$.

### 3. Invariants and Monotones
Let $H(P_t) = -\sum_{q \in Q_t} \frac{|q|}{|S_t|} \log_2 \frac{|q|}{|S_t|}$ be the Shannon entropy of the equivalence class distribution. Let $cc(E_t)$ be the number of weakly connected components in $E_t$.

| Primitive | Conserved (Invariant) | Monotone Quantity | Falsifiable Claim (SMT Verification) |
| :--- | :--- | :--- | :--- |
| **COMPRESSION** | $|S_t|, E_t$ | $|Q_{t+1}| \le |Q_t|$ | $\exists P_{drop} \text{ s.t. } |Q_{t+1}| > |Q_t|$ is **UNSAT**. |
| **EXPANSION** | $|S_t|, E_t$ | $H(P_{t+1}) \ge H(P_t)$ | $\exists P_{new} \text{ s.t. } H(P_{t+1}) < H(P_t)$ is **UNSAT**. |
| **WARPING** | $|S_t|, P_t, |Q_t|$ | If $\Delta E^- = \emptyset$, $cc(E_{t+1}) \le cc(E_t)$ | If $\Delta E^- = \emptyset$, $cc(E_{t+1}) > cc(E_t)$ is **UNSAT**. |
| **FOLDING** | $H(P_t)$ (if uniform) | $|S_{t+1}| \le |S_t|$ | $\exists \pi \text{ s.t. } |S_{t+1}| > |S_t|$ is **UNSAT**. |
| **REINDEXING** | $|S_t|, |Q_t|, |E_t|, H(P_t)$ | $|Adm_{t+1}| = |Adm_t|$ | $\exists \phi \text{ s.t. } |Adm_{t+1}| \neq |Adm_t|$ is **UNSAT**. |

### 4. The RATCHET Condition
A sequence of updates $\vec{U} = (U_A, U_B)$ satisfies the **Ratchet Condition** (order-sensitivity) if the operators do not commute up to isomorphism: $[U_B \circ U_A](M) \not\cong [U_A \circ U_B](M)$.
*   **Finite Witness:** A tuple $W = (x, y, U_A, U_B)$ where $x,y \in S_t$ such that $(x,y) \in \sim_{BA}$ but $(x,y) \notin \sim_{AB}$ (or vice versa), or where $x \in Adm_{BA} \oplus x \in Adm_{AB}$.

### 5. Minimal Test Fixture
**Initial State ($t=0$):**
*   $S_0 = \{0, 1, 2, 3, 4, 5, 6, 7\}$
*   $P_0 = \{p_1, p_2\}$ where $p_1(x) = x \bmod 2$, $p_2(x) = x \bmod 4$.
*   $E_0 = \{(x, (x+1) \bmod 8) \mid x \in S_0\}$.
*   $C = \{c_1\}$ where $c_1(v_1, v_2) \iff (v_1 = 0)$. Thus $Adm_0 = \{0, 2, 4, 6\}$.

**Update Sequence:**
1.  $t=0 \to 1$ (**COMPRESSION**): $P_{drop} = \{p_2\}$.
2.  $t=1 \to 2$ (**WARPING**): $\Delta E^+ = \{(x, (x+4) \bmod 8)\}$, $\Delta E^- = \emptyset$.
3.  $t=2 \to 3$ (**FOLDING**): Surjection $\pi(x) = x \bmod 4$. (Valid since $\ker(\pi) \subseteq \sim_2$).

**Predicted Values (Fixture Pins):**
| $t$ | $|S_t|$ | $P_t$ | $|Q_t|$ | $H(P_t)$ | $|E_t|$ | $cc(E_t)$ | $|Adm_t|$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **0** | 8 | $\{p_1, p_2\}$ | 4 | 2.0 | 8 | 1 | 4 |
| **1** | 8 | $\{p_1\}$ | 2 | 1.0 | 8 | 1 | 4 |
| **2** | 8 | $\{p_1\}$ | 2 | 1.0 | 16 | 1 | 4 |
| **3** | 4 | $\{p_1'\}$ | 2 | 1.0 | 4 | 1 | 2 |

**Kill-Controls (SMT Assertions expected to fail/UNSAT):**
1.  **Fake Compression Control:** Assert $\exists P_{drop} \subset P_n$ such that $(\forall x,y \in S_n, p_{drop}(x) = p_{drop}(y)) \land (|Q_{n+1}| < |Q_n|)$. *(Fails because dropping a constant probe cannot merge distinct classes).*
2.  **Fake Expansion Control:** Assert $\exists p_{new}$ such that $(\forall x \in S_n, p_{new}(x) = p_{old}(x)) \land (H(P_{n+1}) > H(P_n))$. *(Fails because adding a redundant probe yields zero information gain).*
3.  **Fake Ratchet Control:** Let $U_A = U_{warp}(\Delta E^+ = \{(0,4)\})$ and $U_B = U_{fold}(\pi(x) = x \bmod 4)$. Assert $[U_B \circ U_A](E) = [U_A \circ U_B](E)$. *(Fails because folding first collapses 0 and 4, making the subsequent warp an invalid self-loop or redundant edge, whereas warping first creates a valid edge that is then absorbed by the fold).*