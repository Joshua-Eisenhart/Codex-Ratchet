# Entanglement Theory: Complete Mathematical Reference

## Reference: Horodecki x4 "Quantum Entanglement" Rev. Mod. Phys. 81, 865 (2009)

---

## 1. Separability

### 1.1 Definition

A bipartite state rho_{AB} on H_A tensor H_B is **separable** iff:

    rho_{AB} = sum_i p_i rho_i^A tensor rho_i^B

with p_i >= 0, sum p_i = 1. Otherwise it is **entangled**.

**Pure state separability**: |Psi>_{AB} is separable iff |Psi> = |psi>_A tensor |phi>_B (product state). Equivalently: the Schmidt rank is 1.

### 1.2 Schmidt Decomposition

For any bipartite pure state |Psi>_{AB} with d_A <= d_B:

    |Psi> = sum_{i=1}^{d_A} sqrt(lambda_i) |a_i> tensor |b_i>

where lambda_i >= 0, sum lambda_i = 1, {|a_i>} orthonormal in H_A, {|b_i>} orthonormal in H_B.

The Schmidt coefficients sqrt(lambda_i) are unique (up to ordering). The Schmidt rank = number of nonzero lambda_i.

Entangled iff Schmidt rank >= 2.

**Proof of Schmidt decomposition**: Write |Psi> = sum_{jk} c_{jk} |j> tensor |k>. The matrix C = (c_{jk}) has SVD: C = U D V^dagger. Then |a_i> = sum_j U_{ji}|j>, |b_i> = sum_k V_{ki}*|k>, lambda_i = d_i^2.

### 1.3 Separability Problem

Deciding whether a given rho is separable is **NP-hard** (Gurvits 2003) in general dimension.

For 2x2 and 2x3: completely solved by PPT criterion.
For higher dimensions: various necessary conditions, none individually sufficient.

---

## 2. PPT Criterion (Peres-Horodecki)

### 2.1 Partial Transpose

The partial transpose of rho_{AB} with respect to B:

    (rho^{T_B})_{ij,kl} = rho_{il,kj}

Equivalently: (|i><j| tensor |k><l|)^{T_B} = |i><j| tensor |l><k|.

### 2.2 PPT Criterion

**Theorem (Peres 1996)**: If rho is separable, then rho^{T_B} >= 0 (all eigenvalues non-negative).

**Proof**: If rho = sum p_i rho_i^A tensor rho_i^B, then rho^{T_B} = sum p_i rho_i^A tensor (rho_i^B)^T. Since (rho_i^B)^T >= 0 (transpose preserves eigenvalues), and the sum of tensor products of PSD matrices is PSD, rho^{T_B} >= 0. QED.

Contrapositive: If rho^{T_B} has a negative eigenvalue, then rho is entangled. Such states are called **NPT** (negative partial transpose).

### 2.3 Sufficiency for Low Dimensions

**Theorem (Horodecki^3 1996)**: For C^2 tensor C^2 and C^2 tensor C^3:

    rho separable <==> rho^{T_B} >= 0

So for 2-qubit systems, PPT is both necessary AND sufficient for separability.

**Proof sketch**: Uses the result that any positive map P: M_2 -> M_2 (or M_2 -> M_3) can be decomposed as P = P_1 + P_2 . T where P_1, P_2 are CP maps and T is the transpose. Then the condition (id tensor P)(rho) >= 0 for all positive P reduces to rho^{T_B} >= 0.

### 2.4 PPT Entangled States (Bound Entanglement)

For C^3 tensor C^3 and higher: there exist states that are PPT but ENTANGLED. These are **bound entangled** states (Horodecki 1998).

Example: The Horodecki 3x3 state is PPT but not separable (proven by the range criterion).

Properties of bound entangled states:
- Cannot be distilled to singlets by LOCC (hence "bound")
- Have positive partial transpose
- Still useful for some quantum information tasks (activation, etc.)
- Their existence makes the separability problem fundamentally hard

---

## 3. Concurrence

### 3.1 Definition (2-Qubit)

For a 2-qubit state rho, define the spin-flipped state:

    rho_tilde = (sigma_y tensor sigma_y) rho* (sigma_y tensor sigma_y)

where rho* is the complex conjugate in the computational basis.

Form the matrix R = rho rho_tilde. Let lambda_1 >= lambda_2 >= lambda_3 >= lambda_4 be the square roots of the eigenvalues of R (taken non-negative).

**Concurrence**:

    C(rho) = max(0, lambda_1 - lambda_2 - lambda_3 - lambda_4)

### 3.2 Properties

- C in [0, 1].
- C = 0 iff rho is separable (for 2-qubit states).
- C = 1 for maximally entangled states.
- Convex: C(sum p_i rho_i) <= sum p_i C(rho_i).
- For pure states |Psi> = a|00> + b|01> + c|10> + d|11>: C = 2|ad - bc|.

### 3.3 Proof of Pure State Formula

For pure |Psi>, rho = |Psi><Psi|:

    rho_tilde = (sigma_y tensor sigma_y)|Psi*><Psi*|(sigma_y tensor sigma_y)

    R = |Psi><Psi| . (sigma_y tensor sigma_y)|Psi*><Psi*|(sigma_y tensor sigma_y)

R has rank 1, so only one nonzero eigenvalue.

    lambda_1^2 = <Psi|rho_tilde|Psi> = |<Psi|(sigma_y tensor sigma_y)|Psi*>|^2

    <Psi|(sigma_y tensor sigma_y)|Psi*> = <Psi| sigma_y tensor sigma_y |Psi*>

Working in computational basis:
    sigma_y|0> = i|1>, sigma_y|1> = -i|0>
    (sigma_y tensor sigma_y)|00> = -|11>, |01> -> |10>, |10> -> |01>, |11> -> -|00>

So: (sigma_y tensor sigma_y)(a*|00> + b*|01> + c*|10> + d*|11>) = -d*|00> + c*|01> + b*|10> - a*|11>

    <Psi|(sigma_y tensor sigma_y)|Psi*> = -ad* + bc* + cb* - da* = -2(ad - bc)* + conjugate terms...

Actually more carefully:
    = a(-d*) + b(c*) + c(b*) + d(-a*) = -(ad* + da*) + (bc* + cb*) = -2Re(ad) + 2Re(bc)

Hmm, let me redo. <Psi| = a*<00| + b*<01| + c*<10| + d*<11|.

(sigma_y tensor sigma_y)|Psi*> = (sigma_y tensor sigma_y)(a*|00> + b*|01> + c*|10> + d*|11>)

sigma_y tensor sigma_y acts as: |00> -> (i|1>)(i|1>) = -|11>, |01> -> (i|1>)(-i|0>) = |10>,
|10> -> (-i|0>)(i|1>) = |01>, |11> -> (-i|0>)(-i|0>) = -|00>.

So: = -a*|11> + b*|10> + c*|01> - d*|00>

<Psi|(sigma_y tensor sigma_y)|Psi*> = a*(-d*) + b*(c*) + c*(b*) + d*(-a*) 
= -a*d* + b*c* + c*b* - d*a*
= -2a*d* + 2b*c*
= 2(bc - ad)*  (taking complex conjugate: = 2(b*c* - a*d*))

Wait: a*(-d*) = -a*d*, b*(c*) = b*c*, c*(b*) = c*b* = b*c*, d*(-a*) = -d*a* = -a*d*.

Sum = -2a*d* + 2b*c* = 2(b*c* - a*d*).

So |...|^2 = 4|ad - bc|^2, giving lambda_1 = 2|ad - bc|, and C = 2|ad - bc|. QED.

### 3.4 Concurrence for Bell-Diagonal States

For rho = sum_{i=1}^{4} p_i |B_i><B_i| where |B_i> are Bell states with populations p_1 >= p_2 >= p_3 >= p_4:

    C = max(0, 2 p_1 - 1)

Entangled iff p_1 > 1/2 (one Bell state dominates).

---

## 4. Entanglement of Formation

### 4.1 Definition

    E_F(rho) = min_{decompositions} sum_i p_i E(|psi_i>)

where the minimum is over all pure-state decompositions rho = sum p_i |psi_i><psi_i|, and E(|psi>) = S(Tr_B(|psi><psi|)) is the entanglement entropy.

### 4.2 Wootters Formula (2 Qubits)

**Theorem (Wootters 1998)**: For 2-qubit states:

    E_F(rho) = h((1 + sqrt(1 - C^2))/2)

where C = C(rho) is the concurrence and h is the binary entropy:

    h(x) = -x log_2 x - (1-x) log_2(1-x)

**Proof sketch**: 
1. Show that the "entanglement of formation" optimization can be solved analytically for 2 qubits.
2. The key insight: the concurrence C(|psi>) = |<psi|psi_tilde>| for pure states determines E(|psi>) monotonically via E = h((1+sqrt(1-C^2))/2).
3. The convex roof construction (minimizing over decompositions) can be solved because for 2 qubits, the optimal decomposition is into states of equal concurrence.
4. This follows from the properties of the matrix R = sqrt(sqrt(rho) rho_tilde sqrt(rho)).

### 4.3 Properties

- E_F is an entanglement monotone: non-increasing under LOCC.
- E_F(rho) = 0 iff rho is separable (for 2 qubits, using PPT equivalence).
- E_F(|Phi+>) = 1 ebit.
- Additivity of E_F was OPEN for years; finally shown to NOT be additive in general (Hastings 2009, same paper disproving minimum output entropy additivity, via the duality E_F <-> S_min).

---

## 5. Negativity

### 5.1 Definition

    N(rho) = (||rho^{T_A}||_1 - 1) / 2

where ||X||_1 = Tr(sqrt(X^dagger X)) = Tr|X| is the trace norm.

Equivalently: N = sum of absolute values of negative eigenvalues of rho^{T_A}.

### 5.2 Logarithmic Negativity

    E_N(rho) = log_2 ||rho^{T_A}||_1 = log_2(1 + 2N)

### 5.3 Properties

- N >= 0, with N = 0 for PPT states. (Hence N = 0 for separable states, but also for PPT entangled states.)
- For 2x2: N > 0 iff entangled (PPT = separable in this case).
- Computable: just diagonalize the 4x4 partial transpose (for 2 qubits).
- E_N is an entanglement monotone (non-increasing under LOCC).
- E_N is additive: E_N(rho tensor sigma) = E_N(rho) + E_N(sigma).
- E_N upper bounds distillable entanglement: E_D(rho) <= E_N(rho).
- NOT convex (but logarithmic negativity IS an entanglement monotone despite non-convexity — it satisfies the monotonicity condition directly).

### 5.4 For Pure States

For |Psi> with Schmidt decomposition |Psi> = sum sqrt(lambda_i) |a_i b_i>:

    N = (sum_i sqrt(lambda_i))^2/2 - 1/2 ... 

Actually, more directly: rho^{T_B} has eigenvalues lambda_i lambda_j for the diagonal block and +/- sqrt(lambda_i lambda_j) for off-diagonal. For 2-qubit pure states:

    lambda_1 = cos^2(theta/2), lambda_2 = sin^2(theta/2)

    ||rho^{T_B}||_1 = lambda_1^2 + lambda_2^2 + 2 lambda_1 lambda_2 = (lambda_1 + lambda_2)^2 = 1... 

No wait. Let me compute directly.

For |Psi> = sqrt(lambda)|00> + sqrt(1-lambda)|11>:

rho = lambda|00><00| + sqrt(lambda(1-lambda))|00><11| + sqrt(lambda(1-lambda))|11><00| + (1-lambda)|11><11|

rho^{T_B}: transpose the second index: |00><01| -> |01><00|, etc.

rho^{T_B} = lambda|00><00| + sqrt(lambda(1-lambda))|01><10| + sqrt(lambda(1-lambda))|10><01| + (1-lambda)|11><11|

Eigenvalues: lambda, (1-lambda), sqrt(lambda(1-lambda)), -sqrt(lambda(1-lambda)).

So N = sqrt(lambda(1-lambda)) = C/2 where C = 2 sqrt(lambda(1-lambda)) is the concurrence.

For maximally entangled (lambda = 1/2): N = 1/2, E_N = 1.

---

## 6. Quantum Discord

### 6.1 Definition

Classical mutual information I(A:B) = H(A) + H(B) - H(AB) can be equivalently written as I(A:B) = H(A) - H(A|B). Quantumly, these two forms DIFFER because measurement disturbs quantum states.

**Quantum mutual information**: I(A:B) = S(A) + S(B) - S(AB)

**Classical correlation** (Henderson & Vedral 2001):
    J(A:B) = S(A) - min_{POVM on B} S(A|measurement outcomes)
           = S(A) - min_{{Pi_j^B}} sum_j p_j S(rho_{A|j})

where rho_{A|j} = Tr_B((I tensor Pi_j^B) rho (I tensor Pi_j^B)) / p_j and p_j = Tr((I tensor Pi_j^B) rho).

**Quantum discord**:
    D(A|B) = I(A:B) - J(A:B)

### 6.2 Properties

- D(A|B) >= 0 (proven by Ollivier & Zurek 2001).
- D(A|B) = 0 iff rho has the form rho = sum_j p_j rho_j^A tensor |j><j| (classical-quantum state, A uncorrelated with B's pointer basis).
- D is NOT symmetric: D(A|B) =/= D(B|A) in general.
- D can be nonzero even for separable states. Separability does NOT imply zero discord.
- Computing D is NP-hard in general (Huang 2014).

### 6.3 Analytic Formula for 2-Qubit X-States

An X-state has the form (in computational basis):

    rho = [[rho_{11}, 0, 0, rho_{14}],
           [0, rho_{22}, rho_{23}, 0],
           [0, rho_{32}, rho_{33}, 0],
           [rho_{41}, 0, 0, rho_{44}]]

For X-states, the optimal measurement for computing discord is known to be a projective measurement in the (theta, phi) direction, and the optimization reduces to a 1D minimization.

For the special case of Bell-diagonal states (a = b = 0, T diagonal):

    D = min_{k in {1,2,3}} [S(A) + S(B) - S(AB) - (stuff depending on max |t_k|)]

The explicit formula involves the binary entropy of functions of the t_k.

---

## 7. Bell-CHSH Inequality

### 7.1 CHSH Operator

For observables a, a' on A and b, b' on B (each with eigenvalues +/-1):

    B_CHSH = a tensor b + a tensor b' + a' tensor b - a' tensor b'

### 7.2 Classical Bound

For local hidden variable theories: |<B_CHSH>| <= 2.

**Proof**: For any fixed hidden variable lambda, a, a' in {+1, -1} and b, b' in {+1, -1}. Then:

    a(b + b') + a'(b - b') = +/-2 (one of b+b', b-b' is 0, the other is +/-2)

Averaging: |<B_CHSH>| = |sum p(lambda)(a(b+b') + a'(b-b'))| <= 2. QED.

### 7.3 Quantum Bound (Tsirelson)

    |<B_CHSH>| <= 2 sqrt(2) = Tsirelson bound

Achieved by |Phi+> with measurements:
    a = sigma_z, a' = sigma_x, b = (sigma_z + sigma_x)/sqrt(2), b' = (sigma_z - sigma_x)/sqrt(2)

**Proof of Tsirelson bound**: B_CHSH^2 = 4I - [a, a'] tensor [b, b']. Since ||[a,a']|| <= 2 and ||[b,b']|| <= 2 (for operators with eigenvalues +/-1), we get ||B_CHSH^2|| <= 8, so ||B_CHSH|| <= 2sqrt(2).

More precisely: B^2 = 4I tensor I - [a,a'] tensor [b,b']. Using ||[a,a']||^2 = ||aa' - a'a||^2 <= ||2I - {a,a'}||... The cleaner proof uses B^2 = 4 - [a,a'][b,b'] and |<B>|^2 <= <B^2> <= 4 + |<[a,a'][b,b']>| <= 4 + 4 = 8.

### 7.4 Horodecki Criterion

For 2-qubit states with correlation tensor T:

    max_CHSH |<B_CHSH>| = 2 sqrt(t_1^2 + t_2^2)

where t_1 >= t_2 >= t_3 >= 0 are the singular values of T (sorted decreasingly).

Violates CHSH iff t_1^2 + t_2^2 > 1.

**Important**: A state can be entangled but NOT violate any Bell inequality (e.g., Werner states with 1/3 < p < 1/sqrt(2)).

---

## 8. Monogamy of Entanglement

### 8.1 Coffman-Kundu-Wootters (CKW) Inequality

For a 3-qubit pure state |Psi>_{ABC}:

    C^2(A, BC) >= C^2(A, B) + C^2(A, C)

where C(A, BC) is the concurrence of A with the joint system BC, and C(A, B), C(A, C) are concurrences of the reduced 2-qubit states.

**3-tangle** (residual entanglement):

    tau_3 = C^2(A, BC) - C^2(A, B) - C^2(A, C)

This is a genuine 3-party entanglement measure. tau_3 >= 0 by CKW.

- For |GHZ> = (|000> + |111>)/sqrt(2): tau_3 = 1 (maximal 3-party entanglement).
- For |W> = (|001> + |010> + |100>)/sqrt(3): tau_3 = 0 (all entanglement is bipartite).

### 8.2 General Monogamy

For n qubits:

    C^2(A_1, A_2...A_n) >= sum_{j=2}^{n} C^2(A_1, A_j)

This means: if A is highly entangled with B, it cannot be simultaneously highly entangled with C. This is a purely quantum phenomenon (classical correlations can be freely shared).

### 8.3 Monogamy and Quantum Cryptography

Monogamy is the basis for the security of quantum key distribution: if Alice and Bob share near-maximal entanglement, no eavesdropper Eve can be significantly entangled with either of them.

---

## 9. Entanglement Distillation

### 9.1 Definition

Entanglement distillation: given n copies of rho_{AB}, produce m copies of the maximally entangled state |Phi+> using only LOCC.

**Distillable entanglement**: E_D(rho) = sup{r : rho^{tensor n} can be distilled to r n ebits, asymptotically}

### 9.2 Key Results

- For pure states: E_D = S(rho_A) (entanglement entropy), achieved by the BBPSSW protocol.
- For NPT mixed states: E_D > 0 (can always distill something).
- For PPT states: E_D = 0 (cannot distill, even though they may be entangled — this is bound entanglement).
- Distillable entanglement is generally NOT additive and NOT computable.

### 9.3 Hierarchy of Entanglement Measures

    E_D <= E_F (entanglement cost >= distillable entanglement)
    E_D <= E_N (logarithmic negativity upper bounds distillation)
    E_D <= E_R (relative entropy of entanglement)

For pure states: E_D = E_F = E_R = E_N = S(rho_A). All measures agree.

For mixed states: generally E_D < E_F (irreversibility of entanglement manipulation).

---

## 10. Multipartite Entanglement

### 10.1 Classification Problem

For n parties, entanglement classification under LOCC/SLOCC becomes exponentially complex.

**3 qubits**: Two inequivalent classes of genuine tripartite entanglement (SLOCC):
- GHZ class: (a|000> + b|111> type)
- W class: (|001> + |010> + |100> type)

These cannot be converted into each other even probabilistically.

### 10.2 Entanglement Witnesses

An observable W is an entanglement witness if:
- Tr(W sigma) >= 0 for all separable sigma
- There exists an entangled rho with Tr(W rho) < 0

Every entangled state is detected by some witness (Hahn-Banach separation theorem applied to the convex set of separable states).

**Construction**: For a target entangled state |Psi>:

    W = alpha I - |Psi><Psi|

with alpha = max_{separable sigma} <Psi|sigma|Psi>.

For |Phi+>: alpha = 1/2, so W = I/2 - |Phi+><Phi+|.

### 10.3 Entanglement Measures for Multipartite Systems

- **Geometric measure**: E_G = 1 - max_{product |phi>} |<phi|Psi>|^2.
- **Meyer-Wallach measure**: Q = 2(1 - (1/n) sum_i Tr(rho_i^2)) where rho_i is the reduced state of qubit i.
- **Genuine multipartite negativity**: Based on partial transposes w.r.t. all bipartitions.

No single measure captures all aspects of multipartite entanglement. The classification problem is one of the major open problems in quantum information theory.
