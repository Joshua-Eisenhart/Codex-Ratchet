# Known Discipline Debt Ledger

Track items that violate project discipline (CLAUDE.md, doctrine memos) and need correction. Pay down deliberately, don't accumulate silently.

## Format
Each entry: `[date] DEBT: <what> | RULE BROKEN: <which doctrine/rule> | REPAYMENT: <what closes it>`

## Open

- **[2026-04-14] DEBT: 8 evolutionary/clustering integration sims authored before isolated tool-capability probes existed.** Tools added without sequence: ribs, deap, evotorch, datasketch, pymoo, hypothesis, optuna, hdbscan, umap, sklearn. RULE BROKEN: "Classical sims free; nonclassical gated on tool-sims" + four-sim-kinds doctrine (capability probe must precede tool-to-lego integration). PARTIAL REPAYMENT 2026-04-14: 7 evolutionary/clustering probes committed (ribs/deap/evotorch/datasketch/pymoo/hypothesis/optuna) + 11 core manifest tool probes committed (z3/cvc5/sympy/clifford/e3nn/pyg/geomstats/toponetx/rustworkx/xgi/gudhi). PARTIAL REPAYMENT 2026-04-15: all 7 evolutionary integration sims now canonical with overall_pass=True and substantive manifest reasons ≥25 chars. REMAINING: hdbscan, umap, sklearn capability probes still missing before those 3 integration sims can be re-promoted canonical.

- **[2026-04-14] DEBT: Status label "8 PASS" used in commit message and chat report.** RULE BROKEN: four-label discipline (`exists / runs / passes local rerun / canonical by process`). REPAYMENT: future commit messages cite the explicit label earned. The 8 sims earned `passes local rerun` (single fresh run this session), NOT `canonical by process`.

## Closed

- **[2026-04-14] DEBT: 4 sims (hypothesis, optuna, pymoo, and related) had stub manifest reasons.** CLOSED 2026-04-15: all 7 evolutionary canonical sims verified with substantive manifest reasons ≥25 chars; ribs/deap/evotorch/datasketch/pymoo/hypothesis/optuna all overall_pass=True; check_manifest.py gate hardened.
