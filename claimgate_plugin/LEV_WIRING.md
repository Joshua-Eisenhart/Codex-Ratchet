# Wiring the higher-level claimgate into Lev OS

Cross-checked against the live Lev checkout
`~/lev-main/.worktrees/current-main-20260715/` (2026-07-20 inventory).
The rule: reuse what Lev already fires; do not reimplement it.

## The socket: `lev exec --verifier` (harness-fired, agent cannot skip)

`claim_verify.py` is designed to be the `<cmd>` of a Lev verifier loop. Lev runs
it as `/bin/sh -lc <verifier_command>`, treats `exitCode === 0` as pass, and
auto-writes durable evidence — the agent never chooses whether this runs.

```
lev exec "<task>" \
  --verifier 'python3 claimgate_plugin/claim_verify.py <receipt> --require tier0,tier4' \
  --until 'verifier passed'
```

On each verifier run Lev writes (evidence, from the inventory):
- `result.json` schema `lev.loop_verifier_result.v1` and `gate-proof.json`
  — `core/exec/src/loop/until.ts:154-181`
- an `exec.gate.run` LevEvent with `driver: loop-verifier`, `verdict`,
  `evidence_refs`, `proof_refs`, `exit_code` — `until.ts:202-218`
- run evidence whose `claim_verdicts` field is first-class and replay-graded
  — `core/exec/src/run/evidence.ts:56-91`

`claim_verify.py` emits a `claim_verdicts` array in exactly that shape
(`[{claim: "tierN", verdict: pass|fail, evidence_ref}]`), so the verdict lands
in Lev's model without translation.

## Validating the recorded verdict: `lev gate validate`

Once a gate-run event exists, its completeness/authority is checkable for free:

```
lev gate validate <gate-id>
```

Validates the `GateRun` record (`core/exec/src/gate-run.ts:12-27`,
`core/exec/src/handlers/gate.ts:53-91`): a command-driver gate must carry
exit_code + stdout + stderr; historical read-only evidence is rejected.

## Registering as a plugin (no Lev fork)

Two sanctioned paths (inventory §5):
1. Shell-check gate row in `dna/gates.yaml` (v2 schema: status/category/rule/
   scope/check/on_fail; lifecycle aspirational→declared→enforced→auto-enforced).
2. Evaluator pack in a loader root — `plugins/*/evals`, `.lev/eval/suites`
   (`core/eval/src/evaluator-pack-loader.ts:60-68`): a `*.eval.yaml` +
   `policies/gate-policy.yaml`. This is the ClaimGate-plugin home; it keeps the
   verifier on the plugin boundary and reworkable per Lev release.

Trigger at admission/verify time via `flowmind.programs[].trigger` →
`core/event-dispatch/src/trigger-dispatcher.ts:126-225`.

## What Lev already runs (do NOT rebuild — inventory §7)

- command/exit-code verification (`--verifier`), gate-evidence validation,
  durable event log, schema-validation (`graph_validate`), Jaccard
  near-duplicate (`graph_find_similar`), writer-side admission (`emit.ts`:
  AJV + vocab + sha256 receipt + collision + reject-log), constraint-manifold
  C1 finitude / C2 non-commutation at boot.

## What Lev DECLARES but does NOT enforce (the real build targets)

- **ratchet-forward floor comparison** — the biggest gap: nothing compares a new
  value against a prior floor and rejects weakening; the `constrain` op just
  appends (`core/context-graph/src/handlers/graph-apply-overlay.ts:75-94`). This
  is the literal meaning of "ratchet", enforced NOWHERE on either side. Highest-
  value next build: a durable floor (Lev event log) + a gate that FAILs a claim
  that weakens it.
- immutability enforcement, term-fence (registry inert), hash-chained
  provenance (`previous_hash`). Kernel-side ABAC C3-C5 is vaporware — do not
  depend on it (`dna/graph.yaml:31-36`).

The 5-gate `ratchet-admission.flow.yaml` is a Phase-2+ stub
(`system-flowmind-executor.ts:240-278`) — compose the real primitives above
behind `claim_verify` rather than waiting on that YAML to execute.
