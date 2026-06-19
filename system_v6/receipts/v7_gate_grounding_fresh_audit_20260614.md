# v7 Gate-Grounding — Fresh-Context Audit Findings (2026-06-14)

```yaml
receipt_kind: fresh_context_audit
status: FINDINGS — not CLEAN (3 blocking gaps in the recovery spec, caught pre-implementation)
audits: system_v6/foundations/v7_gate_grounding_law_DRAFT_20260614.md
claim_ceiling: doctrine draft; the law doc admits nothing; this receipt records what must be fixed before the gate refactor (task 6)
provenance: workflow w4lmqgaut (v7-gate-grounding-law); fresh-context fabrication-auditor, did not author the doc
```

## What is solid
- Per-gate grounding map: **10 of 14 gates** trace to a properly-defined axiom/constraint. The 4 pure schema/process validators (`validate_receipt`, `validate_sim_agent_role_cards`, `validate_wizard_loop_receipt`, `validate_wizard_worker_receipts`) are honestly flagged ungrounded.
- Owner-tunable forks **preserved, not collapsed** (`tension_preserved: true`): the root-sentence fork (relation-as-primitive vs constraint-as-primitive); the four cross-field readings; N01 weak-vs-strong.
- The doc self-flagged its own weakest point: `validate_math_only_packet.py` is **grounded-in-intent but inverted-in-form** (blacklist where the axiom-true form is the b_kernel definedness allow-list). No fabrication.

## Three blocking findings (must fix before the task-6 refactor)
1. **OVER-REJECTION RISK.** `L0_LEXEME_SET` = 19 primitives only. Standard math vocabulary (`holonomy, hopf, spinor, pauli, bloch, eigenvalue, curvature, connection, …`) is outside L0 and has no admitted-registry entry. A naive blacklist→allow-list inversion would reject the entire existing estate, GOLD included.
   - **Fix:** pre-populate the **admitted-math-term registry** with the standard vocabulary (each admitted via the proper TERM_DEF path, traceable to L0 + a definition) **before** the fence is applied. The fence is `L0 (19) + admitted-registry`, not `L0` alone.
2. **SCOPE CONFUSION (OVERLAY as output key vs primitive input).** Routing `OVERLAY_TERMS` (`entropy, geometry, information, symmetry, …`) to quarantine would break result-JSON keys in 100+ sims (`entropy_shannon`, `mutual_information`, `geometry_check`). Entropy/geometry are legitimate **derived measures to compute and key** — they are forbidden only as **primitive inputs/definitions**, per the axiom "entropy is a *later* admissible measure."
   - **Fix:** the definedness fence governs the **admission/definition surface** (what a sim is built from: formulas, primitive keys, definitions), **not** every computed output key. Draw that scope line explicitly in the gate.
3. **TWO DECORATIVE GROUNDING CITATIONS** (citation fixes, not fabrication):
   - `validate_estate_conventions.py` cites order-noncommutation/nonassociativity (1.3) but enforces finite-witness stability pins (sign/entropy-base/handedness) → cite **finitude (1.4)** only.
   - `validate_name_math_correlation.py` cites F01/N01 lineage (2.3) but enforces naming-surface discipline → cite **naming-surface/definedness (1.8)**; the F01/N01 ancestry check lives in `validate_v7_admission.py`, not here.

## Corrected recovery plan (supersedes Part 4 of the law doc)
- **Prerequisite:** build the admitted-math-term registry (standard math vocabulary admitted through TERM_DEF, each traceable to L0 + a definition).
- **Then** invert `validate_math_only_packet.py` to the definedness fence — scoped to inputs/definitions, not output keys.
- **Then** route through `validate_v7_admission.py` as "every term properly defined + every claim derived from admitted antecedents," tying ancestry to the b_kernel Stage-3 forward-reference (M(C) build-order embargo).
- Fix the two decorative citations in the grounding map.

Honest note: b_kernel mechanizes the **definedness + exclusion-first** axioms; it does **not** enforce the three root expressions (noncommutation/nonassociativity are SIM-layer). Do not overclaim the kernel proves order/grouping — it gates the vocabulary that may name them.
