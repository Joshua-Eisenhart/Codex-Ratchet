# Verification Receipt

**Build:** `CONSTRAINTBOX_COMPLETE_STANDALONE_20260725_v2`
**Date:** 2026-07-25
**Disposition:** bounded local packaging checks passed
**Promotion:** `false`

## Executed checks

| Check | Result |
|---|---|
| Python source compilation | passed |
| Unit and hostile tests | 40 passed, 0 failed |
| Python wheel build and isolated target install | passed |
| Wheel artifact | `constraintbox-0.2.0-py3-none-any.whl`, SHA-256 `1e8bc638778f60691bab94203365ffd0b15021bdac1f3ba3ecf8849f384dbde2` |
| Core demo | passed |
| Finite SAT example | `BOUNDED_SAT` with witness |
| Finite UNSAT example | `BOUNDED_UNSAT` |
| JSON parsing | 10 files parsed |
| E0 constraint estate | `READY`; NumPy, SciPy, Z3, cvc5 and TLA+ exercised |
| E1 manifold estate | `READY`; JAX x64, Diffrax, quimb and cotengra exercised |
| E2 science estate | `READY`; PySINDy, PyDMD and pymdp exercised |
| Cross-estate parity | `READY`; NumPy/JAX/quimb agreed on F1 |
| TLA+ model checking | passed 45-state controller model and mutation control |
| E3 cloud estate | local negative: failed closed without NVIDIA/CUDA |
| Full CR integration | not run |
| Full 16-stage CR Sim Fleet integration | not run |
| LevOS bridge | not run |

## Interpretation

These checks show that the packaged core runs, its current tests pass, and
optional dependency absence is visible. They do not certify scientific claims,
prove security against a privileged hostile user, validate the proposed
manifold, or demonstrate the full simulation estate.

Machine-generated environment, inventory, and digest files accompany this
receipt.
