# Session 2026-04-14 — Plan + Findings

## Summary

238 canonical/classical sims PASS across ~20 parallel agent waves in one session. Commits: cd96e49e, f08d5ea9, 663a870a + auto-sweeper commits every 5-10 min.

## Wave Ledger

### Round 1 (72 sims)
| Wave | Count | Load-bearing mix |
|---|---|---|
| Thermo engines + bridges | 10 | numpy + z3/sympy |
| Five-framework classicals + bridges | 20 | numpy + z3/torch/clifford |
| Geometry classicals + bridges | 12 | numpy + torch/clifford/e3nn/z3 |
| F01 deep | 15 | z3/sympy/clifford/pytorch (cvc5 parity) |
| N01 deep | 15 | z3/sympy/clifford/rustworkx (cvc5 parity) |

### Round 2 (72 sims)
| Wave | Count |
|---|---|
| F01×N01 coupling (exclusion language) | 8 |
| Entropic Monism doctrine mirrors | 10 |
| Framework pairwise couplings | 10 (8 interacting / 2 additive) |
| G-tower deep reductions | 8 |
| Ladder L13-L19 | 7 (ladder L0-L19 now complete) |
| cvc5 parity retrofit on z3 sims | 10 |
| TopoNetX + GUDHI deep | 8 |
| Rustworkx deep | 8 |
| Geomstats deep | 8 |
| Classical doctrine mirrors | 12 |
| Autograd deep | 8 |
| Triple framework coexistence | 6 (4 interacting / 2 additive) |
| Triple-tool compound | 6 |

### Round 3 (94 sims, geometry-focused)
| Wave | Count | Notes |
|---|---|---|
| Axis pairwise couplings | 10 | All 10 pairs non-commute |
| Ladder pairwise couplings | 10 | L0-L19 pairs |
| cvc5 + e3nn matrix fill | 10 | cvc5 LB count 9→14, e3nn 6→11 |
| Fence BC/T UNSAT | 12 | T5/T7 flagged as surrogate readings |
| G-tower deep (second wave) | 10 | Pin/Spin, G2 probe |
| Weyl/Hopf deep | 10 | gudhi linking number included |
| Framework internals deep | 10 | All five frameworks |
| Geometry non-commutative pairs | 10 | All 10 positives: A∘B ≠ B∘A |
| G-tower ordering ratchet | 8 | 5 rigid pairs, 1 partially flexible, z3 UNSAT |
| Clifford rotor deep | 8 | Cl(3)/Cl(6), BCH second-order |

### Round 3 maintenance + ablation
| Wave | Outcome |
|---|---|
| 4-shell + pent coexistence | 6/6 PASS (interacting by axiom construction — caveat flagged) |
| Ablation irreducibility harness | scripts/ablation_harness.py; 24/27 irreducible, 0 decorative across 10 compound sims |
| Full ablation sweep | 86 sims, 99 pairs: 86.9% irreducible, 0 decorative, 11 baseline-fails flagged |
| Canonical cleanup | 100 demoted to classical_baseline, 3 dynamic-self-gating; backlog 106→0 static |
| Inventory re-probe | 1,399 probes (+686), 272 canonical, 166 with non-numpy LB |

## Infrastructure Running

- `scripts/autonomous_reseed_loop.sh` — PID 22427, 8h deadline 22:56, auto-respawns runners
- 10 `overnight_two_runner.sh` processes, lane-A=3 parallel, lane-B=5 parallel
- Long commit sweeper (7.5h) auto-committing every 10min to `overnight_logs/long_sweeper_*.log`
- Unrun backlog sweep (7h, PID 31129) attacking never-run sims

## Key Findings

1. **Geometry-ratchet test works** — 10/10 non-commutative pairs confirmed A∘B ≠ B∘A; G-tower chain is rigid in 5/6 tested orderings (partially flexible in GL/O/SO triple).

2. **Ablation honest** — 0 decorative tools across 86 compound+deep sims. Load-bearing declarations verified by monkey-patch subprocess ablation.

3. **Inventory false-positive** — the "1,125 never-run" count was heuristic-driven (filename-based JSON lookup); many sims emit differently-named JSONs. Real unrun backlog is smaller. Flag: replace name-matching with content-based detection.

4. **Cleanup done** — 106 canonical-without-non-numpy-LB sims honestly demoted to classical_baseline. No fabricated z3 hooks.

5. **Fence doc gap** — LADDERS_FENCES_ADMISSION_REFERENCE.md lacks verbatim T5/T7 rows; surrogate readings were used and flagged in scope_note.

## Open Gaps

- F01 deep sims 01-05 fail ablation baseline (but passed standalone earlier) — env drift in harness subprocess suspect
- `sim_compound_z3_clifford_pyg_so3_admissibility` pre-existing baseline failure
- 7 sims declare no `load_bearing` at all (nothing to ablate)
- Triple-stack ordering sims declined pending pairwise-matrix closure
- Constraint-manifold 4-layer nesting declined pending shell-local verification
- BC08, BC10, T2, T4, T6, T8 fence sims still missing
- Inventory detection heuristic needs content-based rewrite
