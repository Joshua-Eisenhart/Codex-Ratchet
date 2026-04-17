# 2026-04-12 Audited Overnight 8h Run Contract

Status: RUN CONTRACT FOR THIS OVERNIGHT CONTROLLER SESSION

## System root
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5`

## Live authority hierarchy
1. `docs/LLM_CONTROLLER_CONTRACT.md`
2. `docs/ENFORCEMENT_AND_PROCESS_RULES.md`
3. `docs/EXPLICIT_CONTROLLER_MODEL.md`
4. `docs/ANOMALOUS_COMPUTER_SCIENCE_TRANSLATION.md`
5. `docs/16_lego_build_catalog.md`
6. `docs/17_actual_lego_registry.md`
7. `docs/PYTORCH_RATCHET_BUILD_PLAN.md`
8. `docs/TOOLING_STATUS.md`
9. `docs/MIGRATION_REGISTRY.md`
10. `docs/TOOL_MANIFEST_AUDIT.md`
11. `docs/LLM_RESEARCH_GAP_MATRIX.json`
12. `docs/plans/sim_backlog_matrix.md` as the primary live queue
13. `docs/plans/sim_truth_audit.md` as the primary live truth-status surface
14. `docs/plans/tool_integration_maintenance_matrix.md` as the primary live tool-depth surface
15. `docs/plans/controller_maintenance_checklist.md` as the primary live run-operations surface
16. `docs/plans/on-demand-telegram-runner.md` as the default operating-mode note
17. `docs/plans/wiki_ingest_and_lego_maintenance.md` for repo/wiki synchronization rules
18. `docs/archive/*` only as supporting geometry/pre-Axis reference corpus, not as queue authority
19. repo-root `/docs` is not an authority root for this run

## Highest-priority missing or partial geometry/pre-Axis legos
- `hopf_map_s3_to_s2`
- `hopf_fiber_equivalence`
- `hopf_connection_form` / `transport_geometry` / `holonomy_geometry`
- `weyl_chirality_pair`
- `chiral_density_bookkeeping`
- `pauli_generator_basis` / `left_right_asymmetry`
- `composition_order_noncommutation`
- `cell_complex_geometry`
- `persistence_geometry`

## Highest-priority QIT-aligned Carnot/Szilard legos
Keep these in a separate classical/QIT lane and only advance when geometry workers are blocked or a geometry wave closes cleanly.
- `qit_carnot_finite_time_companion`
- `qit_carnot_hold_policy_companion`
- `qit_szilard_record_companion`
- `qit_szilard_substep_companion`
- `qit_szilard_bidirectional_protocol`

## Wrong or derived surfaces to treat carefully
- repo-root `/docs` is not the planning root
- `docs/plans/2026-04-12-overnight-8h-run-plan.md` is a derived run-plan surface and should not override the live queue/truth/control surfaces
- any bridge/Axis/flux summaries are derived surfaces and remain blocked behind lower geometry/chirality/differential packets
- wiki raw ingest pages remain ingest sources, not authority

## Heartbeat / anti-stuck / audit rules
- read authority docs before each bounded packet if the session is fresh
- work bottom-up only: carrier -> geometry -> chirality/operator -> topology -> bipartite local -> late entropy/bridge gates
- geometry-before-axis; no bridge/Axis widening; no flux promotion
- only run parallel lanes when file sets do not overlap
- after each successful packet:
  - rerun with Makefile interpreter `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3`
  - run `system_v4/probes/probe_truth_audit.py`
  - run `system_v4/probes/controller_alignment_audit.py`
  - patch only directly stale ledger/truth/wiki surfaces
- if a worker repeats the same failure twice without a new hypothesis, mark blocked and pivot
- every heartbeat must report: current lane, last grounded command/result, health state, files/results changed, next bounded step
- allowed status labels only: `exists`, `runs`, `passes local rerun`, `canonical by process`
