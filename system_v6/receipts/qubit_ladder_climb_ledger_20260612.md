# The Qubit-Ladder Climb Ledger (2026-06-12 — the standing debt table)

```yaml
receipt_kind: climb_ledger
rule: the wiki contract — EVERY layer, EVERY nesting relation, and the FULL integration
  climbs 1Q -> 2Q -> 3Q... rung by rung; 1Q/2Q never proves a layer; 3Q = the QIT floor
update_discipline: this ledger updates on every rung commit; the queue derives from it
```

| Layer / object | 1Q | 2Q | 3Q (the QIT floor) |
|---|---|---|---|
| The carve (M(C), layers 1-2) | DONE (twice-audited) | DONE (218fac1a1) | DONE-as-count-fixture (the v1: full matrix zero-mismatch, GHZ/W honest, CKW earned; v0 demoted) |
| The freeze/registry | DONE (1Q) | DONE (2Q) | DONE (3Q) + 4Q DONE (gcm_4q, 3822 reduced cut-matrices stored, cut_state_available=true, audited) |
| Geometry attach (3-12) | DONE (748fca97c) | DONE (the real-states v1; the v0 vindicated as approximation) | owed |
| Connection/flux (10-12) | DONE (geometric) | DEPRIORITIZED | runtime flux: v0 VOID; v1 DOCTRINE-SPLIT (independent L/R: J_cut/J_ent opposition KILLED, J_chi chirality survives guarded; 3Q-floor SUPPORTED); next = pre-registered independent-generator sweep |
| Entropy families | DONE (c6155e4d7) | DONE (8326405e6: the informative rung LIVE — structural negativity split, real witnesses) | owed (3Q families; CKW monogamy) |
| Dynamics (the runner) | DONE (v0+v1) | DONE (GNVW: L=-2/R=+2 opposite INDEX earned + independent-reflection-repaired; mirror-conjugacy NOT earned, dressing over-free) | owed |
| The order matrix | DONE (ec648675d, 5-step alphabet) | **OWED** (the matrix on the 2Q object) + the full Part-C alphabet at 1Q | owed |
| The 16 stages | DONE-as-diagnosed (fef28db67: graded alignment = the v2) | **OWED** (the stages on 2Q states) | owed — the stages at the QIT floor |
| Tensor/Cl(6)/the towers (17-23) | n/a (these layers BEGIN at 2Q/3Q) | partial (the 2Q carve touches 17-18) | **THE FRONTIER** — untouched |

| The nesting tower (the law itself) | n/a | DONE (<=2Q: exact=product) | DONE (<=3Q: exact=EMPTY, probe-only — the root axiom DEEPENS: at 3Q a~b is the ONLY non-empty tower) |

| The carve @ 4Q | n/a | n/a | DONE-as-count-fixture (555->546/9, full matrix 0-mismatch) |
| The carve @ 5Q | n/a | n/a | DONE-as-count-fixture (556->547/9, Cl(10)) |
| The carve @ 6Q | n/a | n/a | DONE-as-count-fixture (557->548/9, Cl(12); rung 6) |
| The carve @ 7Q | n/a | n/a | DONE-as-LEAN-count-fixture (558->549/9, hash+sample storage 3.9M, scale wall fixed, Cl(14); rung 7) |

## The unlock chain

The ONE in-flight lane (the 2Q freeze + cut) gates four 2Q rungs: geometry-v1 (real states),
flux@2Q, dynamics@2Q (GNVW), the order matrix@2Q. They launch on its landing. The 3Q rung
(the QIT floor — Cl(6), C^8, where runtime flux and memory claims first become possible)
opens after the 2Q row fills. Independent of the freeze: the order matrix's full Part-C
alphabet extension at 1Q (its audit's named follow-up).

## CORRECTION (owner-triggered, 2026-06-12): the ladder is NOT lost — two distinct statuses

THE EXISTING LADDER FEEDSTOCK (built, audited, scratch-valid — the free-math axis):
| Rung | What exists |
|---|---|
| 1Q | exact closure (6489a6929 EXACTNESS EARNED), the spinor 4pi/SO(3) rows, finite incidence q=3/q=4 |
| 2Q | the boundary packet |
| 3Q | THE FLOOR: geo_s1_three_qubit_floor_exact (Cl(6), C^8, exact-integer, tau rows) + stage_lifted_spinor_shell_n3 + terrain_spinor_flux_nest_n3 |
| 4Q | support + lifted shell n4 + terrain nest n4 (lock-refreshed 4f757c48c) |
| 5Q | safety margin + lifted n5 |
| 6Q-8Q | scaling stress (b27d22317) + lifted n6-n8 (Cl(12/14/16), W-entropy anchors, IC 65536) |

THE LEDGER ABOVE tracks the OTHER axis: which rungs are ATTACHED to the carved M(C) under
the frozen IDs (the nested climb per the contract). The work ahead = ATTACHMENT of existing
feedstock, not rebuilding rungs — e.g., the 3Q rung's attach = the carve at 3Q consuming
the EXISTING Cl(6)/C^8 floor machinery by hash, not a from-scratch build. The original
ledger's OWED cells are attachment-owed, and each names its ready feedstock.

## UPDATE 2026-06-12 (late) — drift flag closed + depth-gate frontier

- **Registry body-hash drift flag: CLOSED H1** (04995ea82). The 1Q frozen substrate is now
  drift-immune (body hash 0fddf60c reproducible byte-stable regardless of helper edits) and
  honestly pinned; fix was 5 .py files, ZERO results.json touched (NOT a re-freeze / identity /
  math change). codex2 FIX_SOUND on 5 falsifiers + grok blind panel found & closed a
  negative-rejection coverage gap (live-negative-rerun hardening, empirically proven). **8Q +
  new substrate-consuming packets RE-ENABLED.**
- **Geometry-delta @ 3Q: LANDED** (gcm_nested_geometry_delta_3q_v0, GENUINE_WITH_CAVEATS audit).
  Nested 3Q geometry (A-marginal probe-shell occupation) MOVES under an alternate registry pin
  (L1 0.0218 -> 0.0145) and is stable under the tested alternate probe — i.e. **geometry is
  pin/probe-relative**, consistent with the <=3Q tower (the root axiom surfacing at the geometry
  layer). Caveats being closed in flight: (1) add a same-input null/stable control; (2) downgrade
  the three-engine-independence labeling (only Julia + Python-packet recompute genuine).
- **IN FLIGHT (3 codex2 lanes):** geometry-delta strengthening (caveat close), the **<=4Q nested
  tower** on the committed 4Q cut states (depth — does exact stay EMPTY / probe stay nonempty at
  4Q?), the **8Q carve** lean count fixture (breadth rung 8, now unblocked).

## UPDATE 2026-06-12 (later) — two depth commits + the convergent probe-relativity spine

- **geometry-delta @3Q COMMITTED** (473a4a934, GENUINE_WITH_CAVEATS): nested 3Q geometry is
  PIN/PROBE-RELATIVE — moves under an alternate registry pin (L1 0.0218->0.0145, cross_pin
  stable=false), same-input null control exactly stable (0.0). Decorative z3/cvc5 crossover proofs
  demoted to supportive (blind audit caught: no verdict flip under input corruption). Engines
  honestly labeled (Julia + python_packet load_bearing; JAX/PyTorch supportive).
- **<=4Q nested tower COMMITTED** (0b33ffb07, GENUINE_WITH_CAVEATS): exact all-cut tower = 0
  (EMPTY), probe-relative tower = 466 (multiplicity ~1.58e22). Root axiom HOLDS + (operationally)
  STRENGTHENS at 4Q. "STRENGTHENS" = operational label, NOT a theorem token (audit caveat).
- **THE CONVERGENT FINDING:** across BOTH independent structures tested at depth — the nesting
  *tower* (exact EMPTY at 3Q/4Q, probe-only) AND the *geometry* (moves under alternate pin/probe,
  stable only for identical input) — the probe quotient (a=a iff a~b) is the LOAD-BEARING structure;
  the exact/convention versions collapse or move. The root axiom is not decoration: it is what makes
  the nested object non-empty and what fixes its geometry. Scratch/carrier-pins-relative ceiling holds.
- **IN FLIGHT:** 8Q carve audit (breadth); 5Q freeze/cut-states (the prerequisite that unblocks the
  <=5Q tower depth rung).

## ADDENDUM 2026-06-13 — three standing corrections

### (1) Probe-relativity interpretation WITHDRAWN (tower rows)

The "<=4Q tower exact-EMPTY / probe-466 = root axiom load-bearing / STRENGTHENS" interpretation
committed in the 2026-06-12 (later) update is **withdrawn**. Per
`system_v6/receipts/probe_relativity_overclaim_correction_20260612.md`: the 0-vs-466 contrast is
**definition-sensitive** — relaxing exact from both-sided to one-sided gives exact-OR=544 > 466
(probe). The "exact collapses, only probe survives" framing does NOT survive a reasonable definitional
variation. The COUNTS stand (exact-AND=0, probe=466, exact-OR=544; reproduced). The packets remain
valid `scratch_diagnostic` count fixtures. The "convergent probe-relativity spine / root axiom
STRENGTHENS at 4Q" language is demoted and must not be repeated.

### (2) DONE-vocabulary exception

Every `DONE` cell in this ledger means **DONE-as-scratch-valid**: `gate-N/A`, `scratch_diagnostic`,
`promotion_allowed=false`. No `DONE` row is `canonical-by-process`. The enforcement doc scratch
exception applies (see `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md` — scratch_diagnostic rows
are explicitly out of scope for the canonical-by-process gate; they earn a count-fixture / feedstock
label, not a canonical admission).

### (3) Engine-independence systemic finding (framing, not math)

~43 packets across the estate carry `"engine_consensus": {"independent": true}` where JAX and
PyTorch both call a shared `common.build_packet()` core — structural agreement, not independent
recomputation. This is a **framing overclaim** (severity: HIGH per the finding), NOT a math error;
the core results are not invalidated. Fix = a framing relabel at the shared-core call site; no
mass-regenerate required. Full discriminator + per-packet nuances: see
`system_v6/receipts/engine_independence_overclaim_systemic_20260612.md`.
