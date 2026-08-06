# Tools, Profiles, and Resource Policy

The core is zero-dependency Python.  Optional tools run only for matching task
profiles and preferably in separate processes.

| Tool | Role | Ordinary cadence | Authority ceiling |
|---|---|---|---|
| stdlib | parsing, hashing, process control, SQLite/JSONL, enumeration | every task | operational |
| NumPy | bounded recomputation and array controls | numeric tasks | numeric veto |
| SciPy | named distribution/sparse/optimization controls | selected tasks | function-specific |
| Z3 | finite obligations and impossible-state checks | SMT tasks | encoded bounded result |
| cvc5 | independent solver or encoding comparison | high-value SMT tasks | second encoded result |
| TLC | lifecycle/safety model | development/CI | model result |
| Apalache | symbolic bounded TLA+ analysis | later CI | secondary model result |
| PySINDy | candidate law generation | explicit law-search tasks | proposal only |
| PyDMD | candidate spectral/rate model | explicit rate tasks | proposal only |
| JAX | batched finite numeric worker | later selected profile | observation |
| Julia | independent reference worker | selected CR function | observation |
| Torch/PyG | irregular graph or renesting worker | later/cloud | observation |
| in-toto | command/material/product binding | later high-value runs | execution provenance |

## PySINDy rule

The controller fixes:

- observed variables and units;
- derivative estimator;
- candidate feature library;
- rival libraries;
- training and held-out split;
- residual decomposition;
- acceptance ceiling.

PySINDy may propose a law.  It cannot choose its own hypothesis space and then
validate that law.

## SMT rule

Prefer finite enums and bit vectors.  Integer or real variables must have an
explicit finite operational bound.  `UNKNOWN`, timeout, unsupported encoding,
or missing solver returns `PARKED`.

## Resource rule

Each profile declares:

- timeout;
- maximum finite state count;
- output size;
- optional memory budget;
- source and environment digest;
- fixture-set digest;
- freshness interval.

The full fleet does not boot before every task.  The selected profile runs a
cheap freshness check; the full hostile and maintenance suite runs after
source/environment changes and on a schedule.
