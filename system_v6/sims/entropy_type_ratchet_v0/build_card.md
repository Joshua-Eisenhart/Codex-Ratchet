# BUILD CARD — entropy_type_ratchet_v0 (the owner co-ratchet doctrine made computable)

You are codex1 (builder, high). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build EVERYTHING inside system_v6/sims/entropy_type_ratchet_v0/ (file-disjoint). NO git add/commit. Copy this card into the packet as build_card.md. FILE BOUNDARY: never write audit_verdict.md (builder prose -> builder_self_assessment.md).

## The registered doctrine (READ FIRST: system_v6/receipts/owner_doctrine_entropy_type_ratchet_20260611.md, commit c98b29eb0)
As the constraint layers ratchet, the set of ADMISSIBLE entropy/information types ratchets with them, and the admissible operator families co-ratchet. This packet makes that computable on a committed ratchet sequence.

## The object
Take the committed ratchet sequence from manifold_unified_run_v0 (6903e0388: leaf -> lens -> terrain over the integrated n=3 seed) AND the deep-chain steps (ratchet_deep_chain_v0). At EACH step, compute the TYPE-ADMISSIBILITY TABLE:
- counting entropy (needs: finite support) — value or the NAMED missing structure
- chart-uniform differential entropy (needs: the chart/measure layer + the band-limit convention from manifold_entropy_ledger_v0)
- von Neumann entropy (needs: the density quotient S/~_M — an actual rho)
- conditional vN S(A|B) + mutual information (needs: a bipartition/subsystem split)
- coherent information I_c (needs: a channel/update map)
- the state-plus-record conservation account (needs: a constructed record/syndrome object, z4_syndrome_record_v0 convention)
For each (step, type): status = computable (the exact/numeric value, typed per the ledger) | undefined (the NAMED missing enabling structure — the computation must FAIL with that structure absent, never silently return a number) | degenerate (computable but trivially so — named why). PLUS the operator co-ratchet column: which probe/update families are admissible at each step (witnessed by an actual application or an actual named failure).

## The claims to earn (the doctrine's pre-registered predictions)
1. The admissible-type set changes at NAMED steps only (the enabling-layer table from the doctrine receipt reproduced computationally).
2. N01 ON THE TYPE LADDER: permute the constraint order -> the step at which types become admissible CHANGES (compute the availability sequence under at least 2 permuted orders; the difference is the witness).
3. The operator family co-varies at the same steps.

## Controls (must flip)
- premature-evaluation control: evaluating vN before the density quotient exists must raise/fail with the named missing structure (assert the failure mode, not a sentinel number); same for S(A|B) before the bipartition and I_c before the channel.
- order-shuffle (the N01 prediction): a shuffled layer order must change the availability sequence; if it does not, prediction 2 is KILLED and the packet reports that honestly.
- type-confusion control: a cross-type sum without a declared convention must be REJECTED by the packet's own ledger check (the typed-entropy discipline enforced in-packet).
- degenerate-flag control: a type that is computable-but-trivial before some step (e.g. S(A|B)=S(A) with a product state) must be flagged degenerate, not counted as substantive availability.

## Engineering contract
Honest TOOL_INTENT_MATRIX; three engines per honest mode (Julia reference w/ QuantumOptics-grade density/entropy computation + package_observables; JAX workhorse; PyTorch only if genuinely load-bearing — declare); typed values per manifold_entropy_ledger_v0 (the signed-lens-delta label convention carried); SMT binds the availability TABLE (the negated table identity UNSAT; a perturbed availability entry SAT) over computed statuses, not hardcoded; envelope via scripts/build_three_engine_envelope.py; validators in the honest combo + packet validator; classification scratch_diagnostic, promotion_allowed=false; positive+negative+boundary sections. End with the per-step type-admissibility table + every validator command + status.
