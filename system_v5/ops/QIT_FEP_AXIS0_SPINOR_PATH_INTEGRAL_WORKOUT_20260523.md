# QIT-FEP Axis0 Spinor Path-Integral Workout

Status: **formal-scout candidate, not canon**.

This packet translates the usable part of FEP into the current QIT manifold
without importing classical Markov-chain ontology as a primitive.

## 1. Carrier

The carrier is finite:

```text
H_A = C^2
H_B = C^2
rho_AB in D(H_A tensor H_B)
```

`A` is the engine-visible spinor state. `B` is a finite reference/cut system.
The cut is where Axis0 can read coherent information.

The model does not use a Cartesian center point. State is a density operator
and the runtime object is a finite path ensemble over admissible operator
histories.

## 2. Quantum Hidden Histories

Classical FEP often uses hidden states in a Markov chain. The QIT replacement
is a finite quantum instrument history.

For a finite stage family of instruments:

```text
I_t = {K_{t,a}}
sum_a K_{t,a}^dagger K_{t,a} = I
```

a hidden path is:

```text
h = (a_1, ..., a_T)
K_h = K_{T,a_T} ... K_{1,a_1}
```

The path family is finite. It is Feynman-like because the evidence is a sum
over histories, but it is not a continuum path integral.

## 3. Evidence And Posterior

For a full-rank positive effect `E_A`:

```text
Z_path =
  sum_h Tr[(E_A tensor I_B) (K_h tensor I_B) rho_AB (K_h^dagger tensor I_B)]
```

The unnormalized posterior cut state is:

```text
tau_AB =
  sum_h (sqrt(E_A) tensor I_B)
        (K_h tensor I_B) rho_AB (K_h^dagger tensor I_B)
        (sqrt(E_A) tensor I_B)
```

and:

```text
rho_AB|E = tau_AB / Tr(tau_AB)
```

## 4. QIT Variational Free Energy

The finite quantum free-energy functional is:

```text
F_Q(sigma_AB)
  = D(sigma_AB || tau_AB / Z_path) - log Z_path
```

where `D` is quantum relative entropy.

The posterior minimizes this by construction:

```text
min_sigma F_Q(sigma) = -log Z_path
```

This is an implementation consistency check, not by itself evidence that the
Axis0 candidate is correct.

## 5. Provisional Axis0 Candidate

The scout tests the aggregate:

```text
Phi_QFEP_provisional =
  log Z_path + I_c(A -> B)_{rho_AB|E}
```

with:

```text
I_c(A -> B) = S(rho_B) - S(rho_AB)
```

This is **not** admitted as final Axis0. It is a candidate because it combines:

- finite evidence over noncommuting engine histories;
- coherent-information cut readout;
- spinor/entanglement carrier information;
- no continuous gradient primitive;
- no classical hidden-state primitive.

The additive form is provisional. `log Z_path` and `I_c` remain separately
reported in the receipt.

## 6. Scout Receipt

Implemented:

```text
system_v5/ops/formal_scouts/sim_qit_fep_axis0_path_integral_spinor_probe.py
```

Result:

```text
system_v5/ops/formal_scouts/results/qit_fep_axis0_path_integral_spinor_probe_results.json
```

Fresh validation:

```text
all_pass = true
contract lint = 0 violations
numpy quarantine = no NumPy usage
formal scout fresh rerun validator = pass
git diff whitespace check = pass
```

## 7. Audit Plan

The scout is intentionally split into evidence, controls, and boundaries.
This prevents the finite path-sum identity from being mistaken for scientific
support.

```text
Evidence path:
  noncommuting order survives commuting controls
  entangled cut carries information lost by product control
  manifold coordinates change the candidate readout
  B-reference gauge does not change A-side evidence
  finite-capacity gate rejects over-budget rows
  parameter robustness preserves the order signal over a small grid

Correctness path:
  finite Kraus path sum equals the closed channel
  posterior minimizes the defined relative-entropy free-energy functional

Claim boundary:
  Phi_QFEP_provisional is an additive candidate only
  component ablation shows the aggregate is not unique on current fixtures
  z3 dependency fence is a declared nonpromotion guard, not a derivation
  Axis0 is not canonized
  FEP, Markov blankets, holography, and ER=EPR are not admitted
```

## 8. Load-Bearing Signals

### Noncommuting Order Signal

```text
noncommuting_order_gap = 0.02709174596856334
commuting_quantum_order_gap = 0.0
commuting_classical_order_gap = 0.0
```

The commuting quantum control matters: it separates "quantum" from
"noncommuting." The signal is specifically noncommuting order, not merely use
of Hilbert space.

Path-count scaling remains nonzero:

```text
path_count 4  -> gap 0.02709174596856334
path_count 8  -> gap 0.024895335308016797
path_count 16 -> gap 0.014230348602011
```

This is the path-integral substitute for a classical Markov chain. The hidden
object is a finite noncommuting Kraus history, not a classical state sequence.

### Entanglement Carrier Signal

```text
I_c gap, entangled vs product = 0.08597299491014523
Phi gap, entangled vs product = 0.04183211133489706
```

This supports the user's hypothesis that the information carrier is not a
classical point-state but a finite entangled spinor cut.

### B-Side Reference Gauge Control

The operations and effects act on `A`. Therefore a local unitary on `B` is a
reference-basis gauge change for the fixed cut and must not alter `A`-side
evidence.

```text
rho_A gap                  = 3.0411136596227075e-16
posterior rho_A gap        = 1.2566871346510768e-16
Z_path gap                 = 2.220446049250313e-16
log Z gap                  = 4.440892098500626e-16
I_c gap                    = 4.440892098500626e-16
Phi_QFEP_provisional gap   = 0.0
```

This is **not** a proof that every non-isometric extension of `rho_A` is
equivalent. The cut state is intentionally load-bearing. The control only
blocks spurious dependence on the arbitrary `B` basis for a fixed cut.

### Manifold Variance

Finite grid:

```text
flux in {-1, +1}
eta in {0.28, 0.52, 0.81}
chi in {-0.42, 0.0, 0.39}
```

Result:

```text
grid_size = 18
variance = 0.01477739658942105
flux_mean_gap = 0.16531492915707058
eta_span = 0.08451591404861725
```

This supports exploring Axis0 as a manifold-sensitive cut functional rather
than a single scalar projection.

### Commuting Manifold Flux Null

The same grid is also run with a commuting `Z`-only instrument/effect family.
That null preserves ordinary coordinate variance but erases flux-direction
sensitivity:

```text
noncommuting flux_mean_gap = 0.16531492915707058
commuting flux_mean_gap    = 0.0
commuting variance         = 0.0374651879534308
```

This matters because it separates "there is variance on the grid" from "the
engine sees flux direction through noncommuting dynamics." The current receipt
supports flux as a manifold/dynamics binding signal, not as an automatically
free per-stage axis.

### Component Decomposition

The additive scalar is kept provisional by reporting its pieces separately:

```text
order gaps:
  log_z                    = 0.023151225744149073
  coherent_information     = 0.015610894719935431
  mutual_information       = 0.010626726006251419
  Phi_QFEP_provisional     = 0.03876212046408445
  Phi_QFEP_mutual_info     = 0.012524499737897654

entanglement gaps:
  log_z                    = 0.05018844018447133
  coherent_information     = 0.1411986165439857
  Phi_QFEP_provisional     = 0.09101017635951436

commuting order gaps:
  log_z                    = 0.0
  coherent_information     = 3.608224830031759e-16
  Phi_QFEP_provisional     = 3.3306690738754696e-16
```

So the scout does not claim `log Z + I_c` is uniquely correct. It claims this
candidate has two separately visible pieces: evidence over noncommuting finite
histories and coherent-information cut content.

### Axis0 Component Ablation

The revised scout directly tests whether the aggregate has unique separating
power on the current fixtures. It does not.

```text
candidate              order_gap    entanglement_gap   commuting_gap
log_z_only             0.0231512    0.0501884          0.0
ic_only                0.0156109    0.1411986          3.61e-16
mi_only                0.0106267    0.2467349          3.89e-16
log_z + I_c            0.0387621    0.0910102          3.33e-16
log_z + I(A:B)         0.0125245    0.1965464          3.89e-16
```

All five pass the same first-order controls. This is an important negative
finding: `Phi_QFEP_provisional = log Z + I_c` is not uniquely supported by the
current scout. The next Axis0 work must compare candidate families on full
engine-chart rows and finite-capacity budgets.

### Parameter Robustness Sweep

The first implementation used fixed constants for effect bias, dephasing rate,
and amplitude-damping rate. The revised scout sweeps:

```text
effect_bias in {0.34, 0.48, 0.62}
q_dephase   in {0.06, 0.16, 0.28}
gamma       in {0.07, 0.13, 0.21}
grid_size   = 27
```

Result:

```text
min_order_gap  = 0.0010019519603086113
mean_order_gap = 0.037915135344573754
max_order_gap  = 0.07711372784194415
```

This hardens the noncommuting-order signal against one class of "magic
constant" criticism. The minimum is close to the threshold, so wider sweeps
remain useful and are required before promotion beyond formal scout.

## 9. What This Fixes

This avoids three failures in older FEP framing:

1. Classical Markov chains are no longer primitive. They become a commuting
   ablation.
2. Continuous gradient flow is not primitive. The scout uses finite Kraus
   histories.
3. A Cartesian hidden-state center is not primitive. The carrier is a density
   state on a finite spinor/cut system.

It also tightens the tensor question. Tensors remain allowed as implementation
arrays and as bounded computational tools. What is rejected is raw tensor-index
ontology as the substrate: it is gauge/relabel fragile and can erase cut
entanglement under truncation. The substrate candidate here is a spinor/cut
information network; arrays are the representation.

## 10. Axis0 Interpretation

There are now two distinct Axis0 layers:

```text
chart-level seat:
  b0 = sign(cos(2 eta)) = sign(r_z)

candidate bridge-level readout:
  b0_candidate = sign(Phi_QFEP_provisional)
  Phi_QFEP_provisional = log Z_path + I_c(A -> B)
```

The chart-level bit is a coordinate seat on the Hopf manifold. The bridge-level
candidate is an information readout over a cut posterior. They should not be
collapsed unless a later bridge `Xi : geometry/history -> rho_AB` proves the
identification.

This makes Axis0 less like a local label and more like an admissibility
polarity over finite information flow. That fits the Bekenstein-style derived
constraint: the model needs a finite amount of potential information available
to the finite engine, and Axis0 should read whether a cut history is viable
under that finite capacity.

### Executable Finite-Capacity Gate

The current scout does not compute a physical Bekenstein bound because it has
no radius/energy model. It does implement the derived constraint that matters
for this stage: finite carrier, finite path registry, and rejection of
over-budget rows.

```text
capacity_model      = finite_budget_gate_not_physical_bekenstein_calculation
max_boundary_dim    = 4
max_path_count      = 16
capacity_budget     = log(4) + log(16) = 4.1588830833596715 nats

observed carrier_dim = 4
observed path_counts = {4, 8, 16}
observed admitted    = true

negative: path_count 32 admitted? false
negative: boundary_dim 8 admitted? false
```

This turns "finite potential information" into an executable scout constraint.
The physical Bekenstein form can later replace the abstract budget once a
radius/energy boundary model exists.

## 11. Spinor / Twistor Network Direction

The current scout uses spinors directly. The next network layer should use:

```text
node i:
  spinor psi_i in C^2
  density rho_i = psi_i psi_i^dagger or mixed rho_i in D(C^2)

edge (i,j):
  entangled cut state rho_ij in D(C^2 tensor C^2)
  edge readouts: I_c(i -> j), I(i:j), negativity, path evidence Z_ij

twistor-style incidence candidate:
  I_ij = omega_i^A pi_{j,A}
  or finite two-spinor incidence classes over edge cuts
```

The twistor layer should not be admitted because the word is attractive. It
needs tests:

1. incidence readout survives spinor gauge but changes under real geometry;
2. it improves an Axis0 or flux prediction beyond pure SU(2) spinor transport;
3. it does not smuggle a Cartesian center or global total order back in;
4. it respects finite capacity and finite path count.

Clifford rotors remain a faithful SU(2) implementation check, not independent
evidence unless a multivector observable survives controls that pure SU(2)
does not.

## 12. Alternative Axis0 Families To Explore

The next smallest falsifiers are:

1. `Phi = I_c(A -> B)` alone;
2. `Phi = I(A:B)` alone;
3. `Phi = log Z_path` alone;
4. `Phi = log Z_path + alpha I_c` with fitted or bounded `alpha`;
5. `Phi = log Z_path + alpha I(A:B)`;
6. `Phi = -S(A|B)` or signed conditional entropy;
7. log-negativity or PPT witness for cut entanglement;
8. sandwiched Renyi or hypothesis-testing relative entropy;
9. weighted shell cuts `sum_r w_r I_c(A_r -> B_r)`;
10. process-tensor / quantum-comb FEP with finite memory cells;
11. finite cellular path lattice over `(eta, chi, flux, path_class)`;
12. integration with the full engine charts rather than the scout's bounded
   instrument family.

Each variant must face the same controls: commuting quantum, classical
commuting, product-state ablation, B-gauge invariance, path-count scaling, and
manifold null.

## 13. Premortem

Here is the premise: it is six months from now. The QIT-FEP Axis0 bridge
program failed. The most likely causes are:

1. The additive scalar `log Z + I_c` was promoted before a bridge `Xi` was
   proven.
2. The scout stayed on bounded toy instruments and never entered the full
   engine charts.
3. Twistor terminology became a decoration because no incidence observable
   beat the spinor/SU(2) baseline.
4. Tensor networks were rejected too broadly, confusing implementation tensors
   with tensor-index ontology.
5. Bekenstein capacity stayed a slogan instead of becoming an executable
   capacity gate on path count, Hilbert dimension, and boundary cuts.

The immediate repair plan is therefore:

1. keep `Phi_QFEP_provisional` noncanonical;
2. run the alternative Axis0 family batch;
3. move from the bounded instrument family into the engine chart rows;
4. add a finite capacity gate to every candidate;
5. require any twistor layer to beat spinor-only controls.

## 14. Current Verdict

The QIT-FEP path-integral spinor formulation is admissible as a
**formal-scout Axis0 candidate family**.

It is not final Axis0. It is a better basis than classical FEP/Markov chains
because its failures and controls are expressed directly in the root language:
finitude, noncommutation, finite capacity, spinor entanglement, and path-order
sensitivity.
