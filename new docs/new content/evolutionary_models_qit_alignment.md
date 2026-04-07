# Evolutionary Dynamics and QIT: Deep Mathematical Alignment

## Reference Note
This document establishes the precise mathematical correspondences between evolutionary dynamics and quantum information theory. Where the mapping is exact (isomorphism), it is stated. Where it breaks (analogy only), the failure mode is identified.

---

## 0. The Core Correspondence

| Evolutionary Object | QIT Object | Mapping Type |
|---|---|---|
| Population frequency vector x | Diagonal density matrix rho = diag(x) | Exact embedding |
| Fitness function f_i | Hamiltonian H = diag(f_i) | Exact (diagonal) |
| Mean fitness f_bar = sum x_i f_i | Energy expectation <H> = Tr(rho H) | Exact |
| Mutation matrix M | Quantum channel E(rho) = M rho M^T | Exact (classical channel) |
| Selection | Non-unitary evolution / measurement | Approximate (nonlinearity) |
| Genetic variance Var(f) | Quantum variance (Delta H)^2 | Exact |
| Genotype space {0,1}^L | Hilbert space C^{2^L} | Exact (basis) |
| Recombination | Entangling operation on multi-locus system | Structural parallel |
| Drift | Depolarizing noise | Exact (finite population) |

**The fundamental tension**: Evolutionary dynamics is generically NONLINEAR (fitness depends on frequencies). Quantum channels are LINEAR. The mapping is exact when fitness is frequency-independent and approximate when it is frequency-dependent. The nonlinearity of selection is the primary obstruction.

---

## 1. Replicator Equation: Population as Quantum State

### 1.1 Basic Formulation

The replicator equation for n types with frequencies x_i:

    dx_i/dt = x_i (f_i(x) - f_bar(x))

where f_bar(x) = sum_j x_j f_j(x) is the population mean fitness. In density matrix form with rho = diag(x_1, ..., x_n):

    d rho_{ii}/dt = rho_{ii} (F_{ii} - Tr(F rho))

For frequency-independent fitness F = diag(f_1, ..., f_n) (constant Hamiltonian):

    d rho/dt = F rho + rho F - 2 Tr(F rho) rho

This is the nonlinear von Neumann equation with a normalization constraint. Compare with the standard von Neumann equation:

    d rho/dt = -i[H, rho]    (unitary, Hermitian H)

The replicator uses the ANTI-COMMUTATOR {F, rho} = F rho + rho F rather than the commutator [H, rho], and adds a nonlinear normalization term. This is because selection is dissipative (non-unitary), not conservative (unitary).

### 1.2 Linearization via Embedding

Define unnormalized variables y_i = x_i * exp(-integral f_bar dt). Then:

    dy_i/dt = f_i y_i

This is LINEAR. In density matrix terms, define sigma = exp(Ft) rho_0 exp(Ft) (unnormalized). Then:

    rho(t) = sigma(t) / Tr(sigma(t)) = exp(Ft) rho_0 exp(Ft) / Tr(exp(Ft) rho_0 exp(Ft))

This is the Lueders rule for non-selective measurement with measurement operator exp(Ft/2). The replicator equation IS a continuous measurement process: nature continuously "measures" the population and the fittest types have the highest detection probability.

### 1.3 Frequency-Dependent Fitness: Payoff Matrix

For evolutionary game theory, fitness depends on population composition via a payoff matrix A:

    f_i(x) = (Ax)_i = sum_j A_{ij} x_j

so f_bar = x^T A x. The replicator equation becomes:

    dx_i/dt = x_i ((Ax)_i - x^T A x)

In density matrix form:

    d rho/dt = A rho^2 + rho^2 A^T - 2 Tr(A rho^2) rho

This is quadratic in rho -- genuinely nonlinear. No linear quantum channel can reproduce this exactly. However, mean-field approximations (replacing rho^2 with rho * Tr(A rho)) recover a linear Lindblad form:

    d rho/dt ~ [A, rho] + {A - Tr(A rho)I, rho}

which is a Lindblad master equation with both Hamiltonian (commutator) and dissipative (anti-commutator) parts.

### 1.4 Lyapunov Functions and Free Energy

The replicator equation has Lyapunov functions that map to quantum free energies:

**Shahshahani metric**: The natural metric on the probability simplex is:

    ds^2 = sum_i (dx_i)^2 / x_i

This is the Fisher-Rao metric = the Fubini-Study metric restricted to diagonal density matrices. Under this metric, the replicator dynamics is a gradient flow:

    dx/dt = grad_Fisher V(x)

where V(x) depends on the fitness landscape.

**KL divergence as Lyapunov function**: For the replicator equation with constant fitness, the relative entropy:

    D_KL(x* || x) = sum_i x*_i log(x*_i / x_i)

where x* is the ESS (evolutionarily stable strategy), is a Lyapunov function:

    d/dt D_KL(x* || x) = -(sum_i x*_i f_i - f_bar) <= 0

In QIT language: S(rho* || rho(t)) is non-increasing under the replicator channel. This is the quantum data processing inequality specialized to diagonal states.

---

## 2. Mutation as Quantum Channel

### 2.1 Mutation Matrix Structure

A mutation matrix M has entries M_{ij} = Prob(type j produces type i). Properties:

    M_{ij} >= 0,    sum_i M_{ij} = 1  (column-stochastic)

This is a classical channel: it maps probability distributions to probability distributions. In Kraus representation:

    E(rho) = sum_k A_k rho A_k^dagger

where the Kraus operators A_k correspond to specific mutation events.

For a mutation matrix M acting on diagonal rho = diag(x):

    E(rho) = M rho M^T

is CPTP iff M is column-stochastic. The channel is:
- **Unital** (E(I/n) = I/n) iff M is doubly stochastic (symmetric mutation rates)
- **Entanglement-breaking** always (diagonal states have no entanglement to break)
- **Degradable** iff the complementary channel has lower capacity

### 2.2 Specific Mutation Channels

**Uniform mutation** (rate mu per site, symmetric):

    M = (1 - mu) I + mu J/n

where J is the all-ones matrix. This gives:

    E(rho) = (1 - mu) rho + (mu/n) I

This IS the depolarizing channel with parameter p = mu. Properties:
- Fixed point: I/n (uniform distribution = maximally mixed state)
- Entropy: S(E(rho)) >= S(rho) for all rho (entropy always increases)
- Capacity: C = log n + (1-mu) log(1-mu) + mu log(mu/n)

**Per-locus mutation on binary sequences** of length L:

For sequences s in {0,1}^L with per-bit error rate epsilon:

    M_{s,s'} = epsilon^{d(s,s')} (1-epsilon)^{L - d(s,s')}

where d(s,s') is the Hamming distance. This factors as a tensor product:

    M = M_1 tensor M_2 tensor ... tensor M_L

where each M_k is a 2x2 bit-flip channel:

    M_k = [[1-epsilon, epsilon], [epsilon, 1-epsilon]]

In QIT: this is L independent depolarizing channels on qubits, one per locus. The tensor product structure is exact.

**Back-mutation (reversible)**: M is doubly stochastic. The channel is unital: E(I/n) = I/n. Detailed balance: M_{ij} pi_j = M_{ji} pi_i for some stationary distribution pi. The channel has a thermal fixed point.

**Irreversible mutation**: M is column-stochastic but not doubly stochastic. The channel has a unique fixed point that is NOT the maximally mixed state. The population converges to a mutation-selection balance that is not the uniform distribution.

### 2.3 Mutation-Selection Balance as Channel Fixed Point

Combined mutation-selection dynamics:

    x(t+1) = M * diag(f) * x(t) / (f^T x(t))

Mutation: x -> Mx (linear channel). Selection: x -> diag(f) x / (f^T x) (nonlinear projection). The composition is:

    rho -> M * f^{1/2} rho f^{1/2} * M^T / Tr(M * f^{1/2} rho f^{1/2} * M^T)

The equilibrium rho* satisfies:

    M * f^{1/2} rho* f^{1/2} * M^T = lambda * rho*

This is an eigenvector equation. rho* is the leading eigenvector of the superoperator E(rho) = M * f^{1/2} rho f^{1/2} * M^T. The eigenvalue lambda = f_bar at equilibrium.

**Connection to Perron-Frobenius**: The superoperator E is positive (maps PSD to PSD) and trace-non-increasing. By Perron-Frobenius, it has a unique dominant eigenvector with positive entries. This eigenvector IS the mutation-selection equilibrium.

---

## 3. Selection as Measurement

### 3.1 Selection as Non-Selective Measurement

Pure selection (no mutation) with fitness f_i acts on the population as:

    x_i -> x_i f_i / f_bar

In density matrix language:

    rho -> F^{1/2} rho F^{1/2} / Tr(F rho)

where F = diag(f_1, ..., f_n). This is a POVM measurement followed by post-selection: the "measurement operator" is M = F^{1/2}, and the "probability of outcome" is p = Tr(F rho) = f_bar.

**One generation of selection = one round of amplitude amplification**:

Starting from rho_0 = diag(x_1, ..., x_n), after t generations:

    rho(t) = F^{t/2} rho_0 F^{t/2} / Tr(F^t rho_0)

The diagonal elements are:

    x_i(t) = x_i(0) f_i^t / (sum_j x_j(0) f_j^t)

As t -> infinity, rho(t) -> |i*><i*| where i* = argmax f_i (the fittest type). Selection purifies the state -- it drives a mixed state toward a pure state, just as repeated measurement drives a quantum state toward an eigenstate.

### 3.2 Truncation Selection as Projective Measurement

Truncation selection: keep the top k fraction, discard the rest. Define the projector:

    P_k = sum_{i: f_i >= f_threshold} |i><i|

Then truncation selection is:

    rho -> P_k rho P_k / Tr(P_k rho)

This IS a projective measurement in the fitness eigenbasis. The "measurement outcome" is "fit" or "unfit." The population state collapses onto the subspace of fit types.

**Post-measurement state**: After truncation to top k types:

    rho_post = sum_{i in top-k} (x_i / sum_{j in top-k} x_j) |i><i|

This is a rank-k density matrix -- the population has been projected onto a k-dimensional subspace. The information loss is:

    Delta S = S(rho_post) - S(rho) = log(sum_{top-k} x_i) - sum_{top-k} (x_i/X_k) log(x_i/X_k) + sum_all x_i log x_i

where X_k = sum_{top-k} x_i.

### 3.3 Selection Is Nonlinear -- The Key Obstruction

The normalization by f_bar = Tr(F rho) makes selection state-dependent. A CPTP map E satisfies:

    Tr(E(rho)) = Tr(rho)    for ALL rho

But selection satisfies:

    Tr(F^{1/2} rho F^{1/2}) = Tr(F rho) = f_bar(rho)    (depends on rho)

So selection is NOT a CPTP map -- it requires post-selection (conditioning on survival). In QIT, this is a non-trace-preserving operation followed by renormalization. The post-selection makes it nonlinear:

    rho -> F^{1/2} rho F^{1/2} / Tr(F rho)

is not linear in rho (denominator depends on rho).

**Resolution**: The EXTENDED system (population + environment) evolves by a CPTP map. Selection corresponds to measuring the environment and conditioning on the outcome "survived." The unconditional evolution (tracing out the environment without post-selection) IS CPTP:

    rho_pop tensor |alive><alive| -> E_total(rho_pop tensor |alive><alive|)

and the conditional state (post-selecting on "alive") is:

    rho_survived = Tr_env(E_total(rho tensor |alive><alive|) * (I tensor |alive><alive|)) / p_survive

This is exactly the Lueders rule for quantum measurement with post-selection.

---

## 4. Fisher's Fundamental Theorem as Quantum Variance Identity

### 4.1 The Classical Theorem

Fisher's fundamental theorem (Fisher 1930, exact form by Price 1972):

    d f_bar / dt = Var(f) = sum_i x_i (f_i - f_bar)^2

The rate of increase of mean fitness equals the additive genetic variance in fitness. In density matrix notation:

    d Tr(F rho) / dt = Tr(F^2 rho) - (Tr(F rho))^2 = (Delta F)^2_rho

This is EXACTLY the quantum variance of observable F in state rho.

### 4.2 Connection to Quantum Uncertainty

The quantum uncertainty relation:

    (Delta A)^2 (Delta B)^2 >= |<[A, B]>|^2 / 4

For diagonal rho and diagonal observables, [A, B] = 0, so the bound is trivial. But for the TIME-ENERGY uncertainty relation (Robertson form):

    (Delta H)^2 >= (d<A>/dt)^2 / (4 (Delta A)^2)

Applied to the replicator equation with H = F (fitness Hamiltonian) and A = any trait:

    Var(f) >= (d<A>/dt)^2 / (4 Var(A))

This says: the fitness variance (= rate of adaptation by Fisher's theorem) bounds how fast any trait can change. More genetic variance = faster evolution = larger quantum uncertainty.

### 4.3 Fisher Information and the Cramer-Rao Bound

The Fisher information for the parameter "time" in the replicator dynamics:

    I_F(t) = sum_i (1/x_i) (dx_i/dt)^2 = sum_i x_i (f_i - f_bar)^2 = Var(f)

This equals the QFI for the time parameter:

    J(t) = 4 (Delta F)^2 = 4 Var(f)

(the factor of 4 is conventional). The quantum Cramer-Rao bound:

    Var(t_hat) >= 1/J(t) = 1/(4 Var(f))

states that the precision of estimating "evolutionary time" is bounded by the fitness variance. In evolutionary terms: you can estimate how many generations have passed with precision inversely proportional to the fitness variance. High variance = fast evolution = easy to detect temporal change.

### 4.4 Generalized Fisher's Theorem (Ewens-Price)

The generalized theorem for any trait z:

    d<z>/dt = Cov(f, z)

In density matrix notation:

    d Tr(Z rho)/dt = Tr(FZ rho) - Tr(F rho) Tr(Z rho) = Cov_rho(F, Z)

This is the quantum covariance of observables F and Z. For F = Z (trait = fitness), this reduces to Fisher's theorem: d<f>/dt = Var(f) = Cov(f, f).

**Multivariate version** (Lande equation):

    d<z>/dt = G * nabla_z f_bar

where G is the additive genetic covariance matrix and nabla_z f_bar is the selection gradient. In density matrix form:

    d<Z>/dt = Cov_rho(F, Z) = Tr(rho {F - <F>, Z - <Z>} / 2)

G corresponds to the quantum covariance matrix of the trait observables, and nabla_z f_bar corresponds to the SLD (symmetric logarithmic derivative) of the fitness functional.

---

## 5. Price Equation as Quantum Covariance

### 5.1 The Full Price Equation

The Price equation (Price 1970):

    Delta z_bar = (1/w_bar) [Cov(w, z) + E(w Delta z)]

where:
- w_i = fitness of individual i (number of offspring)
- z_i = trait value of individual i
- Delta z_i = change in trait value between parent i and mean of its offspring
- w_bar = mean fitness
- z_bar = mean trait value

### 5.2 Density Matrix Form

Define the fitness observable W = diag(w_1, ..., w_n) and trait observable Z = diag(z_1, ..., z_n). Then:

    Cov_rho(W, Z) = Tr(rho WZ) - Tr(rho W) Tr(rho Z)

The Price equation becomes:

    Delta <Z>_rho = [Cov_rho(W, Z) + <W Delta Z>_rho] / <W>_rho

**First term**: Cov_rho(W, Z) / <W> is the change due to selection -- covariance of fitness and trait, normalized by mean fitness. This is the quantum covariance divided by the expectation value.

**Second term**: E(w Delta z) / w_bar = <W Delta Z> / <W> is the change due to transmission bias (mutation, recombination, developmental noise). This is the expectation of the product observable W * DeltaZ.

### 5.3 Multilevel Price Equation and Partial Trace

For structured populations (groups within a metapopulation), the Price equation decomposes into between-group and within-group terms:

    Delta z_bar = Cov_between(W_g, z_bar_g) / W_bar + E_g[Cov_within(w, z)] / W_bar

In density matrix terms: define the bipartite system (group) tensor (individual). The full population state is:

    rho_{GI} = sum_g p_g rho_g tensor rho_{I|g}

where rho_g is the group-level state and rho_{I|g} is the individual state within group g. Then:

- Between-group selection = Cov of partial-traced observables on the group subsystem
- Within-group selection = expectation of covariance on the individual subsystem

    Delta <Z> = Cov_{rho_G}(W_G, Z_G) / <W> + <Cov_{rho_{I|G}}(W_I, Z_I)>_G / <W>

The partial trace Tr_I(rho_{GI}) = rho_G gives the group-level state. The multilevel Price equation IS the decomposition of quantum covariance into subsystem contributions via partial trace.

### 5.4 Where Price Extends to Full Quantum

For non-diagonal rho (coherences between types), the quantum covariance includes off-diagonal terms:

    Cov_rho(W, Z) = sum_{i,j} rho_{ij} (W_{ji} Z_{ij} + Z_{ji} W_{ij})/2 - Tr(rho W) Tr(rho Z)

These off-diagonal contributions represent:
- Linkage disequilibrium (correlations between loci)
- Epistatic interactions (fitness depends on combinations of alleles)
- Recombinational effects (new genotype combinations)

The quantum Price equation with coherences captures multilocus evolution in a single equation. Classical population genetics requires separate tracking of linkage disequilibrium; the density matrix formalism handles it automatically through off-diagonal elements.

---

## 6. Eigen's Quasispecies: Error Threshold as Phase Transition

### 6.1 The Quasispecies Equation

For binary sequences of length L (genotype space {0,1}^L, dimension n = 2^L):

    dx_i/dt = sum_j Q_{ij} f_j x_j - phi(t) x_i

where Q_{ij} = mutation probability from j to i, f_j = fitness, phi = mean fitness. In matrix form:

    dx/dt = (QF - phi I) x

where Q is the mutation matrix, F = diag(f) is the fitness matrix. The steady state is the leading eigenvector of QF.

### 6.2 The Error Threshold

For the single-peak landscape (f_master = sigma, all others f = 1) with uniform per-bit error rate epsilon:

    Q_{ij} = (1-epsilon)^{L-d(i,j)} epsilon^{d(i,j)}

The master sequence frequency at equilibrium:

    x_master = (sigma (1-epsilon)^L - 1) / (sigma - 1)    when sigma(1-epsilon)^L > 1

The error threshold occurs at:

    mu_c = 1 - (1/sigma)^{1/L} ~ ln(sigma) / L    for large L

When mu > mu_c:  x_master -> 1/n  (delocalized, maximally mixed)
When mu < mu_c:  x_master > 0     (localized, near-pure state)

### 6.3 QIT Interpretation: Decoherence Transition

The error threshold is a decoherence transition:

| Below threshold (mu < mu_c) | Above threshold (mu > mu_c) |
|---|---|
| rho near pure state |i*><i*| | rho near I/n (maximally mixed) |
| Low entropy S(rho) ~ 0 | High entropy S(rho) ~ log n |
| Information preserved | Information destroyed |
| Quantum error correction succeeds | Error correction fails |

**Exact mapping to quantum error correction**: The error threshold condition:

    (1-epsilon)^L > 1/sigma

is the quantum error correction condition: the fidelity of the encoded state after L independent noise channels must exceed the threshold for recovery. sigma plays the role of the code distance (how much redundancy protects the information). The genome length L is the number of physical qubits.

**Threshold as channel capacity**: The per-bit mutation rate epsilon defines a binary symmetric channel (BSC) with capacity:

    C(epsilon) = 1 - H_2(epsilon)

where H_2 is the binary entropy. The error threshold condition becomes:

    L * C(epsilon) > log_2(sigma)

The genome must have enough capacity (L bits at rate C per bit) to encode the fitness advantage (log sigma bits). This is Shannon's channel coding theorem applied to evolutionary information.

### 6.4 Quasispecies as Gibbs State

At mutation-selection equilibrium, the quasispecies distribution is:

    x_i ~ exp(beta_eff * f_i) * (mutation corrections)

where beta_eff = 1/T_eff with effective temperature T_eff related to the mutation rate. At low mutation (low T), the distribution concentrates on the fittest type (ground state). At high mutation (high T), the distribution spreads (thermal state approaches maximally mixed).

The density matrix form:

    rho_eq ~ exp(-beta_eff H_fitness) / Z

where H_fitness = -diag(f_1, ..., f_n) (negative fitness as Hamiltonian, because lower H = higher fitness = more probable). This IS the Gibbs state. The error threshold is the melting temperature T_c where the ordered (localized) phase transitions to the disordered (delocalized) phase.

---

## 7. NK Landscapes as Hamiltonian Spectra

### 7.1 NK Model Definition

Kauffman's NK model: genome of N loci, each with K epistatic interactions. The fitness of sequence s = (s_1, ..., s_N), s_i in {0, 1}, is:

    f(s) = (1/N) sum_{i=1}^{N} f_i(s_i, s_{i_1}, ..., s_{i_K})

where {i_1, ..., i_K} are the K neighbors of locus i, and f_i: {0,1}^{K+1} -> R is a random function.

### 7.2 Hamiltonian on the Hypercube

The genotype space {0,1}^N is the vertices of the N-dimensional hypercube. The fitness function f: {0,1}^N -> R defines a Hamiltonian:

    H = -sum_s f(s) |s><s|

(negative sign: fitter = lower energy). This is a diagonal operator in the computational basis.

**K = 0 (additive fitness)**: H = -sum_i h_i sigma_z^{(i)}, a non-interacting spin Hamiltonian. The ground state is a product state. The landscape has a single peak. The mutation channel preserves additivity.

**K = 1 (pairwise epistasis)**: H = -sum_i h_i sigma_z^{(i)} - sum_{<i,j>} J_{ij} sigma_z^{(i)} sigma_z^{(j)}, an Ising model. The landscape can have multiple peaks. The ground state can be entangled (in the quantum extension).

**K = N-1 (maximum epistasis)**: H has 2^N random eigenvalues with no structure. The landscape is uncorrelated (random energy model). The eigenvalue distribution approaches a Gaussian. Finding the ground state is NP-hard.

### 7.3 Spectral Properties

The eigenvalue distribution of the NK Hamiltonian:

    K = 0:    All eigenvalues determined by N independent parameters
    K small:  Eigenvalue gaps proportional to 1/N^{1/2}
    K = N-1:  Eigenvalue distribution -> Gaussian(mean, var/2^N)

The density of states rho(E) = (1/2^N) sum_s delta(E - f(s)) determines the partition function:

    Z(beta) = integral rho(E) exp(-beta E) dE

The thermal density matrix rho_beta = exp(-beta H)/Z samples the landscape at resolution set by temperature. High T (beta -> 0) samples uniformly (exploration). Low T (beta -> infinity) concentrates on peaks (exploitation). Simulated annealing = cooling the thermal density matrix.

### 7.4 Landscape Ruggedness as Spectral Gap

The spectral gap Delta = E_1 - E_0 (energy difference between ground and first excited state) determines:

- **Tunneling time**: t_tunnel ~ exp(N * Delta) for barrier crossing
- **Equilibration time**: t_eq ~ 1/Delta for the Markov chain on the landscape
- **Evolution speed**: The time for selection to fix the fittest type scales as 1/Delta

For K = 0: Delta ~ O(1) (fast adaptation)
For K = N-1: Delta ~ O(1/2^N) (exponentially slow, landscape is "glassy")

The spectral gap of the fitness Hamiltonian IS the spectral gap of the corresponding Lindbladian (master equation for mutation-selection dynamics).

---

## 8. Wright-Fisher Model as Discrete Channel

### 8.1 The Wright-Fisher Process

For a population of 2N haploid individuals with two alleles (frequency p of allele A):

    p' ~ Binomial(2N, p_selected) / (2N)

where p_selected = p * w_A / (p * w_A + (1-p) * w_a) incorporates selection.

### 8.2 Channel Representation

The transition probability:

    T(p' | p) = C(2N, 2Np') * p_sel^{2Np'} * (1-p_sel)^{2N-2Np'}

defines a discrete channel from input frequency p to output frequency p'. In density matrix form (discretizing the frequency space to 2N+1 states):

    rho -> T rho T^T

where T_{ij} = T(j/(2N) | i/(2N)).

**Channel properties**:
- Not unital: T does not preserve the uniform distribution (drift is biased toward fixation)
- Absorbing states: p=0 and p=1 are absorbing (once fixed, stays fixed). These are pure states |0><0| and |1><1|.
- Ergodic (with mutation): adding mutation makes the channel irreducible with a unique stationary state

### 8.3 Diffusion Limit (Kimura)

For large N, the Wright-Fisher process converges to the diffusion:

    dp = s p(1-p) dt + sqrt(p(1-p)/(2N)) dW

where s = selection coefficient, W = Wiener process. The transition density satisfies the Fokker-Planck equation:

    d rho/dt = -(1/2) d/dp [2sp(1-p) rho] + (1/(4N)) d^2/dp^2 [p(1-p) rho]

This is a Lindblad equation in the position representation:

    d rho/dt = -i[H_drift, rho] + sum_k (L_k rho L_k^dagger - {L_k^dagger L_k, rho}/2)

where H_drift encodes selection (deterministic drift) and L_k encodes genetic drift (stochastic noise). The drift strength 1/(2N) is the noise rate = decoherence rate. Large N = weak decoherence = nearly deterministic evolution. Small N = strong decoherence = dominated by drift.

### 8.4 Fixation Probability as Measurement Outcome

The fixation probability of a new mutant with selective advantage s:

    u(s) = (1 - exp(-2s)) / (1 - exp(-4Ns))

For neutral mutations (s=0): u = 1/(2N).
For beneficial mutations (s > 0, Ns >> 1): u ~ 2s.

In QIT terms: fixation probability = probability of a specific measurement outcome. The initial state rho_0 = (1/(2N))|A><A| + (1-1/(2N))|a><a| (one copy of mutant allele). The "measurement" is the long-time limit of the drift-selection channel. The outcome probabilities are:

    p(fixation) = u(s)
    p(loss) = 1 - u(s)

The fixation process IS a quantum measurement: an initial superposition/mixture is driven to one of two absorbing pure states by the combined action of deterministic selection and stochastic drift.

---

## 9. Neutral Evolution as Depolarizing Channel

### 9.1 Neutral Theory (Kimura)

Under neutral evolution (all alleles equally fit, s = 0 for all), the only force is genetic drift. The Wright-Fisher process with no selection is:

    p' ~ Binomial(2N, p) / (2N)

The transition matrix T has the property T(I/n) = I/n (the uniform distribution is stationary under neutral drift with mutation). With symmetric mutation, this is a doubly stochastic (unital) channel.

### 9.2 Exact Mapping to Depolarizing Channel

For K alleles with symmetric mutation rate mu between all pairs:

    E(rho) = (1 - K*mu/(K-1)) * DRIFT(rho) + (K*mu/(K-1)) * (I/K)

where DRIFT is the binomial sampling channel. In the diffusion limit:

    E(rho) = (1 - t/N_e) rho + (t/N_e) (I/K)

This IS the depolarizing channel with parameter p = t/N_e:

    E_depol(rho) = (1-p) rho + p (I/d)

**Exact correspondence**:
- Effective population size N_e = inverse decoherence rate
- Number of alleles K = Hilbert space dimension
- Neutral mutation rate mu = depolarizing noise rate
- Genetic diversity theta = 4 N_e mu = coherence parameter

The heterozygosity (probability two random alleles differ):

    H = 1 - Tr(rho^2) = 1 - sum x_i^2

is the linear entropy S_lin(rho) = 1 - Tr(rho^2). Under neutral evolution:

    H(t) = H_eq + (H_0 - H_eq) exp(-t/(2N_e))

where H_eq = theta/(1+theta). This is exponential decay toward the equilibrium purity -- exactly the behavior of the depolarizing channel.

### 9.3 Coalescent as Reverse Channel

The coalescent (Kingman 1982) traces lineages backward in time. Two lineages coalesce (merge into a common ancestor) at rate 1/N_e per generation.

In QIT terms: the coalescent IS the reverse (adjoint) channel. Forward: depolarizing (diversity increases). Backward: concentrating (lineages merge, diversity decreases). The adjoint of the depolarizing channel is itself depolarizing (self-adjoint with respect to the Hilbert-Schmidt inner product), which corresponds to the time-reversibility of neutral evolution.

The coalescent tree structure encodes the entanglement structure of the population: sequences that share a recent common ancestor are "entangled" (correlated) through their shared ancestry.

---

## 10. Lotka-Volterra as Coupled Hamiltonian Systems

### 10.1 The Equations

The Lotka-Volterra equations for n species with abundances N_i:

    dN_i/dt = N_i (r_i + sum_j a_{ij} N_j)

where r_i = intrinsic growth rate, a_{ij} = interaction coefficient. For two species (predator-prey):

    dN_1/dt = N_1 (a - b N_2)     (prey)
    dN_2/dt = N_2 (-c + d N_1)    (predator)

### 10.2 Hamiltonian Structure

The two-species Lotka-Volterra system has a conserved quantity (Volterra integral):

    V = d N_1 - c ln(N_1) + b N_2 - a ln(N_2)

This defines level curves that are the phase-space orbits. The system is Hamiltonian with:

    H(q_1, p_1) = a p_1 - c exp(p_1) + b q_1 - d exp(q_1) (Huh... nope, need correct coords)

Using the substitution q_i = ln(N_i):

    dq_1/dt = a - b exp(q_2)
    dq_2/dt = -c + d exp(q_1)

This has Hamiltonian:

    H(q_1, q_2) = d exp(q_1) - c q_1 + b exp(q_2) - a q_2

with symplectic structure dq_1 ^ dq_2.

### 10.3 QIT Mapping

The density matrix for the Lotka-Volterra system: normalize the abundances:

    rho_LV = diag(N_1/N_total, ..., N_n/N_total)

The interaction matrix A = (a_{ij}) plays the role of the Hamiltonian. The dynamics is:

    d rho/dt = A rho + rho A^T - 2 Tr(A rho) rho + (growth terms)

For the conservative (Hamiltonian) part: the orbits are energy surfaces of H. The system does NOT equilibrate -- it oscillates. In QIT terms: this is unitary-like evolution (the Hamiltonian structure prevents entropy increase).

**Where the mapping is approximate**: The Lotka-Volterra system is nonlinear (interaction terms couple the species). The QIT analog would require a nonlinear quantum channel. For small perturbations around equilibrium, the linearized dynamics IS a proper Lindblad equation with both Hamiltonian (oscillatory) and dissipative (damping) parts:

    d(delta rho)/dt = -i[H_osc, delta rho] + D(delta rho)

where H_osc generates the oscillations and D provides damping toward equilibrium (if the equilibrium is stable).

### 10.4 Competitive Exclusion as Purification

The competitive exclusion principle: n species competing for k < n resources cannot coexist at equilibrium. In QIT terms: the channel defined by resource competition has a fixed point of rank at most k. The population state rho is driven toward a rank-k state (at most k surviving species). This is purification under the competition channel.

---

## 11. Evolutionary Game Theory: Payoff as Hamiltonian

### 11.1 Two-Player Symmetric Games

Players choose from strategies {1, ..., n}. The payoff matrix A has entry A_{ij} = payoff to strategy i when opponent plays j. A mixed strategy is a probability vector p = (p_1, ..., p_n).

**Expected payoff**: E[payoff] = p^T A q where q is the opponent's strategy. In density matrix form:

    <payoff> = Tr(rho_1 tensor rho_2 * H_A)

where H_A = sum_{ij} A_{ij} |i><i| tensor |j><j| and rho_k = diag(p_k) for player k.

### 11.2 Nash Equilibrium as Fixed Point

A Nash equilibrium (p*, q*) satisfies:

    p^T A q* <= p*^T A q*    for all p
    p* A q <= p*^T A q*      for all q

In density matrix form: rho* is a fixed point of the best-response channel:

    BR(rho) = argmax_sigma Tr(sigma tensor rho * H_A)

For a symmetric game: BR(rho) = |i*><i*| where i* = argmax_i (A rho)_i. The Nash equilibrium rho* satisfies BR(rho*) = rho* (or rho* is a mixture over pure best responses).

**Replicator dynamics as relaxation to Nash**: The replicator equation d x_i/dt = x_i((Ax)_i - x^T Ax) is the gradient flow (under the Shahshahani metric) toward Nash equilibria. Interior Nash equilibria are fixed points of the replicator dynamics.

### 11.3 Evolutionarily Stable Strategy (ESS) as Thermal Stability

An ESS p* satisfies:
1. p*^T A p* >= p^T A p* for all p (Nash condition)
2. If p*^T A p* = p^T A p*, then p*^T A p > p^T A p (stability)

In QIT terms: rho* is an ESS if it is a Nash equilibrium AND is stable under perturbations. The stability condition says: the free energy landscape has a strict local minimum at rho*. Small perturbations (mutant invasions) are driven back to rho* by the replicator dynamics.

**ESS = ground state of the interaction Hamiltonian**: An ESS has the property that no small perturbation can lower the "energy" (= negative payoff). It is a local ground state, stable against all local excitations. Global ESS = global ground state.

### 11.4 Quantum Extension

In quantum game theory (Eisert et al. 1999), strategies are unitary operators U in SU(2), and the initial state is entangled:

    |psi_0> = J |00>

where J = exp(i gamma sigma_x tensor sigma_x / 2) is an entangling gate (gamma measures entanglement). Players apply U_1 tensor U_2, then disentangle and measure. The payoff:

    <payoff> = Tr(rho_final * H_A)

where rho_final = (J^dagger (U_1 tensor U_2) J) |00><00| (J^dagger (U_1 tensor U_2) J)^dagger.

**Key result**: At maximal entanglement (gamma = pi/2), the quantum Prisoner's Dilemma has a Nash equilibrium at (Q, Q) where Q = i sigma_y = [[0, -1],[1, 0]], with payoff (3,3) -- Pareto-dominating the classical Nash (D,D) with payoff (1,1). Entanglement enables cooperation.

**Mapping**: The payoff matrix A becomes the Hamiltonian H_A. Classical mixed strategies (diagonal rho) are a subset of quantum strategies (general rho). The quantum game's Nash equilibria include all classical equilibria plus new entangled equilibria. The extra degrees of freedom (off-diagonal coherences and entanglement) expand the strategy space.

---

## 12. Summary of Exact vs. Approximate Mappings

### Exact Mappings (Isomorphisms)

1. **Population vector <-> diagonal density matrix**: The n-type population IS a diagonal density matrix. All algebraic properties transfer exactly.

2. **Mutation matrix <-> classical channel**: Column-stochastic mutation matrices ARE classical CPTP maps. The Kraus representation, composition rules, and entropy inequalities all apply.

3. **Fisher's theorem <-> quantum variance identity**: d<H>/dt = Var(H) = (Delta H)^2 is the same equation in both frameworks. No approximation.

4. **Price equation <-> quantum covariance**: Cov_rho(W,Z) = Tr(rho WZ) - Tr(rho W)Tr(rho Z) is exact for diagonal observables.

5. **Neutral evolution <-> depolarizing channel**: The symmetric mutation + drift process IS the depolarizing channel. Effective population size = inverse decoherence rate. Exact.

6. **Error threshold <-> decoherence threshold**: Both are phase transitions at critical noise rate. The mathematical structure (leading eigenvalue crossing) is identical.

7. **Wright-Fisher absorbing states <-> measurement outcomes**: Fixation = collapse to a pure state. The absorbing Markov chain structure is exactly a measurement channel.

### Approximate Mappings (Structural Parallels)

1. **Selection <-> measurement**: Selection is nonlinear (fitness-dependent normalization); quantum measurement is linear (trace-preserving). The extended-system construction (post-selection) bridges this gap but adds complexity.

2. **Frequency-dependent fitness <-> state-dependent Hamiltonian**: When f = f(x) = f(rho), the dynamics is nonlinear in rho. Quantum channels are linear. Mean-field approximation recovers a Lindblad equation but loses correlations.

3. **Recombination <-> entangling gate**: Recombination creates correlations between loci, analogous to entangling gates. But recombination is irreversible and probabilistic; entangling gates are unitary. The mapping holds at the level of correlation structure, not dynamics.

4. **Lotka-Volterra <-> coupled oscillator Hamiltonians**: The Hamiltonian structure is exact for conservative two-species dynamics, but approximate for dissipative multi-species systems.

5. **NK landscape <-> spin glass Hamiltonian**: The correspondence of the fitness function to a Hamiltonian is exact. The dynamics on the landscape is approximate because evolutionary search is not thermal equilibrium.

---

## References

- Cohen, Sharir, Shashua, "On the Expressive Power of Deep Learning: A Tensor Analysis" COLT (2016)
- Eigen, "Self-organization of matter and evolution of biological macromolecules" Naturwissenschaften 58 (1971)
- Eisert, Wilkens, Lewenstein, "Quantum Games and Quantum Strategies" PRL 83 (1999)
- Ewens, "Mathematical Population Genetics" 2nd ed. (2004)
- Fisher, "The Genetical Theory of Natural Selection" (1930)
- Frank, "George Price's contributions to evolutionary genetics" J. Theor. Biol. 175 (1995)
- Frank, "Natural Selection. V. How to read the fundamental equations" J. Evol. Biol. 25 (2012)
- Hofbauer & Sigmund, "Evolutionary Games and Population Dynamics" (1998)
- Kauffman, "The Origins of Order" (1993)
- Kimura, "The Neutral Theory of Molecular Evolution" (1983)
- Kingman, "The coalescent" Stoch. Proc. Appl. 13 (1982)
- Nowak, "Evolutionary Dynamics" (2006)
- Page & Nowak, "Unifying Evolutionary Dynamics" J. Theor. Biol. 219 (2002)
- Petz, "Quantum Information Theory and Quantum Statistics" (2008)
- Price, "Selection and Covariance" Nature 227 (1970)
- Price, "Fisher's fundamental theorem made clear" Ann. Hum. Genet. 36 (1972)
- Saakian & Hu, "Exact solution of the Eigen model with general fitness functions" PRA 69 (2006)
- Sella & Hirsh, "The application of statistical physics to evolutionary biology" PNAS 102 (2005)
- Wright, "Evolution in Mendelian populations" Genetics 16 (1931)
