# Tier D — Boundary Admissibility UNSAT Certificates

Preconditions: read `ops/HERMES_RULES.md`. Run preflight. Verify Tier B gate passed: all 5 `~/wiki/projects/codex-ratchet/tier_b_<layer>.md` files exist.

## Objective

Produce four z3/cvc5 UNSAT certificates proving structural impossibility at each layer boundary. Existence alone is insufficient — every boundary must be an exclusion proof.

Per harness/07: "UNSAT is structural; existence is contingent."

## Boundaries (one Sonnet worker each, separate worktrees)

| Worker | Boundary | Question |
|---|---|---|
| D1 | G → Hopf | which Hopf classes are UNSAT on non-E-class root systems? |
| D2 | Hopf → Weyl | which chirality choices are UNSAT on given fibration winding? |
| D3 | Weyl → Flux | which flux orientations are UNSAT without spinor carrier? |
| D4 | Flux → Pauli | which Pauli axes are UNSAT without flux orientation? |

## Worker template

Read:
- `~/wiki/harness/00_READ_FIRST.md`
- `~/wiki/harness/02_constraint_admissibility_primer.md`
- `~/wiki/harness/06_coupling_program_order.md`
- `~/wiki/harness/07_z3_unsat_primacy.md`
- `system_v4/probes/SIM_TEMPLATE.py`
- `~/wiki/projects/codex-ratchet/tier_b_<lower_layer>.md`
- `~/wiki/projects/codex-ratchet/tier_b_<upper_layer>.md`
- `system_v4/probes/tool_integration_z3_sympy.py`
- `system_v4/probes/tool_integration_cvc5_sympy.py`

Scope: your boundary only.

Output: `system_v4/probes/boundary_<lower>_to_<upper>_admissibility.py`.

Requirements:
- `classification = "canonical"`
- `TOOL_MANIFEST`: z3 OR cvc5 is `load_bearing`; sympy `load_bearing` or `supportive`
- Positive section: ≥1 admissible composition (SAT, supporting)
- Negative section (MAIN): ≥2 UNSAT certificates on forbidden compositions
- Boundary section: edge cases (degenerate windings, trivial root systems, etc.)

UNSAT certificate shape:
- symbolic encoding of lower-layer structure `S_L`
- symbolic encoding of upper-layer candidate `C_U`
- admissibility predicate `A(S_L, C_U)`
- assert `¬A(S_L, C_U) ∧ C_U claimed-valid`
- solver returns UNSAT → `C_U` excluded on `S_L`
- store: encoding, predicate, UNSAT proof object, interpretation

## Anti-tautology check (worker runs before commit)

- UNSAT caused by contradictory axioms added for this proof? → reject
- Same UNSAT derivable without lower-layer structure reference? → boundary claim false, reject
- No physically-meaningful witness of the exclusion? → weak certificate

## Result JSON required keys

```
boundary: "<lower>_to_<upper>"
positive_admissible: [list of SAT witnesses]
negative_unsat: [list of {candidate, encoding, proof_hash}]
boundary_edge: [list of boundary cases + result]
anti_tautology_check: {passed: bool, reasoning: str}
```

Commit: `"tier-d/D<n>: <boundary> admissibility UNSAT certificates"`.

## Auditor (Sonnet, fresh terminal — NOT Haiku; judgment required)

Read: `~/wiki/harness/07_z3_unsat_primacy.md`, `~/wiki/harness/08_anti_patterns.md`.

For each D1–D4:
- ✓ Canonical classification + `load_bearing` SMT tool
- ✓ ≥2 UNSAT certificates per boundary
- ✓ Each UNSAT non-tautological (independently re-run solver on stored encoding; confirm UNSAT)
- ✓ Each UNSAT references lower-layer structure (cannot be derived without it)
- ✓ Language discipline: grep banned verbs in probe file and result JSON
- ✓ Positive + negative + boundary sections present
- ✓ No cross-layer scope creep

Store re-verification results at `~/wiki/projects/codex-ratchet/tier_d_audit.md`.

Return PASS or specific failure list per boundary.

## Gate

- ✓ 4 boundary probes exist, all canonical, `SIM_TEMPLATE` conformant
- ✓ 8+ UNSAT certificates total (≥2 per boundary)
- ✓ All UNSAT independently re-verified by auditor
- ✓ Anti-tautology check passed per boundary
- ✓ No banned verbs in any Tier D probe or result

## Save

- `~/wiki/projects/codex-ratchet/tier_d.md` — gate evidence
- `~/wiki/projects/codex-ratchet/tier_d_audit.md` — auditor raw
- `~/wiki/projects/codex-ratchet/tier_d_certificates.md` — human-readable summary per UNSAT: what is excluded, why, proof

## Report

Telegram L3 once: `"Tier D gate PASSED at <timestamp>. 4 boundaries proved; <N> UNSAT certificates verified."`

Blocker modes (escalate, do not fake):
- UNSAT turns out tautological → research signal, not a bug. Report to L3 for owner review.
- Boundary produces only SAT (no exclusions found) → boundary may not be meaningful; report to L3.

## Post-gate

Tier E (composed Axis 0 canonical sim) becomes available. L3 will produce Brief for Tier E using D certificates as admissibility inputs. Do not start Tier E work.
