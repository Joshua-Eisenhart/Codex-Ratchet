# BUILD CARD — round3_s4_heavy_discriminator_v0 (phase-2 HEAVY-LOCAL pass, layer S4 only)

You are codex2 (builder, high). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build EVERYTHING inside system_v6/sims/round3_s4_heavy_discriminator_v0/ (file-disjoint). NO git add/commit. Copy this card into the packet as build_card.md.

## Authority + scope
The round-3 LIGHT program is complete (committed: S2 bc22216bc, S3 b5e30224d, S4 fe09e11cb, S5 8980e3b2e, S6/S7 fe3c3ffc4, S9 2dd6a87cf). The consolidated heavy queue lives in system_v6/sims/round3_s9_alias_pass_v0/audit_verdict.md ("Consolidated Round-3 Heavy Queue On Disk") — READ IT + the registry de44219ed (S4 heavy teeth definitions) + the S4 light verdict (round3_s4_alias_pass_v0/audit_verdict.md, the per-candidate demotion table + the Choi/Kraus-depth caveat). This packet runs ONLY the FOUR queued S4 heavy rows:
- S4.R3.1_z_amplitude_damping_pair — N01/commutator + fixed-axis rows
- S4.R3.2_x_amplitude_damping_pair — z-probe quotient descent/mortality
- S4.R3.3_dephase_rotate_hybrid — shell preservation/leakage then N01
- S4.R3.5_weak_nonunital_pauli_channel — fixed-axis + Choi positivity
NO other layer's heavy rows; the registry stop rule + cost guard bind.

## The heavy teeth (per the registry: these are the rows the light pass could NOT run)
1. CHOI SPECTRA: exact Choi matrices for each candidate channel pair vs the committed anchor DzDxRxRz (pinned parameters from geo_s4: lambda=7/10, p=3/20); eigenvalues as exact algebraic numbers where feasible, else certified rational intervals labeled as bounds. Choi positivity verified per candidate (R3.5 especially).
2. N01/COMMUTATOR ROWS: the order-gap signature (Z-then-X vs X-then-Z pattern per the repo's N01 discipline) computed exactly per candidate; the full N01 signature where the queue names it.
3. z-PROBE QUOTIENT DESCENT/MORTALITY: does the candidate descend to the committed quotient and preserve/break the mortality rows (the light pass's pinned z-probe convention carries — label pin-relative results per the S2 rule).
4. SHELL PRESERVATION/LEAKAGE (R3.3): exact computation of shell-restricted action; leakage = computed, not asserted.
5. PER-CANDIDATE FINAL VERDICT: excluded-by-<named-heavy-row> w/ exact witness / genuine co-survivor (earns the label ONLY now, with this packet as the citable receipt) / convention-pinned + reopenable. Never silently merge; the vocabulary standards from all six light verdicts bind.

## Controls: the anchor must pass every heavy row it defines (self-consistency); a deliberate alias (reparameterized anchor) must remain alias under heavy teeth; the light pass's excluded R3.4 must stay excluded if re-tested (regression row); SMT (z3+cvc5+Julia Z3) binds computed Choi/commutator/quotient values w/ UNSAT + perturbed SAT flips.

## Engineering contract
Three engines per honest TOOL_INTENT_MATRIX (heavy rows have real numeric/spectral content: Julia reference w/ exact/QuantumOptics-grade computation + package_observables; JAX workhorse; PyTorch ONLY if a genuine tensor/autograd claim path exists — declare honestly), envelope via scripts/build_three_engine_envelope.py, validators (state the honest flag combo), packet validator, classification scratch_diagnostic, promotion_allowed=false, positive+negative+boundary sections. Mind the machine: this is heavy-LOCAL — keep matrix sizes finite/pinned, no sweeps beyond the registry's named rows. End with the per-candidate verdict table + every validator command + status.
