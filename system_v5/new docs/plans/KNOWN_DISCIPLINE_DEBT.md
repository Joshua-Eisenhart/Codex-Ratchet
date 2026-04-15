# Known Discipline Debt Ledger

Track items that violate project discipline (CLAUDE.md, doctrine memos) and need correction. Pay down deliberately, don't accumulate silently.

## Format
Each entry: `[date] DEBT: <what> | RULE BROKEN: <which doctrine/rule> | REPAYMENT: <what closes it>`

## Open

- ~~**[2026-04-14] DEBT: 8 evolutionary/clustering integration sims authored before isolated tool-capability probes existed.**~~ **CLOSED 2026-04-15**: sim_capability_hdbscan_isolated (8/8), sim_capability_umap_isolated (7/7), sim_capability_sklearn_isolated (7/7) all committed at bfbf1456. All 10 tools (ribs/deap/evotorch/datasketch/pymoo/hypothesis/optuna/hdbscan/umap/sklearn) now have isolated capability probes. Integration sims eligible for canonical promotion.

- **[2026-04-14] DEBT: Status label "8 PASS" used in commit message and chat report.** RULE BROKEN: four-label discipline (`exists / runs / passes local rerun / canonical by process`). REPAYMENT: future commit messages cite the explicit label earned. The 8 sims earned `passes local rerun` (single fresh run this session), NOT `canonical by process`.

## Closed

- **[2026-04-14] DEBT: 8 evolutionary/clustering integration sims authored before isolated tool-capability probes existed.** CLOSED 2026-04-15: sim_capability_hdbscan_isolated (8/8), sim_capability_umap_isolated (7/7), sim_capability_sklearn_isolated (7/7) committed at bfbf1456. All 10 tools now have isolated probes; integration sims eligible for canonical promotion.

- **[2026-04-14] DEBT: 4 sims (hypothesis, optuna, pymoo, and related) had stub manifest reasons.** CLOSED 2026-04-15: all 7 evolutionary canonical sims verified with substantive manifest reasons ≥25 chars; ribs/deap/evotorch/datasketch/pymoo/hypothesis/optuna all overall_pass=True; check_manifest.py gate hardened.
