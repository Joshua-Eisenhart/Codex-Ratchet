# engines/ — real-substrate engines and the cross-validation contract

Four independent numerical routes compute the same 16-stage contract; their
agreement is the validity mechanism (method-artifact exclusion), their
disagreement is a finding. Never widen a tolerance to make a substrate pass.

```
oracle_targets.py     numpy/scipy RK4 oracle  -> targets.json   (the contract)
jax_engine.py         JAX, exact superoperator expm, vmap+jit -> jax_results.json
torch_engine.py       PyTorch, batched matrix_exp (CPU/CUDA)  -> torch_results.json
julia_engine.jl       Julia, LinearAlgebra exp                -> julia_results.json
validate_engines.py   compares every *_results.json to targets; exit 0 = GREEN
```

Contract per stage (t0–t7 × 2 native operators): Bloch vectors of both N01
orders (terrain-first and operator-first), the order gap, plus per-terrain
non-unitality bit and fixed-point z. Derived invariants: 16 distinct stages,
16/16 positive order gaps, the 8/8 fusion split. Tolerances live in
`targets.json` and are part of the contract.

## Laptop setup (macOS)

```bash
cd <bundle>/engines
python3 -m venv .venv && source .venv/bin/activate
pip install numpy scipy "jax[cpu]" torch          # torch: CPU wheel is fine
python3 oracle_targets.py                          # writes targets.json
python3 jax_engine.py && python3 torch_engine.py
python3 validate_engines.py                        # expect GREEN
```

Julia (first run is the test — authored without a Julia runtime available):
```bash
julia -e 'using Pkg; Pkg.add("JSON")'
julia julia_engine.jl
python3 validate_engines.py                        # now validates 3 substrates
```

Verified in this sandbox: numpy oracle + JAX + PyTorch agree (GREEN) — RK4
integration vs two independent matrix-exponential implementations, matching to
1e-6 across all 16 stages. Julia is the remaining route; if it disagrees,
report the numbers rather than adjusting anything.

## Notes that will save you time

- **Float64 is mandatory.** `jax_engine.py` sets `jax_enable_x64` itself; if
  you refactor, keep it — JAX defaults to float32 and will fail the 1e-6
  contract by ~1e-4. Torch uses complex128 explicitly. On GPU, prefer CPU or
  float64-capable devices for the contract run; float32 GPU runs need the
  widened tolerance declared in `targets.json` (1e-3) and must say so.
- **The coherent axis is (1,1,1)/√3 and is load-bearing** (see
  `sims_and_scripts/axis_loadbearing_n01_sim.py`): on the z-axis convention the
  four Fe stages commute exactly with their terrains and 16/16 order
  sensitivity collapses to 12/16. Don't "simplify" H₀ to σz.
- **vec convention is column-stacking** (`vec(ρ) = ρ.T.reshape(4)` in
  numpy/torch, `reshape(transpose(ρ), 4)` in Julia). Mixing conventions
  produces transposed superoperators that still pass CPTP-looking sanity
  checks — the contract will catch it, but check this first if a substrate
  goes RED.
- **Regenerate `targets.json` only from `oracle_targets.py`**, never by hand;
  it is the single source of truth for model constants, and all engines read
  their constants from it (one place to change parameters).
- Scaling up (3-qubit / Cl(0,6) rung): the superoperator design generalizes —
  dims go 4→64, `expm` cost grows, JAX/torch batching becomes the point. The
  contract schema is dimension-agnostic except the Bloch readout, which should
  become a Pauli-basis expectation vector.


## 3-qubit lane (the owner's "at least 3 qubits" floor)

```
oracle_targets_3q.py     numpy RK4 oracle on C^8  -> targets_3q.json (63-dim Pauli contract)
jax_engine_3q.py         JAX exact 64x64 superoperator expm -> jax_results_3q.json
validate_engines_3q.py   compares *_results_3q.json to targets_3q.json; exit 0 = GREEN
```

The 3-qubit lift is GENUINELY multi-qubit, not the 1-qubit channel tensored with
identity: the coherent Hamiltonian carries a ZZ chain coupling (J_COUP), so the
evolution does not factorize. Verified: max negativity across q0|q1q2 is 0.038 > 0
(real entanglement), and all 16 stages stay distinct in the 63-dim Pauli-expectation
space (min pairwise 0.174). The readout is the 63-vector over non-identity 3-qubit
Pauli strings; the 8/8 non-unitality fusion split and 16/16 order gaps are preserved.
Verified in this sandbox: numpy RK4 oracle vs JAX exact-expm agree to ~1e-12 on all
16 stages in the full 63-dim space -- a two-method cross-check on C^8.


## Substrate status (verified in this sandbox)

Three independent numerical routes now confirmed at BOTH scales (1q and 3q):
  numpy RK4 oracle  vs  JAX exact-expm  vs  PyTorch matrix_exp
- 1-qubit: all three agree on the 16-stage Bloch contract.
- 3-qubit (C^8): all three agree to ~1e-12 across all 16 stages in the 63-dim
  Pauli-expectation space.
PyTorch runs clean here (torch 2.12.1, CPU, complex128) -- no Bus error.
Julia (julia_engine.jl / a 3q analogue) is the remaining 4th route; run it on
the laptop. If it disagrees, report the numbers, do not adjust tolerances.

## Does the engine process information?

`sims_and_scripts/info_processing_sim.py` answers yes, concretely: each stage is
applied as a quantum channel to a message qubit maximally entangled with a
reference, and the information metrics (output entropy, coherent information,
mutual information, and the full Choi process matrix) show all 16 stages doing
DISTINCT information work. See figures/info_processing.png.


## Julia — 4th substrate, now verified in-house (2026-07-02)

Julia 1.10.5 was installed in the sandbox and julia_engine.jl / julia_engine_3q.jl RAN
and validated against the numpy oracle: 1q min-dist 0.0276 (matches jax/torch), 3q worst
pvec dev 9.89e-13 on C^8. So ALL FOUR routes (numpy RK4 oracle, JAX exact-expm, PyTorch
matrix_exp, Julia stdlib exp) now agree at both scales.

FINDING (CLAUDE.md rule 1, worth keeping): the FIRST Julia run DISAGREED (1q min-dist
0.096). Cause: Julia is column-major, so the original `reshape(transpose(rho),4)` did not
reproduce numpy's column-stacking `vec(rho)=rho.T.reshape(4)`. Fixed to `reshape(rho,4)` /
`reshape(v,2,2)`. This is exactly the kind of cross-substrate convention bug the 4th route
exists to catch -- and it caught it before the laptop did.

The Julia engines are DEPENDENCY-FREE (hand-rolled JSON reader/writer, stdlib LinearAlgebra
only) -- they run on any Julia with no `] add`, no registry. Just `julia julia_engine.jl`.
