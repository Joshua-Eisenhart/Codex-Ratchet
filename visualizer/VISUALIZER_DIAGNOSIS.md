# Visualizer Static Diagnosis

## A. Render Blockers

1. Likely hard panel failure: duplicate global helper `commutator`.
   - `visualizer/ratchet-visualizer.html:50-52` loads `lie_structure.jsx` before `connes_triple.jsx`.
   - `visualizer/lie_structure.jsx:52` defines `function commutator(A, B)` for 2x2 complex Lie matrices.
   - `visualizer/connes_triple.jsx:95` later defines `function commutator(D, a)` for 4x4 real Connes matrices.
   - Because Babel browser scripts share the page global scope, the Connes helper overwrites the Lie helper. Then `visualizer/lie_structure.jsx:130` calls the Connes helper on Lie matrices and throws `TypeError: Cannot read properties of undefined (reading '0')`.
   - Exact fix: rename both helpers to panel-local names, e.g. `lieCommutator` in `lie_structure.jsx:52,130` and `connesCommutator` in `connes_triple.jsx:95,137,142`.

2. No missing local script files.
   - Every local `<script src=...>` in `ratchet-visualizer.html` resolves under `visualizer/`.
   - The failure is not a missing local include.

3. Secondary global/data hazard: Engine Rosetta payload loaded under the wrong global.
   - `visualizer/cycle-invariant-correlation-data.js:1` exports `window.CYCLE_INVARIANT_CORRELATION_DATA`.
   - `visualizer/carnot_engine.jsx:39`, `visualizer/szilard_engine.jsx:39`, and `visualizer/rosetta_panel.jsx:521` read `window.ENGINE_ROSETTA_DATA`.
   - Result: the Rosetta boundary panels fall back to empty data even though the payload with `tier_correlations` exists.
   - Exact fix: either export an alias `window.ENGINE_ROSETTA_DATA = window.CYCLE_INVARIANT_CORRELATION_DATA` after loading the file, or update those panels to read `CYCLE_INVARIANT_CORRELATION_DATA` and normalize field names.

## B. Data And Mapping Gaps

1. Highest severity: source-of-truth contract is broken by stale/archival payload paths.
   - `visualizer/DESIGN.md` says values must cite mirrored browser payloads and canonical result paths, with sim/proof outputs as source of truth.
   - Multiple `*-data.js` files still cite `/Users/joshuaeisenhart/Desktop/Codex Ratchet/...`, not this checkout.
   - Affected loaded files include `cycle-receipt-coupling-candidate-registry-data.js`, `engine-lab-open-row-audit-data.js`, `engine-lab-successor-coverage-data.js`, and `szilard-open-row-consolidation-data.js`.
   - Affected unloaded files include `carnot-asymmetric-direction-graveyard-data.js`, `engine-lab-sidecar-graveyard-data.js`, and `szilard-open-failure-graveyard-data.js`.

2. High severity: receipt index advertises missing current-checkout result files.
   - `visualizer/iching_engine.jsx:81-98` lists 19 result paths; 13 are missing in `system_v4/probes/a2_state/sim_results/`.
   - Missing examples: `rosetta_triad_modes_results.json`, `rosetta_lego_coupled_array_results.json`, `engine_lab_next_work_queue_results.json`, `engine_lab_successor_coverage_audit_results.json`, `szilard_open_row_consolidation_results.json`.
   - `prime_qit_sidecar_probe_results.json` is also listed, but the checked-in result is `prime_qit_sidecar_probe_N64_results.json`.

3. High severity: the main `data.js` system map is stale and mismapped.
   - `visualizer/data.js:7-10` declares snapshot `2026-04-14T00:00Z` and commit `ce0480e1`.
   - Many referenced artifacts in `visualizer/data.js` do not exist in current `system_v4/probes/a2_state/sim_results/`, including `density_hopf_geometry_results.json`, `foundation_hopf_torus_geomstats_clifford_results.json`, `pure_geometry_hopf_tori_results.json`, `g_structure_tower_results.json`, and `lego_weyl_hopf_spinor_bridge_results.json`.
   - The current checkout has different Hopf/Weyl/fiber/base result names, e.g. `geomstats_hopf_weyl_fiber_base_s3_s2_distance_results.json`, `clifford_hopf_weyl_fiber_horizontal_base_tangent_inner_product_results.json`, `sympy_hopf_connection_curvature_c1_integral_results.json`, and related tool capability/integration receipts.

4. Medium severity: current system coverage is very incomplete.
   - Current `system_v4/probes/a2_state/sim_results/` has 268 `*_results.json` files.
   - The visualizer loads 16 data payloads and only a small engine-lab/Rosetta subset.
   - Major current surfaces underrepresented: tool capability and tool integration receipts, Hopf/Weyl/fiber/base geometry receipts, Clifford/geomstats/e3nn/JAX/PyTorch/JULIA capability rows, SMT/backend agreement audits, and current graveyard/control batteries.

5. Medium severity: existing but unloaded browser payloads are invisible.
   - Files present but not loaded by `ratchet-visualizer.html`: `carnot-asymmetric-direction-graveyard-data.js`, `engine-lab-sidecar-graveyard-data.js`, `prime-qit-sidecar-graveyard-data.js`, `prime-rosetta-sidecar-fit-data.js`, `szilard-open-failure-graveyard-data.js`.
   - This hides negative/control evidence that should matter for claim boundaries.

6. Medium severity: generated JS payloads are partial mirrors, not exact result mirrors.
   - For direct existing pairs, summaries match, but full objects differ. Examples: `carnot-dual-stack-data.js`, `szilard-dual-stack-data.js`, `cycle-invariant-correlation-data.js`, `engine-lab-open-row-audit-data.js`, and `six-bit-gray-code-cycle-data.js`.
   - That is acceptable only if the payload declares itself as a visual subset and keeps canonical path/provenance current.

## C. Ordered Fix Plan

1. Fix the hard render blocker first: rename the two `commutator` helpers and their call sites.
2. Add a static duplicate-top-level guard for all loaded `.jsx` files, treating duplicate `function` names as warnings and duplicate `const`/`let` as failures.
3. Repair the Engine Rosetta global mismatch: either alias `CYCLE_INVARIANT_CORRELATION_DATA` to `ENGINE_ROSETTA_DATA` or update all panels to use the actual exported global.
4. Replace hardcoded receipt rows in `SimReceiptIndexPanel` with a generated manifest from `system_v4/probes/a2_state/sim_results/`, so missing files cannot be labeled canonical loaded/indexed.
5. Regenerate or delete stale browser payloads whose source paths point at `/Users/joshuaeisenhart/Desktop/Codex Ratchet`.
6. Refresh `visualizer/data.js` from current `system_v4` docs/results, or split it into explicit fallback/demo data so it cannot masquerade as current source-backed system state.
7. Load the existing graveyard/negative-control payloads, especially `engine-lab-sidecar-graveyard-data.js`, `szilard-open-failure-graveyard-data.js`, and `prime-qit-sidecar-graveyard-data.js`.
8. Add a static contract check: every visualizer result path must exist in this checkout, every loaded data global must be consumed by at least one panel, and every consumed data global must be loaded or explicitly fallback-labeled.
