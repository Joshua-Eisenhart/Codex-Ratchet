# V8 First-Rung Gate Status

Status timestamp: 2026-07-15. Scope: `tolerance_to_equivalence_ratchet_rung_v0` only.

## Earned green

| Gate | Result | Code evidence |
|---|---|---|
| G0 preregistered object | PASS | Frozen spec/object-card hashes and pre-builder receipt validate |
| G1 exact census | PASS | Julia, JAX, and PyTorch reproduce the frozen `n=1..5` counts |
| G2 three-engine closure | PASS | Both fixtures agree exactly; numeric divergence is zero |
| G3 dual SMT | PASS | z3 and cvc5 independently return SAT/UNSAT/UNSAT/SAT |
| G4 coface drive | PASS | Loss changes `1 -> 0`; drive is `1` |
| G5 tooth/HOLD controls | PASS | Positive commits; reverse/null/universal/scrambled/flat HOLD |
| G6 plural MSS | PASS | Complete two-element nondominated antichain returned |
| G7 closed lanes | PASS | Engine outputs declare and validate no peer-result reads |
| G8 source/runtime/ceiling | PASS | Sources, results, runtimes, scratch classification, and ceiling are bound |
| G9 validator/mutations | PASS | Five coherent tamper envelopes are rejected |
| G10 deterministic Lev replay | PASS | Four `lev.validate` gates pass under the pinned no-model executor |

The final code decision is `COMMIT_ONE_BOUNDED_SCRATCH_TOOTH`; the state is `TOOTH_1_COMMITTED_SCRATCH`.

## Preserved red and blocked launch conditions

| Boundary | Current state | Consequence |
|---|---|---|
| Commit binding | New packet is source-hash-bound but still untracked in an isolated worktree | Not a clean-tree release receipt |
| Lev ProofBundle | `proof_backed_execution=false`; no runtime caller wrote a ProofBundle | Official launch remains blocked |
| Lev evaluator | Advisory evaluator red is retained | No proof-backed promotion claim |
| Full tool estate | Historical 95 operational passes and 29 edges bind an older Ratchet tree | Not current V8 evidence |
| Baseline regressions | One old deep-stack golden is tree-bound; one legacy Wizard v4.2 validator is absent | Historical suite is not all green |
| Skill inventory | Claude-agent inventory expectation is red and installed/repo skill parity drifts | General skill-update claim blocked |
| Claude bridge task | Fable 5 alias/auth/backend resolved, but the capped smoke ended `error_max_budget_usd` | Bridge completion is red; never a gate |
| Provider control plane | NVIDIA and xAI are not admitted as deterministic gate authorities | Quota/model drift cannot affect a tooth |
| Scientific/general claim | Held-out families, canonical QIT carrier, and theorem-level generalization are absent | No formal, release, or scientific promotion |

## Lev boundary

The pinned clean executor is `/Users/joshuaeisenhart/lev-main/.worktrees/eval-projection-contract/core/poly/bin/lev` at commit `856acb1a5de42528a9a54272435d98a9fe226186`, tree `3f3488781d48a64b22c43c08ccfaa2b503d49524`, executable SHA-256 `f258ae313d515cae4ff848a45df78cfcc6a2d48c9ce1ade9c316276b00ef0c61`.

Lev is accepted here only as deterministic orchestration. Bare `lev` resolves to another checkout. Empty commands, `fail_closed:false`, arbitrary failure terminals, mutable runtimes, model/provider commands, and absent negative controls are rejected by the packet's static flow validator before execution.

## Claim ceiling

The strongest allowed sentence is:

> One bounded finite tolerance-to-equivalence scratch tooth passed G0-G10 on frozen fixtures under independent Julia, JAX, PyTorch, z3, cvc5, controller, mutation, and no-model Lev checks.

Nothing in this packet licenses the sentence “V8 is launched” or “the Ratchet/QIT theory is proven.”
