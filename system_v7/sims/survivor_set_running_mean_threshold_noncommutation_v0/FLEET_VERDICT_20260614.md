# Fleet verdict — noncommutation REAL, "emergence" framing stripped, rounding artifact fixed

**Full-fleet adversarial audit (wf w3lcat7qr): 9 verdicts, codex2 arbiter. Verdict = MIXED.** The restriction-noncommutation is REAL and survives; the "emergence" framing was an OVERCLAIM and is withdrawn; a rounding-convention artifact was caught and removed. scratch_diagnostic, promotion_allowed=false. Status: `passes local rerun` (exact + jax legs agree, 62/105). This is the HONEST, narrowed result — NOT the ratchet-emergence goal of task 14.

## Fleet roster + tally
codex2-high (MIXED), codex2-medium (MIXED), gemini-3.1-pro (GENUINE), deepseek-v4-pro (MIXED), qwen3.7-max (MIXED), claude-recompute-1 (MIXED), claude-recompute-2 (OVERCLAIMED). glm-5.1 + kimi-k2.6 = UNAVAILABLE (OpenRouter reasoning models exhausted max_tokens=4000 inside the reasoning channel before emitting a verdict — raise to >=12000 next time). Arbiter (codex2): **MIXED**, genuine_count=1, overclaimed_count=6, engineered_count=0.

## Confirmed overclaims (and the fixes applied)
1. **Rounding-convention artifact (the linchpin).** The original headline 44/105 used Python banker's `round(mean)`. Recomputation (claude-recompute-1, codex2, and my own pre-emptive check): **floor→0/105 (fully confluent), banker-round→44, half-up→32, ceil→62.** The choice of `round()` was undisclosed and load-bearing — it determined whether noncommutation existed at all.
   - **FIX:** switched to the REAL-VALUED mean (no rounding) — "survive iff your 1-count is at or above the running average." Convention-free: **62/105 with `>=`, 64/105 with `>`**, identical at N=5,6,7.
2. **"Emergence" overclaimed (6/7 reject).** Every returning verdict except gemini rejected or weakened the label; it is order-dependent survivor-set filtering under a natural state-reactive cut, not strong emergence.
   - **FIX:** all "emergence" claim keys renamed to `running_X_admits_order_dependence`; an explicit `emergence_label: REJECTED` note added; honest_scope rewritten.
3. **fixed_reference isolator is partly tautological.** Static predicates commute by set-intersection, so 0 is mathematically guaranteed — it CONFIRMS necessity of running-set dependence but is not independent causal evidence (codex2-high, both claude-recompute).
   - **FIX:** `tautology_caveat` added to the spec; the load-bearing content reframed onto the necessary-not-sufficient pair.
4. **"Robust across N" is weak.** The count is N-independent because it is fixed by the window-SIZE structure, not the configuration space (claude-recompute-1).
   - **FIX:** `robustness_caveat` added — the real robustness is convention-freeness + both inequality variants, not N.

## What genuinely survives (the narrowed, fleet-checked result)
- The noncommutation is REAL (unanimous): a natural state-reactive cut admits order-dependent survivor sets for a generic 62/105 window-pair fraction, convention-free.
- **State-dependence is NECESSARY (fixed_reference→0) but NOT SUFFICIENT:** `floor(mean)` — also a state-dependent threshold — is confluent (0), as are three other natural state-reactive families (ensemble-consistency, competitive-exclusion, minority). This **refutes qwen's strongest objection** ("any state-reactive threshold trivially noncommutes") — floor(mean) is a direct counterexample.

## Held divergences (preserved, not collapsed)
- **Overall:** gemini-3.1-pro alone calls it GENUINE with emergence justified; the other 6 returning verdicts call it MIXED/OVERCLAIMED while preserving the real noncommutation.
- **Isolator:** gemini/codex2-medium/deepseek/qwen say it isolates; codex2-high + both claude-recompute say it is a set-intersection tautology.

## Disposition (for task 14)
This sim does NOT earn the ratchet-emergence goal. It earns a narrow, honest, fleet-survived fact (state-reactive cut → generic order-dependence, necessary-not-sufficient). The strong "ratchet genuinely emerges from natural local rules" remains OPEN — and note this rule is NOT local (the mean is a global aggregate). The meta-lesson holds: the build→fleet loop FALSIFIES the inflated framing reliably (it stripped "emergence," caught the rounding linchpin); it did not hand back a strong positive. Cite THIS verdict, not the builder's self-claim.
