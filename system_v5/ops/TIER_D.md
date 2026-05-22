# Tier D — Boundary Admissibility UNSAT Certificates

Historical April 2026 Hermes tier plan. Do not execute or treat
`classification = "canonical"` language below as current formal-scout readiness
or promotion without a fresh repo preflight, current user authorization, and the
current v5 readiness/sim-estate indexes.

> Historical worker preamble from the old Hermes plan, not current Codex
> instruction: spawned Claude workers received Block B from
> `~/wiki/harness/SALIENCE_PREAMBLE.md`.


Preconditions: read `system_v5/ops/HERMES_RULES.md` and `system_v5/ops/SIM_RUNNER.md`. Preflight. Tier B must be honestly complete enough for the four Tier D boundaries, not merely green by summary or override. Runner is live.

## Role

Hermes spawns Sonnet Claude Code workers per boundary. Workers write boundary probes and append to `system_v5/ops/queue_tier_d.txt`. Runner executes. Workers never run sims.

## Objective

Four z3/cvc5 UNSAT certificates proving structural impossibility at each layer boundary. Per harness/07: UNSAT is structural; existence is contingent.

## Boundaries

| Worker | Boundary | Question | Probe path |
|---|---|---|---|
| D1 | G → Hopf | which Hopf classes UNSAT on non-E-class root systems? | `system_v4/probes/boundary_g_to_hopf_admissibility.py` |
| D2 | Hopf → Weyl | which chirality choices UNSAT on given fibration winding? | `system_v4/probes/boundary_hopf_to_weyl_admissibility.py` |
| D3 | Weyl → Flux | which flux orientations UNSAT without spinor carrier? | `system_v4/probes/boundary_weyl_to_flux_admissibility.py` |
| D4 | Flux → Pauli | which Pauli axes UNSAT without flux orientation? | `system_v4/probes/boundary_flux_to_pauli_admissibility.py` |

One Sonnet worker per boundary, separate worktrees.

## Worker template

Read:
- `~/wiki/harness/00_READ_FIRST.md`
- `~/wiki/harness/02_constraint_admissibility_primer.md`
- `~/wiki/harness/06_coupling_program_order.md`
- `~/wiki/harness/07_z3_unsat_primacy.md`
- `system_v4/probes/SIM_TEMPLATE.py`
- `~/wiki/projects/codex-ratchet/tier_b_<lower>.md`
- `~/wiki/projects/codex-ratchet/tier_b_<upper>.md`
- `system_v4/probes/tool_integration_z3_sympy.py`
- `system_v4/probes/tool_integration_cvc5_sympy.py`

Requirements for each boundary probe:
- `classification = "canonical"`
- `TOOL_MANIFEST`: z3 OR cvc5 `load_bearing`; sympy `load_bearing` or `supportive`
- Positive section: ≥1 admissible composition (SAT, supporting only)
- Negative section (main): ≥2 UNSAT certificates on forbidden compositions
- Boundary section: edge cases (degenerate windings, trivial root systems, etc.)

### UNSAT certificate shape

- symbolic encoding of lower-layer structure `S_L`
- symbolic encoding of upper-layer candidate `C_U`
- admissibility predicate `A(S_L, C_U)`
- assert `¬A(S_L, C_U) ∧ C_U claimed-valid`
- solver returns UNSAT → `C_U` excluded on `S_L`
- store: encoding, predicate, UNSAT proof object, interpretation

### Anti-tautology self-check (before commit)

- UNSAT from contradictory axioms added for this proof? → reject
- UNSAT derivable without lower-layer structure reference? → reject
- No physically-meaningful witness of exclusion? → weak certificate, flag

### Result JSON required keys

```
boundary: "<lower>_to_<upper>"
positive_admissible: [SAT witnesses]
negative_unsat: [{candidate, encoding, proof_hash}]
boundary_edge: [{case, result}]
anti_tautology_check: {passed: bool, reasoning: str}
```

Commit: `"tier-d/D<n>: <boundary> admissibility UNSAT certificates"`. Append basename to `system_v5/ops/queue_tier_d.txt`. Do NOT execute.

## Auditor (Sonnet — NOT Haiku; judgment required)

Read: `~/wiki/harness/07_z3_unsat_primacy.md`, `~/wiki/harness/08_anti_patterns.md`.

After runner DONEs the probe:
- ✓ Canonical, load-bearing SMT tool
- ✓ ≥2 UNSAT certificates per boundary
- ✓ Each UNSAT independently re-verified (fresh solver instance on stored encoding)
- ✓ Each UNSAT references lower-layer structure
- ✓ Language discipline: grep banned verbs in probe and JSON
- ✓ Positive + negative + boundary sections present
- ✓ No cross-layer scope creep

Store re-verification at `~/wiki/projects/codex-ratchet/tier_d_audit.md`.

## Gate

Hard launch gate before Tier D:
- Tier B must not be merely "green by authority override"
- relevant Tier B lego surfaces must show zero pending and zero unresolved FAIL on the lower-layer work needed for D1-D4
- if lower-layer lego completion is still disputed, Tier D stays blocked

- ✓ 4 boundary probes committed
- ✓ Runner reports DONE for all 4
- ✓ ≥8 UNSAT certificates total (≥2 per boundary)
- ✓ All UNSAT independently re-verified
- ✓ Anti-tautology check passed per boundary
- ✓ No banned verbs in any probe or result

## Save + Report

- `~/wiki/projects/codex-ratchet/tier_d.md` — gate evidence
- `~/wiki/projects/codex-ratchet/tier_d_audit.md` — auditor raw
- `~/wiki/projects/codex-ratchet/tier_d_certificates.md` — per-UNSAT summary

Telegram L3 once: `"Tier D gate PASSED at <timestamp>. <N> UNSAT certificates verified."`

Blocker modes (escalate, do not fake):
- UNSAT turns out tautological → research signal; report for owner review
- Boundary produces only SAT (no exclusions) → boundary may not be meaningful; report

## Post-gate

Tier E (composed Axis 0 canonical) becomes available. L3 drafts Brief E using D certificates as inputs. Do not start Tier E work.
