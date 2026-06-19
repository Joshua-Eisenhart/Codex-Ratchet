# axis0_terrain_engine_leap_v0 — BAD TWIN FIXTURE

**Type:** Negative fixture (designed to FAIL gates)
**Purpose:** Verify that gate scripts fire on specific, named failure modes.
**Status:** exists — not intended to run, pass, or be promoted.

## What this fixture does

This sim is deliberately broken in four documented ways:

### Defect 1 — Jargon name with no F01/N01 ancestry
Top-floor vocabulary (axis0 / terrain / engine) appears in the sim name and result fields.
`f01_ancestry` and `n01_ancestry` are both `null`. There is no grounding in the
distinguishability root. This exercises name-drift detection.

### Defect 2 — Count-tautology SMT tagged `load_bearing` (GATE-2)
Both the JAX leg (z3) and the PyTorch leg (cvc5) call:
```
solver.add(n == computed_count)
solver.add(n == EXPECTED_count)
```
Both are SAT by construction. No structural predicate, no sign relation, no
erased flip with a math reason. Both are tagged `load_bearing`.

**Expected gate:** `validate_smt_not_tautology.py` fires 4 violations (jax, pytorch, envelope x2).

### Defect 3 — Unfenced verdict-bearing dynamic tokens (GATE-FIREWALL)
- `axis0_earned: true` in jax_results — no audit_verdict or control evidence
- `axis0_terrain_engine_activated: true` in pytorch_results — same
- `axis0_terrain_engine_survived: true` in envelope_results — same
- `axis0_earned_claim_string: "axis0 terrain engine has earned admission..."` — prose promotion word "earned" without local fence

**Expected gate:** `validate_canon_firewall.py` fires prose_promotion_leak, tier2_dynamic_claim, unbacked_engine_independence.

### Defect 4 — Shared build_packet / by-construction independence (GATE-ENGINE)
Both `axis0_terrain_engine_leap_v0_jax.py` and `axis0_terrain_engine_leap_v0_pytorch.py`
call the same `build_packet()` function. Both result files have `reads_peer_result: true`.
`engine_consensus.independent: true` in the envelope is therefore by-construction.

**Expected gate:** `validate_three_engine_sim_result.py` fires `jax.reads_peer_result must be false`.

## Gate run results (2026-06-14)

| Gate | Result |
|------|--------|
| `validate_smt_not_tautology.py` | FIRES — 4 violations (ok: false) |
| `validate_canon_firewall.py` | FIRES — 29 violations (ok: false) |
| `validate_three_engine_sim_result.py` | FIRES — jax.reads_peer_result must be false |

## What this fixture does NOT test

- Julia leg is not implemented (no `.jl` source); envelope stub only
- Actual z3/cvc5 execution not required (counts are static in JSON)
- This is not a math test; there is no claimed math in this packet

## Do not fix this sim

The violations are intentional. If a gate change causes this sim to pass,
the gate has been weakened. Investigate the gate, not this fixture.

claim_ceiling: scratch_diagnostic
promotion_allowed: false
formal_admission_allowed: false
