# BUILD CARD - ring_checkerboard_automaton_v0 (the owner's pre-AI model, classical floor)

You are codex1 (builder, xhigh). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build EVERYTHING inside system_v6/sims/ring_checkerboard_automaton_v0/ (file-disjoint). NO git add/commit. Copy this card into build_card.md. FILE BOUNDARY: never write audit_verdict.md; set the no_builder_audit_verdict envelope gate.

## Authority (read in order)

1. system_v6/receipts/owner_doctrine_cellular_automata_ring_checkerboard_20260611.md (3d1932d8f) - the doctrine + falsifiers + the binding gate order (classical first; QCA/index = v1, NOT here).
2. system_v6/receipts/ring_checkerboard_provenance_20260611.md (b549de51f) - THE OWNER'S ACTUAL STRUCTURE (quoted verbatim from the pre-axes apple notes) + the draft build-card skeleton + the estate (the v4 checkerboard probes, the v6 support-graph scratch packet, the readout automaton's alternating/paired periodicity). REALIZE THE OWNER'S OBJECT, not a generic CA: nested checkerboard support w/ parity coloring, rings with DISCRETE STEPS (use the owner's named sizes - realize at least steps-per-ring in {4, 8, 16} w/ the design parameterized so 32/64 are reachable later), rings ATTACHED at ring steps (the nesting), flat mode (spinning mode = a later variant; say so).
3. system_v6/receipts/attractor_basin_criterion_20260611.md - the basin contract + THE GUARD in full.

## The object

A finite classical partitioned automaton on the owner's ring-checkerboard support: cells = ring steps (+ nested attached rings), parity coloring = the two update phases (even-phase then odd-phase local updates - the partitioned/two-phase scheme), an explicit LOCAL update rule per phase (the rule operates on a cell + its ring neighbors only - LOCALITY is the doctrine's named missing ingredient; the rule family should be small and pinned, not swept).
A. THE PHASE TEST (the doctrine's expectation 1): realize the two directed loop orders on the structure - the ALTERNATING phase pattern (deductive: even/odd/even/odd) vs the PAIRED/block pattern (inductive: blocks updated together) as two realized update disciplines; compute whether they yield distinguishable dynamics on the same support (terminal structure, orbit structure) under the declared probe family. The B constraints bind: both directed orders preserved; an order-shuffle control must CHANGE the dynamics (a realization where it does not is source-invalid).
B. THE BASIN CONTRACT: the full partition machinery on the automaton dynamics - SCCs, terminal classes w/ absent-exit proofs, may/must, Lyapunov/monotone observable IF one exists for the pinned rules (if none exists, say so honestly - do not invent one), the 7 negative controls (similarity-only MUST fail; non-partitioned scramble control: destroy the two-phase structure -> the dynamics must change, computed).
C. NESTING ROW (bounded): one attached-ring level (a ring attached at each step of the base ring, the owner's "each ring's discrete step would then have Ring attached") - does nesting change the terminal structure vs the bare ring (computed comparison)? No claims beyond one level.
D. MICROSTATE-COUNT ROW (the owner's stated purpose: "manage engine stages and micro states"): the state-count and terminal-count tables per steps-per-ring in {4,8,16} - reported as data, NO 64/engine claims (fenced; the engine placement is a later packet).

## Controls

non-partitioned scramble (must change dynamics), order-shuffle (must change), label-permutation (must NOT change counts), a frozen-phase control (only one phase updating -> the degenerate dynamics computed and flagged - the frozen-factor lesson applied proactively).

## Engineering contract

Honest TOOL_INTENT_MATRIX (graph machinery = genuine claim paths: Julia Graphs.jl reference + package_observables; JAX; PyTorch/PyG if genuinely load-bearing for the transition graphs - declare honestly); SMT binds computed terminal counts/phase separations (UNSAT + computed-perturbation flips, no tautological flips); envelope via scripts/build_three_engine_envelope.py; validators (honest combo) + packet validator (use the POST-AUDIT-IDEMPOTENT boundary pattern: assert the envelope no_builder_audit_verdict field, not file absence) + small pytest; classification scratch_diagnostic, promotion_allowed=false; positive+negative+boundary sections. Keep sizes small per the resource guard. End with: the phase-test verdict, the basin partition tables, the nesting comparison, every validator command + status.
