# Formal kernel status

**Status:** local candidate; `promotion_allowed: false`

The fresh contained-product checkpoint is **D1e** below. Earlier dated
receipts remain historical evidence at their stated ceiling; they are not
silently upgraded by the newer package or source-suite result.

This is the top-view index for the lean ConstraintBox formal kernel. “Admitted”
means that a fixed controller path can call the named instrument under a
bounded profile. It does not mean the instrument decides policy, proves truth,
or releases an LLM output.

## A. Tool and method decisions

| Index | Tool or method | Value to ConstraintBox | Remove? | Admission | Current ceiling |
|---:|---|---|---|---|---|
| A00 | CPython 3.11, 3.12, or 3.13 plus selected standard-library modules | executes the controller, strict parsers, finite reference methods, hooks, ledgers, receipts, and external-process brokers | keep as the explicit base runtime | active interpreter must satisfy one portable core profile; receipts retain local observed paths and digests | local runtime consistency only; Python is not an OS sandbox or an independent trust root |
| A01 | Z3 | external SMT decision for finite typed request obligations; can return solver-specific evidence | keep | request gate | one bounded encoding; no unrestricted truth claim |
| A02 | CVC5 | independent external SMT decision over the same finite typed obligations | keep | request gate | one bounded encoding; no unrestricted truth claim |
| A03 | bounded exhaustive enumeration | controller-owned CPython reference checker for the finite encoding | keep, but name it as a method | active profile-verified CPython internal request-gate method; not a package or external tool | only the enumerated finite domain |
| A04 | SymPy | exact rational normalization with a mature symbolic implementation | keep | default task `formal.symbolic.polynomial_qq` | one controller-built univariate polynomial over `QQ`; no model-authored expression parser |
| A05 | Rustworkx | efficient graph construction, acyclicity, topological order, and reachability | keep | default task `formal.workflow.prerequisite_dag` | declared graph mechanics only; no semantic correctness of nodes or workflow |
| A06 | Maude 1.6.0 | independent observation of one controller-defined bounded rewrite/state transition | keep outside the default request gate | one isolated worker profile, bounded streams, active compatible distribution/API check, per-run parent-to-worker artifact binding, and current positive/negative/replay controls | not hostile-code containment, a generic rewrite service, a release gate, or formal/canonical admission |
| A07 | TLC | explicit-state check of a bounded hash-pinned candidate single-run abstract state-ordering skeleton and its negative control | keep | required half of offline temporal pair | four narrow abstract invariants only; no implementation correspondence, conformance, or liveness claim |
| A08 | Apalache | independent symbolic check of the same bounded skeleton and negative control | keep | required half of offline temporal pair | four narrow abstract invariants only; no implementation correspondence, conformance, or liveness claim |
| A09 | Hypothesis | hostile structured-input generation, ordering tests, and fixed-seed deterministic regeneration | keep outside decision runtime | tests only; the general doctor may import it for diagnostic inventory | generated test cases only; no saved-counterexample replay or production decision authority |
| A10 | NumPy | useful bounded numerical substrate and dependency for external libraries | keep available; remove only from default formal policy | optional `numeric` extra; no default formal task | no default CB admission until a precise bounded numeric contract is hardened |
| A11 | PySINDy and other NumPy-backed analysis tools | valuable external workload and failure source | do not put in the lean kernel | external sim estate | only each executed, receipt-bound function |
| A12 | JAX, PyTorch, Julia, SciPy, Diffrax, PyDMD, PyMDP, PyKoopman, Quimb/Cotengra, e3nn, graph/topology, and CR systems | difficult real workloads for ConstraintBox to govern and audit | do not put in the lean kernel | external sim estate or downstream consumer; fourteen fixed bounded profiles are controller-callable | only each named operation and explicit integration receipt |
| A13 | NVIDIA hosted and OpenRouter free-model routes | optional plain-language audit and user guidance after a deterministic box decision is frozen | keep outside every decision gate | advisory sidecar only | provider response validity and binding only; no truth, disposition, retry, release, pricing, or promotion authority |
| A14 | typed boundary contract | makes CB core, external formal runtimes, external sim operation profiles, and receipts mutually exclusive roles | keep | `formal.boundary.constraintbox_scope` uses Z3, CVC5, and bounded CPython enumeration | typed scope map only; not a natural-language truth detector or engine-readiness claim |

The answer for NumPy is therefore precise: ConstraintBox **can** use NumPy.
It is not too heavy and it is not banned. It is simply unnecessary for the
three default formal tasks, and the current NumPy profile has not earned
default admission. Installing `constraintbox[numeric]` is an explicit optional
choice.

## B. Authority index

| Index | Decision | Owner | Untrusted party may supply | Untrusted party may not select |
|---:|---|---|---|---|
| B01 | task routing | deterministic controller registry | one registered task kind | arbitrary profile or tool |
| B02 | operation and bounds | fixed profile | typed payload fields | API, solver, tolerance, timeout, or resource ceiling |
| B03 | runtime identity | controller-owned portable profile, pre/post active-runtime receipt, and live API identity checks where the library runs in-process | none | executable, library version, worker, callable, JAR, or model |
| B04 | evidence interpretation | deterministic comparator and receipt schema | a claimed bounded result where the schema calls for one | disposition, claim ceiling, exception, or waiver |
| B05 | admission or release | deterministic controller gates | a repaired candidate for a new pass | self-release or promotion |
| B06 | explanation | advisory LLM or deterministic renderer | criticism and guidance | alteration of policy or receipt |

An instrument reports an observation. The controller validates the observation
against an independent reference or negative control and assigns the
disposition. No instrument and no LLM has standalone authority.

### B1. Mini-LevOS execution index

The embedded mini-LevOS is a small CB-native execution kernel. It borrows
typed-node, hook, transition, and bounded-loop mechanics from LevOS; it does
not import LevOS, an LLM, or a flow author as decision authority.

| Index | Mechanism | Current binding | Authority boundary | Current ceiling |
|---:|---|---|---|---|
| M01 | compiled flow policy | fixed nodes, registered handlers, exhaustive signal transitions, required nodes, hard step/visit/retry and receipt bounds | the controller compiles and hashes the policy | no arbitrary model-authored flow documents |
| M01a | topology preflight | controller-derived non-retry projection of the fixed proposal flow is checked by Rustworkx and an independent reference before the provider is called | fixed policy and evaluator select the graph and result | no user/provider graph, and the check does not give Rustworkx semantic or release authority |
| M01b | controller-owned execution lease | the fixed proposal flow opts one hook into a policy-bound lease; controller selects the stable slot outside the per-run receipt root and seals its digest, root-derived monotonic clock domain, public acquire/release records, and pre/post verification in the receipt | only the guard handles the token and lifecycle; failure before the callback prevents invocation and every failure maps to `HOLD`; an expired same-domain slot is reclaimable | first hook only; no heartbeat in v1, no other hook coverage, distributed lease, crash/reboot recovery, OS sandbox, full-duration callback fencing, or release authority |
| M02 | `PROPOSAL` hook | only after topology preflight and the M01b lease pre-verification, controller dispatches one provider call; the provider can return only untrusted candidate bytes and a sealed observation artifact digest | the fixed flow moves only `OBSERVED` to the proposal gate or `PARKED` to a terminal | no provider-selected transition, retry, claim, release, policy, or lease token |
| M03 | `TOOL` hook | fixed handler emits `OBSERVED` data and cannot choose the next node | transition table chooses the successor | handlers currently execute in the controller process and must be trusted, fixed code |
| M04 | `GATE` hook | fixed handler revalidates opaque evidence and emits a typed signal | the handler cannot emit a terminal or release decision | deterministic gate result only; no general truth claim |
| M04a | historical Lev eval observation | fixed two-node `observe-foreign-eval` TOOL then `replay-verify-foreign-eval` GATE retains one controller-bound five-file historical path, commits only request/receipt/snapshot hashes, persists a source-private binding record, then replays retained bytes | `OBSERVED` is the only route to the gate; a successful gate `PASS` has one fixed target, `PARKED`; neither foreign verdict nor source path is a transition input | historical structural observation only; no live Lev invocation, `ELIGIBLE`, `RELEASED`, ClaimGate result, comparator, or sim/FlowMind-execution claim |
| M04b | isolated Leviathan dry-run reference | optional adapter reads the exact `sdlc-exec-validate` source shape, runs `lev exec --dry-run` under a fresh XDG root, normalizes one `lev.run_seal.v1`, and maps its bounded control structure to a CB-native `TOOL -> GATE` reference flow | Lev's `validate` is recorded as `lev.exec`, not treated as a CB gate; a source-shape mismatch, proof-bearing receipt, passing receipt, or non-dry-run seal blocks the comparison | one named dry run and structural mapping only; no whole-Lev equivalence, model/provider execution, evaluator truth, release, promotion, or idempotency claim |
| M05 | positive terminal rule | every transition to `ELIGIBLE` or `RELEASED` requires an accepted `GATE` `PASS` and all required nodes discharged | enforced by the kernel and replay verifier | workflow eligibility or bounded local release route, not canonical admission |
| M06 | semantic event ledger | hash-chained events, separately retained head, and caller-held expected receipt root | positive receipts are self-verified before return and reverified by the caller | local tamper evidence, not an external signature |
| M07 | runtime check | active portable-profile CPython receipt is checked before and after every hook/transition step | runtime drift forces `HOLD` | identity consistency, not hostile-code containment |

The first external capability uses exactly two nodes:

```text
fixed PyTorch tool -> OBSERVED -> deterministic receipt gate -> PASS -> ELIGIBLE
```

`ELIGIBLE` on this path means only that the one function receipt passed. The
result explicitly sets `release_allowed: false` and `promotion_allowed: false`.

## C. Fixed formal-task index

| Index | Task kind | Typed input surface | Instrument and independent check | Default controller policy |
|---:|---|---|---|---|
| C01 | `formal.symbolic.polynomial_qq` | bounded lists of integer degree/numerator/denominator fields plus a canonical claim | SymPy `Poly` over `QQ` versus stdlib `fractions.Fraction` | fixed variable, degree, coefficient-bit, term, operation, and claim bounds |
| C02 | `formal.workflow.prerequisite_dag` | canonically sorted bounded node and edge lists | Rustworkx versus stdlib Kahn/DFS reference | fixed node/edge caps and required `intake -> proposal_ready` reachability |
| C03 | `formal.transition.current_box_phase` | exactly `from_state`, `action`, and `to_state` | Maude root-rule observation versus the controller transition table | fixed states, actions, transitions, Maude version, worker hash, application count, and timeout |
| C03a | `formal.boundary.constraintbox_scope` | exact typed registry of `cb:*`, `formal-runtime:*`, `sim:*`, and `evidence:*` identifiers | Z3 + CVC5 + bounded CPython reference agree that cross-role conflation flags are false | fixed full registry; an external profile in a CB role is `BLOCKED`, not silently reclassified |
| C04 | `formal.levos.flowmind_contract_structure` | one strict foreign `lev dna compile --json`-shaped envelope for the fixed `flowmind_contract` graph | CB extracts only node IDs and `next`/`branches`, then uses Rustworkx versus its stdlib reference | fixed compiler-shaped envelope and controller-pinned topology, read-only envelope, `gate_compiler_not_executor -> done`, 128 nodes, 512 edges; no producer authentication, Lev execution, ClaimGate, or equivalence claim |
| C05 | offline state-skeleton pair | no user-selected model or backend | TLC and Apalache over the same pinned candidate TLA+ single-run skeleton, four narrow invariants, and evidence-removal mutant | both backends required; resolved Java command and explicitly configured external runtime directory, pinned JAR/model/config/expectation hashes, recorded Java content hash with post-run stability check, exploration bound, and timeout |

The offline pair is not an implementation-conformance task. The candidate
model is one anonymous, abstract, single-run state-ordering skeleton from
`RECEIVED` to a terminal label. It does not establish correspondence to the
Python controller or model the future full retry, lease, proposal-repair,
release, concurrency, liveness, or refinement behavior.

All registered formal payloads enter through a regular-file-only CLI reader
bounded to the controller maximum plus one byte. The controller repeats the
length decision before full hashing or profile evaluation. Oversized direct
API inputs therefore receive no purported complete input digest; their
evidence contains only the observed length, the fixed maximum, and a bounded
prefix commitment.

SymPy and Rustworkx execute in the controller process. Their profiles pin the
installed distribution bytes and check load-bearing live bindings before and
after execution, including negative controls for correct-constant and
genuine-path callable substitution. The SymPy task constructs exactly one
controller-built `QQ` polynomial with one generator and typed rational output;
it never parses model-authored expressions. Rustworkx additionally has a
load-bearing, controller-derived topology preflight in the fixed proposal
flow. These controls block the tested substitutions; they are not OS
containment against arbitrary code already executing inside the controller
process. Maude and the temporal checkers use subprocess boundaries, with the
narrower resource and identity ceilings stated in their receipts. The current
Maude worker uses capped incremental stdout/stderr collection, a new process
group, bounded controller enumeration, and an exact CPU/resource-policy
receipt. Its controller-owned limit bootstrap runs inside the fresh isolated
Python child before Maude imports, avoiding a post-thread controller
`preexec_fn`/fork. On macOS its memory-policy launcher is `taskpolicy`; on platforms
where it is supported it uses `RLIMIT_AS`. This is a bounded local subprocess
boundary, not proof of hostile-code containment, a generic rewrite executor,
or a load-bearing release gate.
Maude is a declared core dependency. Its compatible distribution version and
live API surface are policy; wrapper/native-library hashes are per-run
parent-to-worker binding observations, never developer-machine policy inputs.
The temporal policy names only safe relative JAR locations. A user supplies an
absolute `CONSTRAINTBOX_FORMAL_RUNTIME_DIR` and a `java` command on `PATH`; a
missing or incompatible external temporal runtime is typed `PARKED`, not
silently substituted.
The current wheel packages this formal surface and its four formal resources.
It does not yet package every checkout-relative resource used by older
non-formal commands, so it is not a complete standalone distribution of all
ConstraintBox surfaces.

### C1. Governed external sim-operation profile registry

X01–X14 are `sim:*` external operation profiles.  The controller-owned
external-validation adapter is CB source, but neither the adapter nor a receipt
turns a simulation engine into a CB-core tool.  This role distinction is
checked by `formal.boundary.constraintbox_scope` before a full product/evidence
status map is accepted.

| Index | Capability | Fresh controller input | Real operation | Deterministic controls | Public status ceiling |
|---:|---|---|---|---|---|
| X01 | `pytorch-jacobian-v1` | fresh bound coefficients and point | pinned worker calls `torch.func.jacrev` on CPU `float64` | analytic, wrong-value, and zero-boundary checks | one bounded Jacobian operation |
| X02 | `jax-autodiff-v1` | fresh bound coefficients and vector | worker calls `jax.grad`, `jax.vmap`, `jax.jit` under x64 | positive, wrong-value, boundary | one bounded autodiff operation |
| X03 | `pysindy-affine-generator-v1` | fresh affine generator and supplied exact derivative | worker calls `SINDy.fit` and `predict` | positive, wrong-value, boundary | one bounded candidate-generator operation |
| X04 | `julia-diffeq-v1` | fresh ODE rate and state | strict Julia carrier calls `ODEProblem`, `solve`, `Tsit5` | positive, wrong-rate, boundary, carrier binding | one bounded Julia ODE operation |
| X05 | `scipy-expm-rotation-v1` | fresh rotation parameters | worker calls `scipy.linalg.expm` | positive, wrong-value, boundary, semantic replay, operation poison | one bounded matrix-exponential operation |
| X06 | `diffrax-tsit5-affine-flow-v1` | fresh affine-flow parameters | worker calls `ODETerm`, `Tsit5`, `PIDController`, `diffeqsolve` | positive, wrong-value, boundary, semantic replay, operation poison | one bounded Diffrax operation |
| X07 | `graph-topology-crosscheck-v1` | fresh controller-owned finite complex and graph | worker calls GUDHI, TopoNetX, XGI, NetworkX, igraph, Rustworkx, PyG, and `torch.linalg.eigvalsh` | cross-library value agreement, wrong-value, and boundary controls | one bounded graph/topology crosscheck, not graph-stack readiness |
| X08 | `pydmd-discrete-rate-v1` | fresh discrete-rate sequence | worker calls `DMD.fit`, `eigs`, `reconstructed_data` | positive, wrong-value, horizon boundary | one bounded decomposition operation |
| X09 | `pymdp-two-state-inference-v1` | fresh two-state model | worker calls `Agent.infer_states`, `infer_policies` | positive, wrong-value, alternate-observation boundary | one bounded inference operation |
| X10 | `pykoopman-identity-edmd-v1` | fresh contraction trajectory | worker calls `Koopman.fit`, `predict`, `EDMD.fit` on fixed Identity+EDMD | positive, wrong-value, zero boundary | one explicitly bounded PyKoopman surface |
| X11 | `quimb-cotengra-bounded-suite-v1` | fresh bounded density and triangle path | worker calls Quimb density APIs and `HyperOptimizer.search` | positive, wrong-value, boundary, per-row operation poison, receipt replay | two bounded tensor-network operations |
| X12 | `multiengine-dlpack-diffeq-v1` | fresh controller-derived DLPack/JAX and Julia challenges | real Torch DLPack -> JAX transfer plus independent strict-carrier Julia solve | positive, wrong, boundary, severance, replay | one cross-engine local diagnostic, not engine readiness or a canonical sim |
| X13 | `basic-packet-cross-engine-v1` | immutable legacy fixture, bound to controller run/policy/source artifacts | JAX, PyTorch, PySINDy, Julia, and legacy PySINDy-to-Julia artifact consumer | embedded packet recomputation and receipt validation | one legacy JSON-handoff diagnostic, explicitly not a scientific DLPack bridge |
| X14 | `e3nn-wigner-crosscheck-v1` | fresh bounded integer-degree request | worker calls `e3nn.o3.wigner_3j` | exact symmetry and wrong-value controls with independent replay | one bounded equivariant-tensor operation |

X01–X14 are external to the kernel. They do not establish engine readiness,
simulation-stack readiness, CR truth, scientific correctness, hostile-host
containment, or canonical promotion. The legacy full estate uses fixed
fixtures; its evidence must not borrow a fresh-challenge capability claim.

## D. Build order

The two workstreams can proceed in parallel, but their evidence must stay
separate.

| Order | Workstream | Deliverable | Admission test | Status ceiling |
|---:|---|---|---|---|
| D01 | CB kernel | strict bytes, canonical JSON, typed request, fixed registry, hash-chain receipt | duplicate/ambiguous input and policy-selection attacks fail closed | controller substrate only |
| D02 | CB kernel | Z3 + CVC5 + internal enumeration agreement and deterministic failed-clause feedback | SAT, UNSAT, disagreement, abstention, exception, and replay controls | bounded request gate |
| D03 | CB kernel | SymPy exact-data task | typed `QQ` construction, valid/hostile/severance/mutation and semantic-replay controls | one rational polynomial claim |
| D04 | CB kernel | Rustworkx workflow task and proposal topology preflight | DAG, cycle, skipped prerequisite, reachability, severance, mutation, replay, and controller-derived preflight controls | graph mechanics only |
| D05 | CB kernel | Maude transition task | bounded stream collection, process-group teardown, in-child CPU/resource bootstrap, bounded worker enumeration, and valid/hostile/replay controls | one fixed local transition observation; no containment or release claim |
| D06 | CB kernel | paired TLC/Apalache offline model check | positive model, evidence-removal mutant, version/artifact drift, bound binding, timeout, and replay controls | four narrow predicates over one abstract single-run state skeleton only; standalone offline pair, not yet a proposal/retry/release-flow gate |
| D07 | CB kernel | actual untrusted proposal, repair, retry, and ClaimGate loop | fixed Rustworkx topology preflight -> leased proposal observation -> deterministic proposal gate -> optional one retry -> ClaimGate gate; all events replay | one fixed two-attempt profile with injected offline provider controls and a local cooperative lease on the proposal hook; no live provider claim, general agent lease, standing/floor/seal composition, or canonical admission |
| D08 | external sim estate | each tool executes at least one real bounded operation with independent negative and severance controls | no import-only, manufactured JSON, or stdlib substitution can pass | function receipt, not whole-engine readiness |
| D09 | external sim estate | selected cross-engine serialized integrations | both producer and consumer operations are severance-sensitive and replayable | named integration only |
| D10 | feedback loop | use real sim-estate failures as reproducible ConstraintBox training/tuning cases | failure changes a deterministic gate, test, or explanation contract and survives replay | harness improvement, not scientific proof |

### D1. Current implementation checkpoint

| Index | Implemented path | Current state | Next blocking step |
|---:|---|---|---|
| P01 | explicit CPython runtime and operations | fresh local full-suite and formal-operation evidence in the current untracked working tree | retain runtime/source pins when packaging changes |
| P02 | typed mini-LevOS hooks, transitions, bounds, ledger, replay, and fixed topology preflight | fresh local replay evidence for fixed external flows and the controller-derived `topology-preflight -> PROPOSAL -> GATE -> ClaimGate` route | isolate any future untrusted handler before admitting it |
| P02b | strict Lev DNA/FlowMind structural ingress | two fresh local calls to the named Lev DNA compile command produced byte-identical supplied artifacts; both entered the fixed Mini-LevOS formal tool-to-gate flow, retained raw bytes, and required Rustworkx/reference agreement. Receipts explicitly mark producer and source-path authentication false. | add an explicit source-identified producer witness and a real Lev evaluator command case before any CB↔Lev execution comparison; current result is compiler-artifact structure only |
| P02c | strict Lev eval-bundle observation | the current candidate source places the strict five-file observer inside a fixed historical-only two-node Mini-Lev flow. The tool retains one controller-bound historical path; the gate replays only retained CB bytes; a valid replay ends `PARKED`. A durable source-private binding record supports reload after source removal. The contained test surface includes deleted-source/fresh-process replay, persisted-receipt tamper, retained-snapshot tamper to `HOLD`, missing source to `PARKED`, and a foreign `fail` that still ends `PARKED`. | one captured dry-run path can support structural observation only; it does not establish a real sim, a FlowMind execution, a ClaimGate ingestion path, a live Lev operation, comparator, producer authentication, immutable pre-capture selection, or a positive CB disposition |
| P02d | isolated Leviathan Mini-Lev reference | fresh `r2` ran the live Lev `sdlc-exec-validate` source under `--dry-run`, retained a normalized non-proof `lev.run_seal.v1`, verified the exact source graph against CB's stronger tool/gate/retry/terminal mapping, and ran negative controls rejecting `execution_success` plus proof-bearing/passing receipt variants | one local Lev dry run and one CB fixture; it does not prove full Lev, LLM/provider execution, evaluator correctness, repeated-intent idempotency, release, or promotion |
| P03 | X01–X14 capability registry through fixed `TOOL -> GATE` flows | retained external-validation `r23` ran fourteen named operation/integration profiles; every flow has a controller-origin attestation and retained independent replay. The core bundle deliberately excludes the external estate and treats a missing configured runtime as `PARKED`. | migrate adapters one at a time and run a clean external-install verifier before any portable-external-product claim; do not promote the full estate |
| P03a | execution lease first binding | the actual proposal flow's `proposal-observation` hook acquires, pre-verifies, invokes, post-verifies, and releases through a controller-selected stable slot; a root-derived clock domain is policy-bound, public records and requirement digest replay from the Mini-Lev receipt, and a same-domain expired slot has a regression proof of reclamation | extend deliberately, one controller-selected hook at a time; v1 has no heartbeat, no distributed/crash/reboot recovery, no hostile-process boundary, no full-duration callback fence, and no release authority |
| P04 | request intake and personalized MMM into the actual LLM proposal path | fixed Mini-LevOS retry, lease, and ClaimGate graph pass injected offline provider controls; no live model operation is claimed | bind the complete ClaimGate post-receipt/floor/ledger/seal pathway |
| P05 | deterministic release path through all standing, floor, ledger, and evidence checks | not connected end to end | remove the direct paths that bypass the full fired hook and ledger verification |
| P06 | verified frozen box snapshot into NVIDIA or OpenRouter explanation | local candidate source and offline sidecar controls; no live provider operation, availability, free-price, or billing claim | retain zero authority and separate provider receipts; perform a live operation only when an owner deliberately authorizes both credential use and disclosure of the frozen advisory brief |

### D1a. Historical local evidence — 2026-07-29

The following was reported from the then-current untracked working tree. It is
retained as historical evidence only and does not establish a fresh rerun of
the current source. It never supports canonical promotion:

| Evidence | Result | Literal ceiling |
|---|---|---|
| full ConstraintBox suite | normal: `827 passed, 319 subtests`; optimized Python: `827 passed, 319 subtests`, with pytest's generic `-O` warning plus six PyDMD third-party docstring escape warnings | local regression coverage; warnings are not passing assertions or substitutes for a gate |
| CVC5 request gate | a direct CLI request exited zero in normal and `-O`; Z3, CVC5, and the CPython finite reference each returned `BOUNDED_SAT` | one explicit request-clause encoding; result was only `ELIGIBLE_FOR_PROPOSAL` with promotion false |
| Mini-Lev proposal path | focused current source tests bind both `proposal-observation` visits to a policy-bound root-derived execution-lease clock domain; they cover domain mismatch, expired same-domain stale-slot reclamation, expiry, callback failure, release persistence failure, and an injected offline provider that repairs through `topology-preflight -> PROPOSAL -> GATE -> PROPOSAL -> GATE -> ClaimGate -> RELEASED` | source/test integration only; no live model, provider availability, hostile-process containment, crash/reboot recovery, full-duration callback fence, or canonical-release claim |
| X01–X12 through fixed capability suite | fresh local `r14`: 12/12 controller challenges were `ELIGIBLE`; each used a fresh child operation and a separate fresh-child replay, with the replay result retained at a portable suite-relative path alongside the controller-origin attestation. The suite invoked PyTorch, JAX, PySINDy, Julia, SciPy, Diffrax, PyDMD, PyMDP, PyKoopman, Quimb, and Cotengra APIs; it also ran a real Torch DLPack -> JAX transfer with an independent Julia lane and a separately labelled legacy PySINDy-to-Julia packet | named operations/integrations only; `release_allowed: false`, `promotion_allowed: false`, and no engine readiness |
| legacy external diagnostic packet | JAX, PyTorch, PySINDy, Julia, plus the PySINDy-to-Julia handoff passed their bounded controls in fresh `r2` output | diagnostic external estate evidence, not CB-kernel membership or general stack readiness |
| broad legacy-estate rerun (`r7`) | real S1/S2/S3 APIs were invoked, including NumPy/SciPy/Z3/CVC5/JAX/Diffrax/Quimb/Cotengra/PySINDy/PyDMD/PyMDP/PyTorch; the S3 aggregate completed; old locks still drift, legacy PyKoopman/Dimod are `UNTESTED`, and S4 accurately failed on the CPU-only host | diagnostic execution only; it is deliberately not capability-profile admission or whole-estate readiness |
| Maude bounded transition task | a real isolated Maude 1.6.0 worker produced the controller-checked transition observation with bounded-process controls | one current local task only; no hostile-code-containment, general-rewrite, or release claim |
| TLC/Apalache temporal pair | fresh outside-sandbox `formal temporal` receipt: TLC 2.19 and Apalache 0.58.3 both passed the pinned positive skeleton, evidence-removal mutant, post-run hashes, and semantic replay | one abstract offline state-token lifecycle pair; no controller correspondence, retry/lease/release/liveness/concurrency/refinement, or sim-estate admission |

The first direct request invocation exposed a CVC5 binding teardown crash: it
printed an apparent result and then exited `139`. It was not counted as a
pass. The finite CVC5 compiler was refactored from cyclic nested closures to
module-scope helpers, and a real child-process clean-exit control now protects
against this false-green shape. Evidence is retained at
`/Users/joshuaeisenhart/Documents/Codex/2026-07-27/new-chat/outputs/formal_kernel_actual_20260729_r1/`.

### D1b. Current contained-product checkpoint — r20

The following was rerun after binding the strict foreign Lev eval observer into
its fixed two-node Mini-Lev flow, adding source-private durable replay, and
hardening retained-file traversal. It is a local source and selected-runtime
checkpoint, not an installation, whole-estate, provider, or promotion claim.

| Evidence | Result | Literal ceiling |
|---|---|---|
| full ConstraintBox suite | normal: `849 passed, 319 subtests`; optimized Python: `849 passed, 319 subtests` | current local source regression only; optimized mode emitted Pytest's generic `-O` advisory and six third-party PyDMD docstring escape warnings |
| r20 contained core | fresh contained source bundle and isolated verifier receipt are emitted under the dated `constraintbox_contained_core_20260730` output directory | a source bundle with dependencies intentionally external; neither a wheel/container nor host-independent runtime |
| r20 isolated extraction verifier | historical receipt expected `VERIFIED` under the then-local interpreter with 13 declared checks, including the fixed Mini-Lev proposal topology unit, strict observer unit, retained-byte/restart flow unit, and a fail-closed absent-estate `PARKED` case; current core verification uses portable CPython profiles | fixture-based boundary tests plus contained smoke operations; no live provider, full sim estate, or whole-Lev integration claim |
| fixed proposal topology | the contained unit executes the pinned Rustworkx profile on the controller-derived non-`RETRY` Mini-Lev projection and independently replays the receipt | fixed four-node proposal topology mechanics only; callbacks are test doubles and Rustworkx cannot select a transition, release, or promotion |
| captured Lev eval through fixed flow | the selected `cr-constraint-battery-pass-trace-eval` dry-run bundle yielded one `lev.measurement.v1` trace row, a deferred projection, and a foreign `pass`; the current CB flow receipt SHA-256 is `c4f4e3541a1cc10d5789f5edb1bc2acbe9afe4bfe7da14def21043cc7d9c3d44`, its retained-observation receipt SHA-256 is `66591cc081b4c4847829ce0f7614a592d55aba14272fa2f4b187b1e4ab9ca893`, and its terminal is `PARKED` | structural observation of one foreign dry-run path; it does not prove a sim ran, transfer the foreign pass, authenticate Lev, select a positive CB disposition, or create a ClaimGate/CB admission |

The r20 bundle and its verifier receipt are retained under
`/Users/joshuaeisenhart/Documents/Codex/2026-07-27/new-chat/outputs/constraintbox_contained_core_20260730/`.

### D1c. Current feedback and external-workload checkpoint — r21

This local candidate checkpoint adds one narrow, adversarially useful fact to
the core boundary: a real external operation that fails a deterministic replay
control reaches the repair planner without becoming an LLM decision, a retry,
or a promotion.

| Evidence | Result | Literal ceiling |
|---|---|---|
| full ConstraintBox suite | normal: `853 passed, 324 subtests`; optimized Python: `853 passed, 324 subtests` | local working-tree regression only; optimized mode emitted Pytest's generic `-O` advisory and six third-party PyDMD docstring escape warnings |
| real-worker non-pass rehearsal | source-owned `scripts/run_failure_rehearsal.py` ran an isolated SciPy `scipy.linalg.expm` normal worker (exit `0` with witness), a deliberately operation-severed replay worker (exit `86`), and the ordinary exact severance control (exit `86`); the registered dispatcher emitted `BLOCKED/controller_recomputed_check_failed`, the planner retained a source/runtime/ledger-bound `failure_event`, and the fixed hook retained an independently replayed unpoisoned same-profile rerun | one deliberate controller rehearsal, not a natural SciPy failure, broad engine result, automatic repair/tuning, or public fault interface |
| non-pass receipt replay hardening | `FAIL/controller_recomputed_check_failed` now revalidates normal/replay/severance row grammar, controller transport/binding hashes, source/runtime/artifact pins, recomputed controls/expectations, and the exact severance record; rehashed row/control/binding tampering is refused | applies to this explicitly bounded non-pass shape; other missing-runtime/artifact/source non-passes stay their narrow typed outcomes |
| fresh 12-profile capability suite | `ELIGIBLE`, 12/12 fixed profiles, each executed in one fresh child and replayed in a second; aggregate SHA-256 `26075ac4978797bfe2e458c36499b96041b921c90b17663a27bea100ab9082f7` is retained at `outputs/cb_integrated_capabilities_20260730_r21/capability_suite_result.json` | named external operations and two bounded cross-engine handoffs only; no full-estate readiness, CR truth, scientific claim, release, or promotion |
| r21 contained core | local source bundle `constraintbox-core-0.3.1-r21.zip` and isolated verifier receipt are emitted under the dated `constraintbox_contained_core_20260730` output directory | contained source candidate only; external SciPy failure regression and all sim workloads remain outside its smoke surface because their native estate is intentionally not packaged |

The repair contract has `selected_action: fresh_rerun` for this exact
controller-recomputed failure, but `execution_authorized: false` and zero
attempts. The separate fixed rehearsal can invoke the same controller-owned
non-mutating follow-up and retain its `PARKED` review outcome; it still does
not authorize a retry loop, source/environment repair, tuning, release, or
promotion.

### D1d. Explicit bound rerun and outcome — r22 candidate

The r22 source adds a narrow separate action, not an executable repair plan:

```text
verified BLOCKED fresh_rerun plan
  -> explicit --execute-fresh-rerun acknowledgement
  -> same controller-selected capability in a new disjoint directory
  -> parent contract regenerated again after dispatch
  -> normal verifier plus fixed fresh CPython verifier child
  -> repair_outcome.json
```

The fixed rehearsal starts with an actual isolated SciPy `scipy.linalg.expm`
normal worker, while only its replay control is operation-severed by a
source-owned scope. Once that scope closes, the r22 follow-up runs the
unmodified registered SciPy profile. Its normal and replay worker calls
genuinely use `scipy.linalg.expm`; the new receipt is `PASS`, and a fresh
verifier child replays it. The retained outer outcome remains
`PARKED/FRESH_RERUN_ELIGIBLE_REVIEW_REQUIRED`, `repair_resolved: false`, and
non-promoting. This is a real test of the loop's receipt plumbing, not a claim
that SciPy naturally failed, that CB repaired anything, or that the entire sim
estate is ready.

The command surface has exactly an existing capability-run directory, a new
disjoint run directory, and a fixed acknowledgement. It does not accept a
capability, model, request ID, worker, command, action, profile, verifier,
tolerance, retry, or output override. The plan's zero authorization is
preserved: the separate invocation does not spend it and has no CB
source/environment mutation action. Both runs must retain the same fixed capability, flow policy,
registry, origin/runner/issuer source pins, and runtime identity. If the
parent contract changes after dispatch, no outcome is retained.

| Evidence | Result | Literal ceiling |
|---|---|---|
| r22 full source suite | normal: `855 passed, 324 subtests`; optimized: `855 passed, 324 subtests` | working-tree regression only; optimized mode emitted Pytest's generic `-O` advisory and six third-party PyDMD docstring escape warnings |
| r22 real failure-to-outcome regression | real SciPy normal worker witness → test-local operation-severed replay control → verified `fresh_rerun` plan → unpatched real SciPy rerun → second fresh CPython replay child → outer `PARKED/FRESH_RERUN_ELIGIBLE_REVIEW_REQUIRED` outcome | the initial fault is deliberately induced; no natural engine defect, automatic repair, tuning, source/environment change, release, or promotion is claimed |
| r22 fresh fixed capability suite | `ELIGIBLE`, 12/12 controller-selected profiles; each profile ran in one fresh child and was independently replayed in a second; aggregate SHA-256 `9b4f4de1b17672142ccb1ba3cbf2c5de7daa69636a38a81203c5eed1918ceb3e` at `outputs/cb_integrated_capabilities_20260730_r22/capability_suite_result.json` | bounded named operations and two bounded handoffs only; not full-estate readiness, CR truth, science, release, or promotion |

### D1e. Current contained-core and runtime-contract checkpoint — 2026-07-31

This checkpoint replaces neither the historical r20–r22 evidence nor the
external-estate boundary. It records the current working-tree package and the
latest fixed-operation suite with the portability result made explicit.

| Evidence | Result | Literal ceiling |
|---|---|---|
| prior full source regression | `864 passed`, `327 subtests passed` under the selected CPython; one `jsonschema.__version__` deprecation warning | historical local source regression only; it predates the r7 graph-replay and portable-PyDMD/PyMDP changes, so it is not a current full-regression claim |
| contained-core build contract | `scripts/build_contained_core_bundle.py` emits a manifest-bound source ZIP; the handoff ZIP and its separate verification receipt are generated outside the source archive to avoid a self-referential hash claim | source bundle only; it excludes CPython, native/external engine runtimes, credentials, providers, and the broad simulation estate |
| current extracted-core verifier contract | `scripts/verify_contained_core_bundle.py` declares 29 fresh-extraction operations: runtime profile, demo, MMM/SMT, missing-assumptions park, SymPy, typed CB/sim-boundary positive and negative cases, a real Maude transition, Rustworkx/Mini-Lev topology, local repair/lease/foreign-observation units, the contained Leviathan-reference unit, provider-policy controls, attractor-basin adapter/CLI surfaces, absent-estate park, typed temporal-runtime absence `PARKED`, and two ClaimGate fixtures | contained-core smoke only; adapter CLI checks do not run external engines, and the Leviathan unit uses fixtures without requiring or running Lev. This is not an external-engine, live-provider, full-Lev, hostile-host, release, or promotion claim |
| prior fresh core wheel smoke | `dist/20260731-r4/constraintbox-0.3.3-py3-none-any.whl`, SHA-256 `2d85ce6784b5efbbcccd3e10ae9c9cda3c024809270754729c3b5c53679c699c`; fresh venv dependency resolution, `pip check`, installed-origin, runtime, Z3/CVC5/reference, SymPy, and Rustworkx checks all passed | historical clean installation proof for the lean core only; it predates r7 and does not install or prove external sim workloads |
| fresh r7 13-profile capability suite and core chain | external suite SHA-256 `d5fa7ee03e2c9307be626565e34fb78e1a44c8e3f7198089b26bec16eb03ed94` and integrated result SHA-256 `0189282af412c92a2922b7458921d0cb4919751077b204b02bc04e6737527f59` were `ELIGIBLE`: each profile executed in a fresh child and independently replayed; the receipt then traversed Z3/CVC5/reference enumeration, Mini-Lev lease, Rustworkx, SymPy, Maude, TLC/Apalache, and ClaimGate | named local operations/instruments only; no engine readiness, clean external-install proof, CR truth, scientific claim, release, or promotion |
| fresh r8 portable-policy core chain | `outputs/cb_integrated_core_20260731_r8_portable_result.json` was `ELIGIBLE`, with the 13 fixed external profiles independently replayed and a 16-stage core chain through Z3/CVC5/CPython reference method, Mini-Lev lease, Rustworkx, SymPy, Maude, TLC/Apalache, and ClaimGate; `llm_decision_authority: false` and `llm_input_used: false` | local source/runtime evidence only. The selected sim-stack alias resolves to the existing main environment, so this is not a clean-core-install or full-engine-readiness result. |
| fresh isolated Leviathan/Mini-Lev reference | `outputs/leviathan_minilev_reference_20260731_r2_result.json` was `ELIGIBLE`: the exact five-node Lev source shape, an isolated non-proof `lev.run_seal.v1` dry run, CB retry-success and retry-exhaustion controls, explicit source-to-CB correspondence, and proof-bearing/non-dry-run rejection controls all passed; both `llm_decision_authority` and `leviathan_decision_authority` are false | one local source/runtime comparison only; it does not establish full Lev parity, provider/model activity, evaluation truth, cross-run idempotency, external-engine readiness, release, or promotion. |
| fresh 14-profile external suite including e3nn | `outputs/capability_suite_20260731_e3nn_result.json`, SHA-256 `b16e80079ae1d504d622ad8dfacc4216c44a3ee381a7cbd8915f1400b44c6747`, was `ELIGIBLE`: every fixed profile executed in one fresh child and had a separate fresh-child replay. The fourteenth profile invoked `e3nn.o3.wigner_3j` on controller-selected `(1,1,0)` and `(1,1,2)` coupling triples with wrong-value, boundary, and operation-poison controls. | local source/runtime evidence only; it is not clean external-install proof, whole-engine readiness, CR truth, scientific proof, release, or promotion. Four historical profiles remain `LEGACY_HOST_BOUND`. |
| fresh clean-core Maude installation proof | a new temporary virtual environment installed the current core and its declared dependencies, passed `constraintbox runtime verify`, and produced an `ELIGIBLE` real Maude transition receipt from that environment's own `site-packages`; the retained result is `outputs/clean_core_maude_20260731_result.json` | proves the base formal core can load and run Maude without source-embedded host paths; it does not install temporal JARs, external simulation engines, or establish broader engine readiness |
| external runtime-contract report | nine `PROFILE_IMPLEMENTED_UNVERIFIED` direct adapters: PyTorch, JAX, PySINDy, Julia DifferentialEquations, SciPy, Diffrax, graph/topology crosscheck, PyDMD, PyMDP; four `LEGACY_HOST_BOUND`: PyKoopman, Quimb/Cotengra, multiengine DLPack/DiffEq, legacy basic packet; clean external-install count is zero | a source-policy migration index, not a clean-host external-install result. A green operation row must not be read as a portable external product. |

The source of authority for the full mapping is
`constraintbox.capability_suite._RUNTIME_CONTRACT_BY_CAPABILITY`, and
`EXTERNAL_SIM_RUNTIME_CONTRACT.md` is covered by a test that keeps its
identifier/status rows aligned with that table. The deterministic controller,
not an LLM or an audit model, owns both the operation disposition and this
runtime-policy classification.

### D2. Supplied old-audit reconciliation

| Index | Old concern | Current classification | Literal current meaning |
|---:|---|---|---|
| R01 | `constraint_box/` is untracked | still open | all CB evidence is working-tree local and cannot be called canonical |
| R02 | fired-hook receipt selector misses current result paths | still open | the installed pre-commit hook does not cover every named result location |
| R03 | gate ledger has no live authority | partial | append is fired, but verification is still manual and current rows are not a keyed production trust root |
| R04 | ratchet floor can be skipped | partial | some stores and missing-store handling improved, but CB's direct gate path still bypasses the full floor path |
| R05 | tests use precomputable fixed fixtures | partial | X01 now has a fresh bound challenge; the legacy estate and full packet remain fixed |
| R06 | evidence seal is not on release | still open | sealing remains a sibling CLI rather than a mandatory model-release step |
| R07 | standing and applicability are isolated | still open | their CLIs exist, but the main CB release path does not consume them |
| R08 | intake and personalized MMM stop before the model path | fixed for the current narrow proposal profile | `constraintbox run` now requires and independently revalidates a READY box snapshot, derives the task from its captured request, and uses its compiled personalized context; direct task files fail closed |
| R09 | gate path bypasses parts of ClaimGate | partial | `run_agent` reaches `gate.py`, but that direct path bypasses the full post-receipt hook, floors, and gate-ledger verification |
| R10 | missing/stale discharge observations are not producible in the live constructor | still open | isolated tests exist, but production constructs one complete same-time observation set |
| R11 | inherited LLM harness provenance and provider-content shortcut | still open | external providers remain untrusted proposal/advice sources and must not become gate authorities |

## E. Removal and addition rule

A tool belongs in the default kernel only when all of the following exist:

1. a narrow typed object that the controller, not the LLM, constructs or
   validates;
2. fixed resource, operation, runtime, and claim bounds;
3. a real caller from a registered controller path;
4. a positive control, independent negative control, dependency/operation
   severance, mutation test, and semantic replay;
5. typed handling for missing dependency, executed failure, disagreement, and
   drift;
6. a receipt that cannot be promoted by the tool, the request, or an LLM.

Tools that fail this rule are not necessarily useless. They remain optional or
external until a concrete task earns admission. This is why NumPy stays
available without being a default formal task, while the full simulation
estate stays outside the lean kernel.
