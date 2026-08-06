# ConstraintBox Capability Execution Matrix

## Boundary

ConstraintBox is the deterministic harness.  CPython, the request gate,
Z3/CVC5 plus the bounded enumeration reference, typed Mini-LevOS transitions,
and receipt verification are inside its local controller boundary.  Simulation
engines are external workloads.  They are never imported as the CB kernel and
their output cannot choose a gate, transition, retry, release, promotion, or
claim ceiling.

```text
explicit user request
  -> CPython request shape + Z3/CVC5/enumeration agreement
  -> controller-selected fixed capability profile or formal task
  -> controller-derived Rustworkx topology preflight where the fixed proposal route applies
  -> Mini-LevOS TOOL/PROPOSAL observation -> deterministic GATE validation
  -> hash-chained flow receipt + independent replay
  -> bounded external-capability result or bounded local release route

No LLM or external engine chooses an arrow in this chain.
```

The user can authorize a named fixed profile in a request.  That is not an
ability to supply code, a module, executable, worker, function, challenge,
gate, tolerance, transition, retry budget, or disposition.

## Runtime roles

| Layer | What actually runs | Authority |
|---|---|---|
| CPython | The explicit local interpreter and ordinary bounded reference algorithms | Executes controller code; it is not an implicit library or a solver substitute. |
| NumPy | Explicit support library for the PySINDy capability and other selected numeric adapters | Not a default semantic gate or a substitute for SMT; its concrete use is receipt-bound. |
| Request gate | Typed request intake, bounded enumeration, Z3, CVC5, clause feedback | Accepts or parks the input shape; no LLM judgment. |
| Core formal tools | Z3, CVC5, SymPy, Rustworkx, Maude, and CPython reference checks | Deterministic, bounded checks selected by controller policy; Maude is one bounded subprocess task, never a general executor. |
| Mini-LevOS | Typed `TOOL -> GATE` capability flows and `topology-preflight -> PROPOSAL -> GATE -> ClaimGate` proposal flow, fixed transitions, budgets, hash-chain ledger, receipt replay | Selects transitions and terminal state; hooks only return typed observations/signals. |
| Leviathan dry-run reference | Optional isolated `lev exec --dry-run` observation of `sdlc-exec-validate`, a narrow run-seal normalizer, source-shape correspondence, and negative dry-run-boundary controls | `EXTERNAL_NOT_CB_KERNEL`; the Lev flow, model, provider, evaluator, and escalation path cannot select a CB transition, gate, retry, release, or promotion. |
| External capabilities | fixed PyTorch, JAX, PySINDy, Julia, SciPy, Diffrax, graph/topology crosscheck, PyDMD, PyMDP, PyKoopman, Quimb/Cotengra, e3nn, and two named cross-engine profiles | Return bounded evidence only; `EXTERNAL_NOT_CB_KERNEL`. |
| Advisory LLM/provider sidecars | Optional NVIDIA/OpenRouter explanation route | Post-decision explanation only; zero authority over any previous result. |

## Fixed external capability profiles

| ID | Real operation | Mini-Lev flow | Required controls | Ceiling |
|---|---|---|---|---|
| `pytorch-jacobian-v1` | `torch.func.jacrev` on CPU float64 | fixed PyTorch tool then gate | positive, wrong-value, boundary | One bounded Jacobian operation; not PyTorch or estate readiness. |
| `jax-autodiff-v1` | `jax.grad`, `jax.vmap`, `jax.jit` under x64 | fixed JAX tool then gate | positive, wrong-value, boundary | One bounded JAX operation; not JAX or estate readiness. |
| `pysindy-affine-generator-v1` | `pysindy.SINDy.fit` and `predict` on a controller-built affine generator | fixed PySINDy tool then gate | positive, wrong-value, boundary | One bounded system-identification candidate operation; not a CR result. |
| `julia-diffeq-v1` | `DifferentialEquations.ODEProblem`, `solve`, `Tsit5` | fixed Julia tool then gate | positive, wrong-value, boundary | One bounded ODE operation; not Julia or estate readiness. |
| `scipy-expm-rotation-v1` | `scipy.linalg.expm` on a bounded rotation generator | fixed SciPy tool then gate | positive, wrong-value, boundary, semantic replay, operation poison | One bounded matrix-exponential operation; not SciPy or estate readiness. |
| `diffrax-tsit5-affine-flow-v1` | `ODETerm`, `Tsit5`, `PIDController`, `diffeqsolve` | fixed Diffrax tool then gate | positive, wrong-value, boundary, semantic replay, operation poison | One bounded ODE flow; not Diffrax, JAX, or estate readiness. |
| `pydmd-discrete-rate-v1` | `DMD.fit`, `eigs`, `reconstructed_data` | fixed PyDMD tool then gate | positive, wrong-value, horizon boundary | One bounded discrete-rate decomposition; not PyDMD or estate readiness. |
| `pymdp-two-state-inference-v1` | `Agent.infer_states`, `infer_policies` | fixed PyMDP tool then gate | positive, wrong-value, alternate-observation boundary | One bounded two-state inference operation; not PyMDP or estate readiness. |
| `pykoopman-identity-edmd-v1` | `Koopman.fit`, `predict`, `EDMD.fit` with fixed Identity+EDMD | fixed PyKoopman tool then gate | positive, wrong-value, zero boundary | One admitted PyKoopman surface; not full PyKoopman or estate readiness. |
| `quimb-cotengra-bounded-suite-v1` | Quimb density APIs plus Cotengra `HyperOptimizer.search` | fixed combined tool then gate | positive, wrong-value, boundary, row operation poison, receipt replay | Two bounded tensor-network operations; not Quimb/Cotengra or estate readiness. |
| `multiengine-dlpack-diffeq-v1` | CPU `torch.func.jacrev` then real Torch DLPack to JAX, plus an independent strict-carrier Julia DifferentialEquations solve | fixed cross-engine tool then gate | positive, wrong, boundary, operation-severance, semantic replay | One controller-bound cross-engine diagnostic; not general engine readiness or a canonical/CR sim. |
| `e3nn-wigner-crosscheck-v1` | `e3nn.o3.wigner_3j` on the fixed triples (1,1,0) and (1,1,2), CPU float64 | fixed e3nn tool then gate | positive, wrong-value, selection-rule boundary, seed-scale binding, operation poison | One bounded Wigner-3j crosscheck; not e3nn or estate readiness. |
| `basic-packet-cross-engine-v1` | existing fixed JAX, PyTorch, PySINDy, Julia packet and the PySINDy-to-Julia artifact consumer | fixed legacy packet tool then gate | embedded packet recomputation, source/artifact binding, Mini-Lev receipt validation | One legacy fixed-fixture diagnostic. Its JSON handoff is explicitly not a scientific DLPack bridge, readiness result, or full-stack result. |

Every profile binds controller-selected input or, for the explicitly labelled
legacy packet, an immutable fixed fixture. It pins its local source and runtime
surface, runs its named real API, writes a two-node Mini-Lev flow ledger, and
validates that receipt before it is reported as `ELIGIBLE`. The controls in the
table are exact: a wrong-value rejection is not a second wrong-engine
execution, and replay or operation-poison evidence is only claimed on the rows
that record it.

## Public routes

| Route | Purpose | Does not mean |
|---|---|---|
| `constraintbox capability-box` | The actual narrow front door for the fixed PyTorch profile. It captures user/context artifacts, runs the Mini-Lev flow, then independently verifies the nested flow and capability artifacts. | LLM proposal acceptance, release, engine readiness, CR truth, science, or canonical status. |
| `constraintbox engine-test --capability ID` | Static test-only dispatch for one of the fourteen fixed profiles. It does not accept custom Python or worker arguments. | A user/LLM selected tool or a generic proposal handoff. |
| `constraintbox capability-suite` | Controller-selected sequential run of all fourteen fixed Mini-Lev capability profiles. It has no component, worker, gate, or parallelism override. | A general capability, a combined scientific claim, engine readiness, release, or promotion. |
| `constraintbox engine-test` with no capability | Legacy broad external-estate diagnostic. It proves named operations and the bounded PySINDy-to-Julia artifact handoff on that run. | CB core, a lean default path, full sim-engine readiness, or a scientific result. |

The broad diagnostic remains useful as a test target for CB.  It must stay
outside the kernel and must not be substituted for individual capability
receipts.

## Current integration evidence, 2026-07-29 `r9` / `r7`

All paths below use the canonical local CPython runtime and are local,
working-tree evidence only.  `constraint_box/` is untracked, so none is a
canonical or Git-source-admitted result.

| Receipt path | Route | Result |
|---|---|---|
| `/Users/joshuaeisenhart/Documents/Codex/2026-07-27/new-chat/outputs/leviathan_minilev_reference_20260731_r2_result.json` | optional Leviathan dry-run reference | The live `sdlc-exec-validate` source shape and an isolated `lev.run_seal.v1` dry-run were observed. CB independently exercised retry-success and retry-exhaustion flows; the source-to-CB structural mapping and proof-bearing-receipt rejection controls both passed. |
| `/Users/joshuaeisenhart/Documents/Codex/2026-07-27/new-chat/outputs/cb_integrated_capabilities_20260729_r9/capability_suite_expanded_result.json` | `capability-suite` | One fixed-order combined run reached `ELIGIBLE`; all twelve child flows wrote and self-validated their own receipt and ledger artifacts. Independent post-run recomputation matched every child capability and flow receipt hash and found every ledger/head artifact. |
| `/Users/joshuaeisenhart/Documents/Codex/2026-07-27/new-chat/outputs/cb_integrated_capabilities_20260729_r7/legacy_s1_current_diagnostic.json` | S1 broad legacy diagnostic | Real NumPy, SciPy, Z3, and CVC5 APIs ran with recorded controls. The tier is `DRIFT` because the old lock is absent/mismatched; TLC is unavailable to this legacy worker because its JAR is not supplied. |
| `/Users/joshuaeisenhart/Documents/Codex/2026-07-27/new-chat/outputs/cb_integrated_capabilities_20260729_r7/legacy_s2_current_diagnostic.json` | S2 broad legacy diagnostic | Real JAX, Diffrax, Quimb, and Cotengra APIs ran. Diffrax and Quimb are `READY`; JAX/Cotengra retain legacy-version drift. |
| `/Users/joshuaeisenhart/Documents/Codex/2026-07-27/new-chat/outputs/cb_integrated_capabilities_20260729_r7/legacy_s3_current_diagnostic.json` | S3 broad legacy diagnostic | The aggregate completed: real PySINDy, PyDMD, PyMDP, and CPU PyTorch APIs all ran. PyKoopman and Dimod legacy rows remain explicitly `UNTESTED`; tier state is `DRIFT` from the missing old lock. |
| `/Users/joshuaeisenhart/Documents/Codex/2026-07-27/new-chat/outputs/cb_integrated_capabilities_20260729_r7/legacy_s4_current_diagnostic.json` | S4 GPU diagnostic | `nvidia-smi` is absent and the JAX/Torch CUDA witnesses fail on this CPU-only host; CuQuantum is `UNTESTED`. This is an honest failure, not a capability-suite result. |

### Core formal operations refreshed in the same runtime

| Receipt path | Controller-owned operation | Result |
|---|---|---|
| `/Users/joshuaeisenhart/Documents/Codex/2026-07-27/new-chat/outputs/cb_integrated_core_20260729_r10/symbolic_result.json` | `sympy.Poly(..., domain=sympy.QQ).as_dict()` | `ELIGIBLE` for one bounded typed rational polynomial. |
| `/Users/joshuaeisenhart/Documents/Codex/2026-07-27/new-chat/outputs/cb_integrated_core_20260729_r10/workflow_result.json` | `PyDiGraph`, DAG, topological-order, and reachability checks against a CPython reference | `ELIGIBLE` for one bounded prerequisite graph. |
| `/Users/joshuaeisenhart/Documents/Codex/2026-07-27/new-chat/outputs/cb_integrated_core_20260729_r10/transition_result.json` | isolated Maude 1.6.0 one-step controller transition under the final in-child resource bootstrap | `ELIGIBLE` for one bounded controller-defined transition; it is not a generic rewrite or release gate. |
| `/Users/joshuaeisenhart/Documents/Codex/2026-07-27/new-chat/outputs/cb_integrated_core_20260729_r10/temporal_result_host.json` | TLC 2.19 plus Apalache 0.58.3 over the pinned abstract lifecycle skeleton | Both backends passed positive, evidence-removal mutant, post-run hashes, and semantic replay under the host runtime. This standalone pair has no proposal/retry/release-flow caller. |
| `/Users/joshuaeisenhart/Documents/Codex/2026-07-27/new-chat/outputs/cb_integrated_core_20260729_r10/request_assessment.json` | Z3, CVC5, and CPython enumeration input gate | All three returned bounded SAT for an explicit request; the controller allowed only `ELIGIBLE_FOR_PROPOSAL`, never a tool result or release. |
| `/Users/joshuaeisenhart/Documents/Codex/2026-07-27/new-chat/outputs/cb_integrated_core_20260729_r10/request_parked_assumptions.json` | Z3, CVC5, and CPython enumeration input gate | All three returned the same bounded UNSAT result for the missing-assumptions fixture; the controller parked it and emitted one exact resubmission question. |
| `tests/test_agentrun.py` and `tests/test_proposal_minilev_flow.py` | controller-injected overclaim then repair, replayed through `topology-preflight -> PROPOSAL -> GATE -> PROPOSAL -> GATE -> ClaimGate` | local offline test evidence only; the provider never selects graph, retry, terminal, or release. |
| `tests/test_maude_rewrite.py` | isolated Maude 1.6.0 transition worker with capped streams, process-group teardown, CPU/resource policy receipt, and bounded enumeration | one local bounded state-transition observation; not hostile-code containment, a generic rewrite facility, or a release gate. |

## Explicit gaps before any stronger claim

- `execution_lease.py` is now an experimentally tested local owner/TTL/
  heartbeat/nonce candidate, but it is not wired into the Mini-Lev production
  path and authorizes neither a transition nor output release.
- The Mini-Lev proposal path invokes the existing `run_gate` ClaimGate
  boundary, not the full post-receipt/floor/ledger/seal composition.
- The Leviathan reference is one named source-level graph and one dry-run
  envelope. It does not establish whole-Lev equivalence, a live provider/model
  operation, FlowMind evaluator correctness, or cross-run idempotency.
- The proposal flow has fresh injected-provider tests, not a live provider
  operation or provider-availability claim.
- The TLC/Apalache pair is a real offline formal execution, but it checks only
  its pinned abstract skeleton and is not yet consumed by the proposal,
  retry, lease, or release route.
- Maude supports one bounded local transition observation. It is not a general
  rewrite executor, hostile-code containment boundary, or release gate.
- NVIDIA/OpenRouter observations remain advisory sidecars.  They cannot change
  an input gate, tool receipt, terminal transition, release, or promotion.
- The declared broad estate is not fully runnable: TLC lacks its legacy JAR;
  Dimod and CuQuantum acceptance profiles are unimplemented; and this host has
  no NVIDIA/CUDA witness. Those are explicit external-estate gaps, not
  import-only successes or reasons to call the CPU suite full-stack ready.

## Current test gates

The complete ConstraintBox suite was run against this working tree with the
canonical interpreter on 2026-07-29:

| Command mode | Result |
|---|---|
| Normal | `791 passed, 312 subtests passed in 217.67s` |
| Optimized (`-O`) | `791 passed, 7 warnings, 312 subtests passed in 225.54s` |

The optimized warnings are pytest's generic notice that bare Python assertions
are disabled under `-O` plus PyDMD third-party docstring escape warnings. They
are not passing assertions or substitutes for deterministic gate checks.
