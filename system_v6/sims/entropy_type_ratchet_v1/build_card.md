# BUILD CARD — entropy_type_ratchet_v1 (the DISCOVERY design; v0 died BY_CONSTRUCTION)

You are codex1 (builder, xhigh). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build EVERYTHING inside system_v6/sims/entropy_type_ratchet_v1/ (file-disjoint). NO git add/commit. Copy this card into build_card.md. FILE BOUNDARY: never write audit_verdict.md; set the no_builder_audit_verdict gate.

## Why v1 (read first, in order)
1. system_v6/receipts/owner_doctrine_entropy_type_ratchet_20260611.md INCLUDING the v0 adjudication entry (b6e150c78): v0 = BY_CONSTRUCTION because a hand-written PRIMARY_STEP_PLAN declared the enables. THE BINDING DESIGN RULE FOR v1: **no declared enables lists anywhere on the claim path.**
2. system_v6/sims/entropy_type_ratchet_v0/audit_verdict.md — the full failure analysis (what was earned: the in-packet N01 mechanics; what was not).

## The discovery design
Maintain ONE actual evolving state object (consume the manifold_unified_run_v0 mechanism: the integrated n=3 seed + its ratchet sequence leaf -> lens -> terrain, extended by the deep-chain Z4/Z2 lens steps). At EACH step, for EACH type, the packet ATTEMPTS THE CONSTRUCTION of the enabling object from the actual current state artifacts:
- counting entropy: enumerate the actual finite support — succeeds iff the support object exists.
- chart/differential entropy: construct the chart measure from the actual chart object — succeeds iff the chart layer has been applied to THIS state.
- vN: construct rho by the actual quotient map (partial trace / density quotient applied to the live state vector) — before the quotient step the construction must fail because the quotient map object is absent from the state lineage, and the failure is CAUGHT with the named missing structure extracted from the exception path, not from a lookup.
- conditional vN / MI: construct the actual bipartition (tensor factorization of the live state) — fails before a factorization exists; degenerate-flag computed when the factorization yields a product state.
- coherent information: construct the actual channel object from the step's update map — fails before an update map exists in the lineage.
- state-plus-record: construct the syndrome table from the actual lens preimages (the z4_syndrome_record_v0 convention) — fails before a lens with preimage structure exists.
AVAILABILITY = the computed construction outcome (success w/ the typed value / failure w/ the structurally-extracted missing object / degenerate w/ the computed witness). The operator co-ratchet column likewise: ATTEMPT the operator application (e.g. a CPTP map needs rho — apply it and record success/failure), never a requirement map.

## The predictions (from the doctrine receipt — now genuinely testable)
1. Availability changes at the steps where construction starts succeeding — compare the DISCOVERED table against the doctrine's enabling-layer table: agreement = the doctrine's table earned; disagreement = a FINDING (report which row, never smooth).
2. N01 on the type ladder: permute the actual constraint application order (the real operations on the real state, not step dicts) — the discovered availability sequence must change; cite both sequences.
3. Operator co-ratchet: the attempted-application outcomes co-vary with the same steps.

## Controls
- The premature-evaluation control is now STRUCTURAL (the heart of the discovery design): show one full failure object per type (the caught construction failure naming the missing structure).
- A spoofed-enable control: inject a declared-enable shortcut for one (step,type) and verify the packet's own validator REJECTS it (the anti-v0 regression gate).
- Type-confusion (cross-type sum rejected), degenerate-flag (product-state S(A|B)), order-shuffle per prediction 2.

## Engineering contract
Honest TOOL_INTENT_MATRIX; three engines (Julia reference w/ QuantumOptics density/entropy machinery + package_observables; JAX; PyTorch where genuinely load-bearing); typed values per the ledger; SMT binds the DISCOVERED table (negated identity UNSAT; a computed-perturbation SAT flip through the construction path — the 2ad726598 standard: no tautological flips); envelope via scripts/build_three_engine_envelope.py; validators --require-pytorch --strict-source-backed --require-tool-intent (or honest subset, stated); packet validator + pytest incl. the anti-v0 regression gate; classification scratch_diagnostic, promotion_allowed=false; positive+negative+boundary sections. End with the discovered per-step table + the doctrine-table comparison + every validator command + status.
