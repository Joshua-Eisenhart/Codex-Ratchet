# BUILD CARD: terrain_operator_precedence_64_matrix — full 64-cell chart matrix + degeneracy diagnostic (weld-3 ingredient)

One object, one claim, one card. CLAIM UNDER TEST: the chart lattice of 64 cells (8 terrain realizations x 8 signed operators) can be computed as MEASURED BEHAVIORS — one behavior-fingerprint row per cell from the committed source-locked forms — and its degeneracy structure diagnosed by a declared fingerprint-family ladder, classifying every collapse as probe_coarseness / commuting_degeneracy / definition_alias / intended_degeneracy_candidate / bug_or_underinstrumented.

This is the CHART object. It is NOT the 6-axis hexagram runtime probe (the existing n_distinct=16 evidence) — that is a different object; the result must state this boundary and never conflate them (four parallel 64-constructions preserved per the mine receipt §A5). No closure claim: n_distinct=64, if found, is 64 distinct ONLY under the named fingerprint family.

Ceiling: classification="scratch_diagnostic", promotion_allowed=false, formal_admission_allowed=false. No axis-level admission, no Axis-6 "earned" doctrine claim, no engine/runtime closure, no IGT.

## Read first (binding)
1. system_v6/receipts/matrix64_mine_20260610.md — THE SPEC (sections A-D verbatim; the D2 fingerprint ladder is the diagnostic design)
2. system_v6/receipts/terrain_operator_map_20260609.md:36-39, 54, 108-140, 163-172
3. system_v5/READ ONLY Reference Docs/operator math explicit.md (Ti/Te/Fi/Fe channel/unitary forms; UP/DOWN = composition order only, :3-4, 796-810)
4. system_v5/READ ONLY Reference Docs/terrain math.md:56-83, 118-150 + terrain rosetta strong math.md:149-183 (8 terrain laws, 16 placements, structural lock)
5. system_v6/sims/terrain_generator_sheet_packet/ + system_v6/sims/source_locked_operator_base_packet/ — REUSE their source-locked generator/operator forms (cite; do not re-derive)
6. system_v6/sims/mct_dynamic_admissibility_packet_v0/ — carrier lineage (Hopf/Weyl density carrier; cite pin_block_sha256). Do NOT promote to nested/rung maps (mine receipt D1 carrier boundary).

## PIN block (frozen; identical across legs)
- cells: terrain_id in {Se/Funnel, Se/Cannon, Ne/Vortex, Ne/Spiral, Ni/Pit, Ni/Source, Si/Hill, Si/Citadel} x signed_operator_id in {Ti+,Te+,Fi+,Fe+,Ti-,Te-,Fi-,Fe-}; address key (terrain_id, signed_operator_id, stage_id, suboperator_id) per scaffold :121.
- precedence semantics: '+' = Phi_T(O(rho)); '-' = O(Phi_T(rho)) (terrain_operator_map :36-39).
- states: one pinned nondegenerate rho (PINNED-CHOICE, source-quoted, NOT an eigenstate of any pinned generator) + a generic-state sweep over a pinned sample of the committed carrier rows (subset size pinned).
- fingerprint ladder F0-F8 exactly as mine receipt D2 (address / final-density / order-pair / Delta+norms / observables / entropy-purity / spinor-sheet-loop / trajectory / axis4-vs-axis6 orthogonality); FP_TOL pinned; every Fk emits n_distinct(Fk), class map, largest class, intra-class differing fields, recovered_over_16, invariant_collapse_under_all_F.
- terrain/operator forms: imported source-locked from the committed packets, with their PIN lineage cited.

## Build gates
G1. 64 rows, each with COMPUTED behavior columns: both ordered outputs, Delta_{T,O} matrix + norms, entropy/purity deltas, observables — label-only rows are a build failure.
G2. Ladder executed fully: per-Fk receipts as pinned; the per-collapse classification verdicts assigned with the supporting computed evidence named (a verdict without a cited computed field is a failure).
G3. Commuting control: at least one cell whose terrain/operator pair commutes by the source math must show Delta = 0 (within FP_TOL) — and a pinned noncommuting cell must show Delta != 0; both as DISTINCT-pair operations (no self-pairs).
G4. Erased-axis control: collapsing the precedence sign (compute only one order) must merge the signed pairs under F2/F3 — the flip that proves the sign column is doing work.
G5. Axis-4/Axis-6 orthogonality cell (F8): vary loop-order class with precedence fixed and vice versa; report independent movement; never merge the two order DOFs.
G6. Load-bearing SMT (z3 AND cvc5 separately): derive from COMPUTED matrix entries that a pinned noncommuting cell's Delta is structurally nonzero (real rows -> UNSAT for "Delta = 0"; erased/symmetrized control -> SAT). Hardcoded literals = failure.
G7. Boundary statement: result carries an explicit field distinguishing this chart object from the eng_64_hexagram runtime object, citing the mine receipt's four-construction table; the 16-class hexagram map is referenced as related-but-different evidence only.
G8. Honest distinctness: report n_distinct under every Fk with no "64 achieved" language unless under a named Fk, and intended_degeneracy_candidates listed separately.

## Controls
commuting-pair zero (G3), erased-precedence merge (G4), label shuffle (class maps invariant under relabeling), FP_TOL sensitivity row (n_distinct vs tolerance sweep — tolerance gaming check), trivial-fingerprint control (F0 address must give 64 trivially and be excluded from behavior claims).

## Engines (three-engine claim-bearing; identical PIN)
Julia = canon (QuantumOptics channels, Z3.jl). JAX = the 64-cell x state-sweep batch + z3/cvc5 python. PyTorch = class-map/collapse graph lane (collapse classes as graph components; torch machinery). NumPy control-lane only.

## Files to create (one folder, atomic)
system_v6/sims/terrain_operator_precedence_64_matrix/
  terrain_operator_precedence_64_matrix_julia.jl / _jax.py / _pytorch.py / _envelope.py
  build_card.md (verbatim copy)
  results/*.json
No audit_verdict.md. No edits to existing files.

## Acceptance (re-run mechanically)
Legs exit 0 fresh; validator --require-pytorch ok:true; PIN identical with both reuse lineages cited; G1-G8 receipt fields present; controls fired with values; ladder complete with per-Fk class maps; ceiling fields exact.
