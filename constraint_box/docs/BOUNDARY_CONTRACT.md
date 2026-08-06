# ConstraintBox boundary contract

ConstraintBox governs the use of selected simulation-engine operations.  It is
not the simulation-engine estate.  A package or library name alone does not
decide which side of that boundary an item belongs on: the controller uses a
role-bearing identifier and a fixed typed registry.

| Layer | Identifier namespace | Role | Contained-core source product? | Not a claim of |
|---|---|---|---|---|
| Controller runtime | `cb:cpython-controller-runtime` | Explicit CPython runtime for CB's parsers, hooks, ledgers, and bounded reference methods | Yes | a bundled Python installation or host sandbox |
| CB formal gate | `cb:*` formal-gate IDs | Deterministic gate implementations such as Z3/CVC5, SymPy, Rustworkx, and Maude profiles | Yes | a general theorem/truth system |
| Mini-LevOS | `cb:minilev-runtime`, `cb:claimgate-chain` | CB-native typed flow, hooks, bounded retries, leases, receipts, and direct ClaimGate chain | Yes | Leviathan itself or LLM decision authority |
| External adapter | `cb:external-sim-validation-adapter` | Controller-owned code that launches and checks a bounded external profile | Yes | an engine runtime or an engine passing merely because the adapter imports |
| External formal runtime | `formal-runtime:*` | TLC/Apalache installations configured outside the source product | No | a contained toolchain or current availability |
| External sim operation profile | `sim:*` | One named operation or bounded integration used as a CB test subject | No | broad engine readiness, CR proof, or CB-core membership |
| Evidence | `evidence:*` | A receipt, index, or human-classified regression reference | No | a component, tool, or engine |
| LLM/advisor | `llm:*` or provider-specific observation | Proposal, explanation, user guidance, or critique after controller evidence is fixed | No authority | gate selection, disposition, retry, or release |

The same library can appear in more than one layer only when its *role* is
different.  For example, `cb:rustworkx-workflow-gate` is a contained CB graph
gate, while Rustworkx called inside `sim:graph-topology-crosscheck-v1` is
external sim-test evidence.  Likewise, NumPy may be a minimal Python
dependency in an external profile without becoming a CB decision authority.

## Enforced typed report

Full product/evidence status claims must be submitted as
`constraintbox.boundary-contract.v1` to
`formal.boundary.constraintbox_scope`.  The request contains the complete
fixed role registry rather than a free-form `tools` inventory.

The controller encodes these exclusions in Z3, CVC5, and a bounded CPython
reference enumeration:

- a CB-core role cannot contain a `sim:*` operation profile;
- an external sim-profile section cannot contain a `cb:*` component;
- a sim profile or evidence identifier cannot claim CB-core membership;
- the contained source bundle cannot claim that it contains the external sim
  engines.

All three must agree.  A valid role map is `ELIGIBLE` only for typed boundary
separation.  A conflated map is `BLOCKED` with
`boundary_role_conflation`; a malformed or untyped status map is `BLOCKED`
with `boundary_contract_invalid`.

```bash
PYTHONPATH=src python -m constraintbox formal run \
  --task formal.boundary.constraintbox_scope \
  --request-id boundary-valid-example \
  --payload fixtures/formal/boundary_contract_valid.json \
  --run-dir /tmp/constraintbox-boundary-valid
```

`fixtures/formal/boundary_contract_conflated_sim_as_cb_core.json` is the
regression fixture for the observed failure: it puts
`sim:pytorch-jacobian-v1` in a CB formal-gate field.  It is deliberately
blocked and produces deterministic retry feedback.  The fixture is
human-classified evidence of the earlier bad summary; CB does **not** claim to
infer arbitrary natural-language meaning from prose.

## Authority and limit

The controller renders the role matrix from the accepted typed contract.
Free prose and LLM explanation are untrusted commentary.  The immutable
controller prompt context tells a provider this distinction before it proposes
anything, but the provider cannot make the boundary decision.

This is a structural scope gate, not a general natural-language truth detector.
It prevents an untyped or conflated status report from becoming authoritative;
it does not prove whether every sentence in arbitrary prose is semantically
correct.  Future external validation runs must bind their current receipt IDs
and hashes into a controller-generated boundary contract before they can be
presented as a product/evidence status map.
