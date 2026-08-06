# Contained ConstraintBox core product

ConstraintBox is a deterministic harness for untrusted user and LLM work.  The
core owns request intake, MMM/profile compilation, fixed Mini-LevOS
tool-to-gate flow, formal checking, bounded feedback, receipts, and its local
ClaimGate chain.  An LLM may provide an untrusted proposal or advisory prose;
it does not determine a gate, a disposition, or promotion.

## Product boundary

The contained-core ZIP is a source product.  It includes the source plus the
local resources its core smoke surface needs:

- `src/`, `config/`, `mmm/`, `fixtures/`, `formal/`, `workers/`, and the
  local `claimgate_plugin/` chain;
- bounded external-capability definitions, tests, requirements, and supporting
  docs, which remain explicitly outside the core runtime contract;
- the deterministic builder, manifest, and isolated-extraction verifier.

It intentionally excludes CPython, installed/native dependencies, Node.js,
Julia, GPU software/drivers, credentials, remote providers,
`external_sim_estate`, and the surrounding Codex-Ratchet checkout.  Those are
environmental or external-workload dependencies, not hidden parts of CB.

## Practical guides

Use these as three separate boundaries rather than one blended installation
story:

- [CORE_INSTALL.md](CORE_INSTALL.md): contained CB core installation and
  verification only.
- [SIM_SETUP.md](SIM_SETUP.md): separately installed simulation runtimes and
  their compatibility/profile status.
- [CROSS_ENGINE_INTEGRATION.md](CROSS_ENGINE_INTEGRATION.md): CB's bounded
  verification of an already-installed external workload.
- [SIM_INTEGRATION_EVIDENCE.md](SIM_INTEGRATION_EVIDENCE.md): the actual
  external-operation test matrix, retained receipts, and separate evidence
  bundle procedure.
- [MINILEV_PROVIDER_RUNTIME.md](MINILEV_PROVIDER_RUNTIME.md): contained
  provider/notary code, explicit key-runtime setup, and the current proposal
  route ceiling.

Adapter source may be inside the source ZIP for inspection and deterministic
profile checks. It is not an installed simulation runtime or the sim estate.

## Explicit host requirements

| Host component | Required by the contained verification | Included in the ZIP? |
|---|---|---|
| CPython 3.11, 3.12, or 3.13 | active portable core-profile verification | no |
| Z3, CVC5, SymPy, Rustworkx, Maude | deterministic SMT, exact-expression, Mini-Lev graph, and bounded rewrite gates | no; required Python packages in that runtime |
| Node.js | the in-box ClaimGate checker | no |
| Java plus TLC/Apalache JARs | separately configured offline temporal pair | no; explicit external formal-runtime directory |
| Writable absolute CB runtime directory | provider-notary keys for an actual Mini-Lev proposal run | no; explicit `CONSTRAINTBOX_RUNTIME_DIR` selected by deployer |
| Julia, JAX, PyTorch, PySINDy, GPU stack | external simulation workloads | no; intentionally absent from core |

The verifier always uses the interpreter that invoked it. It preserves that
interpreter's launcher path—so a venv launcher is not accidentally resolved to
its base Python—and begins with `constraintbox runtime verify`. A missing or
incompatible core library yields `PARKED` or `BLOCKED`; the verifier never
selects another interpreter, installs a dependency, or treats a base-Python
fallback as a pass.

The temporal pair is deliberately separate from the contained source bundle:
set `CONSTRAINTBOX_FORMAL_RUNTIME_DIR` to an externally installed JAR directory
when running it. The bundle's policy uses that declared setting and safe
relative artifact paths; it carries no developer-machine path. In a bare core
verification, temporal absence is a required `PARKED` result, not a simulated
pass.

## Mini-LevOS and LevOS boundary

CB is a small Python Mini-LevOS, not a copy of all LevOS.  The contained
controller owns the graph policy, hooks, retry bounds, receipts, and final
disposition.  LevOS and the sim estate remain external producers or workloads.
Their text, JSON, status fields, and LLM-facing declarations do not acquire
CB authority merely by being present in an input artifact.

| Surface | Contained CB role | Current connection | Decision authority / ceiling |
|---|---|---|---|
| Mini-LevOS | fixed tool-to-gate flows, hook identity, bounded state/retry, hash-chain receipt | load-bearing CB runtime | CB only; never release or promotion authority |
| provider/notary harness | contained receipt capture, executor/notary split, signature verification, local-process/OpenRouter/NVIDIA adapters, and deterministic provider gate | `constraintbox._provider_harness`; explicit deployer key directory and static pre-start route selection | untrusted provider output only; no model-selected transition, retry, release, or promotion |
| Rustworkx | actual DAG, cycle, order, and reachability operation, cross-checked by a small Python reference | load-bearing CB formal graph profile | finite topology only; no node-semantic or whole-workflow claim |
| Lev DNA → FlowMind | strict foreign compiler-artifact intake | `formal.levos.flowmind_contract_structure` accepts one controller-pinned, Lev-shaped `dna.compile` envelope | structural projection only; not a Lev runtime, ClaimGate, or equivalence claim |
| Lev eval bundle | fixed historical-only Mini-Lev observation flow over a strict five-file foreign bundle (`run`, decision, measurement JSONL, deferred projection, seal) | `constraintbox observe-lev-eval` binds one selected historical **path**, retains it, and replays only the retained bytes through `observe-foreign-eval -> replay-verify-foreign-eval -> PARKED` | path/digest relationship only; even a clean replay stops `PARKED`, and a foreign verdict never becomes a CB disposition, ClaimGate result, or promotion |
| agent lease | CB `ExecutionLeaseStore` plus controller-owned Mini-Lev guard | first live binding wraps the bounded proposal flow's `proposal-observation` hook: acquire -> pre-verify -> callback -> post-verify -> release; the frozen policy binds a state-root-derived local monotonic clock domain and nonce-free public records are sealed in the Mini-Lev receipt | local cooperative lifecycle for one hook only; same-domain expiry can recover, but no heartbeat in v1, no coverage of every hook, no hostile-process sandbox, distributed lease, reboot recovery, full-duration callback fencing, or release authority |
| ClaimGate → Lev history | foreign historical material only | current Lev has a noncanonical inbox memo, not a ClaimGate producer, schema, CLI, or consumer | do not claim that CB can ingest a Lev-produced ClaimGate artifact; never treat `live_lev_consumed`, pass, ledger, or promotion fields as CB authority |
| Lev sim-witness | future external sim-evidence comparison seam | current adapter/tests are non-authoritative and not a live lane | CB must independently hash, rerun, and gate before any comparison |
| simulation engines | external workload library | fixed capability profiles run real bounded operations and return receipts | neither part of the core nor proof of broad engine readiness or CR truth |

The first bridge deliberately accepts one narrow, versioned Lev compiler
envelope.  It requires `operation.id == "dna.compile"`, a read-only side
effect, an allowed policy, an `ok` result, a controller-pinned graph/data key
set, and empty foreign evidence lists.  It rejects controller-authority fields.  It
retains the exact foreign bytes under the CB request run, reduces only node IDs
and `next`/`branches` targets to canonical `{nodes, edges}`, and then routes
that projection through the existing Rustworkx plus reference checker.  It
does **not** execute `op`, `eval`, descriptions, prompts, agents, hooks, or
profile-hint content from Lev.

```text
external Lev DNA compiler output
  -> CB strict foreign-observation intake + raw-byte digest/retention
  -> CB canonical topology projection
  -> Rustworkx + independent Python reference
  -> fixed CB controller decision
```

The caller must provide a captured compiler artifact; CB does not silently
spawn or trust a Lev runtime.  For the current bounded bridge:

```bash
cd /Users/joshuaeisenhart/lev-main
./core/poly/bin/lev dna compile dna/core/flowmind.dna.yaml --json \
  > /absolute/lev-dna-compile.json

cd /path/to/constraint_box
PYTHONPATH=src python \
  -m constraintbox formal run \
  --task formal.levos.flowmind_contract_structure \
  --request-id levos-flowmind-example \
  --payload /absolute/lev-dna-compile.json \
  --run-dir /absolute/cb-levos-flowmind-run
```

An eligible result says only that a supplied external artifact matched the
expected compiler-shaped envelope and controller-pinned topology, then had an
acyclic, reachable structural projection under the active compatible runtime. CB
does not authenticate the producer, the source path, or the owning Lev
checkout from JSON alone. It does not say that Lev executed the graph, that
its declared `eval` strings are true, that a Lev agent was leased, or that
ClaimGate/Lev admitted anything. Raw-byte retention is a local cooperative
filesystem receipt, not hostile-process containment.

### Lev eval artifact observation

The separate eval observer is intentionally narrower than a CB↔Lev execution
comparison. It is not a direct CLI side path: the public command builds one
fixed, historical-only Mini-Lev flow with exactly two nodes:

```text
observe-foreign-eval (TOOL: retain selected foreign bytes)
  -> OBSERVED
replay-verify-foreign-eval (GATE: replay retained CB bytes only)
  -> PASS
PARKED
```

There is no `ELIGIBLE`, `RELEASED`, ClaimGate, retry, lease, foreign-status
transition, or live Lev invocation in this flow. The controller fixes the
nodes, transitions, maximum two steps, and final `PARKED` ceiling. A foreign
`pass` and a foreign `fail` therefore cannot choose different CB terminals.

The flow takes an already-created historical Lev run directory plus the
controller-bound expected execution and suite identities. It requires exactly
these captured files as inputs:

```text
run.json
decision.json                 (lev.eval_decision.v1)
measurements.jsonl            (lev.measurement.v1 lines)
measurement-series/projection.json
seal.json                     (lev.run_seal.v1)
```

CB snapshots the raw bytes, hashes all five, requires every in-bundle path
reference to resolve to the selected run, recomputes the decision ID, the
available decision digests, measurement identities/generation/timestamps, and
the seal's intent, obligation, evidence, and outcome links. It explicitly
marks `trace_cases_digest` and `command_cases_digest` as **foreign and
unrecomputed**, because raw case-result arrays are absent from this bundle.
The current projection is checked as a deferred, unmaterialized projection;
it is not mistaken for a measurement-series proof.

The controller binds the selected source-directory text digest, expected
execution ID, expected suite ID, and current observer profile before capture.
This is a selected historical **path**, not a pre-capture immutable archive or
producer-authenticated manifest. Only scalar commitments enter the Mini-Lev
context and ledger: the controller request hash, retained-observation receipt
hash, and retained-snapshot hash. The raw source path and foreign
verdict/status do not become flow inputs or terminal selectors. A separate
durable binding record contains only the source-path hash and fixed IDs, never
the source-path text; `load_lev_eval_observation_flow()` uses it to replay the
persisted flow after process restart. The gate rereads the retained CB
snapshot, not the original Lev directory. Consequently the flow can replay
after the selected foreign directory is removed. A retained-byte, binding,
profile, symlink, or replay mismatch is `HOLD`; a missing or structurally
rejected historical foreign bundle is ordinary `PARKED` without a capture
receipt.

The retained five-file snapshot is a CB-private forensic artifact and copies
the foreign bytes exactly. Its `run.json` and `seal.json` may therefore include
the producer's absolute paths. That path privacy boundary applies to the
Mini-Lev receipt/ledger, CLI result, and durable binding record—not to the raw
snapshot itself. Do not expose the snapshot directory as a public report.

```bash
PYTHONPATH=src /declared/cpython \
  -m constraintbox.cli observe-lev-eval \
  --request-id historical-lev-eval-example \
  --source-run-dir /absolute/lev-eval-run \
  --expected-execution-id selected-lev-execution-id \
  --expected-suite-id selected-lev-suite-id \
  --run-dir /absolute/cb-lev-eval-observation-flow
```

A clean replay says only that CB captured and replay-checked a self-consistent
foreign Lev path under this fixed v1 contract; the CB result is still
`PARKED`. It does not say the suite ran a real sim, that a FlowMind graph
executed, that the foreign `pass` is true, or that Lev or ClaimGate admitted
the result. A later controller-owned comparator must combine a fresh CB engine
receipt with this retained observation before either can affect a CB task
decision.

Separately, CB's own bounded proposal flow now has one live controller-owned
lease boundary. The controller—not the provider, user request, or foreign Lev
artifact—chooses the fixed slot and state root. It performs `acquire`, verifies
ownership before and after the callback, and records a `RELEASED` or failed
release outcome in the hash-chained Mini-Lev receipt. A callback is not run if
acquisition fails; any lifecycle failure yields `HOLD`. Tokens never enter the
receipt. Its policy binds a monotonic clock domain derived from the stable
controller root, so an expired slot can be reclaimed by a later flow in that
same domain. A reboot, root move, or different host/domain remains `HOLD`
until an explicit future recovery protocol exists. This is deliberately only a
cooperative local filesystem lease around `proposal-observation`; it is not a
general agent lease, heartbeat protocol, OS sandbox, full-duration callback
fence, or proof about a Lev runtime.

The current Lev checkout does not yet produce a ClaimGate-ingestion artifact
for CB to consume. Its only ClaimGate-named material is a noncanonical inbox
memo; the active `lev gate validate` path validates Lev AgentFS gate events,
not ClaimGate evidence. CB can retain that memo as untrusted explanatory
context, but it has no formal task or authority effect. A future bridge needs
an explicit source-identified artifact schema and a fresh producer/consumer
command receipt before it becomes an integration.

### Extraction and comparison order

| Order | CB-owned addition | External comparison | Gate before moving on |
|---:|---|---|---|
| 1 | fixed FlowSpec / graph projection | Lev DNA compile artifact | strict input, raw digest, Rustworkx/reference agreement |
| 2 | fixed two-node historical Lev eval observation flow | captured `lev.eval_decision.v1` / `lev.run_seal.v1` bundle | retained-byte replay must pass before a fixed `PARKED`; it must not claim a suite executed a real sim |
| 3 | formal skills and deterministic evaluator registry | selected Lev evaluator command case | retained command receipt must show a real checker executed, not path/trace-only evidence |
| 4 | hook-bound execution lease | first live Mini-Lev `proposal-observation` visit | done for one hook: acquire, verify before/after, and release on success or failure; every later hook must opt in explicitly |
| 5 | sim-engine foreign-observation adapters | Lev sim-witness evaluator | fresh CB engine receipt, source/reference digests, and separately retained host receipt |
| 6 | fixed field comparator | live Lev result/seal | controller blocks any mismatch; neither side can promote |

This order prevents the common false green: a package, path, JSON envelope, or
LLM explanation looking integrated when no deterministic consumer actually
ran.

From `constraint_box/`, build and verify a new artifact with:

```bash
python scripts/build_contained_core_bundle.py \
  --output /absolute/output/constraintbox-core-0.3.4.zip

python scripts/verify_contained_core_bundle.py \
  --bundle /absolute/output/constraintbox-core-0.3.4.zip \
  --receipt /absolute/output/contained-core-verification.json
```

The verifier checks every archive member and manifest digest, extracts to a
fresh temporary directory, then runs this exact core surface:

| Operation | Expected result | Boundary proved |
|---|---|---|
| `constraintbox runtime verify` | exit `0` / `ELIGIBLE` | active interpreter and core libraries satisfy a declared portable profile; it does not select/install a runtime |
| `constraintbox demo` | exit `0` | core runtime is loadable |
| `constraintbox mmm smt --json` | exit `0` | local MMM/context inputs resolve |
| missing-assumptions request | exit `4` | deterministic intake parks rather than inventing assumptions |
| typed exact SymPy task | exit `0` | bounded exact symbolic checker runs |
| typed CB/sim boundary, valid fixture | exit `0` / `ELIGIBLE` | declared CB, formal-runtime, sim, and evidence roles stay disjoint |
| typed CB/sim boundary, conflated fixture | exit `1` / `BLOCKED` | an external sim profile cannot be relabeled as CB core |
| typed CB/sim boundary regression unit | exit `0` | positive, conflation, malformed, and mutation cases remain fail-closed |
| real Maude transition task | exit `0` / `ELIGIBLE` | the named bounded rewrite operation runs; this is not hostile-process containment |
| absent external TLC/Apalache runtime | exit `4` / `PARKED` | missing temporal JARs cannot become a simulated pass |
| pinned Lev-shaped FlowMind fixture | exit `0` | contained Mini-Lev foreign-observation structural gate runs; the fixture does not attest an external Lev producer |
| source-only origin-bound failure-repair unit | exit `0` | synthetic receipts and results cannot select repair; the broader controller-flow fault injection requires the separate external estate |
| Mini-Lev execution-lease unit | exit `0` | fixed hook lifecycle exercises success, expiry, callback failure, and failed release; it makes no live-provider or hostile-process claim |
| integrated receipt/lease/Mini-Lev unit | exit `0` | lease state and retained flow receipts agree under the bounded integrated path |
| fixed Mini-Lev Rustworkx topology unit | exit `0` | controller-owned proposal flow executes the pinned Rustworkx DAG/reachability profile and independently replays the receipt; its callbacks are test doubles, not LLM or provider evidence |
| foreign Lev eval-observation unit | exit `0` | contained adversarial fixtures prove the five-file observer rejects altered in-bundle relationships and retains no foreign decision authority |
| fixed Mini-Lev foreign-eval observation-flow unit | exit `0` | contained fixtures exercise retention, retained-byte replay, deleted-source replay, tamper-to-`HOLD`, and foreign `fail` remaining `PARKED`; no foreign field can select a positive CB terminal |
| contained Leviathan-reference unit | exit `0` | one fixture-bound structural Mini-Lev comparison runs; no live Lev or whole-Lev equivalence is claimed |
| external-validation runner unit | exit `0` | the adapter's dispatch/verification boundary remains typed; no external estate is installed by this check |
| Hypothesis adversarial-intake unit | exit `0` | structured hostile cases remain tests with no production decision authority |
| external-validation index unit | exit `0` | evidence-index status and role declarations remain internally consistent |
| contained provider-harness unit | exit `0` | provider output stays untrusted and cannot select controller authority |
| proposal-provider-policy unit | exit `0` | the static provider seam cannot choose transitions, release, or promotion |
| attractor-basin adapter boundary unit | exit `0` | packaged adapter source remains external-engine-facing rather than a bundled engine runtime |
| attractor-basin controller `--help` | exit `0` | the opt-in controller CLI is path-portable and inspectable; no engine runs |
| attractor-basin envelope verifier `--help` | exit `0` | the independent verifier CLI is present and inspectable; no prior receipt is admitted by help output |
| external-engine box request | exit `4` / `PARKED` | missing external estate cannot become a host-path or fake engine pass |
| in-box ClaimGate clean fixture | exit `0` | local chain resolves and runs inside the extracted box |
| in-box ClaimGate under-depth fixture | exit `3` | the same chain refuses insufficient depth |

The nonzero outcomes are expected fail-closed results, not admissions or
promotion.  Every verification receipt remains `promotion_allowed: false`.

## Sim engines stay external

The sim engine estate is outside CB.  CB may dispatch a declared engine profile
and validate its returned receipt, but a missing estate must park or fail; it
must never be substituted by an import check, NumPy-only calculation, or
handwritten JSON claiming a different engine ran.

The contained suite controller owns one narrow integration feedback hook.  In
fixed profile order, its first verified non-pass consumes the only decision. A
closed `fresh_rerun` mapping can cause exactly one derived, same-capability
fresh child and independent replay under the suite directory; every other
mapping records zero execution attempts and stops the hook. The hook cannot
change source, dependencies, environment, profile, command, verifier,
tolerance, release, promotion, or tuning state, and it accepts no LLM or user
action choice. Its receipt remains `PARKED` even when the new external check
is eligible. This is a deterministic test-and-evidence loop for the external
estate, not automatic repair or a claim that all simulation engines are ready.

```text
contained CB core --dispatches/validates--> external sim workload
external sim workload --returns bound receipt--> contained CB gate/ledger
```

An engine receipt needs bounded inputs, actual operations, positive/wrong/
boundary controls, source/runtime identity, and an identified consumer where
there is a handoff.  A local profile result is not broad engine readiness,
external-estate admission, a CR claim, or release.

## Feedback and tuning status

CB catches concrete issues—missing assumptions, unsat clauses, wrong-polarity
controls, operation severance, source/runtime drift, GPU unavailability, and
receipt refusal.  The bounded external-capability path now has its first live,
deterministic failure consumer:

```text
fixed dispatcher + external capability receipt + retained Mini-LevOS ledger
  -> canonical capability_flow_result.json + controller_origin_attestation.json
  -> fixed-origin check + current semantic-ledger replay
  -> capability-failure event
  -> controller-selected repair_plan.json
```

`engine-test --capability` and `capability-suite` persist the canonical result
only after a fixed dispatcher selected the registered runner, then retain a
result-bound `controller_origin_attestation.json`. The suite independently
requires that sidecar, the static capability-to-flow map, current source pins,
and semantic ledger replay before a component can appear eligible. For a
verified `BLOCKED` or `PARKED` result, they also write one `repair_plan.json`
beside the capability artifacts. The plan binds the origin attestation, parent
receipt, flow receipt, retained ledger head, flow policy, and runtime identity.
It uses a closed status/reason table; an unrecognized reason maps to `park`.
A `PASS` cannot be converted into a repair plan, and handwritten or merely
self-consistent JSON cannot enter this consumer path.

The first end-to-end non-pass rehearsal is a separate source-owned external
instrument, not a public capability option: a registered SciPy profile runs a
real isolated `scipy.linalg.expm` operation, then only its replay call is
routed through the existing controller-selected operation poison. Its retained
`failure_rehearsal_result.json` binds the `BLOCKED` receipt, origin
attestation, zero-authority `fresh_rerun` plan, and the later unpoisoned
same-profile rerun. The plan itself still has zero authorized actions. The
non-pass receipt validator checks the retained normal/replay/severance rows,
source/runtime/artifact pins, recomputed controls, and exact severance record
before the plan can be accepted. The fixed suite hook then independently
replays the clean fresh run and retains `PARKED` review state. This proves one
deliberately induced real-worker failure reaches the deterministic planning and
follow-up boundaries; it does not assert a natural SciPy fault, automatic
repair/tuning, engine readiness, release, promotion, or LLM authority.

The fourteen-profile `capability-suite` uses a fixed two-child pattern for each
component: one fresh CPython child dispatches the controller-selected external
profile, and a second fresh CPython child independently replays the retained
origin, Mini-LevOS ledger, and capability-specific receipt validator. The
parent aggregates only the compact replay result. This keeps optional native
library state from a prior profile from becoming evidence for a later one, and
turns a child crash, timeout, malformed output, or replay failure into an
`EVALUATION_ERROR` component rather than an eligible aggregate. It remains a
bounded profile suite, not proof that arbitrary simultaneous or mass
multi-engine simulations are integrated.

This is deliberately still a non-executing contract. Every plan has
`execution_authorized: false` and zero authorized attempts. It cannot install
a dependency, modify source, launch a rerun, change a tolerance, choose a
verifier, release, promote, or let an LLM decide any of those things.

The contained core now provides one **separate**, explicitly acknowledged
bounded follow-up for a plan whose closed controller mapping selected only
`fresh_rerun`:

```text
verified non-executing repair contract
  -> explicit fixed acknowledgement + new disjoint output directory
  -> same fixed dispatcher and plan-bound capability only
  -> parent re-derivation after dispatch
  -> in-process receipt replay + second fresh CPython replay child
  -> linked repair_outcome.json (outer PARKED; human review required)
```

The command takes no capability, request ID, action, worker, command, profile,
verifier, tolerance, retry, or output override. Its new request ID is derived
from the plan digest; the profile generates a fresh controller challenge under
the unchanged fixed profile/fixture definition. Before an outcome is retained,
CB requires the same capability, flow policy, controller registry, full
origin/runner/issuer source pins, and runtime identity. It revalidates the
parent after the external run, so drift prevents `repair_outcome.json` from
being written. A successful rerun remains `FRESH_RERUN_ELIGIBLE_REVIEW_REQUIRED`
with `repair_resolved: false`; it does not repair a source or environment,
spend the plan's zero retry budget, establish engine readiness, or permit
release/promotion.

Only the deterministic controller selects a permitted repair category. No LLM
repair proposal is consumed; no later proposal path may redefine the verifier,
alter tolerances, declare success, or promote the result.
