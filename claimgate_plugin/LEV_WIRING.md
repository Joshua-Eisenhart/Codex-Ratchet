# Wiring the higher-level claimgate into Lev OS

Cross-checked against the live Lev checkout
`~/lev-main/.worktrees/current-main-20260715/` (2026-07-20 inventory), and
against the Lev repo root `~/GitHub/lev` (2026-07-22 live verification — see
"The binary" and "Steering-consume" sections below, which correct and extend
the 2026-07-20 inventory).
The rule: reuse what Lev already fires; do not reimplement it.

## The binary: `lev exec` / `lev gate validate` vs `core/poly/bin/lev`

Two different `lev` binaries are in play and they are NOT interchangeable:

- The **global `lev`** (`~/.local/bin/lev`, a symlink into
  `~/lev-main/.worktrees/current-main-20260715/core/poly/bin/lev`) has `exec`,
  `gate validate`, and the rest of the surface documented below — verified live.
  It does **not** have an `orchestration` subcommand: `lev orchestration ...`
  returns `Unknown command: orchestration` (verified 2026-07-22).
- The **poly build in the Lev repo root** (`./core/poly/bin/lev`, run from
  `~/GitHub/lev`) is the one that ships `orchestration claimgate-steering
  consume`. Run it from the Lev repo root, not via the global symlink, until
  that command lands in the lev-main worktree the global binary points at.

Everything under "The socket" and "Validating the recorded verdict" below is
unaffected — those subcommands work on the global binary. Only the
steering-consume path in the next section needs the repo-root poly binary.

## Steering-consume: the host-recompute path (`orchestration claimgate-steering consume`)

```
./core/poly/bin/lev orchestration claimgate-steering consume <run-dir> [--json] [--no-write]
```

Run from the Lev repo root. This is the passive **consumer** half of the
ClaimGate -> Lev host/source split: it reads a five-file source projection
(`run.json`, `proof-spec.json`, `eval-job.json`, `eval-job-output.json`,
`boundary.json`) and **independently recomputes** the verdict host-side — a
source projection cannot self-promote. Three verdicts:

| Verdict | Meaning |
|---|---|
| `host_consumed` | Recomputed verdict = `pass`; the source projection's claim is admitted. |
| `host_reviewed_failed` | Structurally consumed, but the recomputed verdict is not `pass` (for example `conditional`) — correctly reviewed and correctly not admitted. |
| `host_blocked` | The projection overclaims host authority (for example `live_lev_consumed` or `release_admission_allowed` set `true` in a *source* file) — refused before recompute even runs. |

Two Lev gates enforce this in `dna/gates.yaml` (`status: enforced`,
`owner: claimgate`):

- `claimgate_steering_admitted` — the `good` fixture must come back
  `host_consumed` with `Recomputed verdict: pass`.
- `claimgate_blocks_overclaim` — the `bad` fixture (an overclaiming
  projection) must come back `host_blocked`.

**Verified live 2026-07-22**, from the Lev repo root:

- `good` fixture (`core/orchestration/test-fixtures/claimgate-steering/good`):
  `ClaimGate steering run: host_consumed` / `Projected verdict: pass` /
  `Recomputed verdict: pass` / `Live Lev consumed: true`.
- `bad` fixture (`core/orchestration/test-fixtures/claimgate-steering/bad`):
  refused with `Cannot issue ClaimGate host execution witness for invalid
  projection: run_metadata.live_lev_consumed_forbidden,
  run_metadata.release_admission_allowed_forbidden,
  run_metadata.properly_integrated_forbidden` — the correct outcome, but see
  "Known findings for the Lev dev" below: the CLI text no longer contains the
  literal token `host_blocked`, so `claimgate_blocks_overclaim`'s grep
  misreports this correct refusal as a gate failure.

## `lev_steering_producer.py` -> consume: a real CR receipt end to end

`claimgate_plugin/lev_steering_producer.py` is the CR-side **producer**: it
renders a `post_receipt_gate.sh` run on a real CR ratchet receipt into the
same five-file source projection the consumer above reads. Verified live
2026-07-22 on a real receipt, not a synthetic fixture:

- Input: `ratchet_contract/ratchetings/results/cut_dependent_entropy.json`
  (`post_receipt_gate.sh` hook_exit `3`, i.e. tier0 `ADMISSIBLE` +
  `claim_verify` `INSUFFICIENT_DEPTH` + floor `PARKED` — admitted, deeper
  audit still owed, not a rejection).
- Producer output: a projection with `claim_ceiling: adapter_partial`,
  `release_admission_allowed: false`.
- `consume --no-write` on that projection: `ClaimGate steering run:
  host_reviewed_failed` / `Projected verdict: conditional` / `Recomputed
  verdict: conditional` / `Live Lev consumed: false`.

This is the correct outcome: Lev recomputed the verdict, agreed it is
`conditional`, and refused to admit a probe-depth receipt as if it were a
full pass. A receipt that reaches hook exit `0` (full pass on all required
tiers) is the case expected to come back `host_consumed` — not yet
demonstrated here, only the exit-3 case has been run end to end.

The producer's own docstring (as shipped in this pack) still says the
consume surface is "NOT reachable from the installed `lev` CLI" and the path
is "BLOCKED-ON-PRODUCER" — that was true against the global binary and is now
superseded by the verification above (repo-root poly binary, not the global
one). The docstring itself was not edited as part of this pass; treat the
verification in this file as the current state.

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

## The other enforcement leg: CR-local fired-side git hook

The Lev-side paths above ("The socket", "Steering-consume") are one leg of
"the gate fires, the agent doesn't call it." The other leg lives entirely on
the CR side, with no Lev dependency, and closes a real gap: on 2026-07-22 a
receipt shipped without anyone running the gate on it, because nothing forced
the call. The fix is `claimgate_plugin/hooks/pre_commit_gate_receipts.sh` +
`claimgate_plugin/hooks/install_git_hooks.sh`:

- `install_git_hooks.sh` installs a `.git/hooks/pre-commit` that always execs
  the version-controlled `pre_commit_gate_receipts.sh` — so a gate update
  ships with the repo, not with an untracked hook copy. Idempotent; backs up
  any pre-existing pre-commit hook once.
- `pre_commit_gate_receipts.sh` runs on every `git commit`: for each staged
  `ratchet_contract/`, `system_v8/`, or `fuel_gate/` `results/*.json` file
  that looks like a ratchet receipt (has a `verdict` or `classification`
  field), it runs `post_receipt_gate.sh` on it and maps the exit code —
  `0` (VERIFIED) and `3` (INSUFFICIENT_DEPTH, admitted-not-rejected) both
  allow the commit; `1` (REJECTED) **blocks** the commit and prints the fix;
  any other exit (tooling/IO error) warns but does not brick the commit.

This is a git-level fire, independent of whether the agent remembers to call
`post_receipt_gate.sh` itself, and independent of whether Lev's own verifier
socket is wired up yet. Both legs enforce the same underlying gate; neither
supersedes the other.

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

## v2 — hardened after adversarial red-team (2026-07-20)

v1 was red-teamed and had 4 confirmed holes (all: the agent authored its own
pass-criteria). v2 moves ALL verification policy outside agent write-control,
matching the Lev dev's approved design `20260716-claim-submission-evaluation-
admission.yaml` (observation -> deterministic measurement -> decision; operator
never assembles methodology; `cannot false-green`):

- tier2/3 argv comes from `gate_registry.json` (external), NEVER the receipt. A
  receipt that declares its own `verification.*.cmd` is REJECTED outright.
- the receipt only names a `claim_kind`; the registry maps kind -> required tiers.
  An unclassified receipt is INSUFFICIENT_DEPTH (exit 3), never green.
- tier4 admits an audit only if: exact `verdict: CLEAN` token (substring banned —
  "NOT CLEAN" no longer passes), an `auditor:` identity that differs from the
  receipt producer (self-audit rejected), AND a current evalcheck
  EVALUATOR_CALIBRATED receipt for that auditor against a sealed deck.
- cross-tier bootstrap guard: the sibling AUDIT file is hash-pinned before any
  tier runs; a tier that creates/modifies it -> REJECTED.
- tri-valued exit: 0 VERIFIED, 1 REJECTED, 3 INSUFFICIENT_DEPTH, 2 error.
  Consumers must match `verdict == "VERIFIED"` exactly, not startswith.

Latest-Lev note: the flowmind YAML executor is STILL a boot-stub on origin/main;
the 923-line claim/eval/admission design is approved but runtime-unmaterialized.
`claim_verify` is a runnable prototype of its `deterministic_case` evaluator; the
`hybrid_case` (LLM audit as observation, measured not trusted) is realized here by
gating tier4 on evalcheck calibration.

## Known findings for the Lev dev

- **Stale grep in `claimgate_blocks_overclaim` (`dna/gates.yaml`).** The gate's
  `check` greps the `bad`-fixture consume output for the literal token
  `host_blocked`. Verified 2026-07-22: the CLI's actual refusal text for that
  fixture is `Cannot issue ClaimGate host execution witness for invalid
  projection: run_metadata.live_lev_consumed_forbidden, ...` — a correct
  refusal, but it does not contain the substring `host_blocked` anywhere.
  Behavior is right (the overclaim is refused); the gate's assertion is
  stale and would report this correct refusal as a gate failure (RED) if
  run today. Fix is on the Lev side: either match the refusal message this
  code path actually emits, or emit a `host_blocked` token from that refusal
  path to match the gate's original intent. Not a ClaimGate-side defect.
