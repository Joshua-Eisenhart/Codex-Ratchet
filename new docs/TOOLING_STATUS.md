# Tooling Status

Date: 2026-04-05
Supersedes: CURRENT_TOOL_STATUS__INSTALLED_VS_MISSING_VS_NOT_WIRED.md,
            CURRENT_TOOL_STATUS__OPERATIONAL_CLASSIFICATION.md,
            CURRENT_PROPER_INSTALL_AND_LOCATION_RULE_NOTE.md,
            NONCLASSICAL_SYSTEM_TOOL_PLAN.md

---

## Canonical Interpreter

`/opt/homebrew/bin/python3` — all live skills and probes must use this.
No references to `.venv_spec_graph` in runtime paths.

---

## Tool Status

### GREEN — Imported and meaningfully used in probes/runtime

| Tool | Where used | What it does |
|---|---|---|
| networkx | v4_graph_builder, qit_graph_stack_runtime, graph_builder, probes | Core graph construction, MultiDiGraph, node/edge ops |
| numpy | everywhere | Numeric backbone |
| pydantic | schema validation | Typed schemas for artifacts |
| jsonschema | artifact validation | JSON structure validation |
| pytest | test suites | Executable test gates |
| sympy | operator basis proofs | Symbolic math proofs (B3.2, B3.3) |

### YELLOW — Imported but shallow or optional usage

| Tool | Where used | What it does | Gap |
|---|---|---|---|
| hypothesis | test_density_matrix_invariants, test_graph_invariants_deep, strata_verifier | Property-based testing with @given | Not core logic, testing only |
| torch | sim_axis0_orbit_phase_alignment, graph_tool_integration | Tensor creation, cosine similarity | Only tensor ops, no ML/autograd |
| torch_geometric (PyG) | graph_tool_integration, sim_axis0_orbit_phase_alignment | HeteroData construction | Optional sidecar, try/except fallback |
| clifford | clifford_edge_semantics_audit, graph_tool_integration | Cl(3) multivector edge enrichment | Optional sidecar, gracefully degradable |

### RED — Installed but not actually imported or used

| Tool | Status | Detail |
|---|---|---|
| z3 | Installed, NOT directly imported | pySMT is the abstraction layer; z3 is backend only |
| toponetx | Installed, never imported at module level | Commented but not used; dynamic import in try/except returns error dict |

### MISSING — Not installed under canonical interpreter

| Tool | Why it matters |
|---|---|
| cvc5 | Alternative SMT solver; not blocking |
| quimb | Tensor network library; future |
| qutip | Quantum toolbox; future |
| ripser | Persistent homology; future |

---

## .venv_spec_graph Migration

**Status: COMPLETE. Deletion-ready pending owner confirmation.**

- All 5 tier-1/tier-2 runtime skills migrated to canonical interpreter
- Zero live runtime blockers remaining
- 46 files still reference `.venv_spec_graph` — all historical/documentation, not runtime
- ~1GB reclaimable on deletion
- Two dead-code constants remain (cosmetic, not blocking)

See: VENV_SPEC_GRAPH_POST_MIGRATION_VALIDATION.md (2026-04-04) for full audit.

---

## Sidecar Policy (from core_docs)

1. Owner graph (NetworkX) is source of truth
2. Sidecars are read-only projections
3. Sidecars may annotate but not create owner nodes/edges
4. No sidecar may claim ownership without promotion gate
5. Sidecar output is ephemeral (regenerable)
6. No sidecar runs during live engine step

---

## Heartbeat

Heartbeat launchd agent UNLOADED as of 2026-04-04. Path fix applied
(was `/home/ratchet/`, now `/Users/joshuaeisenhart/`). macOS TCC blocks
`/bin/bash` from accessing `~/Desktop` via launchd. Re-enable requires
Full Disk Access for bash or moving repo out of Desktop.
