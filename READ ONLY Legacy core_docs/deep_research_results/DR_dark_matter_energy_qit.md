# Dark Matter and Dark Energy as Entropic Operators in a QIT Cosmology

## Cosmological baseline for galaxy stability and accelerated expansion

In the standard cosmological framework (spatially flat “base”-ΛCDM), the roles played by “dark matter” and “dark energy” are operational rather than ontological: they are the names attached to (a) extra gravitating mass needed to explain the growth and binding of cosmic structure, and (b) a component (or effective modification) needed to explain the late-time, accelerating expansion of the Universe. Observationally, high-precision fits to the cosmic microwave background (CMB) anisotropies from the entity["organization","Planck Collaboration","cmb cosmology collaboration"] strongly constrain the cold dark matter density and the matter density parameter in ΛCDM (e.g., constraints on \(\Omega_c h^2\) and \(\Omega_m\)), and remain consistent with a dominant dark-energy component in the late universe. citeturn1search2turn1search9

The “galaxy stability” side of the story is historically tied to flat galaxy rotation curves: if luminous (baryonic) mass were the only gravitating source, orbital velocities would fall roughly as \(v(r)\propto r^{-1/2}\) outside the luminous mass distribution, but measured velocities remain high at large radii. Early quantitative rotation-curve work (e.g., Andromeda/M31) directly reported substantial mass extending well beyond the bright disk. citeturn5search47turn5search12  Contemporary cosmology folds this into halos of cold, (approximately) collisionless matter as a scaffold for galaxy formation and large-scale structure, consistent with diverse gravitational evidence (rotation curves, lensing, CMB, and structure growth). citeturn10search0turn1search2

image_group{"layout":"carousel","aspect_ratio":"16:9","query":["flat galaxy rotation curve Rubin Ford Andromeda M31 plot","Bullet Cluster dark matter map blue pink gravitational lensing","Type Ia supernova Hubble diagram accelerating expansion"],"num_per_query":1}

A particularly influential “direct” line of evidence for unseen mass uses merging galaxy clusters where gravitational lensing maps peak away from the dominant baryonic component (X-ray emitting gas), as in the Bullet Cluster (1E 0657−56 / 1E0657−558). The observational argument is that the lensing-inferred mass is spatially associated with the collisionless galaxy distribution rather than the collisional gas, implying a large non-luminous mass component. citeturn3search1turn10search0

On the “accelerating expansion” side, late-1990s Type Ia supernova Hubble diagrams showed distant supernovae were dimmer than expected in a decelerating universe, consistent with acceleration and a non-zero cosmological constant (or, more generally, a dark-energy component). This is documented in discovery-era analyses and follow-on datasets from the high-redshift supernova teams. citeturn0search0turn6search43turn6search2  As summarized by entity["organization","NASA","us space agency"] and the entity["organization","European Space Agency","space agency europe"], dark energy is currently treated as “whatever” produces acceleration, with leading interpretations including a cosmological constant (vacuum energy), dynamical fields (quintessence-like), or modifications of gravity on cosmic scales. citeturn6search2turn6search12turn6search11

## Translating into Codex-Ratchet entropic operators

Your Codex-Ratchet framing replaces “dark matter” and “dark energy” as physical substances with two information-theoretic primitives acting on a correlation graph:

- **Dark Matter (DM) as a negentropic anchor:** an operator that *holds correlations together* and resists decoherence-driven loss of structure.
- **Dark Energy (DE) as an unconstrained, maximally mixed channel:** a global CPTP mixing process that increases entropy and washes out correlations.

In quantum information theory, the most direct “correlation-as-a-scalar” quantity that matches your language is **quantum mutual information**. For a bipartite state \(\rho_{AB}\), the quantum mutual information is
\[
I(A\!:\!B)_\rho \;=\; S(\rho_A)+S(\rho_B)-S(\rho_{AB}),
\]
and can be written as a quantum relative entropy:
\[
I(A\!:\!B)_\rho \;=\; S\!\left(\rho_{AB}\,\|\,\rho_A\otimes\rho_B\right),
\]
so it measures distinguishability between the joint state and the uncorrelated product of marginals. citeturn1search7turn1search13turn1search38

Your “maximally mixed channel” is canonically modeled by the **depolarizing channel**. For a qubit,
\[
\mathcal D_p(\rho)=(1-p)\rho + p\,\mathrm{Tr}(\rho)\,\frac{\mathbf 1}{2},
\]
equivalently a uniform mixture over Pauli errors. citeturn7search0turn7search5  This captures your “drive to maximal entropy” intuition: as \(p\to 1\), outputs approach \(\mathbf 1/2\) regardless of input.

For *continuous time*, a standard modeling move is to treat depolarization as a Markovian semigroup with a decay rate that maps to an effective \(p(t)\) such as \(p(t)=1-e^{-\Gamma t}\) (up to conventions). This is common in open-system parameterizations that relate noise strength to exposure time. citeturn9search0turn9search1

Finally, “continuous-time CPTP evolution” is naturally expressed by a GKLS/Lindblad master equation generator (the general form of generators producing CPTP semigroups). citeturn2search0turn3search7turn4search4

## A bipartite QIT Hamiltonian that binds galaxies using mutual information

### Galaxy-as-subsystem model and bipartite graph

Let there be \(N\) “galaxies,” each represented as a \(d\)-dimensional quantum subsystem with Hilbert space \(\mathcal H_i\simeq \mathbb C^d\), total space \(\mathcal H=\bigotimes_{i=1}^N \mathcal H_i\). Define a **bipartite interaction graph** \(G=(V,E)\), \(V=\{1,\dots,N\}\), with a partition \(V=V_L\cup V_R\) and edges only across the cut: \(E\subseteq V_L\times V_R\).

A correlation graph in your sense is then induced from the evolving state \(\rho(t)\) by edge weights
\[
w_{ij}(t) \;\equiv\; I(i\!:\!j)_{\rho(t)} \quad\text{for }(i,j)\in E
\]
(and optionally for all pairs if you want emergent edges).

### Constructive Hamiltonian: entanglement-favoring edge terms

A simple, explicit bipartite Hamiltonian that “wants” to create/maintain correlations across edges is a sum of two-body entangling terms. Two useful constructions are:

**Projector-to-maximally-entangled edge binding (qudits).**  
Let \(|\Phi_d\rangle=\frac{1}{\sqrt d}\sum_{k=0}^{d-1}|k\rangle|k\rangle\) and \(\Pi_{ij}^{(\Phi)}=|\Phi_d\rangle\langle\Phi_d|\) on \(\mathcal H_i\otimes\mathcal H_j\). Define
\[
H_{\mathrm{DM}} \;=\; -J \sum_{(i,j)\in E} \Pi_{ij}^{(\Phi)}.
\]
Intuition: when an edge pair \((i,j)\) is driven toward \(|\Phi_d\rangle\), the pair becomes maximally entangled (pure), with \(S(\rho_i)=S(\rho_j)=\log d\) and \(S(\rho_{ij})=0\), hence \(I(i\!:\!j)=2\log d\) (maximal). This links “edge energy minimization” with “mutual-information maximization.” citeturn1search7turn1search13

**Heisenberg/Pauli edge binding (qubits, \(d=2\)).**  
On qubits, a standard entangling interaction on a bipartite graph is
\[
H_{\mathrm{DM}} \;=\; J\sum_{(i,j)\in E}\bigl(X_iX_j+Y_iY_j+Z_iZ_j\bigr),
\]
which creates strong two-site correlations and, on bipartite lattices, supports antiferromagnetic entanglement patterns. The essential point for Codex-Ratchet is not the condensed-matter phase details, but that this is a **local, bipartite, correlation-generating Hamiltonian**: it supplies the “negentropic anchor” that continuously rebuilds correlations that noise tries to erase.

### Codex-Ratchet “entropic Hamiltonian” variant (state-dependent operator)

If you want the operator to be *literally proportional to mutual information*, you can define an **effective entropic Hamiltonian functional** (state-dependent, hence not a standard physical Hamiltonian):
\[
\mathcal H_{\mathrm{MI}}[\rho] \;\equiv\; -J\sum_{(i,j)\in E} I(i\!:\!j)_\rho,
\]
where \(I(i:j)_\rho\) is computed from reduced states \(\rho_i,\rho_j,\rho_{ij}\). This is “entropic” because it is written directly in terms of von Neumann entropies (or relative entropies). citeturn1search7turn1search13

This is the cleanest way to match your statement “DM is not particles but an entropic operator holding correlation graphs together”: the binding energy is literally \(-J\times\) (correlation).

## Continuous global depolarizing noise channel as “Dark Energy”

### Discrete-to-continuous depolarization and CPTP structure

For a single qubit (or qudit), depolarization is a CPTP map that mixes input toward maximally mixed state. citeturn7search0  In a continuous-time exposure model, noise strength is often parameterized as a monotone of time, e.g., \(p(t)=1-e^{-\Gamma t}\) (convention-dependent), linking your “continuous global depolarizing” to a semigroup. citeturn9search0turn9search1

For an \(N\)-galaxy universe, “global” can mean either:

1) **Fully global depolarization** on \(\mathcal H\): \(\rho\mapsto (1-p)\rho + p\,\mathbf 1/d^N\).  
2) **Global coverage of local depolarization**: apply independent depolarization to every galaxy, \(\rho\mapsto (\mathcal D_{p})^{\otimes N}(\rho)\).

In practice (and for the “local survive / global tear at large \(N\)” effect you want), option (2) is the more structurally meaningful: it damps higher-body correlations faster than low-body ones, producing a natural scale separation. citeturn9search10turn8search16

### Continuous-time generator (GKLS/Lindblad form)

A standard mathematically controlled way to express “continuous global noise” is via a GKLS/Lindblad generator \(\mathcal L\) yielding a CPTP semigroup \(e^{t\mathcal L}\). The canonical GKLS form was established in foundational work on completely positive dynamical semigroups (GKS and Lindblad). citeturn2search0turn3search7

A convenient “local depolarizing across all galaxies” generator is:
\[
\frac{d\rho}{dt}
\;=\;
-i[H_{\mathrm{DM}},\rho]
\;+\;
\gamma_{\mathrm{DE}} \sum_{i=1}^N \left(\frac{\mathbf 1_i}{d}\otimes \mathrm{Tr}_i(\rho)\;-\;\rho\right).
\]
Each summand is a local “replace subsystem \(i\) by maximally mixed and keep the rest” contraction; the full sum is “global” because it acts everywhere, continuously.

For qubits, an equivalent GKLS representation is a Pauli-jump Lindbladian (a continuous-time Pauli/depolarizing semigroup viewpoint), connecting to the “Pauli semigroup” literature. citeturn7search1turn7search2

## Critical tuning where local structure survives but global structure tears at large N

### Why “large N tearing” is natural under depolarizing noise

Under independent local noise, **multipartite/global correlations decay increasingly fast with system size**, because “global structure” typically lives in high-weight operator components (many-body coherences). This shows up concretely in analyses of multiqubit disentanglement under local depolarizing channels. citeturn9search10

A second, complementary mechanism is **finite-speed correlation propagation** under local Hamiltonians: Lieb–Robinson-type bounds imply an effective “light cone” for information/correlation growth with a velocity scale that depends on interaction strengths. citeturn8search2turn8search17  If correlations can only spread out to distance \(\sim v_{\mathrm{LR}}t\) by time \(t\), while depolarizing noise is steadily damping correlations, then there is generically a finite effective correlation length. Past that length, mutual information edges fall below threshold, and the correlation graph fractures.

### A usable tuning parameter and an operational “phase boundary”

Let:

- \(J\) be the DM anchoring strength (Hamiltonian coupling).
- \(\gamma_{\mathrm{DE}}\) be the DE depolarization rate.
- \(G\) be the base bipartite interaction graph with diameter \(\mathrm{diam}(G)\).

Define a dimensionless “Codex-Ratchet cosmology control knob”:
\[
\kappa \;\equiv\; \frac{J}{\gamma_{\mathrm{DE}}}.
\]

Then define two operational structure metrics (these are what you can *actually verify*):

**Local survival metric (edge coherence).**  
Fix a correlation threshold \(I_\mathrm{min}\) and a time horizon \(T\). Define
\[
S_{\mathrm{local}}(\kappa,N)\equiv \frac{1}{|E|}\sum_{(i,j)\in E}\mathbf 1\!\left[I(i\!:\!j)_{\rho(T)} \ge I_\mathrm{min}\right].
\]

**Global integrity metric (giant component / spanning structure).**  
Build a thresholded correlation graph \(G_T\) on nodes \(V\) with an edge \((i,j)\) if \(I(i\!:\!j)_{\rho(T)} \ge I_\mathrm{min}\). Let
\[
S_{\mathrm{global}}(\kappa,N)\equiv \frac{|C_{\max}(G_T)|}{|V|},
\]
the fraction of nodes in the largest connected component.

Now the “cosmology-like regime” you asked for is exactly:
- \(S_{\mathrm{local}}(\kappa,N)\) stays high (galaxies stay bound locally),
- while \(S_{\mathrm{global}}(\kappa,N)\) collapses for large \(N\) (global structure tears).

This is the QIT analog of “bound structures resist expansion while the universe accelerates apart.”

A practical verification goal is to find, for each \(N\), the **critical window**
\[
\kappa_{\mathrm{local}} \;<\; \kappa \;<\; \kappa_{\mathrm{global}}(N),
\]
where:
- \(\kappa_{\mathrm{local}}\) is the smallest value giving stable local edges (roughly \(J \gtrsim \gamma_{\mathrm{DE}}\) in a broad-class sense), and
- \(\kappa_{\mathrm{global}}(N)\) grows with \(N\), because sustaining system-spanning correlations requires outpacing both (i) many-body decoherence scaling, and (ii) finite propagation speed. citeturn9search10turn8search2

### How this matches existing Codex-Ratchet simulation idioms

Your Codex-Ratchet repo already contains simulation idioms that mirror this structure: (a) explicit depolarizing-style mixing toward \(I/d\) to represent environmental scrambling, and (b) explicit tuning sweeps over a “gamma” dissipation strength to identify threshold behavior. fileciteturn42file0 fileciteturn41file0

That makes \(\kappa=J/\gamma\) not only physically motivated in QIT terms, but also implementation-aligned with how your existing probes already frame “scrambling rate vs condensation rate.”

## YAML problem_spec for the critical tuning verification

The “problem_spec.yaml” format used in your connected repos is a top-level `problem:` mapping with `statement`, `for_whom`, `constraints`, `success_criteria`, and `scope.{in,out}`. fileciteturn31file0 fileciteturn43file1

Your last instruction asked me to commit `problem_spec.yaml` directly into your repo. The GitHub connector exposed in this environment appears to provide read-only access (search/fetch) and does not provide a file-write/commit primitive, so I cannot push a commit from here. I’m therefore including the exact YAML body below so you can paste it into `system_v4/research/problem_specs/problem_spec.yaml`.

```yaml
problem:
  statement: >
    Construct and verify a Codex-Ratchet cosmology analog in quantum information theory (QIT)
    where “Dark Matter” and “Dark Energy” are not particles but entropic operators acting on
    a correlation graph of subsystems (“galaxies”).

    Model:
      - Galaxies: N local quantum subsystems {H_i}_{i=1..N}, dim(H_i)=d, total H = ⊗_i H_i.
      - Bipartite interaction graph: G=(V,E), V={1..N}, V=V_L ∪ V_R, E ⊆ V_L×V_R.
      - Dark Matter substitute (negentropic anchor): a bipartite QIT Hamiltonian H_DM that binds
        subsystems by generating/maintaining mutual information along edges E.
          Recommended explicit form (qudits):
            H_DM = -J * Σ_{(i,j)∈E} Π_{ij}^{Φ}
            where Π_{ij}^{Φ} = |Φ_d⟩⟨Φ_d| is the projector onto a maximally entangled qudit pair,
            |Φ_d⟩=(1/√d)Σ_k |k⟩|k⟩.
          (Alternative explicit form for qubits: Heisenberg edge coupling
            H_DM = J Σ_{(i,j)∈E} (X_iX_j + Y_iY_j + Z_iZ_j).)

        Binding observable:
          For each edge (i,j), define weight w_ij(t) = I(i:j)_{ρ(t)} where
          I(i:j) = S(ρ_i)+S(ρ_j)-S(ρ_ij) is quantum mutual information.

      - Dark Energy substitute (global entropy driver): a continuous global depolarizing CPTP channel
        acting on the whole universe, implemented as independent local depolarization on every galaxy:
          ρ(t) = (⊗_{i=1..N} D_{p(t)}^{(i)})[ρ(0)],
          D_p(σ) = (1-p)σ + p * Tr(σ) * I/d.
        Continuous-time parameterization:
          p(t) = 1 - exp(-γ_DE * t).

        Equivalent GKLS generator (preferred for “continuous”):
          dρ/dt = -i[H_DM, ρ] + γ_DE * Σ_{i=1..N} ( (I_i/d) ⊗ Tr_i(ρ) - ρ ).

    Objective:
      Identify the critical tuning regime in the control knob κ = J/γ_DE where:
        (a) local structure survives (edge mutual information remains above threshold on most edges),
        but (b) global structure tears at large N (correlation graph loses system-spanning connectivity).

  for_whom: >
    Codex-Ratchet researchers building “entropic cosmology” operators and validating
    scale-dependent structure vs global depolarizing expansion.

  constraints:
    - >
      MUST use a bipartite interaction graph (V_L ∪ V_R with edges only across the cut).
    - >
      MUST define “structure” operationally using quantum mutual information and a thresholded
      correlation graph constructed from I(i:j) values.
    - >
      MUST implement Dark Energy as a continuous depolarizing CPTP channel (either by GKLS generator
      or an equivalent p(t)=1-exp(-γ_DE t) semigroup); no discrete-only hacks.
    - >
      MUST sweep N (system size) and κ=J/γ_DE to demonstrate the large-N tearing effect.
    - >
      MUST report results at a fixed evaluation horizon T_eval and fixed mutual-information threshold I_min
      (both declared explicitly to avoid post-hoc tuning).

  success_criteria:
    - >
      Provide a reproducible definition of two metrics:
        Local survival: S_local = (1/|E|) Σ_{(i,j)∈E} 1[ I(i:j)_{ρ(T_eval)} ≥ I_min ].
        Global integrity: S_global = |C_max(G_T)|/N where G_T has edges if I(i:j)≥I_min.
    - >
      Empirically determine κ_local (the smallest κ where S_local ≥ 0.8 for all tested N up to N_max/4).
    - >
      Empirically determine κ_global(N) (the κ where S_global first reaches ≥ 0.8 for a given N),
      and show κ_global(N) increases with N (finite-size scaling evidence).
    - >
      Demonstrate a non-empty “cosmology window” for some large N:
        κ_local < κ < κ_global(N) where S_local ≥ 0.8 but S_global ≤ 0.3.
    - >
      Output the critical boundary as artifacts:
        - A table of (N, κ_global(N)) and (N, κ_local proxy) for the sweep range.
        - A short narrative interpretation connecting κ scaling to “local bound vs global expansion.”

  scope:
    in:
      - "Bipartite QIT Hamiltonian construction (explicit operators + parameters)."
      - "Continuous depolarizing CPTP channel (GKLS form or equivalent semigroup)."
      - "Mutual-information-based correlation graph definition and metrics."
      - "Large-N scaling sweep to locate κ-window where local survives but global tears."
      - "Clear declaration of thresholds: I_min, T_eval, and pass/fail cutoffs for S_local/S_global."
    out:
      - "Claims about the true physical ontology of cosmological dark matter / dark energy."
      - "Experimental particle-physics dark matter candidate evaluation."
      - "Non-Markovian noise models (unless explicitly added in a later spec)."
      - "Cosmological parameter fitting to real survey data."
```