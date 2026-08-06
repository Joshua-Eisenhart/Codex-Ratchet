# CR and simulation-tool integration index

This index separates the CB controller, its fixed external capability flows,
and the source-addressed CR slice. “Integrated” is not one boolean: a row may
have a real tool call while lacking a portable installation proof, a CR caller,
or a downstream admission gate.

## Levels

| level | meaning |
|---|---|
| CB-kernel | controller-owned parser, finite reference method, formal tool, Mini-LevOS transition, ClaimGate, or receipt gate can decide a CB disposition |
| tool→gate | a fixed external operation invokes a named API and a deterministic CB flow checks its bounded receipt |
| tool→gate→replay | the operation and its flow receipt are independently replayed in a fresh child |
| source→receipt | CB invokes a registered CR source, records source/result/runtime hashes, and rechecks the declared receipt shape |
| envelope | a source-produced multi-lane result is consumed/rechecked as a bounded external artifact |
| admission | a downstream CB gate consumes the evidence; this index does not treat source→receipt as admission |
| deferred | source or adapter exists, but the required caller, clean installation, runtime, or consumer is missing |

## CB-owned controller surface

| system/tool | functions | level | ceiling |
|---|---|---|---|
| CPython controller | strict intake, bounded enumeration, dispatch, receipt hashing | CB-kernel | controller behavior only |
| Z3 + CVC5 | bounded request/formal obligations and negative controls | CB-kernel | named finite obligations |
| SymPy | typed rational polynomial check | CB-kernel | one bounded exact task |
| Rustworkx | finite prerequisite/flow DAG and reachability | CB-kernel | one declared graph |
| Maude | one fixed transition observation | CB-kernel | one bounded rewrite transition |
| Mini-LevOS | typed TOOL/GATE flows, budgets, leases, ledgers, replay | CB-kernel | controller flow only; not full LevOS |
| ClaimGate | in-box receipt grammar and evidence-depth gate | CB-kernel | named CB receipts; no CR truth |
| manifold validator | finite support, `K_0=log2(|S|)`, order gap, layer typing | CB-kernel | scratch seed; no physical manifold |
| paired-extension reference | finite whole-extension support, order scar, history deletion, MSS frontier | CB-kernel | L1 carrier reference only; no manifold or physics admission |

## Existing fixed external profiles

The capability suite dispatches these rows through the controller-selected
Python/Julia runtime and independently replays each fixed flow:

| tool/API | operation | level | current boundary |
|---|---|---|---|
| PyTorch | `torch.func.jacrev` CPU float64 | tool→gate→replay | one Jacobian, not PyTorch readiness |
| JAX | `jax.grad`, `jax.vmap`, `jax.jit` | tool→gate→replay | one autodiff row, not JAX readiness |
| PySINDy | `SINDy.fit` and `predict` | tool→gate→replay | one affine identification row |
| Julia DifferentialEquations | `ODEProblem`, `solve`, `Tsit5` | tool→gate→replay | one bounded ODE row |
| SciPy | `scipy.linalg.expm` | tool→gate→replay | one rotation exponential |
| Diffrax | `ODETerm`, `Tsit5`, `diffeqsolve` | tool→gate→replay | one affine flow |
| graph/topology | bounded graph construction and crosscheck | tool→gate→replay | one graph row |
| PyDMD | `DMD.fit`, `eigs`, reconstruction | tool→gate→replay | one discrete-rate row |
| PyMDP | `Agent.infer_states`, `infer_policies` | tool→gate→replay | one two-state inference row |
| PyKoopman | `Koopman.fit`, `EDMD.fit`, `predict` | tool→gate→replay | legacy host-bound policy remains |
| Quimb/Cotengra | density APIs and `HyperOptimizer.search` | tool→gate→replay | legacy host-bound policy remains |
| Torch↔JAX↔Julia | CPU DLPack plus strict-carrier Julia solve | tool→gate→replay | one cross-engine diagnostic |
| e3nn | `o3.wigner_3j` fixed triples | tool→gate→replay | one bounded Wigner crosscheck |
| legacy packet | JAX/PyTorch/PySINDy plus PySINDy→Julia artifact | tool→gate→replay | fixed fixture only |

The suite’s portability column is separate from operation status. A local pass
does not establish a clean external installation, GPU availability, or whole
engine readiness. The suite also does not make any external result a CB gate
decision without a separately named consumer.

The fresh 2026-08-03 refresh ran all `14/14` rows as `ELIGIBLE`, with an
independent fresh-child replay also `ELIGIBLE` for every row. The aggregate
receipt is `/private/tmp/cb_capability_suite_refresh_20260803.json` with
SHA-256
`0c0a4dc189ffa6639a754797f4909a2339c59d3809a07f3e30f44217e9dae8ff`.
Its runtime-contract report remains `PARTIAL`: ten rows have a
controller-selected compatibility profile but no clean-install proof, and
four rows remain legacy host-bound (`pykoopman`, `quimb/cotengra`, the DLPack
cross-engine row, and the basic packet). This is a current operation/replay
result, not an all-engine or portable-install result.

## Registered CR slice

`config/cr_sim_slice_v1.json` adds source-addressed entries for the CR checkout:

| CR source | engine | level | fresh result |
|---|---|---|---|
| F01 finite-admissibility lane | Julia | source→receipt | PASS in 2026-08-03 foundation profile |
| F01 finite-admissibility lane | JAX | source→receipt | PASS |
| F01 finite-admissibility lane | PyTorch | source→receipt | PASS |
| F01 three-engine envelope | Python | envelope | FAIL in fresh 2026-08-03 run; registered envelope expects stale result schema |
| N01 noncommutation lane | Julia | source→receipt | FAIL in the 120-second controller run (`source_timeout`); warm standalone rerun is separate evidence |
| N01 noncommutation lane | JAX | source→receipt | PASS |
| N01 noncommutation lane | PyTorch | source→receipt | PASS |
| N01 three-engine envelope | Python | envelope | FAIL in fresh 2026-08-03 run; registered envelope expects stale result schema |
| system_v7 nonunitality source | Python | source→receipt | PASS exit-zero/stdout capture |
| CB GKSL fixture derivation | Python | source→receipt | PASS provenance recheck |
| paired whole-extension Julia lane | Julia | source→receipt | PASS; shared fixture and canonical observation rechecked |
| paired whole-extension JAX lane | JAX/Python | source→receipt | PASS; shared fixture and canonical observation rechecked |
| paired whole-extension PyTorch lane | PyTorch/Python | source→receipt | PASS; shared fixture and canonical observation rechecked |
| paired whole-extension three-engine envelope | Python | envelope | PASS; exact three-lane equality plus independent Z3/CVC5 controls |

All CR rows retain `external_system:true`,
`kernel_membership:EXTERNAL_NOT_CB_KERNEL`, `cr_truth_claim:false`, and
`promotion_allowed:false`. The receipts are evidence that registered sources
ran and that their declared output shape was rechecked, not evidence that CR is
correct.

The fresh isolated `foundation-and-cr` controller run was `7/10 PASS`.
F01 and N01 lane receipts were captured, but both existing envelopes failed
against the current result schema and the N01 Julia lane hit the controller's
120-second source timeout. Its receipt is
`/private/tmp/cb_cr_actual_run.BoeGAh/receipt.json` with SHA-256
`06ab93d72793704fe38c76c14e544323fac02da965d2c5e4f10e3d594c95f7cb`.
The older `10/10` receipt at
`/private/tmp/cb_cr_slice_foundation_and_cr_20260803/receipt.json` is retained
as historical evidence, not a current rerun. These rows remain external and
promotion-disabled.

The separate `paired-extension` profile ran `4/4 PASS` on 2026-08-03. It is a
finite nominalist carrier packet: Julia owns the reference set semantics, JAX
and PyTorch mirror the same fixture, and the envelope is consumed by CB only
after the fixture hash and canonical observation match. Its receipt is
`/private/tmp/cb_paired_extension_run_parent.C9QCM9/run/receipt.json` with SHA-256
`60a43f111cbb1c135f7f1c81e04bd5d97027ed8e03260202c895314b31866155`. The packet
remains `EXTERNAL_NOT_CB_KERNEL`, `cr_truth_claim:false`, and
`promotion_allowed:false`; see [`10_PAIRED_EXTENSION_NOMINALIST_PACKET.md`](10_PAIRED_EXTENSION_NOMINALIST_PACKET.md).

## Execution-first IJK prototype

The attached finite IJK runner is integrated through a distinct telemetry-only
CB command rather than the stricter CR receipt manifest:

```bash
PYTHONPATH=src python -m constraintbox exploratory-ijk \
  --cr-root /Users/joshuaeisenhart/Codex-Ratchet \
  --run-dir /private/tmp/cb-ijk-exploratory-run
```

| source | engine | level | gate behavior |
|---|---|---|---|
| `system_v8/manifold/prototypes/manifold_ijk_engine_prototype.py` | controller-selected CPython | source invocation → isolated output → receipt capture → telemetry | checks report; they do not block execution |

The runner covers a 24-cell I/J/K cofield, opposite `BIND→OPEN` and
`OPEN→BIND` hands, bounded coherent/incoherent path sums, an effective lossy
bracket seam, and a finite dominant-state basin scan. `status: EXECUTED` means
the authored source and its receipt ran; it is not validation, CR truth,
engine-readiness proof, or admission. This lane is deliberately separate from
the strict `cr-slice` profiles so exploratory work can continue while the
model, runtimes, and gate contract are being repaired together.

## Deferred or not integrated

The historical 60-tick engine, full four-terrain schedule, complete 16-stage
engine, basin/attractor admission, GPU/CUDA lane, and whole-manifold settlement
remain deferred. Julia optional-package import presence is not a substitute for
each package’s load-bearing role in a source-addressed receipt. TLC/Apalache and
Java are not required by this CR slice or by the contained CB product.

The next expansion should add one source and one consumer at a time, then run a
negative-control and replay. A larger manifest is not an integration proof by
itself.
