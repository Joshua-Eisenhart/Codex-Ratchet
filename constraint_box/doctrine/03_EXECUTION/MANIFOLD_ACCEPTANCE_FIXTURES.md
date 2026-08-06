# Manifold Acceptance Fixtures

These fixtures exercise proposed layers without declaring the layer ordering
settled.

| Fixture | Formal object | Required observations | Eligible tools |
|---|---|---|---|
| `F0 finite-history` | finite compatible-history set and projection fibres | support count, fibre sizes, Hartley capacity | Python, Z3, cvc5 |
| `F1 density-stratum` | positive trace-one matrix in a fixed finite dimension | spectrum, rank, Rényi-0, von Neumann entropy | NumPy, JAX, Julia, Torch |
| `F2 channel-order` | two finite CPTP maps in both orders | trace/positivity residuals and noncommutation witness | SciPy, JAX, Julia, Torch |
| `F3 history-pair` | finite complex amplitude vector and outer-product field | diagonal probabilities and retained off-diagonals | NumPy, JAX, Julia |
| `F4 extension-fibre` | projection of a finite total history space | exact fibre count and `log2` capacity | Python, SMT, tensor network |
| `F5 tensor-factor` | declared small factor graph | exact contraction versus enumeration | quimb, cotengra, JAX |
| `F6 known-flow` | `dx/dt=-2x` and a wrong rival | held-out residual and fixed feature library | Diffrax, PySINDy |
| `F7 known-rate` | `x[k+1]=0.5x[k]` and wrong claimed rate | recovered mode and held-out error | PyDMD, PyKoopman |
| `F8 finite-FEP` | declared finite MDP with fixed matrices and observations | posterior normalization, action distribution, free-energy telemetry | pymdp, NumPy/JAX oracle |
| `F9 CPU-GPU parity` | byte-identical `F1`–`F3` input | tolerance-bound observable parity and device evidence | JAX CPU/CUDA, Torch CPU/CUDA |

## What these fixtures do not establish

- `F1` does not force density matrices as the unique carrier.
- `F2` does not establish the proposed 16-stage engine schedule.
- `F5` does not prove a global factorization theorem.
- `F6` and `F7` do not let a library select its own hypothesis space.
- `F8` tests one finite active-inference implementation, not the FEP as a root
  law.
- `F9` tests a bounded numerical contract, not unrestricted GPU equivalence.
