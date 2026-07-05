# Capstone audit — ratchet_climb_engine_v1_drive (2026-07-04, fresh context, read-only codex lane)

Overall verdict: BY-CONSTRUCTION. The build+repair commits (4fb9a370d, f8b3cf1fb) overstate the claim.

Per question:
1. Demand minting: BY-CONSTRUCTION — minting appends pre-labeled target_rung 5/6 when commutator_norm>0 and persistence>=2 fire; lift mapped by rung number, not discovered (ratchet_climb_core.py:380, :576).
2. Engine legs: BY-CONSTRUCTION — jax+numpy wrap the same core.run_climb; julia hardcodes mixedness/order values, fires at tick 2 (not independent).
3. Kill controls: GENUINE-W-CAVEATS — real property removals, same outer path, but policy controls, not falsifiers of an independent lift selection.
4. Entanglement-mixedness: GENUINE-W-CAVEATS — Python computes real reduced-state purity; Julia canned; value only triggers the preassigned rung-5 demand.
5. Ledger repair: GENUINE-W-CAVEATS — admitted_receipts_only honest as bookkeeping; not evidence for the climb claim.

Strongest defect: rung identity embedded in minting and lift selection — measured drive facts trigger pre-labeled receipts rather than forcing rungs through an independent admissibility search.

Repair (pre-registered): fact-only drive events (no target_rung); blinded lift selector over candidate lifts; three genuinely independent engine derivations required to agree.

Honest claim ceiling: scratch_diagnostic showing a DESIGNED Axis-0 drive policy can produce frontier 6 while designed controls stop at 4. It does NOT prove Axis-0 genuinely forces rungs 5/6. promotion_allowed=false.
