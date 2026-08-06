# Proposed simulation-estate tiers

These are dependency and acceptance tiers. They are not scientific layers,
engine stages, or levels of truth.

## Tier index

| Tier | Purpose | Required bounded capabilities | Optional or later capabilities | Expected host |
|---|---|---|---|---|
| S1 | lean instruments usable by ConstraintBox | stdlib finite carrier, NumPy density calculation, SciPy channel calculation, Z3 finite obligation | cvc5 reproduction, TLA+/TLC lifecycle model | local CPU |
| S2 | local manifold and engine workhorses | JAX x64 density calculation, Diffrax flow, Quimb tensor calculation, Cotengra path search | Julia independent reference | local CPU, isolated runtime |
| S3 | law, mode, and FEP proposal satellites | PySINDy law fixture, PyDMD rate fixture, pymdp FEP fixture | PyKoopman, CPU Torch, bounded annealing | local CPU, isolated runtime |
| S4 | cloud acceleration and parity | NVIDIA device plus one declared CUDA route | second GPU runtime, cuQuantum, Reactant.jl | pinned Linux/NVIDIA host |

## S1 — lean ClaimGate instruments

| Capability | Exact bounded job | Control | What a pass does not mean |
|---|---|---|---|
| `stdlib_finite` | count complete histories, projections, fibres, and \(H_0=\log_2|\mathcal H|\) | fixture mutation and replay | physical ontology is correct |
| `numpy_density` | eigenvalues, trace, rank, \(S_0\), \(S_1\), dephased entropy | dispatch, mutation, replay, NumPy severance | NumPy is a scientific authority |
| `scipy_channel` | compute a declared two-state matrix exponential | mutation, replay, SciPy severance | arbitrary open-system dynamics are validated |
| `z3_finite` | solve one finite SAT and one contradictory obligation | replay and Z3 severance | an unrestricted theorem is proved |
| `cvc5_finite` | independently solve the bounded solver fixture | replay and cvc5 severance | two encodings are semantically equivalent |
| `tla_controller` | model-check a bounded controller lifecycle | model mutation and replay | the Python implementation refines the model |

This is the only simulation tier imported into routine ConstraintBox use. It
is deliberately small.

## S2 — manifold and engine workhorses

| Capability | Exact bounded job | Native evidence | Main use |
|---|---|---|---|
| `jax_density` | x64 eigenspectrum and entropies for the common 2×2 fixture | actual JAX dispatch plus StableHLO digest | array workhorse and later GPU parity |
| `diffrax_flow` | integrate \(\dot x=ax\) and match \(x(T)=x_0e^{aT}\) | Diffrax solver dispatch | bounded flow and channel studies |
| `quimb_tensor` | independently compute the density fixture | Quimb dispatch | tensor-network candidate work |
| `cotengra_path` | find a nontrivial contraction path | contraction cost and maximum intermediate size | factorization and memory studies |
| `julia_density` | independent density reference | external acceptance profile | second-language witness |

S2 is not loaded for ordinary ClaimGate decisions. It boots only for claim
types whose applicability profile requires it.

## S3 — proposal satellites

| Capability | Exact bounded job | Controller restriction | Honest output |
|---|---|---|---|
| `pysindy_law` | recover \( \dot x=-2x \) using a predeclared degree-1 library | the claimant may not choose the feature library after seeing the data | candidate law plus residuals |
| `pydmd_rate` | recover a declared discrete multiplier | applies only to rate/spectrum claims | candidate eigenvalue |
| `pymdp_fep` | run one small state and policy inference fixture | applies only to declared FEP claims | normalized posteriors and finite objectives |
| `pykoopman_rate` | deferred rival for mode/rate work | must earn distinct coverage | currently untested |
| `torch_density` | deferred CPU rival | not required merely to add an engine count | currently optional |
| `dimod_anneal` | deferred bounded comparator | exact-small enumeration must precede it | currently untested |

PySINDy is a candidate compiler, not an axiom discoverer. Its feature library,
differentiation method, train/held-out split, residual decomposition, and
applicability must be controller-owned.

## S4 — cloud GPU

S4 requires an actual NVIDIA device and a declared route. Importability is not
enough. A useful receipt must include device identity, driver and runtime
versions, x64 policy, input and output hashes, seed where applicable, wall
time, and CPU/GPU parity for the same bounded observable.

The first cloud target should be a small parity fixture or a search whose
result is independently checkable. A GPU-only numeric assertion parks.

## Status vocabulary

| State | Meaning |
|---|---|
| `READY` | all required and optional registered capabilities passed |
| `DEGRADED` | every required capability passed; an optional capability did not |
| `UNAVAILABLE` | a required dependency or required route is absent |
| `DRIFT` | controller, worker, lock, version, or environment differs from the tested declaration |
| `FAILED` | a required bounded witness or control failed |
| `UNTESTED` | an acceptance profile has not been implemented |

`DEGRADED` is usable only when the major-run profile does not require the
missing optional capability.
