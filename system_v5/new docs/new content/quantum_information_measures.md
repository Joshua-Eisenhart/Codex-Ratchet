# Quantum Information Measures: Complete Reference

## Reference: Wilde "Quantum Information Theory" (2nd ed. 2017), Ohya & Petz "Quantum Entropy and Its Use" (1993)

---

## 1. Von Neumann Entropy

**Definition**: For density matrix rho on C^d:

    S(rho) = -Tr(rho log rho) = -sum_{i=1}^{d} lambda_i log lambda_i

where lambda_i are the eigenvalues of rho and log is base 2 (for bits) or natural (for nats).

Convention: 0 log 0 = 0 (by continuity of x log x at x = 0).

### 1.1 Properties

**(P1) Non-negativity**: S(rho) >= 0. Equality iff rho is pure.

**(P2) Maximum**: S(rho) <= log d. Equality iff rho = I/d (maximally mixed).

**(P3) Concavity**: S(sum_i p_i rho_i) >= sum_i p_i S(rho_i).
Proof sketch: Follows from operator concavity of -x log x and Klein's inequality.

**(P4) Unitary invariance**: S(U rho U^dagger) = S(rho) for all unitaries U.

**(P5) Additivity on products**: S(rho_A tensor rho_B) = S(rho_A) + S(rho_B).

**(P6) Subadditivity**: S(rho_{AB}) <= S(rho_A) + S(rho_B).
Equality iff rho_{AB} = rho_A tensor rho_B (product state).

**(P7) Araki-Lieb (triangle inequality)**: |S(rho_A) - S(rho_B)| <= S(rho_{AB}).
Equality conditions: For pure states, S(rho_A) = S(rho_B) and S(rho_{AB}) = 0, so Araki-Lieb is tight.

**(P8) Strong subadditivity (SSA)**: For tripartite state rho_{ABC}:

    S(rho_{ABC}) + S(rho_B) <= S(rho_{AB}) + S(rho_{BC})

This is equivalent to each of:
- S(A|BC) <= S(A|B)  [conditioning reduces entropy]
- I(A:C|B) >= 0  [conditional mutual information non-negative]

Proof: Lieb & Ruskai (1973). Uses Lieb's concavity theorem: the map A -> Tr(exp(log A + K)) is concave for fixed Hermitian K.

**SSA equality condition** (Hayden, Jozsa, Petz, Winter 2004): Equality in SSA iff there exists a decomposition of H_B = direct_sum_j (H_{B_j^L} tensor H_{B_j^R}) such that:

    rho_{ABC} = sum_j p_j rho_{AB_j^L} tensor rho_{B_j^R C}

(Quantum Markov chain condition.)

### 1.2 Continuity: Fannes-Audenaert Inequality

For rho, sigma on C^d with T = (1/2)||rho - sigma||_1 <= 1 - 1/d:

    |S(rho) - S(sigma)| <= T log(d-1) + h(T)

where h(T) = -T log T - (1-T) log(1-T) is the binary entropy.

This is tight (Audenaert 2007 improved the original Fannes bound).

---

## 2. Renyi Entropies

**Definition**: For alpha >= 0, alpha =/= 1:

    S_alpha(rho) = (1/(1-alpha)) log Tr(rho^alpha)

### 2.1 Special Values and Limits

- **alpha -> 0**: S_0(rho) = log(rank(rho)) = Hartley entropy
- **alpha -> 1**: S_1(rho) = S(rho) (von Neumann entropy, by L'Hopital)
- **alpha = 2**: S_2(rho) = -log(Tr(rho^2)) = -log(purity). Called "collision entropy."
- **alpha -> infinity**: S_inf(rho) = -log(lambda_max) = min-entropy

**Proof that alpha -> 1 gives von Neumann**:
S_alpha = log(Tr(rho^alpha))/(1-alpha). Write Tr(rho^alpha) = sum lambda_i^alpha.
At alpha = 1: numerator = log(1) = 0, denominator = 0. Apply L'Hopital:
d/d_alpha [log(sum lambda_i^alpha)] = (sum lambda_i^alpha log lambda_i) / (sum lambda_i^alpha)
At alpha = 1: = sum lambda_i log lambda_i.
d/d_alpha [1 - alpha] = -1.
So lim = -sum lambda_i log lambda_i = S(rho). QED.

### 2.2 Properties

- **Non-increasing in alpha**: S_alpha(rho) >= S_beta(rho) for alpha <= beta.
  This gives: S_0 >= S_1 >= S_2 >= S_inf.
  
- **Additivity**: S_alpha(rho tensor sigma) = S_alpha(rho) + S_alpha(sigma).

- **Non-negativity**: S_alpha(rho) >= 0 with equality iff rho is pure.

- **Maximum**: S_alpha(rho) <= log d with equality iff rho = I/d (for all alpha > 0).

### 2.3 Operational Meanings

- S_0: log of the number of outcomes with nonzero probability (dimension of support).
- S_1: Optimal compression rate (Shannon/Schumacher noiseless coding).
- S_2: -log of collision probability (relevant to randomness extraction).
- S_inf: -log of guessing probability (relevant to cryptographic security).

### 2.4 Sandwiched Renyi Relative Entropy

    D_alpha(rho || sigma) = (1/(alpha-1)) log Tr((sigma^{(1-alpha)/(2alpha)} rho sigma^{(1-alpha)/(2alpha)})^alpha)

For alpha in (0,1) union (1, infinity). Converges to quantum relative entropy as alpha -> 1.

---

## 3. Conditional Entropy

**Definition**: S(A|B) = S(AB) - S(B)

### 3.1 Key Properties

**CAN BE NEGATIVE**: This is a genuinely quantum phenomenon. No classical analog.

For a pure entangled state |Psi>_{AB}:
S(AB) = 0 (pure state), S(B) = S(A) > 0 (entangled, so reduced state is mixed).
Therefore: S(A|B) = 0 - S(B) = -S(B) < 0.

**Maximum negativity**: S(A|B) >= -log d_A. Achieved by maximally entangled state.

**Example**: For |Phi+> = (|00> + |11>)/sqrt(2):
S(AB) = 0, S(B) = 1 bit.
S(A|B) = -1 bit.

**Interpretation of negativity**: -S(A|B) = coherent information = rate of quantum state merging. If S(A|B) < 0, Alice can transfer her share of rho_{AB} to Bob using -S(A|B) ebits of entanglement per copy AND generating |S(A|B)| bits of shared entanglement.

### 3.2 Conditioning on Classical vs Quantum

For a classical-quantum state rho_{XB} = sum_x p_x |x><x| tensor rho_B^x:

    S(B|X) = sum_x p_x S(rho_B^x)

This is always >= 0 (classically conditioned quantum entropy). The negativity of S(A|B) arises specifically when B is quantum and entangled with A.

---

## 4. Mutual Information

**Definition**: I(A:B) = S(A) + S(B) - S(AB)

### 4.1 Properties

- **Non-negative**: I(A:B) >= 0 (follows from subadditivity).
- **Symmetric**: I(A:B) = I(B:A).
- **Zero iff product**: I(A:B) = 0 iff rho_{AB} = rho_A tensor rho_B.
- **Upper bound**: I(A:B) <= 2 min(S(A), S(B)).
  The factor 2 is genuinely quantum: classically I(A:B) <= min(H(A), H(B)).
- **Relation to relative entropy**: I(A:B) = S(rho_{AB} || rho_A tensor rho_B).

### 4.2 Conditional Mutual Information

    I(A:C|B) = S(AB) + S(BC) - S(ABC) - S(B)

Equivalently: I(A:C|B) = S(A|B) - S(A|BC).

**SSA restated**: I(A:C|B) >= 0 for all quantum states. (This is the content of strong subadditivity.)

### 4.3 Operational Meaning

For a quantum state rho_{AB}:
- I(A:B) = amount of total (classical + quantum) correlation.
- Can be decomposed: I(A:B) = J(A:B) + D(A:B) where J is classical correlation and D is quantum discord (see entanglement file).
- For i.i.d. many copies: I(A:B) is the rate of randomness needed to erase correlations.

---

## 5. Coherent Information

**Definition**: I_c(A>B) = S(B) - S(AB) = -S(A|B)

### 5.1 Properties

- Can be negative (for separable states with S(AB) large).
- Can be positive (for entangled states).
- NOT symmetric: I_c(A>B) =/= I_c(B>A) in general.
- For pure states: I_c(A>B) = S(A) = S(B) (reduces to entanglement entropy).

### 5.2 Channel Coherent Information

For a quantum channel N: A -> B, and input state rho_A with purification |phi>_{RA}:

    I_c(N, rho_A) = S(N(rho_A)) - S((id_R tensor N)(|phi><phi|))

**Quantum channel capacity** (Lloyd-Shor-Devetak):

    Q(N) = lim_{n->inf} (1/n) max_{rho^{(n)}} I_c(N^{tensor n}, rho^{(n)})

The regularization (limit over n copies) is generally necessary; single-letter formula is not known to hold for all channels. But for degradable channels:

    Q(N) = max_{rho} I_c(N, rho)  (single-letter formula)

---

## 6. Holevo Bound

**Setup**: Alice prepares states rho_x with probability p_x. Bob receives the ensemble {p_x, rho_x} and performs a measurement.

**Holevo quantity**:

    chi = S(rho) - sum_x p_x S(rho_x)

where rho = sum_x p_x rho_x is the average state.

**Holevo bound**: The accessible information (maximum classical mutual information between Alice's input X and Bob's measurement outcome Y) satisfies:

    I(X:Y) <= chi

**Achievability** (Holevo-Schumacher-Westmoreland): For i.i.d. many copies, the capacity is:

    C = max_{ensemble} chi({p_x, rho_x})

### 6.1 Proof Sketch of Holevo Bound

Use subadditivity and data processing.

Consider the classical-quantum state: rho_{XB} = sum_x p_x |x><x| tensor rho_x

I(X:B) = S(X) + S(B) - S(XB)
       = H({p_x}) + S(rho) - S(sum_x p_x |x><x| tensor rho_x)
       = H({p_x}) + S(rho) - (H({p_x}) + sum_x p_x S(rho_x))    [block diagonal structure]
       = S(rho) - sum_x p_x S(rho_x)
       = chi.

Now Bob measures, getting outcome Y. Data processing: I(X:Y) <= I(X:B) = chi. QED.

---

## 7. Strong Subadditivity and Its Consequences

### 7.1 Equivalent Forms of SSA

All equivalent:
(a) S(ABC) + S(B) <= S(AB) + S(BC)
(b) I(A:C|B) >= 0
(c) S(A|BC) <= S(A|B)
(d) S(AB) + S(BC) - S(B) - S(ABC) >= 0

### 7.2 Consequences

**Monotonicity of relative entropy**: S(rho || sigma) >= S(Tr_B rho || Tr_B sigma)
(Partial trace does not increase relative entropy.)

**Joint convexity of relative entropy**: S(sum p_i rho_i || sum p_i sigma_i) <= sum p_i S(rho_i || sigma_i)

**Concavity of conditional entropy**: S(A|B) is concave in rho_{AB}:
S(A|B)_{sum p_i rho_i} >= sum p_i S(A|B)_{rho_i}

---

## 8. Data Processing Inequality

**For quantum channels**: Let N be any CPTP map. Then:

    S(rho || sigma) >= S(N(rho) || N(sigma))

(Relative entropy cannot increase under quantum channels.)

**For mutual information**: If A -> B -> C is a quantum Markov chain (in the sense that C is obtained from B by a quantum channel):

    I(A:B) >= I(A:C)

**Petz recovery** (strengthened DPI): The deficit in the data processing inequality:

    S(rho || sigma) - S(N(rho) || N(sigma)) >= D(rho || R_N(N(rho)))

where R_N is the Petz recovery map:

    R_N(X) = sigma^{1/2} N^dagger(N(sigma)^{-1/2} X N(sigma)^{-1/2}) sigma^{1/2}

---

## 9. Entropy Inequalities: The Entropy Cone

For n parties, the joint entropy vector (S(rho_S) for all subsets S of {1,...,n}) satisfies:

**n = 2**: Completely characterized by:
- S(A) >= 0, S(B) >= 0
- S(AB) <= S(A) + S(B)  [subadditivity]
- |S(A) - S(B)| <= S(AB)  [Araki-Lieb]

**n = 3**: In addition to pairwise constraints, SSA gives:
- S(ABC) + S(B) <= S(AB) + S(BC)
- (and all permutations)

**Quantum vs. classical cone**: The quantum entropy cone is STRICTLY LARGER than the classical one for n >= 3 (because conditional entropy can be negative). For n = 2, they differ because I(A:B) can be as large as 2 min(S(A), S(B)).

---

## 10. Entropy of Quantum Channels

**Minimum output entropy**: S_min(N) = min_{rho} S(N(rho))

Additivity conjecture (DISPROVED by Hastings 2009):
S_min(N_1 tensor N_2) = S_min(N_1) + S_min(N_2)  --- FALSE in general.

**Entropy exchange**: For channel N with Stinespring isometry V:

    S_e(rho, N) = S((id tensor N)(|phi><phi|)) = S(complementary channel output)

This measures how much information leaks to the environment.

**Relation**: S(N(rho)) - S_e(rho, N) = I_c(rho, N) (coherent information).

---

## 11. Relative Entropy and Its Variants

### 11.1 Quantum Relative Entropy

    S(rho || sigma) = Tr(rho log rho) - Tr(rho log sigma)

if supp(rho) subset supp(sigma), else +infinity.

Properties:
- Non-negative: S(rho || sigma) >= 0, equality iff rho = sigma (Klein's inequality).
- Not symmetric: S(rho || sigma) =/= S(sigma || rho) in general.
- Not a metric (no triangle inequality).
- Joint convexity: S(sum p_i rho_i || sum p_i sigma_i) <= sum p_i S(rho_i || sigma_i).
- Monotone under CPTP maps (data processing inequality).

### 11.2 Max-Relative Entropy

    D_max(rho || sigma) = log min{lambda : rho <= lambda sigma}

Operational meaning: one-shot hypothesis testing.

### 11.3 Relative Entropy of Entanglement

    E_R(rho) = min_{sigma in SEP} S(rho || sigma)

where SEP is the set of separable states. This is an entanglement monotone.
