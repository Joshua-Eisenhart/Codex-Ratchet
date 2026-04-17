# Tier B — Geometry Shell-Local Lego Coverage

Preconditions: read `ops/HERMES_RULES.md`. Run preflight. Verify Tier A gate passed: `test -f ~/wiki/projects/codex-ratchet/tier_a.md`.

## Objective

Every geometry layer has canonical shell-local sims in isolation. Five layers, one Haiku worker each, separate worktrees.

## Layers

| Worker | Scope (file prefix) | Minimum new canonical sims |
|---|---|---|
| B1 | `gtower_*`, `gstack_*` | ≥10 |
| B2 | `hopf_*` | ≥6 |
| B3 | `weyl_*` | ≥6 |
| B4 | `flux_*`, `u1_*` | ≥6 (2 already exist: `sim_flux_stokes_cell_shell_canonical.py`, `sim_u1_orientation_holonomy_shell_canonical.py`) |
| B5 | `clifford_*`, `pauli_*` | ≥4 |

## Worker template (each layer)

Read:
- `~/wiki/harness/00_READ_FIRST.md`
- `~/wiki/harness/06_coupling_program_order.md`
- `~/wiki/harness/07_z3_unsat_primacy.md`
- `system_v4/probes/SIM_TEMPLATE.py`
- Scan `~/wiki/concepts/` for layer-name matches

Scope: your layer prefix ONLY. Do not touch other layers.

Tasks:
1. Inventory: list every existing sim in your scope. Classify `canonical / classical_baseline / broken`.
2. Coverage gaps: which shell-local questions are NOT yet simmed? Use harness/06 step 1: "which objects (states, operators, probes, entropies) are well-defined in isolation?"
3. Write ≥N new canonical shell-local sims to fill gaps (N per table above).
4. Every new sim: `SIM_TEMPLATE` conformant, ≥1 `load_bearing` tool from `{z3, cvc5, sympy, PyG, TopoNetX, Clifford, torch}`.
5. B4 only: you are creating a NEW category. U(1) gauge formulation on standard QED conventions; probe coupling to Pauli carriers as shell-local only (not coupled).

Rules:
- Shell-local ONLY. No cross-layer coupling in this tier.
- Language discipline per `03_language_discipline.md` — no banned verbs.
- If a sim needs another layer to work, DO NOT build it. Log as "requires coupling; deferred to Tier D".
- Commit per sim: `"tier-b/B<n>: <sim-name>"`.

## Auditor (Haiku, after workers report)

Verify per-layer N-count met, `SIM_TEMPLATE` conformance, `load_bearing` tool present, classification correct.

## Gate

- ✓ 5 layer coverage reports at `~/wiki/projects/codex-ratchet/tier_b_<layer>.md`
- ✓ Minimum N new canonical sims per layer met
- ✓ No cross-layer coupling in any Tier B sim
- ✓ Auditor pass

## Report

Telegram L3 once: gate pass OR blocker.
