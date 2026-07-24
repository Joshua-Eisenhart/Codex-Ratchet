# N=3 Whole-State Ratchet Calibration

This is a bounded, repository-independent execution slice. It uses exactly
three qubits, (S,E_1,E_2), so every whole state is an (8\times8) density
matrix. It does **not** claim to simulate the full proposed physical manifold
or prove an absolute minimal sufficient structure.

## What is actually executed

- One shared whole state plus explicit diagram ID and finite \(\mathbb Z_5\)
  boundary cochain.
- Two engine types, each with four outer and four inner stages (16 placements
  total). Each placement has four candidate maps
  \(\{D_z,D_x,U_x,U_z\}\).
- Four distinct ordered hypotheses:
  - `H_native`: the specified native operator at each placement;
  - `H_select`: a stated, demand-specific adaptive choice at each placement;
  - `H_all4`: all four local maps composed in a fixed order;
  - `H_mix`: the convex mixture of the four local maps.
- A fifth coherent-history **control** with class operator
  \(C_b=\prod_k(U_{x,k}+e^{i\phi_k}U_{z,k})/2\). It is postselected and
  non-trace-preserving, so it is not substituted for the ordered engines and
  does not receive licensed Spohn telemetry.
- Explicit projective instruments
  \(\mathcal I_z(\rho)=P_z\rho P_z\), their record probabilities and
  completeness checks.
- Exact whole-witness marginal validation. The supplied \(\rho_{SE_1E_2}\)
  must be positive, trace one, and reproduce every declared restriction. This
  does not make the false claim that pairwise consistency alone guarantees a
  global quantum state.
- Finite survivor extension fibres only:
  \[
  \mathcal F^X_{A/B}(\rho_B)=
  \{\rho_A\in X_A^t:d_1(C_{AB}\rho_A,\rho_B)\le\epsilon\}.
  \]
  Their finite Hartley count and a greedy trace-distance \(\epsilon\)-cover are
  both reported. No cardinality is assigned to a continuum of density matrices.
- SBS diagnostics, kept as diagnostics rather than an object theorem:
  system dephasing distance, conditional fragment root fidelities, binary
  Helstrom guessing probabilities, and
  \(I(E_1:E_2\mid S)\).
- Three SBS falsification controls are preregistered and executed: complete
  environmental-record erasure must reduce guessing to the prior-only Bayes
  rate (chance only for balanced priors) and raise
  conditional-record fidelity; erasing only \(E_2\) must expose a false
  single-fragment broadcast; and pointer-basis phase scrambling must drive the
  system dephasing residual to zero.
- Licensed discrete entropy-production and DPI telemetry. All ordered scratch
  maps are unital CPTP, so \(\tau=I/8\) is invariant and
  \[
  \Sigma_\tau(\rho;\Phi)=D(\rho\Vert\tau)-D(\Phi\rho\Vert\tau)\ge0.
  \]
- A typed Pareto frontier with explicit directions. Incomparable candidates
  survive. The identity/default whole state remains runnable even if dominated.
- A topology failure control and an actual renesting proposal. A torn triangle
  has obstruction
  \(o=a_{01}+a_{12}-a_{02}\pmod 5\neq0\). The proposal removes the incompatible
  cycle edge, pays a structural charge, and the *whole candidate* is settled
  again. All older candidates are also recomputed in iteration 1.
- A boundary-compression falsifier uses \(\lvert GHZ_+\rangle\) and
  \(\lvert GHZ_-\rangle\). They have the same finite cochain and identical
  proper one-/two-body marginals, but
  \(\langle X\otimes X\otimes X\rangle=+1\) versus \(-1\). Consequently the
  measured interior-sensitive distortion is \(\epsilon_\Pi=2\): boundary data
  is sufficient only relative to an explicitly declared probe family.
- All 16 stage deletions, four loop deletions, an order-reversal control,
  `H_all4` versus `H_mix`, and a falsified declared-marginal control.

## Run

```bash
python run_sim.py
python -m unittest -v test_sim.py
```

The runner writes `results/receipt.json` and exits nonzero if any advertised
control fails.

## Claim ceiling

This establishes only that the listed finite mechanisms can coexist and be
executed on one small whole-state carrier. The stage channels and demand
directions are authored calibration choices. It does not derive the 16-stage
chart, Hopf/Weyl geometry, gravity, cosmology, G2/F4/E8, or an ontological object
criterion. It does not prove a universally minimal candidate. It creates a
reproducible finite comparison surface on which later candidates can be
ratcheted and re-offered.
