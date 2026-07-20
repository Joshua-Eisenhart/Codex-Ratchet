# Running the ratchet on the sim engines + Lev OS — operational wiring

Grounded in what exists this session: ratchet_engine.py (self-test PASS), fuel_gate/ and
claimgate/ (exit-code gates, ClaimGate lev-wired with a verified exec.gate.run event),
~100 tools integrated across Julia/JAX/PyTorch (system_v8/tool_ledger/TOOL_LEDGER.md), and
`lev exec/gate/trace`. Honest about the bridge that does not exist yet.

## Division of labor (who does what — nobody does two jobs)
| Component | Job in the ratchet | Concrete libraries / commands |
|---|---|---|
| LLM councils (Claude/codex/grok) | PRODUCE + VET fuel: candidate packages, probes, demand proposals. NEVER judge MSS. | Agent tool, codex, grok; fuel_gate/ audits the pool |
| Julia | Exact semantic OWNER: algebra, order/bracket, identity/reidentification witnesses, proof obligations, canon behavior traces | QuantumOptics, CliffordAlgebras, Octonions, ITensors, Z3.jl |
| JAX | Batched behavior: probe/perturbation/CONTINUATION sweeps at scale, evolvability tournaments | diffrax, quimb, vmap/jit, lineax |
| PyTorch | Learned/graph/basin/world-model candidate behavior | torch_geometric, geomstats |
| SMT (z3 + cvc5) | Admission law SAT_B(C) ∧ UNSAT_B(C∧¬φ); structural impossibility; invariant-agreement checks | z3-solver, cvc5 |
| Ratchet kernel | trace -> partition pi -> L_D -> coarsest-survivor frontier (the MSS operator). PURE CODE | system_v7/constraint_core/ratchet/ratchet_engine.py |
| Fuel gate + ClaimGate | Eligibility (HOLD if pool weak) + receipt admission. Exit codes only | fuel_gate/fuel_adequacy_gate.py, claimgate/claimgate.py |
| Lev OS | SCHEDULE, gate-by-verifier, replay, provenance, immutable receipts. NEVER judges MSS | lev exec/gate/trace; runtime-events.jsonl |

## Runtime, stage by stage — each stage is a Lev exec job gated by a verifier
Lev pattern (verified this session): `lev exec "<step>" --until="verifier passes"
--verifier="python3 <gate>.py <args>" --surface shell` runs the step, gates on the
verifier's EXIT CODE, and records an `exec.gate.run` evidence event (branch pass/fail,
exit code, artifact) in `~/.local/share/lev/events/runtime-events.jsonl`. So each gate
below is just an exit-code command Lev drives:

1. FUEL (LLM councils, OUTSIDE the ratchet) -> candidate packages + probes + demand proposals.
2. `lev exec` fuel_adequacy_gate.py -> exit 1 = HOLD_INSUFFICIENT_FUEL (current pool), exit 0 = proceed.
3. `lev exec` buildability: each candidate compiles + runs its own probes on Julia/JAX/PyTorch. Fail -> Purgatory, no comparison.
4. `lev exec` ENGINE TRACES: Julia (canon), JAX (sweep), PyTorch (learned) each emit finite behavior traces over probes + orders + brackets + perturbations + CONTINUATIONS + next-layer extension.
5. TRACE -> PARTITION bridge (code): two observations share a block iff identical behavior under all probes+continuations. Induces pi_C. [THIS IS THE MISSING PIECE.]
6. THICK D + identity controls: D = D_now ∪ D_persistence ∪ D_evolvability ∪ D_wholenest (persistence/evolvability/nesting emit demand pairs). Identity-honesty controls (relabel / alias split-merge / quotient-factorization x~y => T_h(x)~T_h(y)) run ON the engines (permute labels, replay) -> eligibility.
7. `lev exec` RATCHET KERNEL (ratchet_engine.py): L_D=0 survivors, coarsest-partition frontier, antichain, branches (dead-end -> Purgatory, re-merge allowed).
8. SEMANTIC CONCORDANCE + ADMISSION: Julia/JAX/PyTorch must agree on declared invariants (disagreement -> HOLD_IMPLEMENTATION_DISPUTE, not a vote); z3+cvc5 admission law; ClaimGate admits the receipt by exit code.
9. `lev trace` + evidence event = immutable receipt; Purgatory + renesting; next constraint packet.

## What exists vs the bridge to build
EXISTS: the partition-MSS kernel (self-test PASS); fuel gate + ClaimGate (exit codes; ClaimGate's exec.gate.run event verified in runtime-events.jsonl); ~100 tools integrated across the 3 engines; `lev exec/gate/trace`.
MISSING (the build order): (1) candidates as executable contract packages [ratchet_contract/ v0 building]; (2) the trace->partition bridge; (3) D thickened with persistence/evolvability/nesting demands; (4) the engines wired to emit COMPARABLE traces into the bridge; (5) Lev orchestration of the full stage sequence (only ClaimGate's single exec.gate.run demoed so far).

## One line
LLM councils make fuel -> Lev schedules engine jobs (Julia canon / JAX sweep / PyTorch learned) that emit behavior traces -> code induces partitions on a thick, identity-controlled D -> the partition-coarseness kernel computes the MSS frontier (branches / Purgatory) -> z3+cvc5 admit, ClaimGate gates, Lev records immutable receipts and replays. Lev runs it; code ratchets; LLMs never judge MSS.
