# BUILD CARD — carnot_szilard_landauer_ledger_v1 (the ledger-derived fence; v0's named gate)

You are codex2 (builder, high). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build EVERYTHING inside system_v6/sims/carnot_szilard_landauer_ledger_v1/ (file-disjoint). NO git add/commit. Copy this card into build_card.md. FILE BOUNDARY: no audit_verdict.md; set the no_builder_audit_verdict gate.

## Authority
The committed v0 fence (carnot_szilard_landauer_fence_v0, e10273983) + its audit verdict: CAVEATED CLASSICAL FENCE PASS — the named gate: efficiencies/costs were PINNED COEFFICIENTS, not derived from cycle ledgers; the SAT model witness was not persisted; the N01 control was Julia-only graph-computed. THIS packet closes those three gaps. Classical-boundary lane: classical_baseline ceiling, never nonclassical evidence.

## The object
1. LEDGER-DERIVED ROWS: explicit finite cycle ledgers (per-stroke heat/work entries as exact rationals over pinned T_h=2, T_c=1) for: a reversible Carnot cycle (eta DERIVED from its own ledger = 1 - T_c/T_h), a sub-Carnot irreversible cycle (a pinned loss entry; eta derived < eta_C), a candidate super-Carnot cycle (the ledger that WOULD be needed — its constraint violation derived, UNSAT from the ledger constraints not from an asserted bound), the Szilard cycle w/ the measurement/erasure ledger entries (work k T ln2 derived; the unpaid-erasure variant UNSAT from the ledger), below-Landauer erasure UNSAT likewise.
2. PERSISTED WITNESSES: every SAT row persists its solver MODEL in the result JSON (the broken-fence control's super-Carnot model w/ its numeric eta > 1/2 extracted and stored).
3. THE N01 CONTROL upgraded: the order-sensitivity (measure->feedback->erase vs permuted) computed in ALL claim-bearing lanes (not Julia-only).
4. The connection row carried from v0 (the Landauer-vs-quotient-record labeled observation, co-citing the conservation pair) — unchanged convention language.

## Controls: broken-fence (drop the ledger constraint -> super-Carnot SAT w/ persisted model); equality boundary (reversible limit SAT, convention named); typed bits/nats conversion explicit; a mis-ledgered control (an entry deliberately omitted -> the packet's own consistency gate must catch it).

## Engineering contract
Honest TOOL_INTENT_MATRIX (exact rational arithmetic Julia reference; SMT z3+cvc5 load-bearing on the LEDGER constraints — this is the rare packet where the solvers ARE the primary instrument, derive don't assert; PyTorch honest mode); envelope via scripts/build_three_engine_envelope.py; validators (honest combo, the v0 precedent ran w/o --require-pytorch w/ the omission stated — same honesty here) + packet validator + pytest; classification classical_baseline / scratch_diagnostic, promotion_allowed=false. End with the per-cycle ledger tables + persisted witnesses + every validator command + status.
