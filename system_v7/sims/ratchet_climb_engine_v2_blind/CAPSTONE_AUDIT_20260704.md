# Capstone audit — ratchet_climb_engine_v2_blind (2026-07-04, fresh context, read-only codex lane)

Overall: BY-CONSTRUCTION (second consecutive verdict on this claim family).

1. Drive facts: mostly fact-only (tick, mixedness, commutator/order-gap norms, persistence; no target_rung in facts).
2. Lift selector: NOT a search — fixed ordered candidate table with explicit "rung": 5,6,10,11; on threshold (commutator_norm>0 && persistence>=2 && mixed_split>0.2) returns candidates[0]. No per-candidate measured loss; rungs 6/10/11 never actually tested.
3. Engine legs: partial independence — native matrix drives, but numpy/jax share ratchet_climb_core.py and all three clone the same candidate table + selector predicate. Parity = cloned logic, not independent confirmation.
4. Rung 5: not a genuine forced lift; stopping at 5 honestly reported but 6 was never rejected by a search.

Honest ceiling: scratch_diagnostic — fact-only drive thresholds can trigger a prewired rung-5 receipt while controls stay at 4. NOT evidence of a forced lift or of three independent legs. promotion_allowed=false.

Pattern note (two audits deep): the defect keeps moving one layer down (v1: labeled demands; v2: labeled candidate table). The repair is a SPEC change, pre-registered for v3: (stage 1) a standalone SEPARATION-WITNESS module — given quotient Q_t and accumulated facts, MEASURE whether Q_t conflates fact-classes (no rung labels, own tests, audited before use); (stage 2) lifts enumerated from the ladder definitions, each evaluated by the witness, weakest separating lift selected by a computed presumption score. No candidate table anywhere in code.
