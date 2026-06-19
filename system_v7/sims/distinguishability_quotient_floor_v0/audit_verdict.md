# Audit verdict — distinguishability_quotient_floor_v0

**Classification:** `scratch_diagnostic`
**promotion_allowed:** `false`
**formal_admission_allowed:** `false`
**does_not_self_upgrade:** this verdict is the build's own self-assessment; a builder's
verdict on its own work is not evidence. A fresh-context audit is required before any
citation. Nothing here promotes itself to a higher status by being written.

**Status ladder reached:** `passes local rerun` (the three legs + the agreement check
ran fresh to exit 0 this session). NOT `canonical by process`.

---

## What this sim is

The smallest genuinely-legit pure-math foundation rung for the probe-relative quotient.

- **Finite set S** of four single-qubit density matrices, each `rho = (I + r.sigma)/2`
  for an exact-rational Bloch vector `r` (see `spec.json`). All four are verified PSD,
  Hermitian, trace-1.
- **Probe family M** = `{X, Y, Z}` Pauli expectations. Indistinguishability:
  `rho_a ~_M rho_b  iff  tr(rho_a P) == tr(rho_b P)` for every `P in M`.
- **Quotient S/~_M** computed independently by each leg.

## The measured result (three legs agree)

| Probe family | Quotient classes | Count |
|---|---|---|
| Full `M = {X, Y, Z}` | `{s0}, {s1}, {s2}, {s3}` | 4 |
| Erased `M = {X, Y}` (Z removed) | `{s0}, {s1, s2}, {s3}` | 3 |

`s1` and `s2` share `(<X>, <Y>) = (1/2, 0)` but differ in `<Z>` (`+3/10` vs `-3/10`).
They are **distinguishable** under full M (Z separates them) and **indistinguishable**
under erased M (the merge of `{s1, s2}` is the flip).

## The load-bearing evidence (NOT a count tautology)

The decisive evidence is a real-vs-erased **structural flip** in two SMT solvers, asked
of the flip pair `(s1, s2)`:

> *Does an active probe in M separate s1 and s2?* — encoded as a DISJUNCTION over the
> active probes of `(exact_expectation_a != exact_expectation_b)`, arithmetic over the
> exact rational expectation values.

| Solver | Full `M={X,Y,Z}` | Erased `M={X,Y}` |
|---|---|---|
| z3 | **SAT** (Z separates) | **UNSAT** (no separating probe) |
| cvc5 | **SAT** | **UNSAT** |

This is **not** `solver.add(n == count)`: the assertion is over the actual expectation
values, and the verdict FLIPS when one probe is erased from M. Erasing Z removes the only
formula that could discharge the disjunction, so the existence-of-separating-probe query
becomes UNSAT. That flip is what makes the SMT load-bearing rather than decorative.

## Three engines that genuinely differ

| Leg | Signature computation (unique to it) | Confirms |
|---|---|---|
| Julia | exact Hermitian eigendecomposition (`eigen(Hermitian(rho))`) -> eigenvalues + von Neumann entropy | invariant + entropy |
| JAX | `vmap` batched expectation MATRIX `tr(rho[i] P[j])` in one pass | invariant + SMT flip |
| PyTorch | `torch.autograd.grad` Jacobian `d<P>/d r` -> identity selection `delta_{P,Q}` | invariant + linearity identity |

No leg reads another leg's result (`reads_peer_result: false` in all three); there is no
shared `build_packet` doing the work. The only shared input is `spec.json`, which is pure
DATA (state coordinates + probe identities), not a precomputed invariant. The agreement
on the quotient (4 classes full / 3 erased), expectations equal to 1e-9, is therefore
genuine cross-engine corroboration, not an echo.

## A sharp side-finding (entropy is not the organizing variable)

`s1` and `s2` have IDENTICAL eigenvalues `{0.2085, 0.7915}` and identical von Neumann
entropy `0.5119` (they are related by `Z -> -Z`, a unitary). Yet they are a distinct
pair of classes under full M and merge only when Z is erased. So the class membership is
fixed by the **probe family**, not by the entropy: two states with the same entropy can
be distinguishable, and erasing a probe can merge them. Distinguishability is prior to
the entropy summary.

## Lineage

- **F01** (simultaneous-distinguishability surface): the probe family acts on the finite
  set jointly; `~_M` is the joint kernel of the probe expectations.
- **N01** (order/persistence): exercised only as a fixed-set read here; this rung makes
  **no** order-gap claim. It is the F01 surface alone.
- **Root axiom** `a = a iff a ~ b`: identity here is the class `S/~_M`, probe-relative.

## Honest limits / what would flip the verdict

- This is `scratch_diagnostic`. It does NOT establish a substrate, geometry, coupling,
  bridge, axis, or any nonclassical admission. It is a foundation-rung floor: a finite
  set, a probe quotient, and a real-vs-erased SMT flip.
- The "agreement" claim is exactness-class stability of the quotient and 1e-9 agreement
  of expectations — NOT byte-identical result files (the legs record different fields).
- If a fresh audit finds the two solvers share a hidden encoding path, or that `spec.json`
  smuggles a precomputed answer, or that any leg silently reads a peer, the load-bearing
  claim is withdrawn. As built, none of those hold.

## Reproduce

```
julia distinguishability_quotient_floor_v0_julia.jl
<sim-stack python> distinguishability_quotient_floor_v0_jax.py
<sim-stack python> distinguishability_quotient_floor_v0_pytorch.py
<sim-stack python> check_agreement.py   # exit 0 iff all three agree
```
