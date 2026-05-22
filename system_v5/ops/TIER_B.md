# Tier B — Geometry Shell-Local Lego Coverage

Historical April 2026 Hermes tier plan. Do not execute or treat
`classification = "canonical"` language below as current formal-scout readiness
or promotion without a fresh repo preflight, current user authorization, and the
current v5 readiness/sim-estate indexes.

> Historical worker preamble from the old Hermes plan, not current Codex
> instruction: spawned Claude workers received Block B from
> `~/wiki/harness/SALIENCE_PREAMBLE.md`.


Preconditions: read `system_v5/ops/HERMES_RULES.md` and `system_v5/ops/SIM_RUNNER.md`. Preflight. Tier A gate passed: `test -f ~/wiki/projects/codex-ratchet/tier_a.md`. Runner is live.

## Role

Hermes spawns Claude Code workers per layer. Workers write probes and append to `system_v5/ops/queue_tier_b.txt`. Runner executes. Workers never run sims.

## Layers

| Worker | Scope (file prefix) | Minimum new canonical sims |
|---|---|---|
| B1 | `gtower_*`, `gstack_*` | ≥10 |
| B2 | `hopf_*` | ≥6 |
| B3 | `weyl_*` | ≥6 |
| B4 | `flux_*`, `u1_*` | ≥6 (2 already exist: `sim_flux_stokes_cell_shell_canonical.py`, `sim_u1_orientation_holonomy_shell_canonical.py`) |
| B5 | `clifford_*`, `pauli_*` | ≥4 |

One Haiku worker per layer, separate worktrees. Each layer may spawn sub-workers across sub-domains (e.g. B1 might run 3 sub-Claudes for G₂ / F₄ / E-class separately) — up to 3 sub-workers per layer, still in separate worktrees.

## Worker template

Read:
- `~/wiki/harness/00_READ_FIRST.md`
- `~/wiki/harness/06_coupling_program_order.md`
- `~/wiki/harness/07_z3_unsat_primacy.md`
- `system_v4/probes/SIM_TEMPLATE.py`
- Scan `~/wiki/concepts/` for layer-name matches

Scope: your layer prefix ONLY.

Tasks:
1. Inventory existing sims in your scope. Classify `canonical / classical_baseline / broken`.
2. Identify shell-local gaps per harness/06 step 1: "which objects (states, operators, probes, entropies) are well-defined in isolation?"
3. Write ≥N new canonical shell-local probes to fill gaps.
4. Each new probe: `SIM_TEMPLATE` conformant, ≥1 `load_bearing` tool from Tier A's capability set.
5. B4 only: new category. U(1) gauge formulation on standard QED conventions; probe coupling to Pauli carriers as shell-local only, never coupled.

Rules:
- Shell-local ONLY. No cross-layer coupling.
- Language discipline per `03_language_discipline.md` — no banned verbs.
- If a probe needs another layer → DO NOT build it; log as "requires coupling; deferred to Tier D".
- Commit per probe: `"tier-b/B<n>: <probe-name>"`.
- Append each new probe basename to `system_v5/ops/queue_tier_b.txt`. Do NOT execute.

## Auditor (Haiku, after workers report written)

Tail runner log. For each probe claimed, verify:
- Probe file exists, `SIM_TEMPLATE` conformant
- Runner reports DONE (not FAIL)
- Result JSON: `classification = "canonical"`, ≥1 `load_bearing` tool, positive + negative + boundary sections present

## Gate

- ✓ Per-layer coverage report at `~/wiki/projects/codex-ratchet/tier_b_<layer>.md`
- ✓ Minimum N new canonical probes per layer, all DONE in runner log
- ✓ No cross-layer coupling in any Tier B probe
- ✓ Auditor clean

## Save + Report

`~/wiki/projects/codex-ratchet/tier_b.md`. Telegram L3 once: gate pass OR blocker.
