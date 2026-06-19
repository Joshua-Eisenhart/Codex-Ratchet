# BUILD CARD — spinor_network_surface_v1 (the genuine surface test; v0 died A_CHART_BY_CONSTRUCTION)

You are codex2 (builder, xhigh). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build EVERYTHING inside system_v6/sims/spinor_network_surface_v1/ (file-disjoint). NO git add/commit. Copy this card into build_card.md. FILE BOUNDARY: never write audit_verdict.md; set the no_builder_audit_verdict gate (the post-audit-idempotent pattern, f1907c814).

## Why v1 (read in order — every item below is binding)
1. system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md INCLUDING the v0 adjudication entry (f3d3ad1c1): v0's chart recovery was CIRCULAR (Pauli-axis seed patterns recovering their own cells) and its falsifier was unreachable. The doctrine is OPEN; v1 is its genuine test.
2. system_v6/sims/spinor_network_surface_v0/audit_verdict.md — ALL ten named caveats + the 11-item "What Surface v1 Must Add" list. EVERY item is a requirement here.
3. The repaired estate receipt (0dc215ad3 — consume the TRUE paths; quote the source lines for stored patterns + Hopfield construction).

## The core design rule (the anti-v0 spine)
SEPARATE THE CHART CLASSIFIER FROM NETWORK-STATE GENERATION:
- Predeclare the committed A-chart row set (the 33-cell structure) as the CLASSIFIER, fixed before any state exists.
- Generate stored patterns INDEPENDENTLY of the chart: use the estate's chiral quaternion pattern families (basin3, repaired paths) + at least one entangled (non-product) pattern family + one pinned-random family. NO Pauli-axis product-spinor seeds, NO chart-aligned construction anywhere in generation.
- The recoverability question is then real: do the terminal network states' single-site quotients land in nontrivial committed chart structure that was never injected? EITHER outcome is a result; report it honestly.
- NO-STRUCTURE CONTROLS THAT GENUINELY FAIL (test the falsifier fires): maximally mixed state, quotient-erased state, off-axis rotated states, a wrong-row classifier — each must produce recovery=FAIL through the real predicate (verify the failure branch executes; v0's was unreachable via a string mismatch).

## The remaining v1 requirements (from the audit's 11-item list, all binding)
- A REAL retrieval channel: explicit finite transition relation or a CPTP/Kraus/Lindblad-class map w/ trace + positivity + the exact update relation COMPUTED (no declarative admissibility).
- Trapping/absent-exit/escape evidence from the TRANSITION RELATION (graph evidence, not booleans over a seed set).
- Spurious-attractor search: exhaustive where feasible at this size, else bounded enumerated/sampled w/ a declared coverage denominator + negative controls. (Their absence on a small Hopfield carrier is suspicious — find them or explain.)
- The non-Hermitian control must break the SAME Lyapunov/monotone row the positive claim uses (or be demoted to sanity).
- Julia independently recomputes chart/basin/typed/SMT rows (no scalar stubs); JAX/PyTorch independent enough that agreement is not common-module echo (or the mode declared honestly); PyTorch load-bearing via autograd on the actual retrieval energy descent (or omitted honestly).
- Typed S(A|B) rows on a bipartition that can show non-product structure (the entangled pattern family makes this real); premature evaluation = structural failure (the entropy_type_ratchet_v1 standard, 60376bd9f).
- SMT binds computed values w/ non-tautological flips.

## Engineering contract
Honest TOOL_INTENT_MATRIX; envelope via scripts/build_three_engine_envelope.py; validators --require-pytorch --strict-source-backed --require-tool-intent (or honest subset, stated) + packet validator (post-audit-idempotent boundary) + pytest incl. a falsifier-reachability regression test; classification scratch_diagnostic, promotion_allowed=false; positive+negative+boundary sections; sizes per the resource guard. End with: the recoverability VERDICT (either outcome reported plainly), the basin partition w/ escape-graph evidence, the spurious-attractor table w/ coverage, every validator command + status.
