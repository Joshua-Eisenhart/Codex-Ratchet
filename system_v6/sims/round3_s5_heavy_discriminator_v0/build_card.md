# BUILD CARD — round3_s5_heavy_discriminator_v0 (phase-2 HEAVY-LOCAL pass, layer S5 only)

You are codex2 (builder, high). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build EVERYTHING inside system_v6/sims/round3_s5_heavy_discriminator_v0/ (file-disjoint). NO git add/commit. Copy this card into the packet as build_card.md.

## Authority + scope
Consolidated heavy queue: system_v6/sims/round3_s9_alias_pass_v0/audit_verdict.md — READ IT + the registry de44219ed (S5 heavy teeth) + the S5 light verdict (round3_s5_alias_pass_v0/audit_verdict.md — the normalized table: 8 rows open + queued-heavy-local) + the first heavy precedent round3_s4_heavy_discriminator_v0 (and its audit_verdict.md if present — it sets the heavy-pass standard: exact witnesses per registry-named row, pin_relative honesty, co-survivor labels mintable ONLY here w/ this packet as the citable receipt). This packet runs ONLY the EIGHT queued S5 rows:
- S5.R3.1_alpha_mix_rotation_contraction alpha in {1/4, 1/2, 3/4} — mirror structure + N01 full signature
- S5.R3.2_committed_coeff_epsilon +/-1/20 — fixed-point/basin + N01 gap
- S5.R3.3_nonunital_weak_shift +/-1/20 — validity, fixed point, quotient 56/56
- S5.R3.5_basin_preserving_null — quotient survival + time-flow/N01 row
NO other layer's rows; stop rule + cost guard bind. Keep everything finite/pinned (33-cell grid where basin rows appear; exact rationals/surds; no parameter sweeps beyond the named values).

## The heavy teeth (per registry; anchors = the committed geo_s5 pinned A,b rows + the basin campaign's committed objects)
1. MIRROR STRUCTURE (R3.1 trio): the Ni/Si mirror-frame classification computed exactly per alpha (the S5 light pass's one exclusion R3.4 died on this row — these three carry the alpha-mixed version); N01 FULL SIGNATURE: the complete order-gap signature (not just one pair) per candidate vs the anchor.
2. FIXED-POINT/BASIN (R3.2 pair): exact fixed-point displacement vs the committed anchors; basin rows ON THE 33-CELL GRID per the committed transition-graph machinery (terminal classes w/ absent-exit proofs) — CHART-RELATIVE labels mandatory (fe3754782 rule); the N01 gap exact.
3. VALIDITY + QUOTIENT 56/56 (R3.3 pair): CPTP/positivity validity computed; the quotient 56/56 row per the registry's definition (read it carefully and quote it in the packet).
4. QUOTIENT SURVIVAL + TIME-FLOW (R3.5): does the null candidate survive the committed quotient and reproduce the time-flow/N01 row, or separate?
5. PER-CANDIDATE FINAL VERDICT: excluded-by-<named-heavy-row> w/ exact witness / GENUINE CO-SURVIVOR (mintable only here, this packet = the citable receipt; a minted co-survivor must list every heavy row it passed) / convention-pinned + reopenable. Vocabulary standards from all committed verdicts bind.

## Controls: anchor self-passes all its heavy rows; deliberate reparameterized-anchor alias remains alias under heavy teeth; the light pass's R3.4 mirror exclusion stays excluded (regression); SMT (z3+cvc5+Julia Z3) binds computed values w/ UNSAT + perturbed SAT flips.

## Engineering contract
Honest TOOL_INTENT_MATRIX (basin/graph rows MAY give PyTorch a genuine claim path via torch_geometric — decide honestly and declare; Julia reference w/ Graphs.jl/exact arithmetic + package_observables; JAX workhorse), envelope via scripts/build_three_engine_envelope.py, validators in the honest flag combo (+ the expected-negative check if PyTorch omitted), packet validator, classification scratch_diagnostic, promotion_allowed=false, positive+negative+boundary sections. End with the per-candidate verdict table + every validator command + status.
