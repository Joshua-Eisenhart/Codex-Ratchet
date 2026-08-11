# CB Light current status — 11 August 2026

This is a bounded status of the contained CB Light control plane. It is not a
CB Heavy, simulation, portability-adoption, promotion, or release claim.

## Exact candidate domain and current dispositions

The full row-level ledger is
[`receipts/cb_light_tool_status_ledger_v1.json`](../receipts/cb_light_tool_status_ledger_v1.json).
It contains all 91 proposed Light tools, their locked versions, roles, runtime
and clean-install facts, metadata result, operation probe result, and
current-work selection result. It separately lists the 15 pre-install
exclusions.

Current fact table:

| Lifecycle fact | Result | Meaning |
| --- | ---: | --- |
| Proposed Light tools | 91 | Finite candidate domain only |
| Pre-install exclusions | 15 | Evaluated candidate domain is 106; excluded tools were not admitted to the 91-root install set |
| Runtime exact install/import/provider evidence | 91 / 91 | Contained Light environment only |
| Persistent clean exact install/import/provider evidence | 91 / 91 | One macOS/Python 3.13 clean environment only |
| Operation probes | 87 ADMIT, 4 HOLD | Bounded tool-level behavior, not production integration |
| Current-work selection | 86 selected, 5 hold | No owner adoption authority |
| Owner-approved adoption | 0 | No adoption claim |
| Portable adoption | 0 | No macOS/Linux/Windows matrix claim |
| CB Heavy authorization | 0 | Explicitly out of scope |
| System completion | 0 | A local Light evaluation is explicitly not a product/release completion |

The five current holds are:

| Tool | Blocking constraint(s) |
| --- | --- |
| `annotated-types` | `probe_structure_non_vacuous` |
| `ecdsa` | `local_metadata_compatible` |
| `platformdirs` | `probe_structure_non_vacuous`, `reason_specific_negative` |
| `satispy` | `boundary_observed`, `bounded_reference_agreement`, `probe_structure_non_vacuous`, `reason_specific_negative` |
| `typing-extensions` | `probe_structure_non_vacuous` |

The current-work selection requires all of these constraints for each row:

```text
proposed_light_identity
role_declared
exact_root_pin_installed
declared_import_provider
fresh_subprocess_import
clean_dependency_closure
contained_environment_exact
clean_runtime_closure_agreement
local_metadata_compatible
positive_api_operation
reason_specific_negative
boundary_observed
deterministic_replay
import_severance_observed
bounded_reference_agreement
probe_structure_non_vacuous
cross_receipt_identity_bound
```

## Literal Light/Heavy package boundary

The active Light distribution is built from
[`light_runtime/pyproject.toml`](../light_runtime/pyproject.toml), not from the
legacy mixed repository-root package.  Each refresh runs
[`scripts/audit_cb_light_heavy_separation.py`](../scripts/audit_cb_light_heavy_separation.py),
which builds a fresh Light-only wheel, installs it in a new interpreter, and
requires these negative observations before the evaluation can pass:

- no Heavy import roots or adapter module paths resolve;
- no Heavy files or legacy `constraintbox-legacy` console entry point appear
  in the wheel;
- no Heavy path, shared Ratchet environment, or `system_v5`/engine reference
  appears in an active Light hook/config surface.

The resulting receipt is bound into
`receipts/cb_light_hook_run_v1.json`.  This is local package-boundary evidence
only.  It does not supply a CB Heavy setup, a Light-to-Heavy bridge, a
simulation result, portability adoption, or release evidence.

The hook also compares every actual installed `constraintbox` and `hookkernel`
file against the manifest hashes for `light_runtime/src/`.  The current receipt
records 30 expected/observed files, no missing or unexpected paths, and no hash
mismatches.  This closes the important distinction between a fresh wheel that
*could* be built from current source and the wheel that the contained gate will
actually execute.  A changed checkout followed only by `cb-light refresh` now
holds rather than blessing an older installed wheel.

`cb-light status` reports `evaluation_allowed` for this bounded local state.
`cb-light complete` remains fail-closed with `completion_allowed: false` until
the separate portability, owner approval, real-consumer, and Heavy-profile
transitions earn their own receipts.

## Live reader and writer behavior

`cb-light install` and `cb-light refresh` are the authoritative writer routes.
They use an exclusive lifecycle lock; a second broker writer receives
`CB_LIGHT_LIFECYCLE_LOCK_HELD` as a machine-readable `HOLD` instead of writing
the shared receipt family.  A real two-process lock negative is covered by the
focused suite.  This is deliberately not a claim that arbitrary direct helper
scripts are safe writers; their output is not an authority route.

An intentional contained-source change uses the explicit brokered route
`cb-light install --rebuild-manifest`.  It runs the manifest compiler *inside*
that same lifecycle lock, then verifies the regenerated source contract before
building the Light wheel and refreshing receipts.  Ordinary `cb-light install`
continues to refuse a stale manifest.  The compiler can still be invoked
directly by a developer, but that is not the supported authoritative lifecycle
route and does not earn a lifecycle claim by itself.

`cb-light status` and `cb-light complete` are read-only live gates.  Each runs
a fresh wheel/actual-runtime boundary audit from verifier-owned temporary
directories.  A concurrent real run produced:

| Command | Exit | Local evaluation | System completion |
| --- | ---: | --- | --- |
| `cb-light status` | 0 | true | false |
| `cb-light complete` | 2 | true | false |

No source-tree `build/` or `*.egg-info` product remained.  `complete` reports
the same live evaluation it used for its completion HOLD; it cannot print a
stale `evaluation_allowed: true` after the live boundary failed.

The latest executable verification ran 30 core lifecycle/boundary tests and
19 separate typed-profile/wave tests.  The installed core exercise also ran
Z3, cvc5, SymPy, Rustworkx, and Maude through one bounded deterministic
fixture.  These are local operation facts, not adoption or release evidence.

## Do not conflate the two gate domains

The static ledger and the live SQLite gate deliberately answer different
questions. Neither grants adoption.

| Surface | Domain | Current result | It does **not** mean |
| --- | --- | --- | --- |
| Static install/operation/selection receipts | 91 proposed Light roots + 15 pre-install exclusions | 91 exact installs; 87 operation admits; 86 selected for current work | Five core gate admits, owner adoption, portability, or production use |
| `constraintbox cb-light --db ... probe` SQLite gate | 186 observed distributions, 214 observed objects, and five core deterministic contracts | Five core contracts ADMIT; 48 excluded, 161 hold, 5 open basin; owner adoption 0 | A selection of the static 91 roots, a portable profile, or a CB Heavy claim |

No artifact may infer a subset/superset relationship between these two domains
without a separately validated mapping. Both surfaces explicitly report zero
owner-approved adoption.

`pip` and the separately packaged local Light `constraintbox` wheel are
controller infrastructure, explicitly outside the finite 91-tool candidate
domain. The gate fails `CONTAINED_CONTROLLER_PACKAGE_MISSING` if the controller
package is absent; arbitrary other packages still cause runtime-environment
drift.

## Gate and hook route

```text
Claude Code project settings
  -> root PreToolUse / PostToolUse scripts
  -> constraint_box/.venv/bin/python -I -m hookkernel.cb_light_gate
  -> SQLite domain snapshot + core-probe + selection receipts

legacy pre/post/session adapters
  -> exec the same root scripts
```

The public deterministic front door is:

```text
constraintbox cb-light --db PATH probe
```

It has been exercised against a real SQLite database. All five core contracts
(`z3`, `cvc5`, `sympy`, `rustworkx`, and `maude`) admitted. An actual proposed
package-install payload for `z3-solver` passed the root hook; `jax` was refused
as `PACKAGE_OUTSIDE_CB_LIGHT_PROPOSAL_DOMAIN` by both the root hook and the
legacy pre-tool adapter. This establishes package-mutation gate behavior, not
that Claude Code has fired hooks in every future project session.

The reusable boundary exercise receipt is
[`receipts/cb_light_hook_boundary_exercise_v1.json`](../receipts/cb_light_hook_boundary_exercise_v1.json).
It ran four payload classes through both routes (eight real hook evaluations):

| Payload class | Expected gate result |
| --- | --- |
| Declared `z3-solver` candidate | ADMIT |
| `jax` outside the proposal domain | REFUSE `PACKAGE_OUTSIDE_CB_LIGHT_PROPOSAL_DOMAIN` |
| Mixed declared `z3-solver` plus undeclared `requests` | REFUSE `PACKAGE_OUTSIDE_CB_LIGHT_PROPOSAL_DOMAIN` |
| `pydantic` from the separate control profile | HOLD `CANDIDATE_NOT_SELECTED_FOR_INSTALL` |

The last row is intentional: it proves the hook distinguishes an outright
outside package from a broader candidate that still lacks current-work
selection. Neither result permits installation.

## Separate typed control-plane profile

`pydantic==2.12.5` and `jsonschema==4.26.0` are installed only in
`.venv-control-plane`, not in the exact 91-root Light environment. Its
`constraintbox control-plane` command consumed a real Light SQLite selection
triple and checked the probe interpreter was the contained Light runtime. A
request for `provider_launch` was refused as `REFUSE_UNDECLARED_CAPABILITY`.

That profile was reverified from the final Light-only wheel with all eight
bounded fresh-profile checks passing in
[`receipts/CONTROL_PLANE_FRESH_WHEEL_PROFILE_20260811_DEPENDENCY_GATE.json`](../receipts/CONTROL_PLANE_FRESH_WHEEL_PROFILE_20260811_DEPENDENCY_GATE.json).
The current console positive and negative receipts are
[`cb_control_plane_console_valid_request_20260811.json`](../receipts/cb_control_plane_console_valid_request_20260811.json)
and
[`cb_control_plane_console_invalid_capability_20260811.json`](../receipts/cb_control_plane_console_invalid_capability_20260811.json).
The profile's installed `constraintbox` package resolves under
`.venv-control-plane` and its Heavy adapter module paths do not resolve.

This proves one bounded typed consumer. It proves neither Pydantic membership
in the 91 tools nor adoption, portability, provider launch, CB Heavy access,
or release.

## Bounded local wave fixture, not an LLM swarm

The public `constraintbox wave` command first invokes the current contained
`cb-light status` route.  Before it reads a packet or opens SQLite, it also
requires the invoking typed profile to import the exact separate pins
`pydantic==2.12.5` and `jsonschema==4.26.0`.  The receipt binds the actual
profile interpreter, module origins, expected versions, and observed versions.
Missing or mismatched pins return a fail-closed `HOLD`; they do not silently
fall through to a fixture run.

In the base Light environment, that second gate observes both optional
packages as absent and returns `HOLD_WAVE_CONTRACT_DEPENDENCY_MISSING` without
opening a wave SQLite database or invoking a provider.  In
`.venv-control-plane`, the current public receipt records both exact versions
and their module paths beneath that profile before the bounded fixture starts.

In the separately verified control-plane environment, one sealed local packet
ran exactly three synthetic non-authoritative adapters through a fixed
Rustworkx topology and a local finite FactSet.  Its receipt records
`models/providers/network/CB Heavy: not invoked`, `promotion_allowed: false`,
and no portability or adoption claim.  This is a deterministic fixture only;
it is not a council, a model swarm, a real MMM execution, or a simulation.

A local counterexample returns `SETTLED_REFUTED` at the fixture layer, is
persisted as the negative ledger outcome `REFUSE` with its exact counterexample
reason, and exits 2 from the public CLI.  It cannot look like shell-level
admission.  Python-level fixture helpers remain test/engine internals, not an
additional public authorization route.

## Deliberate next boundaries

1. Run the OS/Python portability matrix before any portable adoption.
2. Add a real deterministic consumer and alternate-entrypoint negative for
   each support tool cohort before treating selection as integration.
3. Keep controller packaging drift as a first-class negative: exact Light
   package tools plus the separately declared controller package must both be
   present.
4. Do not introduce an external/model LLM probe wave until its public API is
   sealed behind the same current-evaluation gate, with a finite input domain,
   positive and negative hypotheses, bounded output schema, deterministic
   evaluator, SQLite receipt, replay, and no CB Heavy capability.
5. Keep the typed profile claim ceiling literal: its current fresh receipt
   proves direct pins and local clean installation, not a full transitive hash
   lock, dependency provenance, multi-OS portability, provider execution, or
   CB Heavy access.
