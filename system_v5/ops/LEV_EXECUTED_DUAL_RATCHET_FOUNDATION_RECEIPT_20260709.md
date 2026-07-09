# Lev-Executed Dual-Ratchet Foundation Receipt

**Date:** 2026-07-09  
**Executor:** Leviathan `lev exec`  
**Lev source:** clean temporary checkout of `origin/main` at `6bcb9974e`  
**Lev receipt:** `rcpt-be10515fab7be705`  
**Lev execution:** `2979679a8b8e`  
**Classification:** local rerun receipt; not canonical admission

## Commands

Lev's Claude-backed executor ran the foundation lane against the live
Codex-Ratchet source:

```text
python3 manifold_dual_ratchet_foundations_v0_numpy.py       exit 0
julia manifold_dual_ratchet_foundations_v0_julia.jl         exit 0
python3 check_agreement.py                                  exit 0
```

Julia was version `1.12.6`. No wiki or Desktop file was written by the Lev
executor. The declared result files were regenerated in:

`system_v7/sims/manifold_dual_ratchet_foundations_v0/results/`

## Measured Results

| Metric | E_then_G | G_then_E |
|---|---:|---:|
| final quotient classes | 42 | 42 |
| permanent Hell rejects | 39 | 39 |
| active Purgatory | 957 | 957 |
| Purgatory -> admitted | 5 | 5 |
| Purgatory -> Hell | 37 | 37 |
| late regions | 11 | 11 |
| narrow-control classes/regions | 33/5 | 33/5 |
| measured Hell re-entry | 0 | 0 |

SMT controls passed in both orders: the Hell monotonicity statements were
`unsat` with the axioms and `sat` when the axioms were erased. NumPy/Julia
parity passed at `1e-9` for class counts, entropy tables, metric spectra, tier
counts, flux totals, binding order, and narrow-control deltas.

The fresh Julia result files use a smaller current schema than the older
checked-in receipt. The older metadata-rich fields are not reconstructed by
this runner; this is recorded as output-schema drift, not as a claim that
those fields were revalidated.

The order is load-bearing in the bounded run: the inhomogeneity binding point
is step 6 for `E_then_G` and step 4 for `G_then_E`, even though the final class,
Purgatory, and region counts agree.

## Claim Ceiling

This is a real dual-ratchet foundation computation and a valid Lev execution
receipt. It does not prove the QIT engine architecture, Axis0, perception,
four substages, or exceptional entropy. The result itself remains the
foundation diagnostic's declared `scratch_diagnostic` / exploratory ceiling.

The next engine experiment must use this foundation as a candidate-survivor
source: geometry and entropy must independently emit the same four minimal
substage classes before any 16 x 4 engine schedule is admitted.
