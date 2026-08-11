# ConstraintBox

**Status:** local candidate; `promotion_allowed: false`

ConstraintBox is a deterministic harness around untrusted user requests and
LLM proposals. The controller—not the user, an LLM, or an instrument—owns the
task registry, profiles, bounds, runtime policy, claim ceilings, disposition,
and release decision. An LLM may propose, criticize, explain, or repair. It
cannot choose its verifier, waive a failed check, reinterpret a receipt, or
release its own output.

ConstraintBox is deliberately smaller than the simulation estate and
Codex-Ratchet (CR). The sim engines and CR supply difficult external workloads
that ConstraintBox can run and constrain. They are not the ConstraintBox
kernel.

## v9 default CLI

The v9 default entrypoint is intentionally small. Its supported core commands
are `python -m constraintbox doctor --json` and `python -m constraintbox
exercise --json`; these are the independent acceptance routes declared by
`PRODUCT_BOUNDARY.v9.json`. Historical wide-CLI commands are retained behind
the named `constraintbox-legacy` entrypoint. ClaimGate composition is an
external legacy surface: use `constraintbox-legacy gate <receipt>` only with a
complete source/plugin installation. It is intentionally not advertised by the
lean default CLI or claimed by its clean-wheel verifier.

The boundary is enforced by role-bearing identifiers, not a flat library list:
`cb:*` is contained controller/gate/mini-Lev/adapter code; `sim:*` is one
external operation profile used as a test subject; `formal-runtime:*` is an
externally configured temporal checker; and `evidence:*` is a receipt or
index, not a component. A library can occur on either side only when its role
is explicit. See [`docs/BOUNDARY_CONTRACT.md`](docs/BOUNDARY_CONTRACT.md).

## Formal kernel boundary

| Item | Kind | Current role | Default formal admission |
|---|---|---|---|
| CPython 3.11, 3.12, or 3.13 plus selected stdlib | explicit base runtime | executes the controller, bounded reference methods, hooks, ledgers, receipts, and brokers | active interpreter must satisfy one declared portable core profile |
| Z3 | external SMT solver | bounded request-obligation decision and feedback | request gate |
| CVC5 | external SMT solver | independent bounded request-obligation decision and feedback | request gate |
| bounded exhaustive enumeration | internal Python reference method, not a tool or package | checks the finite encoding against both solver results | request gate |
| SymPy | external symbolic library | controller-built, typed, exact univariate polynomial check over `QQ` | fixed formal task |
| Rustworkx | external graph library | bounded DAG, topological-order, and required-reachability mechanics | fixed formal task |
| Mini-LevOS | CB-native Python execution kernel | typed hooks, frozen transition maps, retry bounds, leases, hash-chain ledger, and replay | controller-owned formal flow machinery |
| Maude | external rewrite engine | observes one bounded transition from a controller-owned transition table | fixed formal task |
| TLC and Apalache | external offline model checkers | independently check the same hash-pinned candidate single-run abstract state-ordering skeleton, four narrow invariants, and evidence-removal mutant | fixed offline pair |
| Hypothesis | test library | fixed-seed deterministic hostile generation and regeneration in tests | test-only decision role; diagnostic inventory may import it |
| NumPy | optional numeric library | allowed for a future bounded numeric profile or an external workload | allowed, but not a default formal task |
| Leviathan dry-run reference | optional external comparison adapter | observes one named Lev control-plane shape and seal under `--dry-run` | never a kernel dependency or decision authority |

“Finite enumeration” does not name a solver. It is a small internal reference
procedure executed by the active profile-verified CPython runtime over an already bounded finite
domain. Z3 and CVC5 are the actual external SMT tools.

NumPy is not banned. It remains available through the `numeric` extra and can
be used when a bounded numeric task earns a precise contract. The existing
NumPy profile is not registered in the default formal task policy. PySINDy and
the other NumPy-backed simulation workloads remain outside the kernel.

Mini-LevOS is not an LLM-authored Lev clone.  It is the small Python controller
inside CB.  The optional Leviathan adapter runs only an isolated `lev exec
--dry-run`, verifies a limited FlowMind graph/seal correspondence, and proves
that proof-bearing Lev execution is rejected.  It does not import a provider,
model profile, heuristic evaluator, or escalation authority.  See
[`docs/LEVIATHAN_MINILEV_CONFORMANCE.md`](docs/LEVIATHAN_MINILEV_CONFORMANCE.md).

## Fixed controller tasks

The request may choose only a registered task name and supply that task's
typed payload. It cannot select a library, profile, tolerance, bounds, solver,
runtime, timeout, or verdict.

| Task kind | Controller-owned operation | Claim ceiling |
|---|---|---|
| `formal.boundary.constraintbox_scope` | fixed typed CB/core/formal-runtime/sim-profile/evidence registry, checked by Z3, CVC5, and bounded CPython enumeration | typed role separation only; not arbitrary-prose interpretation or engine readiness |
| `formal.symbolic.polynomial_qq` | SymPy `Poly(..., domain=QQ).as_dict()` built only from bounded integer rational fields, then checked against a `fractions.Fraction` reference | one exact bounded coefficient claim |
| `formal.workflow.prerequisite_dag` | Rustworkx DAG, topological-order, and controller-required `intake -> proposal_ready` reachability, cross-checked by a small stdlib implementation | one declared finite dependency graph; no node-semantics or workflow-correctness claim |
| `formal.transition.current_box_phase` | one Maude root-rule application using controller-owned states, actions, transition table, worker source hash, version, and bounds | one declared transition; no truth, confluence, termination, or liveness claim |

The CLI accepts formal payloads only from regular files and reads at most the
controller limit plus one byte. The controller independently checks byte
length before request-ID validation, full hashing, profile lookup, or parsing.
An oversized request gets `input_sha256: null` and a bounded-prefix
commitment; it is never represented as though a complete input digest was
computed.

The SymPy and Rustworkx profiles require the active core profile's compatible
library window and load-bearing live API bindings. A receipt records the local
distribution origin and digest that actually ran, but a path or native-wheel
hash from one developer machine is not global policy. Maude is a declared
core dependency. Its compatible distribution version and live API
surface are policy; local wrapper/native-library hashes are only per-run
parent-to-worker binding observations. The worker has capped output,
process-group teardown, a controller timeout, and a host-enforceable CPU and
memory policy. It is still not a general OS sandbox or hostile-code boundary.

The formal command surface is:

```bash
PYTHONPATH=src \
  python \
  -m constraintbox formal list

PYTHONPATH=src \
  python \
  -m constraintbox formal run \
  --task formal.symbolic.polynomial_qq \
  --request-id example-symbolic-1 \
  --payload fixtures/formal/symbolic_polynomial_valid.json \
  --run-dir /tmp/constraintbox-formal

PYTHONPATH=src \
  python \
  -m constraintbox formal temporal
```

`formal temporal` runs both TLC and Apalache under a hash-pinned controller
policy. The candidate model is only one bounded, abstract, single-run
state-ordering skeleton from `RECEIVED` to a terminal label, with four narrow
invariants and an evidence-removal negative control. It does not establish
Python implementation correspondence or conformance, retry or lease behavior,
release correctness, liveness, concurrency, refinement, general correctness,
or sim-estate admission. The TLC and Apalache JAR contents are hash-pinned.
Install those two JARs into one explicit directory, set
`CONSTRAINTBOX_FORMAL_RUNTIME_DIR` to that absolute directory, and make a
compatible `java` available on `PATH`. CB resolves those installation facts at
runtime, then checks the JAR bytes, Java version, positive run, mutation, and
replay. There are no source-embedded developer paths. With the directory
absent, `formal temporal` is `PARKED`; it never substitutes a Python mock.

```bash
export CONSTRAINTBOX_FORMAL_RUNTIME_DIR=/absolute/path/to/formal-runtime
# That directory contains tla2tools.jar and apalache-0.58.3/lib/apalache.jar.
python -m constraintbox formal temporal
```

The SymPy and Rustworkx operations currently execute in the controller
process. Their typed input and returned evidence are bounded, but they do not
have a separate OS CPU or address-space sandbox. The live-binding checks are
not a claim that a host-level or co-resident arbitrary-code compromise can be
contained by Python introspection.

## Installation groups

The Python dependencies are split by actual role:

```bash
# First select the intended CPython 3.12 or 3.13 interpreter, then create an
# isolated environment.  The commands below work unchanged on macOS and Linux.
python -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python -m constraintbox doctor --json
.venv/bin/python -m constraintbox exercise --json
.venv/bin/python -m pip check

# Windows PowerShell uses the same Python-module interface with this path:
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\python.exe -m constraintbox doctor --json
.venv\Scripts\python.exe -m constraintbox exercise --json
.venv\Scripts\python.exe -m pip check

# Optional bounded profiles; none widens the five-tool core.
python -m pip install '.[numeric]'        # future numeric/external workload support
python -m pip install '.[test]'           # test-only Hypothesis
python -m pip install '.[control-plane]'  # local Pydantic/jsonschema evaluation
```

The base install contains the lean controller dependencies: Z3, CVC5, SymPy,
Rustworkx, and Maude. The default v9 `doctor` and `exercise` commands inspect
and exercise the interpreter that actually invoked them; they never choose a
different Python or turn an absent dependency into a pass. Historical wide-CLI
verification remains explicitly separate as `constraintbox-legacy runtime verify`.
The macOS/Linux/Windows portability matrix is a separate adoption proof: a
successful local installation is not portable adoption.

The wheel currently packages the Python package and the formal-runtime policy,
model, configuration, and expectations needed by the `formal` surface. Several
older non-formal CLI commands still resolve checkout-relative profiles,
fixtures, workers, or ClaimGate material that are not wheel resources. Thus a
source-free formal-kernel wheel is testable now; a source-free standalone wheel
for every historical CLI surface is not yet complete.

Z3 and CVC5 are base dependencies because the two-solver request gate is
central rather than optional. SymPy, Rustworkx, and Maude are also base
dependencies because their bounded formal tasks are load-bearing. `test` adds Hypothesis; it does not promote
Hypothesis into runtime policy. The larger JAX, PyTorch, Julia, SciPy, PySINDy,
PyDMD, tensor-network, topology, or CR stacks are intentionally not packaging
extras of this lean kernel.

The first bounded external packet is governed separately by
[`docs/EXTERNAL_SIM_RUNTIME_CONTRACT.md`](docs/EXTERNAL_SIM_RUNTIME_CONTRACT.md):
it uses controller-selected portable runtime profiles and real fixed operation
checks, while un-migrated satellite adapters remain external test targets.

## Registered CR sim slice

The external CR estate can be invoked through a fixed, source-addressed CB
manifest without making CR part of the CB kernel:

```bash
PYTHONPATH=src python -m constraintbox cr-slice \
  --profile foundation-seed \
  --cr-root /Users/joshuaeisenhart/Codex-Ratchet \
  --run-dir /private/tmp/cb-cr-foundation-run
```

The finite paired whole-extension carrier is available as a separate bounded
profile:

```bash
PYTHONPATH=src python -m constraintbox cr-slice \
  --profile paired-extension \
  --cr-root /Users/joshuaeisenhart/Codex-Ratchet \
  --run-dir /private/tmp/cb-paired-extension-run
```

It runs Julia, JAX, and PyTorch lanes over one fixture and then rechecks a
three-engine envelope. The packet is external, candidate-only, and promotion
disabled; it is not a claim that CR or a physical manifold has been validated.

The execution-first IJK prototype has a separate telemetry-only command. It
runs the fixed source into an isolated output directory and captures its
checks, path/basin measurements, and interpretation lock without turning a
false check into a launch veto:

```bash
PYTHONPATH=src python -m constraintbox exploratory-ijk \
  --cr-root /Users/joshuaeisenhart/Codex-Ratchet \
  --run-dir /private/tmp/cb-ijk-exploratory-run
```

`status: EXECUTED` means the source and its receipt ran; it does not mean all
checks are true. The command is external to the CB kernel, validation- and
promotion-disabled, and intended to expose model/engine/gate issues together.

The `foundation-seed` profile runs the registered Julia, JAX, and PyTorch F01
and N01 lanes plus their three-engine envelopes. `cr-gksl-source` runs the
registered system_v7 source and the CB-facing fixture derivation. The runner
records source/result hashes, selected Python/Julia runtime facts, argv,
bounded stdout/stderr, and a controller recheck of each declared JSON receipt.
Missing runtimes park; non-zero processes, malformed results, or source/result
mismatches fail. Every result is marked `external_system:true`,
`kernel_membership:EXTERNAL_NOT_CB_KERNEL`, `cr_truth_claim:false`, and
`promotion_allowed:false`.

The companion finite seed is checked with:

```bash
PYTHONPATH=src python -m constraintbox manifold-foundation \
  --fixture fixtures/cr/manifold_time_first_seed_v1.json
```

This seed uses finite support capacity `K_0=log2(|S|)` and a typed `Z` boundary
object, then records two order words and leaves nonassociativity as a candidate
layer. It is a scratch diagnostic, not a physical-manifold or CR-validation
claim. See [`docs/07_CR_SIM_SLICE_INTEGRATION.md`](docs/07_CR_SIM_SLICE_INTEGRATION.md)
and [`docs/08_MANIFOLD_FOUNDATION_TIME_FIRST.md`](docs/08_MANIFOLD_FOUNDATION_TIME_FIRST.md).

## First composed box run

```bash
PYTHONPATH=src \
  python \
  -m constraintbox box \
  --request fixtures/requests/assemble_constraintbox_v1.json \
  --run-dir /tmp/constraintbox-first-run
```

This older composed path performs strict request intake, source-bound
MMM/context compilation, and bounded external function tests, including one
PySINDy-to-Julia serialized-artifact handoff. Those engine operations are
external workloads governed by the box, not formal-kernel dependencies.

A passing composed run stops at `READY_FOR_UNTRUSTED_PROPOSAL`. It does not
release an LLM answer. The external audit brief is suitable for an advisory
audit/explainer LLM, but returned advice cannot alter the deterministic
receipt.

The bounded proposal path now accepts only that verified box snapshot:

```bash
PYTHONPATH=src \
  python \
  -m constraintbox run \
  --box-run-dir /tmp/constraintbox-first-run \
  --run-dir /tmp/constraintbox-agent-run
```

Direct task files are disabled. Before creating the agent run or loading a
provider, `run` captures and revalidates the exact box artifact set, request
assessment, current profile compilation, personalized context, and external
PASS receipt. The request, profile, context, packet, and box-receipt hashes
are carried into the prompt, provider input references, final receipt, and any
release receipt. The personalized MMM is therefore part of the actual prompt
rather than a sibling artifact.

The public runner accepts only `--box-run-dir` and `--run-dir`. It exposes no
provider, runtime, command, timeout, or ClaimGate override; deterministic
production choices are fixed by the controller. An explicitly private
injectable helper exists only for offline unit controls and does not establish
hostile-process containment.

The provider/notary code used by that path is inside CB at
`constraintbox._provider_harness`; it is not imported from a parent Ratchet
checkout. Before a real proposal run, the deployer must set an absolute
`CONSTRAINTBOX_RUNTIME_DIR` for local signing keys. A missing location parks
instead of writing under a home directory. See
[docs/MINILEV_PROVIDER_RUNTIME.md](docs/MINILEV_PROVIDER_RUNTIME.md).

The default proposal route is the contained local tool. A deployer may instead
set `CONSTRAINTBOX_PROPOSAL_PROVIDER=openrouter` with `OPENROUTER_API_KEY`, or
`CONSTRAINTBOX_PROPOSAL_PROVIDER=nvidia` with `NVIDIA_API_KEY`. Each route has
a fixed controller-owned model and policy digest; no request, LLM output, or
CLI flag supplies a model id. A selected remote route with no key parks rather
than falling back to Codex. These are offline-tested adapters, not evidence of
live provider availability, free quota, or remote-model admission.

This is one fixed two-attempt proposal profile for a bounded external-tool
claim. Its retries now run through the generic Mini-LevOS executor. The
proposal-observation hook is the first hook inside a controller-owned lease
lifecycle: acquire, verify before the callback, invoke it, verify after it,
then release; a failed lease stage becomes `HOLD`. The lease slot is selected
by the controller outside the per-run receipt directory, and its monotonic
clock domain is derived from that stable local controller root rather than a
random flow ID. An expired same-domain slot can therefore be reclaimed by a
later flow; a reboot, root move, or different host/domain remains a manual
fail-closed recovery case. Only nonce-free public records enter the
hash-chained receipt. This is still not a general user-task completion loop:
no heartbeat is enabled in this first binding, no other Mini-Lev hook is
leased, and it is not hostile-process containment or full-duration fencing of
an uninterruptible callback.

The path still reaches an older direct ClaimGate path that lacks the planned
standing, floor, evidence seal, and keyed ledger composition. `RELEASED` on
this narrow path must not be read as canonical, scientific, or production
admission.

The two optional hosted explainers are separate post-decision sidecars:

```bash
NVIDIA_API_KEY=... PYTHONPATH=src \
  python \
  -m constraintbox advise \
  --box-run /tmp/constraintbox-first-run \
  --provider nvidia \
  --run-dir /tmp/constraintbox-nvidia-advice

OPENROUTER_API_KEY=... PYTHONPATH=src \
  python \
  -m constraintbox advise \
  --box-run /tmp/constraintbox-first-run \
  --provider openrouter \
  --run-dir /tmp/constraintbox-openrouter-advice
```

The fixed registry targets NVIDIA's hosted
`nvidia/nemotron-3-nano-30b-a3b` route and OpenRouter's `openrouter/free`
router. Availability and pricing are external mutable facts, so every receipt
sets `billing_verified: false`; a provider-reported zero cost is metadata, not
an admission claim. Missing credentials, rate limits, quota failures, and
unsupported model or JSON-mode behavior park only that sidecar. The two
providers never vote, change the box disposition, trigger a retry, or acquire
release authority.

The complete proposal, repair, lease, and release system remains narrower than
the intended ConstraintBox; its current connection and ceilings are indexed
below rather than implied by the advisory path.

## External simulation systems

- `../external_sim_estate/basic_packet_v1/` contains current function-level
  workers and neutral fixtures.
- `../external_sim_estate/legacy_estate_v2/` contains older full-estate
  material kept for provenance and maintenance tests.
- `src/constraintbox/external_engine_packet.py` is a narrow broker and
  controller-owned comparator, not evidence that an engine belongs to the
  kernel.

Each external result is function-specific. It does not establish whole-engine
readiness, scientific truth, CR admission, production containment, or
canonical status. Failures in these separate workloads are useful test fuel
for improving ConstraintBox without conflating the workloads with the box.

For the one explicit controller-owned external validation run (all fixed
profiles, formal instruments, and an optional live Lev dry-run comparison),
use [`docs/EXTERNAL_VALIDATION_RUNBOOK.md`](docs/EXTERNAL_VALIDATION_RUNBOOK.md).
It records runtime locations as deployer inputs rather than treating either the
sim estate or Lev as a bundled CB dependency.

The first external operation routed through the mini-LevOS kernel is:

```bash
PYTHONPATH=src \
  python \
  -m constraintbox engine-test \
  --capability pytorch-jacobian-v1 \
  --request-id example-pytorch-1 \
  --run-dir /tmp/constraintbox-pytorch-example
```

The controller creates a fresh bounded mathematical challenge. A pinned worker
executes one real `torch.func.jacrev` operation; a separate deterministic gate
re-derives the expected result and negative/boundary controls. The mini-LevOS
path is `TOOL OBSERVED -> GATE PASS -> ELIGIBLE`. The result is still external,
sets `release_allowed: false`, and makes no whole-PyTorch or sim-stack claim.

Every dispatched capability run now retains a canonical
`capability_flow_result.json` and a result-bound
`controller_origin_attestation.json`. The attestation names the fixed runner,
registered flow, current source pins, and registry digest. Before a suite row
or repair plan can consume the result, CB independently checks that origin and
replays the retained Mini-LevOS ledger. A verified non-pass is then consumed by
the deterministic repair planner, which writes `repair_plan.json` in the same
run directory. The planner uses a closed controller mapping; unknown reasons
stop at `park`. Its output has `execution_authorized: false` and zero attempts,
so it cannot secretly retry, install packages, edit source, change a
verifier/tolerance, release, or
promote. A passing external operation creates no repair plan.

The corresponding failure proof is a separate fixed source-owned instrument,
not a public fault switch. It has no capability, worker, operation, tolerance,
provider, or retry argument:

```bash
PYTHONPATH=src python -B scripts/run_failure_rehearsal.py \
  --run-root /absolute/new/cb-scipy-failure-rehearsal
```

It first performs a real isolated `scipy.linalg.expm` operation, then sends
only the replay worker through the controller-owned operation-severance path.
The resulting `BLOCKED` receipt is origin-attested and mapped to a
`fresh_rerun` repair plan with zero authorized attempts. The same fixed
instrument then runs the unpoisoned same-profile fresh rerun and independently
replays it; the outer outcome remains `PARKED` for review. This demonstrates
that CB catches and preserves a bounded external-operation failure. It does
**not** claim that SciPy failed naturally, that CB repaired/tuned anything, or
that an LLM has authority over the process.

There is now one separately invoked, fixed follow-up for a verified plan whose
controller-selected action is exactly `fresh_rerun`:

```bash
PYTHONPATH=src \
  python \
  -m constraintbox repair-outcome \
  --capability-run-dir /absolute/failed-capability-run \
  --run-dir /absolute/new-disjoint-rerun \
  --execute-fresh-rerun
```

The acknowledgement is an explicit invocation boundary, not authority granted
by `repair_plan.json`: that plan remains `execution_authorized: false` with
zero automatic attempts. The command accepts no capability, request ID,
action, worker, command, profile, verifier, tolerance, retry, or output
override. It regenerates the parent plan; dispatches only its fixed capability
into a new disjoint directory; compares the new flow policy, controller
origin/runner/issuer pins, and runtime identity; and runs a second fresh
CPython receipt verifier. It then writes `repair_outcome.json`. Even if the
new profile receipt is `ELIGIBLE`, the outer outcome remains `PARKED`, with
`repair_resolved: false`, `human_review_required`, and no release or promotion.

`capability-suite` does not let one loaded process stand in for the whole
estate. For every fixed profile it uses one fresh controller-selected CPython
child to execute the profile and a second fresh child to replay the origin,
Mini-LevOS ledger, and capability-specific receipt validator. The small parent
aggregates only those verified summaries. A child crash, timeout, malformed
result, source/runtime drift, or replay failure is an `EVALUATION_ERROR`, not
a pass. This is useful integration pressure for CB and for the sim estate, but
it is still not a broad all-engine readiness or simultaneous-mass-simulation
claim.

After those fixed checks, the suite itself makes at most one repair decision:
the first non-eligible component in the controller's fixed order consumes it.
If its independently replayed closed repair table says `fresh_rerun`, CB alone
derives a new sibling directory and runs exactly one same-capability fresh
child plus independent replay. The result is retained under
`controller_fresh_reruns/` and bound into both that component and the suite
receipt's `repair_hook`. It is still `PARKED`, unreleased, unpromoted, and
unresolved. If the first non-pass selects any other action, the receipt records
`NOT_EXECUTED` with zero attempts; it does not skip ahead to retry a later
failure. The hook has no CLI action/capability/worker/verifier/tolerance
override, does not edit source or the environment, and has no LLM decision
authority. An invalid hook outcome becomes `EVALUATION_ERROR`.

For a controller-owned run produced by direct Python dispatch, the same bounded
consumer can be invoked explicitly:

```bash
PYTHONPATH=src \
  python \
  -m constraintbox repair-plan \
  --capability-run-dir /absolute/capability-run
```

It accepts no user-selected action, model, command, verifier, tolerance, or
output path. It refuses noncanonical inputs, altered sidecars, a changed
ledger, or an `ELIGIBLE`/`PASS` result.

## Tests and current status

```bash
PYTHONPATH=src \
  python \
  -m unittest discover -s tests -v
```

Use `constraintbox request` for the user/MMM/SMT front door and
`constraintbox engine-test` for the external function packet. See
[`docs/FORMAL_KERNEL_STATUS.md`](docs/FORMAL_KERNEL_STATUS.md) for the indexed
admission, removal, ceiling, and build-order audit. The contained Mini-LevOS,
LevOS, and external-sim boundary is maintained in
[`docs/CONTAINED_CORE_PRODUCT.md`](docs/CONTAINED_CORE_PRODUCT.md).
The executable Leviathan-to-Mini-Lev reference boundary is documented in
[`docs/LEVIATHAN_MINILEV_CONFORMANCE.md`](docs/LEVIATHAN_MINILEV_CONFORMANCE.md).
The operational external-run boundary and receipt layout are in
[`docs/EXTERNAL_VALIDATION_RUNBOOK.md`](docs/EXTERNAL_VALIDATION_RUNBOOK.md).
The contained, opt-in three-engine attractor-basin challenge and its strict
CB-core versus external-sim boundary are documented in
[`docs/ATTRACTOR_BASIN_EXTERNAL_VALIDATION.md`](docs/ATTRACTOR_BASIN_EXTERNAL_VALIDATION.md).
