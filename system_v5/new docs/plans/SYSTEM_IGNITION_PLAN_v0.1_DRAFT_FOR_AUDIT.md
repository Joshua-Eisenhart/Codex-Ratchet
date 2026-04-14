# SYSTEM IGNITION PLAN v0.1 — DRAFT FOR AUDIT ONLY
# Do not treat as canonical. Next agent must audit, improve, and decide what to implement.

## Purpose
Provide a bounded, honest, executable path to get the entire Codex Ratchet system running under strict controller discipline while preserving:
- Geometry-first constraint-admissibility manifold
- Micro-lego granularity
- Load-bearing tool integration (no decorative use)
- QIT engines as candidate effective DoF on admitted higher shells (never primitive)
- Hermes as persistent controller with bounded CLI sub-agents (Claude Code print-mode, Codex)
- Strict 4-label truth discipline
- Maintenance as first-class work
- No canon claims until mechanical evidence from full ladder (A-local → E-emergence)

All claims in this document are "candidate admissible under current constraints" or "draft proposal for audit".

## Model Frame (restated nominalist)
The system is a nested simultaneous constraint manifold on shared carriers. Root constraints on distinguishability and probes are prior. Surviving structures are admitted candidates only. QIT engines (feedback, erasure, thermodynamic cycles, demons) are higher-layer aligned effective degrees of freedom that may survive on admitted shells after carrier, geometry, chirality, transport, and coupling tests. They are never assumed fundamental. The ratchet is the ordered dependency chain of mechanical admissibility tests using load-bearing tools. No object is promoted to ToE until micro-legos, bounded couplings, small coexistence, topology-variant reruns, and emergence tests all have evidence.

## Current Honest State (from deep audit 2026-04-14)
- Probes: ~30 rich numpy classical_baseline legos in system_v4/probes/ (density, channels, gates, stabilizer, geometry, topology, discord, etc.). Many have negatives and rich math.
- Migration: All 28 families = NOT_STARTED for torch-native (per MIGRATION_REGISTRY.md).
- Tool depth: Strong numpy/scipy baselines. Severe underuse of PyG (graph writeback), z3 UNSAT, clifford in execution path, TopoNetX/GUDHI, e3nn. Most manifests are honest "not needed" but many probes pre-date SIM_TEMPLATE.
- Plans: The 6 draft documents created in previous turn (.hermes/plans/ and new docs/plans/) are good starters but need deepening with explicit micro-lego list, JSON gap matrix, validator, and full controller orchestration spec.
- Legacy docs: Many in system_v4/docs/ contain premature Axis/bridge language. Treat as historical; do not edit unless the code gate is met.
- Controller surfaces: Fragmented. Hermes must unify under hermes-sim-controller-orchestration pattern.
- Validator: llm_research_enforcement_validator.py exists but needs extension for micro-lego ladder and manifest honesty checks.
- Wiki: Active harness at ~/wiki. Ingest new plans without destroying legacy sources.

Classification (per nonclassical-sim-contract-audit):
- admitted (pre-Axis keeps): ~12 strong local legos
- keep but open: ~15 (missing micro-form or tool depth)
- audit further: legacy Axis/bridge files and older probes with decorative tools or stale classification
- diagnostic_only: many old JSONs and smoke logs
- broken: useful boundary data (e.g. real failures now reported in edge-state writeback)

## Execution Ladder (strict 5 classes — every packet gets exactly one)
A — Local: well-defined in isolation (micro-lego)
B — Pairwise Coupling: interaction or constraint between two families
C — Multi-Shell Coexistence: quantities that become discriminating only under stacking
D — Topology Variant: same test on different topology class (stable vs sensitive)
E — Emergence: quantities that appear only when A-D coverage exists

Status terms (5 only — ban all others):
exists | runs locally | passes local rerun | proof-backed | canonical by process

## Tool Enforcement (must be load-bearing where relevant)
- Impossibility: z3 (UNSAT) + cvc5 cross-check
- Geometry: geomstats, clifford, e3nn
- Graph/relational: PyTorch + PyG (writeback mandatory for rich geometry claims), rustworkx, XGI
- Topology: TopoNetX, GUDHI
- Symbolic: sympy
- All canonical sims must start from SIM_TEMPLATE.py and have non-empty reason fields.

## Micro-Lego Backbone (proposed split — audit and improve this list)
Carrier & Constraint (Phase 1):
- finite_carrier_c2
- density_state_space_dc2
- positivity_constraint
- trace_constraint
- distinguishability_probe

Same-Carrier Geometry (Phase 2):
- hopf_map_s3_to_s2
- hopf_fiber_equivalence
- nested_torus_geometry
- clifford_spinor_geometry
- berry_holonomy
- fubini_study_bures_geometry
- weyl_chirality_pair

Graph/Topology Geometry (Phase 3):
- graph_shell_geometry
- cell_complex_geometry
- persistence_geometry
- state_class_binding

Operator/Channel (Phase 4):
- pauli_generator_basis
- channel_cptp_map
- kraus_operator_sum
- local_operator_action
- composition_order_noncommutation

QIT Engine Baselines (Phase 5 — classical side lane, deep):
- measurement_update_rule
- feedback_control_channel
- erasure_map
- landauer_bound_enforcement
- szilard_engine_cycle
- carnot_information_engine

Later: bounded couplings (e.g. pauli_on_weyl, engine_on_hopf_torus), small coexistence, topology variants, emergence tests. Only then bridge/Phi0/Axis candidates.

## Gap Matrix
See new docs/plans/LLM_RESEARCH_GAP_MATRIX.json (created as draft, all cells start as GAP). Columns = A B C D E. Rows = above micro-legos + QIT engine DoF candidates.

## Controller Architecture (Hermes as persistent controller)
- Hermes owns: queue order, truth labels, scope discipline, maintenance closure, wiki ingest.
- Sub-agents: bounded Claude Code (`claude -p`) and Codex CLI workers. Concurrency cap = 3. Non-overlapping file sets only.
- Dry-run mode mandatory before any wave.
- Heartbeat: Telegram every ~5 min for overnight runs (use Hermes bot only).
- After every packet or batch: controller must reread result JSON, run probe_truth_audit.py and controller_alignment_audit.py, assign truth label, perform maintenance closure if needed.
- Never trust worker prose without direct artifact + audit verification.
- Maintenance surfaces must be updated when honest state changes (backlog, truth audit, tool matrix, 16/17 ledgers, wiki).

## Launch-Ready Surfaces (created as drafts)
- SYSTEM_IGNITION_PLAN_v0.1_DRAFT_FOR_AUDIT.md (this file)
- QIT_ENGINE_MICRO_LEGO_BREAKDOWN.md (deepened)
- QIT_ENGINE_GEOMETRY_COUPLING_MATRIX_DRAFT.md (expanded)
- OTHER_AGENT_AUDIT_CHECKLIST_FOR_QIT_ENGINES.md (strict checklist)
- TOOL_INTEGRATION_REQUIREMENTS_FOR_ENGINE_DOF.md (updated)
- CONTROLLER_ORCHESTRATION_SPEC_v0.1_DRAFT.md (new)
- LLM_RESEARCH_GAP_MATRIX.json (new, all GAP)
- VALIDATOR_IMPROVEMENT_STUB.py (new stub for extension)

## Immediate Phase 0 (what next agent should do first)
1. Deep audit these 8 new surfaces (use nonclassical-sim-contract-audit + truth-audit-and-tool-maintenance).
2. Improve gap matrix and micro-lego list.
3. Extend the validator to enforce micro-ladder, manifest honesty, and no-canon language.
4. Test one micro-lego (e.g. density_state_space_dc2 or positivity_constraint) under full SIM_TEMPLATE with load-bearing z3 + PyG.
5. Run maintenance closure on any stale classification found in legacy docs (downgrade only; never promote).
6. Produce launch manifest for first 5-micro-lego wave.

## Stop Rules
- Never edit 16/17 ledgers, MIGRATION_REGISTRY, or wiki until code/result gate is satisfied and next agent has audited the change.
- No E claims without A-D coverage for that family.
- No bridge/ToE language until full ladder complete.
- If a packet fails on tool depth or negative suite, treat failure as useful data — do not soften the test.

This plan is a draft only. It contains no canonical claims. The next agent must audit every part, improve where weak, and decide the exact first queue.

End of document. Ready for audit.