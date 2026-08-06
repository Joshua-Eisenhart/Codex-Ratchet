# Architecture

## Authority boundary

The load-bearing controller path is small:

```text
TaskRequest
  -> ConstraintBoxController.run
  -> controller-owned Profile.evaluate
  -> ProfileOutcome
  -> DecisionRecord
  -> optional HashChainLedger.append
```

The simulation estate, branch tools, evidence seals, lease, discharge, applicability registry, semantic profiles, and adapters are callable surfaces. They do not enter that controller path unless a caller explicitly wires or invokes them.

## Intake

`src/constraintbox/intake.py` parses one byte snapshot.

- `parse_json_value` decodes UTF-8, rejects duplicate keys, rejects `NaN` and infinity tokens, and recursively rejects non-finite floats.
- `parse_json_object` also requires an object at the root.
- `canonical_json` emits sorted, compact UTF-8 and sets `allow_nan=False`.

The `solve` CLI subcommand does not use this strict path. It calls `json.loads` directly before `FiniteConstraintProblem.from_spec`.

## Controller and profiles

`src/constraintbox/controller.py` owns task-to-profile dispatch. A request supplies `task_kind`, bytes, and `request_id`; it cannot select its own profile.

`ConstraintBoxController.run` hashes the input, validates the request identifier and byte bound, looks up `_task_policy`, calls the selected profile, and constructs a `DecisionRecord`. The record includes the policy and input digests, disposition, reason, evidence, claim ceiling, `controller_emitted=True`, and `promotion_allowed=False`.

Built profiles are:

- `StrictJsonProfile`: strict intake only.
- `AgentProposalProfile`: records candidate material but blocks authority-bearing fields and parks incomplete proposals.
- `FiniteConstraintProfile`: finite enumeration or the optional Z3 backend.
- `RegisteredWorkerProfile`: checks a pinned source digest, creates a new run directory, runs a fixed argument template, and binds exit, stream, argument, and output digests.
- `NumpyAggregateProfile` in `numeric.py`: recomputes a bounded numeric aggregate when NumPy is present.

## Finite constraints

`src/constraintbox/constraints.py` builds `FiniteConstraintProblem` objects. `evaluate_constraint` supports equality, inequality, ordering, membership, `all_different`, tables, and Boolean composition.

`solve_enumerated` exhausts the finite product if it is within `max_states`; otherwise it returns `UNKNOWN`. `solve_z3` handles a smaller shared operator subset and also returns `UNKNOWN` when Z3 is absent, the state bound is exceeded, or an operation is unsupported.

The two backends once disagreed on Python-equal JSON values such as `1`, `true`, and `1.0`, and on unhashable values. `tests/test_constraints_backend_parity.py` guards the fixes with direct regressions and a seeded differential. The claim ceiling remains one declared finite encoding checked within its bound.

## Branching and finite histories

`src/constraintbox/branching.py` provides `BranchLedger.add`, `park`, `prune`, and `merge`. Pruning requires an empty extension count, a bounded-unsatisfiable status, a contract digest, and an evidence reference. Merge requires active probes, a continuation contract, complete equal observations, and a contract digest. Events and non-live statuses retain the history.

`src/constraintbox/ensemble.py` carries finite histories, projections, extension fibres, partitions, finite sums, and history-pair fields. These are libraries. The controller does not call them automatically.

## Evidence

`src/constraintbox/evidence.py` separates a locator from what it claims.

- `EvidenceRef` cannot receive existence, observed digest, or observation time from its constructor.
- `observe` resolves a registered route and inspects the current file.
- `seal_run` re-observes every unique reference and refuses missing, malformed, duplicate, or zero-reference seals.
- `verify_seal` checks the seal and the world again, yielding `SEALED`, `REF_MISSING`, `REF_CHANGED`, or `MALFORMED`.

`FileRoute` blocks absolute paths and `..`. `DigestRoute` requires the stored bytes to hash to their locator.

## Ledger

`src/constraintbox/ledger.py` appends canonical JSON records linked by SHA-256. `HashChainLedger.append` first verifies the entire chain, then writes the new row and updates a retained head. This detects ordinary edits and tail deletion and makes repeated append O(n²).

The default retained head is a sibling file. It is not an independent trust root. An actor who edits and re-chains the ledger can rewrite the sibling head too, after which `verify` succeeds. This open defect is recorded in `PROVENANCE.md`.

## Lease and discharge

`src/constraintbox/lease.py` binds runners to the current staged tree from `git write-tree`. `issue_lease` materializes that tree, runs declared commands, and records exit and stream digests. Verification yields `VALID`, `STALE`, `TREE_MISMATCH`, `ABSENT`, or `MALFORMED`. Unstaged and untracked files are outside the staged tree.

`src/constraintbox/discharge.py` checks typed, dated observations against a declared policy. `PASS`, `FAIL`, and `EVALUATION_ERROR` remain distinct. Missing, stale, undated, ill-typed, or incompletely evaluated variables are evaluation errors rather than evidence that the claim is false.

Both modules are CLI-reachable and tested. Neither has a production caller.

## Simulation estate

`src/constraintbox/estate.py` loads a strict manifest and fixture, checks pinned controller and worker digests, records the exact interpreter, compares the environment to a tested lock, and runs capability workers.

The manifest defines four installation tiers:

| Tier | Scope |
|---|---|
| S1 | lean finite, numeric, solver, and controller instruments |
| S2 | manifold and engine workhorses |
| S3 | proposal-analysis satellites |
| S4 | NVIDIA and cloud acceleration routes |

These are not scientific authority levels.

`EstateRunner.run_tier` aggregates capability states. Required failure controls the tier; optional failure may yield `DEGRADED`. Capability states include `READY`, `DEGRADED`, `UNAVAILABLE`, `DRIFT`, `FAILED`, and `UNTESTED`.

Acceptance mode can run positive, dispatch, mutation, replay, import severance, and operation poisoning controls. It does not run every control for every oracle. Current receipts can name gaps in `controls_not_measured`, while some required capabilities can still reach a passing machine disposition. `PROVENANCE.md` records this as open for solver, path, and FEP oracles. TLA and NVIDIA have separate early-return receipt paths that also do not share the full honesty-field tail.

## External gate and exit codes

`src/constraintbox/gate.py` invokes the external ClaimGate chain and records the resolved root, checker, receipt and registry digests, chain exit, JSON verdict, tier results, and `promotion_allowed=False`.

The verified public mapping is:

| Result | Exit |
|---|---:|
| `ADMITTED` | 0 |
| `REFUSED` | 1 |
| invocation or pre-chain `GateError` | 2 |
| `INSUFFICIENT_DEPTH` | 3 |
| `PARKED` | 4 |
| `EVALUATION_ERROR` | 5 |

Open defects qualify this contract. A missing registry raises an uncaught `FileNotFoundError` rather than `GateError`. The gate derives `disposition` from process exit and reads `chain_verdict` from JSON but does not compare them. An injected chain can therefore produce contradictory fields. Output-write failure in `cli.py` can replace a semantic nonzero exit with 1.

## Applicability gates nothing

`src/constraintbox/applicability.py` maps claim types to required capabilities, and the CLI can run `ApplicabilityRegistry.assess`. Neither `controller.py` nor `estate.py` refers to it. A declared demand does not change a controller or estate decision.

It exists and runs. It is not load-bearing.

## Adapters

`adapters/cr.py` constructs a `SemanticClaimProfile` and returns proposal-only whole-state obligations. `adapters/lev.py` translates a `DecisionRecord` into a digest-bound Lev evidence event while preserving disposition, claim ceiling, and `promotion_allowed=False`.

There is no live Lev transport.

## CLI

`src/constraintbox/cli.py` registers:

- `demo`, `doctor`, `deps`, and `solve`
- `estate`, `estate-parity`, and `preflight`
- `lease issue` and `lease verify`
- `discharge`
- `evidence seal` and `evidence verify`
- `applicability`
- `gate`

The five newer front doors—lease, discharge, evidence, applicability, and gate—have tests and zero production callers. The repository hook invokes the repo-root ClaimGate chain directly.

## One claim through the controller

Follow a finite-constraint claim:

1. A caller constructs `contracts.TaskRequest`.
2. `ConstraintBoxController.run` in `controller.py` validates request identity and size and selects `FiniteConstraintProfile` from `_task_policy`.
3. `FiniteConstraintProfile.evaluate` calls `intake.parse_json_object`.
4. It calls `FiniteConstraintProblem.from_spec` in `constraints.py`.
5. It calls `solve_enumerated` or `solve_z3`.
6. The profile returns `ProfileOutcome` with bounded solver evidence.
7. The controller creates `contracts.DecisionRecord`.
8. If configured, `HashChainLedger.append(record.to_dict())` verifies and appends it.

Do not substitute the direct `constraintbox solve` CLI path for this flow; that command bypasses the controller and strict intake.

## Two ClaimGate trees

`constraint_box/claimgate_plugin/` is a diverged duplicate of the repo-root `claimgate_plugin/`. `PROVENANCE.md` records eight differing files, root-only bypass2 material, and one corpus audit that measured the duplicate tree and reported it as the gate.

The canonical tree is an open owner decision. The repo-root tree currently contains the slop gate and its regression; the box-local duplicate does not. A developer must name the tree being measured and must not merge results from both.
