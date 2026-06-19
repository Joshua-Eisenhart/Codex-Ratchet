# BUILD CARD — round3_s2_alias_pass_v0 (light-symbolic phase 1, layer S2)

You are codex2 (builder, high). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build EVERYTHING inside system_v6/sims/round3_s2_alias_pass_v0/ (file-disjoint). NO git add/commit. Copy this card into the packet as build_card.md.

## Authority + scope
Registry: system_v6/receipts/round3_discriminator_registry_20260611.md (commit de44219ed) — READ IT IN FULL. This packet runs ONLY the S2 layer's LIGHT-SYMBOLIC alias pass (phase 1 of the two-phase rule). The heavy-local pass (S2.R3.5 leaf unions etc.) is NOT authorized here — classify it as open/queued if it survives. The registry's stop rule binds: if all representatives are aliases or known co-survivors, write the classification and STOP (no count inflation).

## The S2 candidates (from the registry table; pinned forms)
- S2.R3.0_committed: f=cos(2eta), g_phi=0, g_chi=0 (control/anchor)
- S2.R3.1_large_gauge_chi_shift: g_chi in {1/2, -1/2} (near-alias / convention-neighbor)
- S2.R3.2_same_curvature_shifted_holonomy: f=cos(2eta)+c, c in {1/4, -1/4}
- S2.R3.3_endpoint_chern_preserving_bump: f=cos(2eta)+eps*sin(2eta)^2, eps in {1/10, -1/10}
- S2.R3.4_two_leaf_holonomy_match: f=cos(2eta)+eps*cos(2eta)*(cos(2eta)-1/2), eps in {1/5, -1/5}

## The pass (exact symbolic, per the registry's phase-1 list)
1. Canonical forms + alias classes: exact symbolic simplification (sympy and/or Julia Symbolics — exact, no floats on the claim path), rational/surd comparison. Apply the registry's alias-detection rules for S2 (the MUB canonical-form lesson: aliases must be detected by canonical form, not by numeric closeness).
2. The expected-teeth rows per candidate (registry column): lifted holonomy convention pin + Stokes boundary gap for R3.1; leaf holonomy spectrum before Chern for R3.2; curvature density + annular Stokes for R3.3; expanded leaf holonomy vector (beyond eta=pi/6, pi/4) for R3.4. Compute each EXACTLY: does the teeth row separate the candidate from the committed anchor (excluded), collapse it into the anchor's class (alias), or leave it a genuine co-survivor (named as such, never silently merged)?
3. Closeness grading honored: report per-candidate verdict = alias / excluded-by-row-X / co-survivor-open, with the exact symbolic witness (the expression that differs or coincides).
4. Output the phase-2 queue: exactly which non-alias representatives remain open for the heavy-local pass (S2.R3.5 stays queued by cost class regardless).

## Controls: a deliberate alias (a pure reparameterization of the committed f must classify as alias, not co-survivor); a deliberate non-alias (wrong-sign f must be excluded by the first teeth row); the anchor must classify as itself.

## Engineering contract
Three engines per the TOOL_INTENT_MATRIX decided honestly (exact-symbolic dominant: Julia Symbolics reference + sympy in the JAX leg + PyTorch only where genuinely load-bearing — declare the honest mode rather than faking tensor work; if the honest mode excludes full PyTorch, run the generic validator without --require-pytorch and SAY SO), z3/cvc5 where a separation claim can be bound as computed UNSAT/SAT w/ a flip control, envelope via scripts/build_three_engine_envelope.py, packet validator, classification scratch_diagnostic, promotion_allowed=false, positive+negative+boundary sections. End by listing validator commands + ok statuses and the per-candidate verdict table.

## TOOL_INTENT_MATRIX

| engine | tool | role | load-bearing gate | positive case | negative/erased control | boundary case | demotion condition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| julia | Symbolics | Julia reference CAS for canonical `f`, `F=dA`, `c1`, holonomy and flux expressions. | Julia/SymPy canonical tuple parity. | Anchor and pure reparameterization simplify to one tuple. | Wrong-sign `f` differs on the first symbolic row. | Heavy-local S2.R3.5 is recorded as queued, not run. | If Symbolics cannot produce the tuple, Julia is not a reference lane. |
| jax | sympy | Exact symbolic workhorse in the Python/JAX lane; no floats on the claim path. | Per-candidate verdicts and canonical tuple hashes. | Anchor class contains anchor plus pure reparameterization only. | Non-alias controls and registry candidates separate by exact witness rows. | Surd leaves are carried exactly as symbolic strings. | If any verdict depends on numeric closeness, packet fails. |
| jax | z3 | SMT binding for finite rational separation rows and flip controls. | Positive exclusion facts are UNSAT under negation. | Expected nonzero rational witnesses are bound from computed rows. | Mutating the witness to zero flips to SAT. | Rational witness rows only; surd tuple comparison remains CAS-backed. | If z3 polarity is not UNSAT/SAT, packet fails. |
| jax | cvc5 | Independent SMT binding for the same rational separation rows and flip controls. | Agreement with z3. | Expected nonzero rational witnesses are bound from computed rows. | Mutating the witness to zero flips to SAT. | Rational witness rows only; surd tuple comparison remains CAS-backed. | If cvc5 disagrees with z3, packet fails. |
| pytorch | omitted | No graph/network/autograd/tensor claim path exists in this light-symbolic pass. | Honest omission in envelope; validator run without `--require-pytorch`. | Not applicable. | Decorative tensor work is forbidden. | PyTorch remains available for later graph/autograd packets only. | Adding PyTorch just to satisfy a count would be overclaiming. |
