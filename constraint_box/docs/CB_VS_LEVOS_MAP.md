# ConstraintBox versus Lev OS map

This document maps relevant Lev OS, FlowMind, and three lev-os repositories to ConstraintBox. Leviathan can let an LLM or agent output become a final judge. ConstraintBox must keep LLM output proposal-only and let code-owned gates choose terminals and transitions.

## Core contrast

FlowMind has typed document validation, bounded execution, expression parsing, measurement scoring, registry generation, and formal proof-of-concept material. ConstraintBox has frozen FlowPolicy, typed nodes and transitions, six budgets, hook signals, terminals, receipts, and solver/tool paths. These are source-level `exists` findings unless a cited command reached `passes local rerun`.

## Capability map

| capability | Lev OS or FlowMind has | ConstraintBox has | boundary | deterministic build |
|---|---|---|---|---|
| FlowMind document parser/validator | lev-main/crates/lev-flowmind-compiler/src/parser.rs:4-20; lev-main/crates/lev-flowmind-compiler/src/document.rs:72-110 — Parses YAML into a typed FlowMindDocument and rejects empty names, missing entry, missing edge targets, and missing dependencies before compilation. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| FlowMind compiler | lev-main/crates/lev-flowmind-compiler/src/compiler.rs:5-45 — Validates a document and compiles it through registered CompilationTarget implementations into target outputs. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| FlowMind pure executor | lev-main/crates/lev-flowmind-compiler/src/executor.rs:7-21,52-112 — Carries cursor, variables, visit counts and total visits; routes by edge labels; stops on failed result or 10,000 total visits. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| FlowMind gate evaluator | lev-main/core/eval/src/gate-evaluator.ts:100-147,157-237 — Tries weighted formulas and parsed expressions, then semantic nodeExecutor, then first-branch fallback. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| FlowMind gate-expression engine | lev-main/core/eval/src/gate-expression.ts:1-35,91-239 — Function-free tokenizer/parser with strict equality, typed ordering, and explicit UNRESOLVABLE tri-state. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| proposal_readiness classifier | lev-main/core/eval/evaluators/proposal_readiness/companions/classifier.mjs:43-99,102-140 — Uses a provider.chat call to classify prose into typed items, then validates the output schema and forbids verdict/decision/pass fields. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| proposal_readiness scorer | lev-main/core/eval/evaluators/proposal_readiness/companions/sensor.mjs:70-150 — Counts typed items, resolves evidence refs, applies numeric floors, and derives accepted/needs_evidence/needs_rework. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| FlowMind audit meta-flow | lev-main/.lev/flows/lev-flowmind-audit.flow.yaml:16-150 — Runs deterministic shell probes, then prompt-driven domain lenses, normalization, synthesis and action emission; terminal is done. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| FlowMind registry extractor | lev-main/tooling/scripts/flowmind-registry.mjs:40-190 — Reads a manifest, extracts metadata/node/step/policy fields, categorizes paths, and writes JSONL registry entries. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| validation-gates catalog | lev-main/.lev/validation-gates.yaml:1131-1170,1500-1615 — Declares prompt-stack and runtime-contract gate catalogs; recursive parse found 16 direct gate:* definitions, 3 enforced and 13 declared. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| gate-eval campaign | lev-main/bench/gate-eval/gate-eval-campaign.flow.yaml:1-30; lev-main/bench/gate-eval/run-gate-eval.mjs:1-205 — Uses a deterministic kernel gate for some predicates and a Bonsai/local LLM semantic evaluator for others; outcome gate compares gate_accuracy >= 0.8. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| TLA+/Z3 FlowMind POC | lev-main/workshop/pocs/tlaplus-z3-flowmind/README.md:45-87; lev-main/workshop/pocs/tlaplus-z3-flowmind/z3/verify_c2_dag.py:25-98 — Models finitude, DAG/cycle detection, graph invariants and assume/guarantee coverage; exports FlowMind/spec-envelope graphs to GraphDocument. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| compiled runtime invariant guard | lev-main/workshop/pocs/tlaplus-z3-flowmind/runtime/z3_guard.py:3-9,45-106 — Compiles invariants ahead of runtime and checks state transitions with pure Python closures; the module states it does not invoke Z3 at runtime. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| agentguard lock manager | scratchpad/agent-lease/lib/lock-manager.js:22-99,106-172 — Creates a project/topic/current-HEAD lock, checks existence and proof marker, appends validation/proof data, and can archive/clear locks. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| agentguard runner | scratchpad/agent-lease/lib/runner.js:186-272,279-310 — Executes configured shell runners with a 600000ms timeout and stops on first failure; optional llm runners override passed from parsed LLM verdict. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| AgentPing core ping/HITL schema | scratchpad/agentping/packages/core/src/domain/ping.ts:242-333 — Defines pending/responded/expired/dismissed ping states and typed human approval/denial plus lease response data. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| AgentPing lease manager | scratchpad/agentping/packages/daemon/src/lease-manager.ts:56-188,310-375 — Tracks pending requests, approves/denies, waits with timeout, creates expiring HMAC tokens, revokes, and checks scope authorization. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| AgentPing runtime-intent approval bridge | scratchpad/agentping/packages/adapters/http-api/src/runtime-intent-approval.ts:75-185 — Requires non-renderer-executable mutation intent, converts approval-guarded mutations to step approval, and maps complete human approval to resume or otherwise hold. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |
| AgentPing HITL receipt builder | scratchpad/agentping/packages/dashboard-manager-server/src/routes/lev-hitl-decision.ts:55-164 — Validates action/actor/decision/evidence/proof/audit/lease/freshness and emits an append-only projection-only decision receipt; it does not perform the operational write. | MiniLevRuntime and FlowPolicy: constraint_box/src/constraintbox/mini_levos.py:204-220 | CB owns verdict and receipt authority | Use typed CB policy and code-owned gates |

## Deterministic replacement map

| LLM or permissive surface | what it decides | CB replacement | source |
|---|---|---|---|
| FlowMind semantic gate nodeExecutor | The semantic nodeExecutor output is interpreted as the branch result. | Encode the condition as FiniteConstraintProblem variables/constraints and call dual_solve; if it cannot be encoded, return HOLD/PARKED, not a branch. | lev-main/core/eval/src/gate-evaluator.ts:102-107,192-227 |
| FlowMind audit domain lenses/normalization/synthesis | Prompt files are used for domain analysis, normalization, synthesis and emitted remediation actions after deterministic probes. | Use schema validation plus rustworkx topology, exact SymPy budget arithmetic and receipt presence/hash checks; retain LLM output as proposal-only annotations. | lev-main/.lev/flows/lev-flowmind-audit.flow.yaml:97-138 |
| Bonsai semantic gate evaluator | A local LLM evaluates semantic predicates when the WASM path is not applicable. | Use the WASM/parser path for typed expressions; use finite schema/constraint encoding for semantic predicates; NONE_FOUND for unconstrained natural-language safety judgment. | lev-main/bench/gate-eval/run-gate-eval.mjs:1-18,43-188 |
| proposal_readiness classifier | The provider classifies proposal prose into acceptance, negative_case, constraint and evidence_ref items. | Replace prose classification with a required structured input schema and explicit caller-supplied typed items; validate with JSON Schema. If prose must be classified, NONE_FOUND within CB’s five tools. | lev-main/core/eval/evaluators/proposal_readiness/companions/classifier.mjs:64-99 |
| agentguard agent-proof release | The agent-authored proof text supplies runner statuses and is accepted unless a status is exactly FAIL. | Run configured shell validators and require exact exit-0 results; bind current diff/branch/hash and output hashes to the receipt. This is the high-severity fake-input finding above. | scratchpad/agent-lease/bin/agentguard.js:401-466 |
| AgentPing human approval | No LLM decides; the human response decides whether all required steps are approved and the bridge emits resume versus hold. | None for the human preference itself. CB can deterministically validate the typed response, required-step completeness, lease/proof/freshness and route HOLD on missing/partial input. | scratchpad/agentping/packages/adapters/http-api/src/runtime-intent-approval.ts:162-185; scratchpad/agentping/packages/core/src/domain/ping.ts:292-333 |
| FlowMind agent node | The compiler labels an agent instruction, but the external agent supplies its StepResult and edge label. | Keep agent generation proposal-only; validate its output against a typed schema and let CB-owned transition/solver gates choose the next state. | lev-main/crates/lev-flowmind-compiler/src/document.rs:44-58; lev-main/crates/lev-flowmind-compiler/src/executor.rs:126-132 |
| LLM-as-judge strategy surface | The strategy taxonomy explicitly includes llm-as-judge outcomes. | Use numeric measurement predicates, bounded replay and dual_solve; NONE_FOUND for open-ended semantic quality judgment without a finite contract. | lev-main/core/eval/src/strategy/types.ts:1-16,39-88 |

## Reusable deterministic primitives

| primitive | mechanism | CB use | source |
|---|---|---|---|
| typed finite graph document validation | Structural schema checks for entry, edge targets and dependencies. | Replace free-form flow acceptance with typed bounded node/edge/terminal schemas. | lev-main/crates/lev-flowmind-compiler/src/document.rs:83-109 |
| pure bounded step executor | State transition function with cursor, edge-label routing, visit counter and hard 10,000 total-visit bound. | Maps directly to FlowPolicy transitions, six budgets and terminal fail-closed behavior. | lev-main/crates/lev-flowmind-compiler/src/executor.rs:52-112 |
| tri-state expression parser | Function-free parser returns true/false/UNRESOLVABLE and routes unresolved comparisons to uncertain/probe/fail rather than silent false. | A schema-bound expression subset can be translated to FiniteConstraintProblem constraints; unresolved remains HOLD/PARKED. | lev-main/core/eval/src/gate-expression.ts:1-35,91-239; lev-main/core/eval/src/gate-evaluator.ts:246-304 |
| numeric evaluator policy | Counts typed observations, resolves refs and applies hard/warn floors deterministically. | Use the typed measurement/policy shape with CB-owned arithmetic and explicit claim ceilings. | lev-main/core/eval/evaluators/proposal_readiness/companions/sensor.mjs:70-150 |
| Z3/CVC5/enumeration consensus | Runs two symbolic deciders plus bounded enumeration and requires three definite execution-valid votes. | Direct CB authority for finite status/equivalence checks; no LLM verdict. | Codex-Ratchet/constraint_box/src/constraintbox/dualsolve.py:492-589 |
| finite enumerated constraint format | Nonempty finite domains, duplicate rejection, typed expression validation, bounded exhaustive SAT/UNSAT. | Canonical deterministic replacement for semantic-match or workflow-agreement judgments when both inputs can be encoded over one finite domain. | Codex-Ratchet/constraint_box/src/constraintbox/constraints.py:95-168 |
| Rustworkx topology projection | Canonicalizes a frozen FlowPolicy, rejects undeclared/duplicate nodes/transitions and validates bounded graph properties. | Direct replacement for DAG/reachability gate decisions. | Codex-Ratchet/constraint_box/src/constraintbox/mini_lev_topology.py:131-257; Codex-Ratchet/constraint_box/src/constraintbox/gate_operations.py:134-205 |
| TLA+/Z3 finitude and DAG proofs | Solver SAT/UNSAT checks for loop exit constraints and cycle detection with counterexample/unsat-core paths. | Direct proof-scout shape for finite budgets and graph invariants, bounded below CB’s five-tool authority. | lev-main/workshop/pocs/tlaplus-z3-flowmind/z3/verify_c1_finitude.py:41-160; lev-main/workshop/pocs/tlaplus-z3-flowmind/z3/verify_c2_dag.py:25-98 |
| compiled transition invariant checks | Precompiled pure functions check every proposed state pair, including terminal safety, with optional hashed cache. | A lightweight runtime guard can supplement, but not replace, CB’s authoritative transition gates. | lev-main/workshop/pocs/tlaplus-z3-flowmind/runtime/z3_guard.py:45-106; lev-main/workshop/pocs/tlaplus-z3-flowmind/runtime/invariant_compiler.py:45-50,164-178,215-238 |
| canonical input/output receipt hashing | Canonical JSON plus SHA-256 input/output and explicit gate verdict. | Directly matches CB’s receipt contract and prevents declaration-only gate claims. | Codex-Ratchet/constraint_box/src/constraintbox/gate_operations.py:1-5,83-92,102-131 |
| agent lease request/expiry/scope state | Pending request map, approve/deny transitions, waiter timeout, expiring signed token and deterministic scope matching. | Use only the ownership/expiry shape; CB must keep verdict/transition authority in MiniLevRuntime. | scratchpad/agentping/packages/daemon/src/lease-manager.ts:70-188,199-231,310-375 |

## Agent-lease lock and lease state machine

The source describes four states and several transitions. It is a candidate FlowPolicy, not a passing CB implementation.

| state | source-derived meaning |
|---|---|
| ABSENT | ABSENT: no current-HASH lock file; deny mode creates PENDING and release mode proceeds freely if absent (agent-lease/lib/lock-manager.js:74-99; agent-lease/bin/agentguard.js:401-407,469-480). |
| PENDING | PENDING: createLock writes LOCK_GUID, CREATED, PROJECT, TOPIC and STATUS=PENDING (agent-lease/lib/lock-manager.js:58-71). |
| VALIDATED | VALIDATED: releaseLock or releaseLockWithAgentProof appends AUDIT_PROOF_PASSED and STATUS=VALIDATED (agent-lease/lib/lock-manager.js:106-172,208-289). |
| ARCHIVED | ARCHIVED: archiveLock copies the current lock to .agentguard/audit and unlinks the active lock (agent-lease/lib/lock-manager.js:292-309). |

### Transitions

| transition | source-derived behavior |
|---|---|
| ABSENT -> PENDING | ABSENT -> PENDING: deny mode calls createLock when current lock does not exist (agent-lease/bin/agentguard.js:469-496). |
| PENDING -> VALIDATED | PENDING -> VALIDATED: release mode parses agent proof, checks configured names, rejects only exact FAIL, then calls releaseLockWithAgentProof (agent-lease/bin/agentguard.js:401-466). |
| PENDING -> VALIDATED | PENDING -> VALIDATED: legacy release can execute configured runners in runRunners and call releaseLock, but the agent-proof release path does not do so (agent-lease/bin/agentguard.js:401-466; agent-lease/lib/runner.js:279-310). |
| VALIDATED -> proceed | VALIDATED -> proceed: deny mode exits 0 when current lock contains AUDIT_PROOF_PASSED (agent-lease/bin/agentguard.js:469-475). |
| VALIDATED -> ARCHIVED | VALIDATED -> ARCHIVED: archiveLock copies then unlinks the active lock (agent-lease/lib/lock-manager.js:295-309). |
| PENDING -> cleared | PENDING -> cleared: clearLock/clearAllLocks unlink lock files, exposed as an explicit administrative clear operation (agent-lease/lib/lock-manager.js:179-194). |

### Stale and crash boundaries

No TTL or stale-state transition exists in agent-lease: CREATED is recorded but never age-checked; the filename follows current short HEAD, so a changed HEAD makes an older pending lock invisible to checkLock while enumeration can still find it (agent-lease/lib/lock-manager.js:22-99). A crash after createLock leaves the file PENDING because there is no finally/recovery transition in the lock manager; normal release checks only the current path and proof marker (agent-lease/lib/lock-manager.js:58-99; agent-lease/bin/agentguard.js:401-415). The missing stale policy is a logic-gap finding at `agent-lease/lib/lock-manager.js:22-99`. AgentPing supplies expiry and scope checks, but human preference remains a human decision.

## Required CB policy

- Treat FlowMind classifiers, semantic node executors, and agent labels as proposals.
- Encode bounded questions in FiniteConstraintProblem where possible.
- Use dual_solve for solver agreement, rustworkx for topology, SymPy for exact arithmetic, and Maude for rewrites.
- Route unresolved semantic questions to HOLD or PARKED. Never select a first branch as a verdict.
- Require fresh validator execution, exact exit status, current input identity, and receipt hashes before release.

## How to check this yourself

Run these commands from the repository root:

```sh
rg -n "nodeExecutor|first branch|UNRESOLVABLE" lev-main/core/eval/src/gate-evaluator.ts lev-main/core/eval/src/gate-expression.ts
rg -n "class MiniLevRuntime|class FlowPolicy|ELIGIBLE|BLOCKED|PARKED|HOLD|RELEASED" constraint_box/src/constraintbox/mini_levos.py
nl -ba agent-lease/bin/agentguard.js | sed -n "401,466p"
```
