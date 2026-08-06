# External validation runbook

ConstraintBox has two deliberately different layers.

| Layer | Contents | May decide a CB disposition? | Included in the contained core bundle? |
|---|---|---:|---:|
| CB kernel | Python controller, deterministic gates, Mini-Lev lease/flow, Z3, CVC5, Maude, Rustworkx, SymPy, ClaimGate | Yes | Yes, subject to the active core runtime profile |
| External validation estate | Sim-engine profiles, TLC/Apalache runtime artifacts, and an optional live Lev checkout | Only through controller-owned receipts and fixed stages | Source/runbook support only; the estate itself is not bundled |

The boundary is intentional. The sim estate tests CB; it is not CB, and an LLM
does not select its tools, formulate its gates, or turn an output into a pass.

## One explicit external run

Use a new, absolute run directory. The runner requires the actual Java binary
and formal-runtime directory as arguments; it never records a developer laptop
path in CB policy.

```bash
PYTHONPATH=src /path/to/selected/python scripts/run_external_validation.py \
  --request-id external-validation-001 \
  --run-root /absolute/new/cb-external-validation-001 \
  --formal-runtime-dir /absolute/formal-runtime \
  --java-executable /absolute/java/bin/java \
  --lev-root /absolute/lev-checkout \
  --subject-root "$PWD"
```

Omit `--lev-root` when no live Lev comparison is requested. In that case the
sim-and-CB run can still be `ELIGIBLE`; the aggregate receipt explicitly marks
the Lev component `NOT_REQUESTED`. A missing or unusable configured dependency
returns `PARKED` or `HOLD`, rather than a synthetic pass.

`java` is made visible only to this validation process and its children. TLC
uses a local loopback socket, so a host sandbox that forbids socket creation
will correctly produce `PARKED`; run it in the intended local execution
environment rather than weakening the checker.

## What the run actually executes

`01_integrated_workload_result.json` is the controller-owned result. Its fixed
stage order includes the external capability suite, Z3+CVC5 with an erased
component control, Maude transitions, the leased Mini-Lev hook, a Rustworkx
workflow check, a pinned Lev FlowMind observation, SymPy exact checking, TLC
and Apalache with positive/replay/mutant controls, ClaimGate, and final Maude
completion.

The capability suite executes and independently replays these external profile
families in fresh child processes:

| Profile | Real operation family |
|---|---|
| PyTorch | Jacobian/autograd operation |
| JAX | autodiff operation |
| PySINDy | bounded affine identification |
| Julia | DifferentialEquations solve |
| SciPy | matrix-exponential dynamics |
| Diffrax | Tsit5 affine flow |
| graph/topology | bounded graph and topology cross-check |
| PyDMD | discrete-rate decomposition |
| PyMDP | two-state inference |
| PyKoopman | identity plus EDMD surface |
| Quimb/Cotengra | bounded tensor-network workload |
| PyTorch to JAX to Julia | DLPack and independent Julia lane workload |
| PySINDy to Julia | identified-rate packet consumer workload |
| e3nn | Wigner cross-check |

The result does **not** claim that every row is one scientific simulation.
There are two concrete producer-to-consumer checks in the current workload:

1. A PyTorch result crosses to JAX through actual DLPack conversion and is used
   by a JAX `jit`/`vmap` computation.
2. A PySINDy-identified rate is canonically serialized, digest-bound, and
   consumed by the Julia DifferentialEquations worker. Removal, byte mutation,
   and rate substitution are negative controls.

The suite receipt is then transformed into fixed finite obligations for Z3 and
CVC5. This binds the formal path to the observed component disposition; it does
not turn a simulator receipt into scientific or CR truth.

## Test-only hostile-input instrument

Hypothesis is deliberately outside the runtime decision path. It is used with
fixed-seed, bounded adversarial tests for intake and solver-precedence controls:

```bash
PYTHONPATH=src python -m pytest -q tests/test_hypothesis_adversarial.py
```

That test exercises malformed/nested-authority request inputs and records
whether deterministic intake and solver precedence refuse them. It does not
choose a production disposition, retry an engine, or grant an LLM authority.

## Receipts to inspect

| Path below `--run-root` | What it proves at most |
|---|---|
| `external_validation_result.json` | Whether the explicitly requested external components were locally eligible in this one run |
| `01_integrated_workload_result.json` | The fixed CB stage chain and its terminal disposition |
| `01_integrated_workload/01_external_capability_suite/` | Per-profile operation receipt and a fresh independent replay receipt |
| `01_integrated_workload/13_temporal_pair.json` | TLC and Apalache positive/replay/mutant control results |
| `02_leviathan_reference_result.json` | Optional live Lev dry-run structural comparison, with no authority over CB |

An `ELIGIBLE` receipt is a local, bounded operation result. It does not prove a
clean installation on another machine, full sim-estate coverage, all LevOS
behavior, CB/Lev implementation conformance, release permission, scientific
truth, or CR truth.

Generate a compact table of the actual receipt-bound API witnesses and replay
paths without letting a model summarize them:

```bash
PYTHONPATH=src python scripts/index_external_validation_receipt.py \
  --run-root /absolute/cb-external-validation-001
```

The command writes `external_validation_index.md` only if it is new. It rejects
receipt paths that escape the declared run root.

## How a model audit fits

An external model may explain the receipt, flag likely missing assumptions, and
suggest a bounded next test. It is not a gate authority. If a model narrative
disagrees with a source-bound receipt or the deterministic handoff checks, the
receipt and controller checks win. Turn that disagreement into a new bounded
negative control or audit-contract test; do not promote the narrative.
