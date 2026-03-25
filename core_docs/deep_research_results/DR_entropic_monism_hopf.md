# Entropic Monism and Emergent Hopf Geometry from Information Exchange

## Executive summary

“Entropic Monism” (as framed in your prompt) can be treated as a constructive research program: start from a *primary* interaction graph of information/entropy exchange, define an operational notion of distance from mutual information, and test whether familiar geometric structures appear as stable attractors under constrained quantum dynamics. This is aligned in spirit with the broader “spacetime-from-entanglement” agenda explored in quantum gravity and holography, where entanglement patterns are treated as architecturally prior to classical geometry. citeturn4search8turn9search0turn4search5

Your axiom (“distance between state A and state B is proportional to the inverse of mutual information”) is workable as an *edge-length heuristic* but is numerically ill-conditioned as written (diverges at \(I\!\to\!0\)) and does not by itself guarantee a proper metric (triangle inequality). A robust solution is to: (i) **regularize** and **monotonically transform** mutual information into finite positive edge lengths, then (ii) define the actual inter-node distance as a **shortest-path (graph geodesic) metric**, which enforces metric axioms independent of the edge transform (assuming nonnegative symmetric edge weights). citeturn5search6turn2search1

To make an \(S^3\) / Hopf-fibration geometry plausibly emerge, “random CPTP couplings” must be *constrained* or *selected*, because generic random CPTP dynamics tends to mix and converge rapidly toward an invariant state (often close to maximally mixed), erasing fine structure. citeturn0search6 A standard remedy is to combine (a) **random entangling interactions** with (b) **engineered dissipation** (non-unital channels) and (c) **selection rules** that minimize an explicit “free energy” objective balancing low entropy with geometric self-consistency. Dissipative state engineering is a well-established technique for driving systems into structured steady states. citeturn0search0

Finally, because a single-qubit *pure-state* Hilbert space is naturally \(S^3\), and the Hopf fibration \(S^1\hookrightarrow S^3\to S^2\) corresponds to quotienting the global phase to yield the Bloch sphere, it is natural to use **\(S^3\) as the target manifold** when you want a “Hopf geometry” signature to appear in an information-derived embedding. citeturn2search49turn7search1

## Conceptual grounding

A useful way to operationalize “Entropic Monism” is to interpret it as a **two-layer model**:

1. **Primitive layer (ontic)**: a directed/undirected graph of “information exchange” events; in the quantum setting, this becomes a network of CPTP couplings that create, redistribute, or erase correlations among subsystems.
2. **Emergent layer (phenomenic)**: geometry is inferred from correlation structure, typically via entanglement entropies and related information measures; time is treated as an ordering parameter of updates or as an emergent thermodynamic arrow tied to monotone functionals (entropy/complexity). citeturn4search8turn9search0turn4search5

This is broadly consonant with modern “spacetime-from-entanglement” perspectives: holographic duality proposals relate entanglement entropies of boundary subregions to bulk geometric quantities via minimal surfaces (Ryu–Takayanagi), and mutual information appears as a diagnostic of connectivity/correlation structure (e.g., vanishing at leading order when regions are “too far” in holographic setups). citeturn4search5turn5search5turn5search7 The entity["organization","It from Qubit","simons collaboration"] program explicitly frames “Does spacetime emerge from entanglement?” as a central motivating question, validating your overall direction as a research hypothesis (not a settled result). citeturn4search8

Entropic-gravity proposals (notably entity["people","Erik Verlinde","entropic gravity proposer"]) treat gravitational dynamics as emergent from information/entropy considerations, explicitly tying “space emergence” to information associated with matter configurations. citeturn9search0turn1search1 This is conceptually adjacent to your “distance from mutual information” axiom, though your proposal is more microscopic/operational (graph + quantum channels) than Verlinde’s macroscopic thermodynamic argument. citeturn9search0

A key technical takeaway from this literature for your simulator design is that *information → geometry* is typically **not automatic** under unconstrained randomness: one usually needs either (i) a known “duality map” (as in AdS/CFT), (ii) structured state ansätze (tensor networks), or (iii) explicit optimization/selection principles that favor geometric regularities over generic mixing. citeturn3search4turn0search6

## Regularized information-distance metrics for finite qubit networks

### Quantum mutual information as the primitive “proximity” observable

For two subsystems \(A,B\) (e.g., individual qubits \(i,j\)) with joint state \(\rho_{AB}\) and reduced states \(\rho_A,\rho_B\), the quantum mutual information is
\[
I(A{:}B)=S(\rho_A)+S(\rho_B)-S(\rho_{AB}),
\]
where \(S(\rho)=-\mathrm{Tr}(\rho\log\rho)\) is the von Neumann entropy. citeturn5search7

Operationally, \(I(A{:}B)\) is also the quantum relative entropy between \(\rho_{AB}\) and \(\rho_A\otimes\rho_B\), so it quantifies deviation from product structure; bounds relating mutual information to trace-distance-like notions of correlation are known (and useful for numerical sanity checks and regularization). citeturn5search6

### Why literal \(d\propto 1/I\) needs regularization

Your axiom \(d(A,B)\propto 1/I(A{:}B)\) encounters three practical problems in finite simulations:

* **Divergence at independence**: initially maximally mixed product qubits have \(I\approx 0\), so \(1/I\) becomes numerically unstable and conceptually infinite.
* **Noise floor + estimator bias**: if MI is estimated (or computed with finite precision), small spurious positive MI can create artificially short edges unless a floor is imposed.
* **Metric axioms**: raw pairwise transforms of a similarity measure do not automatically satisfy triangle inequality; a standard fix is to build a **path metric** on a weighted graph. citeturn2search1turn5search6

### Candidate definitions and tradeoffs

The table below catalogs MI-derived distance candidates that are numerically stable for finite \(N\) and practicable for “emergent manifold” fitting.

| Candidate | Definition (pairwise) | Stability at \(I\to 0\) | Triangle inequality | MI–physics interpretability | Notes |
|---|---|---:|---:|---:|---|
| Regularized inverse MI | \( \ell_{ij}=\alpha\,(I_{ij}+\varepsilon)^{-1} \) | Needs \(\varepsilon>0\) | Not guaranteed | High (closest to axiom) | Good as *edge weight*, but use path metric for distances. |
| Log-inverse MI (recommended) | \( \ell_{ij}=\frac{\alpha}{\beta}\log\!\frac{I_{\max}+\varepsilon}{I_{ij}+\varepsilon} \) | Finite, tunable cap | Not guaranteed pairwise; **yes** after path-metric | High | Matches intuition “correlations decay exponentially with distance” ⇒ distance \(\sim-\log I\). |
| Normalized MI chord distance | \( \ell_{ij}=\alpha\sqrt{1-\frac{I_{ij}}{I_{\max}}} \) | Stable if clipped | Not guaranteed | Medium | Bounded, smooth; less directly tied to exponential decay models. |
| Correlation-distance proxy | \(\ell_{ij}=\alpha\,g\!\left(\|\rho_{ij}-\rho_i\!\otimes\!\rho_j\|_1\right)\) | Stable | Depends on \(g\) | Medium | MI bounds based on correlation distance support sanity checks. citeturn5search6 |
| Jensen–Shannon distance (state-space; not MI) | \(d_{\mathrm{JS}}(\rho,\sigma)=\sqrt{J(\rho,\sigma)}\) | Stable, bounded | Metric (for prob. dists.) citeturn2search1; quantum version largely metric citeturn2search6 | Low for MI-axiom | Useful as *auxiliary* regularizer: keeps states from collapsing into numerical artifacts. |

Key metric facts used above: the square root of the Jensen–Shannon divergence is a true metric for classical distributions, and the quantum Jensen–Shannon distance has been studied with evidence for metric character (formal for pure states; numerical for mixed states). citeturn2search1turn2search6

### Recommended “compile-ready” distance construction

For a qubit network (nodes \(1..N\)) with pairwise MI \(I_{ij}\) (in bits), define:

1. **Cap and regularize MI**
   * \(I_{\max}=2\) bits for qubit–qubit MI (tight upper bound).  
   * \(I^{\mathrm{clip}}_{ij}=\min(\max(I_{ij},0),I_{\max})\).
   * Choose \(\varepsilon\in[10^{-6},10^{-3}]\) bits (numerical floor).

2. **Convert to nonnegative edge lengths**
   \[
   \ell_{ij}=\frac{1}{\beta}\log\left(\frac{I_{\max}+\varepsilon}{I^{\mathrm{clip}}_{ij}+\varepsilon}\right),
   \]
   where \(\beta\) is a scale parameter (acts like an “information inverse temperature”).

3. **Build a sparse weighted graph** \(G\)  
   Use \(k\)-NN by smallest \(\ell_{ij}\) (largest MI) or threshold by \(I_{ij}\ge I_{\mathrm{min}}\). This prevents a dense \(O(N^2)\) edge set from dominating and makes manifold learning feasible.

4. **Define the metric distance as a path metric**
   \[
   d(i,j)=\min_{\pi:i\to j} \sum_{(a,b)\in \pi}\ell_{ab},
   \]
   which guarantees a proper metric on the node set if \(\ell_{ab}\ge 0\). This is the most direct way to keep your axiom’s monotonicity while gaining metric structure. citeturn2search1

### Numerical notes for finite \(N\)

For exact density-matrix simulation, computing all pairwise \(I_{ij}\) requires many partial traces but is straightforward for modest \(N\) (practically \(N\lesssim 12\!-\!16\) on typical hardware with dense matrices). For larger \(N\), you can shift to (i) structured circuit families (e.g., Clifford subsets) or (ii) approximate MI estimation via sampling (classical shadows), but those are extensions beyond the strict “compile-ready” spec. citeturn3search4turn0search6

## CPTP coupling dynamics: ensembles, parameterizations, selection rules

### Why “random CPTP until geometry emerges” needs constraints

Generic random CPTP maps form mixing dynamics that tend to converge exponentially to an invariant state; in many ensembles, that invariant state is close to maximally mixed (or at least featureless at the pairwise MI level), which works against persistent geometric structure. citeturn0search6 Therefore, a viable simulator must add at least one of:

* **Non-unital dissipation** to reduce entropy and stabilize nontrivial steady states (reservoir engineering). citeturn0search0  
* **Selection/acceptance rules** to prefer channel instances that *increase geometric self-consistency* (an algorithmic “entropic oracle”).  
* **Symmetry-broken priors** that bias the dynamics toward an \(S^3\)-like homogeneous manifold rather than generic graph clustering.

### CPTP ensembles suitable for a geometry-emergence simulator

Below is a practical menu of CPTP families (all implementable via Kraus operators or Stinespring dilation) and their roles:

| Ensemble / family | Parameterization | Unital? | Typical entropy tendency | Role in emergence | Key source support |
|---|---|---:|---|---|---|
| Haar-random 2-qubit unitary | \(U\sim\mathrm{Haar}(\mathrm{SU}(4))\) acting on \((i,j)\) | Yes (as a channel) | Preserves global entropy if global unitary; creates entanglement from pure inputs | Creates MI edges; good “stirring” | Random operations framework discusses convergence/mixing properties when combined with tracing/noise. citeturn0search6 |
| Random unitary channel | \(\Phi(\rho)=\sum_k p_k U_k\rho U_k^\dagger\) | Yes | Mixing toward maximally mixed | Use sparingly; mainly for perturbations | Generic random maps converge to invariant state with spectral gap. citeturn0search6 |
| Induced random CPTP via Stinespring | Sample Haar isometry \(V:\mathbb{C}^4\to\mathbb{C}^4\!\otimes\!\mathbb{C}^K\), \(\Phi(\rho)=\mathrm{Tr}_E(V\rho V^\dagger)\) | Typically no | Drives toward invariant state; tunable by ancilla dim \(K\) | “Generic noise” baseline; can model environment | Natural ensemble + algorithms for random CPTP maps. citeturn0search6turn0search2 |
| Depolarizing / dephasing | \(\Phi_p(\rho)=(1-p)\rho+p\frac{I}{4}\) (2-qubit) etc. | Yes | Increases entropy, kills MI | “Reset” control; prevents spurious trapping | Standard noise primitive; use as anti-correlation step. |
| Amplitude damping / thermalizing | Kraus with rate \(\gamma\) (possibly generalized to finite \(T\)) | No | Reduces entropy; creates pointer-basis structure | Provides low-entropy attractors needed for stable geometry | Dissipative engineering can prepare structured steady states. citeturn0search0 |
| Engineered Lindbladian step | \(\rho\mapsto e^{\mathcal{L}\Delta t}(\rho)\) with designed jump ops | No | Drives to designed steady states | Strongest “geometry formation” knob | Dissipation as computational/state-engineering resource. citeturn0search0 |

### Symmetry breaking and chirality selection mechanisms

**Symmetry breaking** is needed because the (product) maximally mixed initial condition has no preferred geometry: all MI are (ideally) zero, so any geometry is equally consistent at \(t=0\). A tiny explicit perturbation (e.g., small random local amplitude damping rates \(\gamma_i\), small random single-qubit Hamiltonian fields, or a single “seed” entangling event) is sufficient to break permutation symmetry and let one basin of attraction dominate.

**Chirality selection**: to bias toward a specific Hopf chirality (left- vs right-handed linking), incorporate a small **parity-odd coupling bias**. A standard two-body chiral interaction in spin systems is the Dzyaloshinskii–Moriya interaction (DMI), of the form
\[
H_{\mathrm{DM}}\propto \mathbf{D}_{ij}\cdot(\mathbf{m}_i\times \mathbf{m}_j),
\]
which arises from broken inversion symmetry and spin–orbit effects and selects a handedness of spin textures. citeturn7search3turn6search7 In your simulator, you can implement a *unitary component* \(U=\exp(-i(H_0+\lambda_{\chi}H_{\mathrm{DM}})\Delta t)\) in the two-qubit step, with small \(\lambda_\chi\) and randomized \(\mathbf{D}_{ij}\) drawn from a distribution that is slightly biased in sign or alignment. citeturn7search3

### Selection rule as an “entropic monism” analog of action minimization

To prevent generic mixing and to favor an \(S^3\) embedding, define an objective (“free energy”) evaluated after each candidate channel application:

\[
F(\rho) = \lambda_S\,S(\rho) \;+\; \lambda_{\mathrm{geom}}\,E_{S^3} \;+\; \lambda_{\mathrm{hom}}\,E_{\mathrm{hom}} \;+\; \lambda_{\chi}\,E_{\chi}.
\]

Where:
* \(S(\rho)\) is global von Neumann entropy (or a proxy if \(\rho\) is large).
* \(E_{S^3}\) measures how well the MI-derived metric embeds as a 3-sphere in \(\mathbb{R}^4\) (defined precisely below).
* \(E_{\mathrm{hom}}\) penalizes degree/edge-weight inhomogeneity (to avoid “one hub + many leaves,” which is low entropy but not \(S^3\)-like).
* \(E_{\chi}\) is a chirality order parameter from the learned embedding (e.g., sign-stable triple products / linking proxies).

Then accept a random CPTP proposal \(\Phi\) via a Metropolis criterion:
* If \(\Delta F\le 0\): accept.
* Else: accept with probability \(\exp(-\Delta F/T)\) with annealed temperature \(T\downarrow 0\).

This makes the simulator a *controlled self-organization* process rather than unconstrained random mixing—consistent with known needs in dissipative engineering and emergent-geometry constructions. citeturn0search0turn0search6turn3search4

## Simulation system targeting an \(S^3\) Hopf geometry attractor

### Why \(S^3\) is the right “Hopf target” for qubits

The Hopf fibration is the fiber-bundle structure \(S^1\hookrightarrow S^3\to S^2\), where each point on \(S^2\) corresponds to a circle fiber in \(S^3\). citeturn2search49 For qubits, a normalized state vector in \(\mathbb{C}^2\) lives on \(S^3\), and modding out by an overall phase yields the Bloch sphere \(S^2\); this is precisely the Hopf fibration viewpoint used in quantum-state geometry discussions. citeturn7search1turn6search3

image_group{"layout":"carousel","aspect_ratio":"16:9","query":["Hopf fibration visualization circles on S3","Hopf link diagram S3 Hopf fibration","Bloch sphere qubit representation","Hopf fibration S3 to S2 fiber circles"],"num_per_query":1}

### Architecture

```mermaid
flowchart LR
  A[State Backend\nρ on (C^2)^⊗N\nExact DM / Approx] --> B[Pair Selector\nsamples (i,j)]
  B --> C[Channel Sampler\nrandom CPTP draw\nfrom ensemble mixture]
  C --> D[Apply Channel\nρ' = (Φ_ij ⊗ I)(ρ)]
  D --> E[Metrics Engine\nS(ρ'), MI matrix I_ij\nedge lengths ℓ_ij, graph metric d_ij]
  E --> F[Embedding + Hopf Detector\nR^4 spectral/MDS embedding\nproject to S^3\nHopf map + chirality estimators]
  F --> G[Objective + Acceptance\nΔF, anneal T\naccept/reject update]
  G -->|accept| A
  G -->|reject| A
  E --> H[Artifacts\ncheckpoints, graphs, metrics, embeddings]
  F --> H
```

### Simulation loop (timeline flowchart)

```mermaid
flowchart TD
  S0[Init\nN qubits, ρ0 = I/2^N\n+ tiny symmetry-breaking seed] --> S1[Warm-up\nfew accepted entangling steps\nraise MI above noise floor]
  S1 --> S2[Annealed evolution\nrepeat:\n(1) choose pair\n(2) sample CPTP\n(3) compute MI distances\n(4) embed to R^4 & project to S^3\n(5) compute ΔF\n(6) accept/reject]
  S2 --> S3[Convergence tests\nwindowed stability of:\nF, S(ρ), E_S3, chirality]
  S3 -->|pass| S4[Output\nfinal ρ*, MI graph, S^3 embedding,\nHopf fibers, logs]
  S3 -->|fail| S2
```

### Concrete mechanism for “Hopf geometry emergence”

The simulator’s “emergent geometry” claim should be pinned to explicit observables. A workable definition:

1. **From state to distances**  
   Compute pairwise MI \(I_{ij}\) and build the metric \(d_{ij}\) using the log-regularized + shortest-path construction above.

2. **From distances to an \(S^3\subset\mathbb{R}^4\) embedding**  
   Use classical multidimensional scaling (MDS) or Laplacian eigenmaps to embed nodes into \(\mathbb{R}^4\) using \(d_{ij}\) as target distances; then project points to a common radius \(R\) (normalize each vector). This yields candidate points \(x_i\in S^3\).

3. **Geometry error \(E_{S^3}\)**  
   Measure stress between graph distances and spherical geodesic distances:
   \[
   E_{S^3}=\frac{\sum_{i<j}\left(d_{ij}-R\arccos\frac{x_i\cdot x_j}{R^2}\right)^2}{\sum_{i<j}d_{ij}^2}.
   \]
   Low \(E_{S^3}\) indicates consistency with a 3-sphere geometry.

4. **Hopf-structure diagnostic (optional but aligned with your request)**  
   Given a representation of \(x_i\in S^3\subset\mathbb{C}^2\) as a normalized spinor \((z_1,z_2)\), compute the Hopf map to \(S^2\):
   \[
   \pi(z_1,z_2) = (2\,\mathrm{Re}(z_1\bar z_2),\,2\,\mathrm{Im}(z_1\bar z_2),\,|z_1|^2-|z_2|^2).
   \]
   Nodes with similar \(\pi\) but different phase should lie along approximate “fibers” (circles). The Hopf fibration structure itself is standard. citeturn2search49turn7search1

5. **Chirality order parameter \(E_{\chi}\)**  
   Use a simple global chirality proxy from embedding triples (or small loops in the nearest-neighbor graph). For example, define triangle orientation signs using 4D bivector wedge products projected to a chosen pseudoscalar; enforce sign consistency over many triangles. (This is a discrete stand-in for “handedness” in the point cloud.) To bias it physically, include a DMI-like term in the entangling unitary component. citeturn7search3turn6search7

### Stability and convergence criteria

A “stable low-entropy \(S^3\) clustering” should be declared only if multiple criteria hold simultaneously over a window \(W\) of iterations:

| Convergence metric | Definition | Typical threshold | Why it matters |
|---|---|---:|---|
| Objective stability | \(\mathrm{Var}_W(F)\) | \(<10^{-6}\)–\(10^{-4}\) | Prevents declaring transient structures “emergent.” |
| Entropy plateau | \(|S(\rho_{t})-S(\rho_{t-W})|\) | small | Ensures low-entropy attractor rather than ongoing thermalization. Dissipation methods justify steady-state targeting. citeturn0search0 |
| \(S^3\) stress | \(E_{S^3}\) | \(<0.05\) (toy) | Primary geometry-fit criterion. |
| Radius concentration | \(\mathrm{CV}(\|x_i\|)\) before projection | small | Checks that embedding naturally concentrates on a sphere (not an artifact of forced projection). |
| Chirality locking | sign-consistency of \(E_\chi\) over \(W\) | stable | Confirms symmetry breaking into a chiral basin (needed for “Hopf handedness”). DMI motivates chirality control. citeturn7search3 |
| Graph homogeneity | degree/weight entropy within band | bounded | Avoids degenerate “cluster-of-clusters” overfitting. |

### Recommended default hyperparameters (practical starting point)

These are pragmatic defaults for a first runnable prototype:

* **N**: start with \(N=12\) or \(N=16\) for exact density matrices; scale up only after validating the pipeline.
* **Pair selection**: mixture of exploration and exploitation  
  \(p(i,j)=\eta\,\text{Uniform} + (1-\eta)\,\text{Softmin}(\ell_{ij}/T_p)\), with \(\eta\sim 0.1\).
* **Channel mixture per proposal**:  
  60% entangling unitary (random Hamiltonian step), 25% induced random CPTP (Stinespring with \(K=2\)), 15% dissipative (amplitude damping + dephasing).
* **Annealing**: \(T(t)=T_0\exp(-t/\tau)\) with \(T_0\sim 1\), \(\tau\sim 10^4\) proposals.
* **Chirality bias**: small \(\lambda_\chi\sim 10^{-3}\!-\!10^{-2}\) in the DMI-like term (enough to pick a basin without dominating).

These choices are consistent with: (i) generic random operations being mixing (so dissipation/selection is needed), and (ii) dissipation being able to stabilize correlated steady states when engineered. citeturn0search6turn0search0

## Compile-ready YAML problem_spec

### Schema grounding from your enabled GitHub connectors

The “problem_spec.yaml” files found in the connected entity["organization","lev-os/leviathan","github repo"] repository use a strict top-level structure:

* top-level key: `problem`
* required fields under `problem`: `statement`, `for_whom`, `constraints` (list), `success_criteria` (list), and `scope` with `in`/`out` lists. fileciteturn34file0L1-L1 fileciteturn42file0L1-L1

Because your request explicitly references the `problem_spec` compile path and asks for “strict YAML,” the spec below **adheres to exactly that structure**, embedding simulator parameters/observables/convergence tests as structured *block-string list items* to remain schema-compatible while still being machine-ingestible by downstream tools that parse the text payload. fileciteturn34file0L1-L1

```yaml
problem:
  statement: >
    Design and validate an "Entropic Monism" toy simulator in which a graph of information/entropy exchange
    among N initially unstructured qubits self-organizes under iterative random CPTP couplings (with explicit
    selection rules and dissipation) into a stable low-entropy mutual-information geometry whose best-fit
    embedding is an S^3 (Hopf-fibration-consistent) manifold in R^4. The operational axiom is that distance
    is a monotone decreasing function of mutual information I(A:B), with explicit regularization and a true
    metric induced as a graph geodesic.
  for_whom: >
    Researchers/engineers building information-theoretic emergence simulators (quantum networks, CPTP dynamics,
    emergent geometry) who need a compile-ready specification with parameters, observables, convergence criteria,
    and artifacts to reproduce an S^3/Hopf-like emergent geometry from mutual-information structure.
  constraints:
    - >
      Initial condition:
        - N is unspecified at compile time; simulator MUST accept N as a runtime parameter.
        - Default N_small_exact = 12 (exact density matrix backend).
        - Initial state is unordered maximally mixed:
            ρ0 = I / 2^N
          with an optional symmetry-breaking seed:
            ρ0 <- (1-δ) ρ0 + δ ρ_seed
          where δ_default = 1e-6 and ρ_seed is a random low-rank perturbation or a single entangling event.
    - >
      Operational axiom -> numerically stable metric:
        - Primitive proximity: quantum mutual information I(A:B) = S(A)+S(B)-S(AB), measured in bits (log2).
        - For qubit pairs, cap I_max = 2 bits.
        - Regularize with epsilon floor ε (epsilon_bits_default = 1e-6):
            I_clip = min(max(I, 0), I_max)
        - Convert to nonnegative edge lengths (recommended):
            ℓ_ij = (1/β) * log( (I_max+ε)/(I_clip+ε) )
          with β_default = 1.0.
        - Build sparse weighted graph via k-NN on smallest ℓ_ij (k_default = 6).
        - Define metric distance as a path metric (shortest-path):
            d(i,j) = min_path Σ ℓ_ab
          (this is the only distance used for embedding and convergence tests).
    - >
      CPTP coupling dynamics:
        - Each proposal selects a pair (i,j) from:
            p(i,j) = η * UniformPairs + (1-η) * Softmin(ℓ_ij / T_pair)
          Defaults: η=0.10, T_pair=0.25.
        - Each proposal samples a CPTP map Φ_ij from a mixture of ensembles:
            (A) Entangling unitary step (prob p_unitary=0.60):
              U = exp(-i Δt (H0 + λ_chi * H_DM))
              where H0 is a random two-qubit Hamiltonian in the Pauli basis,
              and H_DM is a chirality-bias (DMI-like) antisymmetric exchange term.
              Defaults: Δt=0.10, λ_chi=0.01.
            (B) Induced random CPTP via Stinespring (prob p_stinespring=0.25):
              sample Haar isometry V: C^4 -> C^4 ⊗ C^K, K_default=2
              Φ(ρ) = Tr_env( V ρ V† )
            (C) Dissipative step (prob p_dissipative=0.15):
              amplitude damping + dephasing on (i,j) with rates γ, κ
              Defaults: γ=0.02, κ=0.01
        - Apply channel locally:
            ρ' = (Φ_ij ⊗ I_rest)(ρ)
    - >
      Selection rule (required to prevent generic mixing):
        - Define objective ("free energy"):
            F = λ_S * S_global(ρ)
              + λ_geom * E_S3
              + λ_hom * E_homogeneity
              + λ_chi * E_chirality
          Defaults: λ_S=1.0, λ_geom=5.0, λ_hom=0.5, λ_chi=0.25
        - Accept/reject via Metropolis annealing:
            if ΔF <= 0: accept
            else accept with prob exp(-ΔF / T)
          with T(t) = T0 * exp(-t/τ), defaults: T0=1.0, τ=10000 proposals.
    - >
      Geometry emergence target and tests:
        - From d(i,j), embed nodes into R^4 using classical MDS (or Laplacian eigenmaps).
        - Project to candidate S^3 by normalizing each point to radius R_fit.
        - Define S^3 stress:
            E_S3 = Σ_{i<j} ( d_ij - R arccos( (x_i·x_j)/R^2 ) )^2 / Σ_{i<j} d_ij^2
        - Optional Hopf diagnostic:
            interpret x_i as normalized spinor (z1,z2) in C^2 and compute Hopf map π: S^3 -> S^2.
        - Chirality locking:
            define a discrete chirality order parameter from triangle orientations in the k-NN graph in embedding space;
            require sign stability over a window W.
  success_criteria:
    - >
      The simulator produces a stable attractor (no further significant ΔF improvements) under an annealing schedule,
      and does not collapse to the trivial fully mixed / fully featureless mutual-information structure.
    - >
      Low-entropy stabilization is achieved:
        - global entropy S_global(ρ_t) plateaus (|S_t - S_{t-W}| < tol_S over a window),
        - while pairwise MI structure remains nontrivial (mean(I_ij) above noise floor).
    - >
      Geometry emerges as an S^3 best-fit:
        - E_S3 < tol_geom for at least W consecutive accepted steps,
        - embedding radius concentration is high (small variance in ||x_i|| before projection),
        - graph homogeneity penalty does not diverge (no hub-and-spoke degeneracy).
    - >
      Symmetry breaks and chirality selects:
        - chirality order parameter sign is stable over W steps,
        - repeat runs with different random seeds show bimodal chirality outcomes unless a bias λ_chi is applied,
          in which case a preferred chirality dominates.
    - >
      Artifacts are emitted for reproducibility:
        - checkpoints (ρ, MI matrix, distance matrix, embedding coordinates),
        - final summary report with convergence plots and pass/fail of convergence gates.
  scope:
    in:
      - >
        Backend implementations:
          - Exact density matrix backend for small N (default).
          - Pluggable approximation backend interface (optional).
      - >
        Required observables logged each checkpoint:
          - S_global(ρ)
          - single-qubit entropies S(i)
          - pairwise MI matrix I_ij
          - edge lengths ℓ_ij and geodesic distances d_ij
          - adjacency (k-NN) graph and graph statistics (degree distribution, spectral entropy)
          - R^4 embedding coordinates x_i and fitted radius R
          - E_S3 stress and chirality order parameter E_chirality
          - acceptance rate and ΔF statistics
      - >
        Convergence gates:
          - window length W_default = 500 accepted steps
          - tol_F = 1e-5 (objective variance threshold)
          - tol_S = 1e-5 (entropy plateau threshold)
          - tol_geom = 0.05 (S^3 stress threshold)
          - tol_chi = 0.01 (chirality stability threshold)
      - >
        Output artifacts:
          - run_manifest.yaml (all parameters, random seeds, git hash if applicable)
          - checkpoints/step_{t}.npz (ρ or compressed representation, I_ij, d_ij, x_i)
          - graphs/final_graph.graphml
          - embeddings/final_embedding.csv
          - reports/summary.md (convergence + verdict)
    out:
      - >
        Claims of physical reality: this simulator is a toy constructive model and does not by itself establish that
        real spacetime, dimensions, or time must emerge from mutual information in nature.
      - >
        Large-N scalability guarantees: exact density matrix simulation is expected to be limited; scaling beyond
        small N requires approximate backends not mandated in this spec.
      - >
        Full quantum-gravity equivalence: no AdS/CFT or dynamical Einstein-equation derivation is required here;
        only emergence diagnostics within the simulator’s defined observables.
```