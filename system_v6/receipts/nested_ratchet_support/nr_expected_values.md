# Independent expected values: nested-ratchet L/R cut controls

Scope: independent derivation only. I did not read any parallel builder artifacts for this lane.

All entropies below use `log2`, so units are bits.

## 1. Two-qubit signed cut values

Definition:

`S(A|B)_rho = S(rho_AB) - S(rho_B)`.

### 1.1 Product state

For `rho_AB = rho_A tensor rho_B`,

`S(AB) = S(A) + S(B)`, hence

`S(A|B) = S(A)`.

Numbers:

- pure product `|00><00|`: `S(A|B) = 0`.
- maximally mixed product `I/2 tensor I/2`: `S(A|B) = 1`.
- any product two-qubit state: `S(A|B) in [0, 1]`.

### 1.2 Bell state

For `|Phi+> = (|00> + |11>)/sqrt(2)`,

- `rho_AB` is pure, so `S(AB) = 0`.
- `rho_B = I/2`, so `S(B) = 1`.

Therefore:

`S(A|B) = -1`.

This is the minimum possible two-qubit value.

### 1.3 Werner state

Convention:

`rho(p) = p |Phi+><Phi+| + (1-p) I/4`, with `p in [0,1]`.

The eigenvalues are:

- `lambda_1 = (1 + 3p)/4` on `|Phi+>`.
- `lambda_2 = lambda_3 = lambda_4 = (1 - p)/4`.

The marginal is always maximally mixed:

`rho_B = I/2`, hence `S(B) = 1`.

So

`S(A|B) = -lambda_1 log2(lambda_1) - 3 lambda_2 log2(lambda_2) - 1`.

The zero crossing solves:

`-((1+3p)/4) log2((1+3p)/4) - 3((1-p)/4) log2((1-p)/4) = 1`.

Numerical root:

`p_zero = 0.74761383344635764986347374217963434377737845087594`.

Check values:

- `p = 0`: `S(A|B) = +1`.
- `p = 1/3`: `S(A|B) = 0.792481250360578090726869471974`.
- `p = 1/2`: `S(A|B) = 0.548794940695398532581050356569`.
- `p = p_zero`: `S(A|B) = 0`.
- `p = 1`: `S(A|B) = -1`.

Important distinction: for this Werner convention, separability ends at `p <= 1/3`, but negative conditional entropy starts only at `p > 0.7476138334463576...`. So there is a large entangled-but-nonnegative interval.

## 2. General two-qubit bounds and separable-state sign

For two qubits, `dim(A)=dim(B)=2`.

Lower bound from Araki-Lieb:

`S(AB) >= |S(A)-S(B)|`, hence `S(AB)-S(B) >= -S(A) >= -1`.

Upper bound from subadditivity:

`S(AB) <= S(A)+S(B)`, hence `S(AB)-S(B) <= S(A) <= 1`.

Therefore:

`S(A|B) in [-1, +1]`.

Separable nonnegativity:

If `rho_AB = sum_i p_i sigma_A,i tensor tau_B,i`, each product component has

`S(A|B)_{sigma_i tensor tau_i} = S(sigma_A,i) >= 0`.

Quantum conditional entropy is concave, so

`S(A|B)_{sum_i p_i rho_i} >= sum_i p_i S(A|B)_{rho_i} >= 0`.

Thus every separable state must satisfy:

`S(A|B) >= 0`.

Citation anchors:

- Nielsen and Chuang derive conditional-entropy concavity from strong subadditivity.
- Preskill lecture/problem notes state the consequence directly for separable states: `H(A|B) = H(AB)-H(B) >= 0`.
- Sources checked: `https://www.preskill.caltech.edu/ph219/ph219-prob3-2016.pdf`, `https://en.wikipedia.org/wiki/Conditional_quantum_entropy`.

## 3. Order-gap expected values for noncommuting CPTP rung maps

Order gap:

`Delta_order(rho) = || Phi_a(Phi_b(rho)) - Phi_b(Phi_a(rho)) ||_1`.

For qubit states, if the difference matrix is `Delta = (1/2) d . sigma`, then `||Delta||_1 = |d|`.

### 3.1 Exact clean control: distinct-axis unitary rotations

Choose:

- `Phi_a(rho) = R_x(pi/2) rho R_x(pi/2)^dagger`.
- `Phi_b(rho) = R_z(pi/2) rho R_z(pi/2)^dagger`.
- probe `rho = |0><0|`.

These are CPTP maps and are the zero-dephasing limit of distinct-axis dephase/rotation rung maps.

The two output Bloch vectors are:

- `Phi_a(Phi_b(rho))`: `z -> -y`.
- `Phi_b(Phi_a(rho))`: `z -> +x`.

Their Bloch-vector difference has length:

`|(-y) - (+x)| = sqrt(2)`.

Therefore:

`Delta_order = sqrt(2) = 1.4142135623730950488...`.

Equivalent matrix difference:

```text
[[ 0,        -1/2 + i/2 ],
 [ -1/2-i/2,  0        ]]
```

with eigenvalues `+-1/sqrt(2)` and trace norm `sqrt(2)`.

### 3.2 Lossy dephase+rotate reference magnitude

Choose a concrete noisy pair:

- `Phi_a(rho) = R_z(pi/4) D_x(q=0.2)(rho) R_z(pi/4)^dagger`.
- `Phi_b(rho) = R_x(pi/3) D_z(q=0.3)(rho) R_x(pi/3)^dagger`.
- `D_axis(q)(rho) = (1-q) rho + q sigma_axis rho sigma_axis`.
- probe `|+y> = (|0> + i|1>)/sqrt(2)`.

Numerical result:

`Delta_order = 0.10443167194621705`.

Difference matrix:

```text
[[ 0.03043836, 0.04242641 ],
 [ 0.04242641,-0.03043836 ]]
```

eigenvalues:

`-0.05221583597310852`, `+0.05221583597310852`.

Interpretation: noisy dephase+rotate order gaps can be much smaller than the clean unitary `sqrt(2)` anchor, but a generic noncommuting pair should not return machine-zero. Machine-zero means either the maps commute on that probe, the probe is invariant/degenerate, or the implementation collapsed the order.

## 4. Decisive verifier sanity checks

### 4.1 Signed cut monotonicity / shape

For Werner controls under the convention above, `S(A|B)` should decrease from `+1` at `p=0` to `-1` at `p=1`, crossing zero exactly at:

`p = 0.7476138334463576...`.

It is not valid if the claimed crossing is near the separability threshold `p=1/3`; that confuses entanglement onset with negative conditional entropy onset.

Expected shape samples:

- `p=0`: `+1`.
- `p=1/3`: `+0.7924812503605781`.
- `p=1/2`: `+0.5487949406953985`.
- `p=0.7476138334463576`: `0`.
- `p=1`: `-1`.

### 4.2 Separable control hard floor

A separable control must never have:

`S(A|B) < 0`.

Any negative value for a separable control is a red failure unless the state is not actually separable, the entropy base is not `log2`, the subsystem trace is wrong, or the conditional entropy sign/order was reversed.

### 4.3 Two-qubit range hard bounds

Every two-qubit reported signed cut must satisfy:

`-1 <= S(A|B) <= +1`.

Values outside this interval indicate a normalization, trace, log-base, or eigenvalue bug.

### 4.4 Order-gap checks

Run both controls:

1. Commuting control: identical-axis dephasing maps or same-axis rotations should give `Delta_order = 0` up to numerical tolerance.
2. Noncommuting control: the clean `Rx(pi/2), Rz(pi/2), |0>` control must give `Delta_order = sqrt(2)`.
3. Noisy noncommuting control: a dephase+rotate pair should usually give a positive but smaller value, with exact size depending on dephasing strengths and probe.

A rung-stack implementation that always reports zero for noncommuting controls is probably applying the same map twice, sorting/composing maps in a canonical order, reusing the final state, or comparing a state to itself.

### 4.5 Decorative SMT vs derive-in-solver for commutation

Decorative SMT:

- Asserts a precomputed numeric commutator/order gap as a fact.
- Encodes `commutes = true/false` from Python output instead of deriving it.
- Uses uninterpreted functions for `Phi_a`, `Phi_b` and then asserts `Phi_a(Phi_b(rho)) != Phi_b(Phi_a(rho))`.
- Proves only that an already supplied label is satisfiable.

Derive-in-solver commutation check:

- Encodes the actual matrix/channel action, at least for the bounded finite case under test.
- Constructs both composed outputs inside the solver.
- Forms the symbolic/evaluable difference.
- Asks the solver to prove equality for all admitted probes, or produce a concrete counterexample probe for noncommutation.
- Emits the counterexample state and both ordered outputs when noncommutation is claimed.

For this build, a useful SMT/proof claim must derive the order distinction from the channel definitions. A solver wrapper around a Python-computed gap is only a receipt wrapper, not independent proof.
