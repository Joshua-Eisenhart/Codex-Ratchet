# Constraint Box: how this directory was assembled

Landed 2026-07-26. Status as of 2026-07-27: `passes local rerun` for the unit
suite only — 220 tests run, 220 pass, exit 0, measured three times on this host
by the closing lane. Not `canonical by process`. Nothing here is promoted.
`promotion_allowed: false`.

The counts moved twice in one day and the earlier figures are not wrong, only
stale. 194 was the baseline when the 2026-07-26 round opened; 200 when it closed;
213 when this closing round opened, five build lanes having added 13 tests; 220
now. Of the last +7, one is `tests/test_pins_current.py` and six are
`tests/test_mmm.py`, which no card requested — see the unattributed-addition row
below. The passing count has never gone below its baseline.

The earlier "suite is red, 194 run, 193 pass, 1 fail" status was true when
written and became false during the 2026-07-26 lane round. It stayed in this
file for a day after the suite went green. See "The suite went green, and nobody
owns the edit" below.

Constraint Box is the standalone consolidation of the ClaimGate lineage. The
ClaimGate implementation itself stays where it is, at `claimgate_plugin/`. This
directory does not copy it.

## Source packs

All five packs were built on 2026-07-25 and lived only on the Desktop. None had
been committed. Chronological order, with the archive digest each was taken
from:

| Pack | Built | Files | Wheel | sha256 |
|---|---|---:|---|---|
| `CONSTRAINTBOX_LLM_HANDOFF_20260725_v0` | 17:40 | 51 | prototype | `cfbf3281c4dd18605b57eafd613c4b4d1e88d2e440d0fd79b48f68311517e29a` |
| `CONSTRAINTBOX_COMPLETE_STANDALONE_20260725_v1` | 20:07 | 73 | — | `0b45017d4bd3d43807e2021d0a5950c72da865d8cc12885c2f8f47ed4cb1b5ac` |
| `CONSTRAINTBOX_COMPLETE_STANDALONE_20260725_v2` | 20:07 | 113 | 0.2.0 | `2e1f8aadaefa07d4de3e352610da0958acc23c86119a85179617d364fbfddf46` |
| `CONSTRAINTBOX_UNIFIED_SIM_SYSTEM_20260725_v4` | 21:00 | 116 | 0.3.0 | `57e9d915b5742bb4cdb37e4d3e441db19dac7b3ea9ff38bef03ba41af0a74abf` |
| `ConstraintBox_Handoff` (embeds v4 as its seed) | 22:05 | 541 | 0.3.0 | `9ea56e4ec07106c2b9937dce1176273673ebd2225f8949666f291277c1f5f414` |

There is no v3. The handoff's `03_CONSTRAINTBOX_SEED/` is byte-identical to the
v4 pack apart from one added file, `00_SEED_STATUS.md`, which is kept here.

## What was merged, and why

The code advanced from v2 to v4. The documentation regressed. v4 added
`adapters/`, `applicability.py`, `maintenance.py`, and `semantic.py`, and
dropped 26 markdown files that exist only in v2 — the foundation set, the audit
set, and the LevOS extraction map.

This directory therefore takes:

- **code, config, fixtures, tests, receipts, workers, scripts, docs** from v4;
- **`doctrine/`** from v2, holding the dropped documents in their original
  grouping (`00_START_HERE`, `01_FOUNDATION`, `02_ARCHITECTURE`, `03_EXECUTION`,
  `05_AUDIT`, plus four manifest-level documents).

`doctrine/` is the layer that carries the threat model, the hostile test matrix,
the branch/prune/merge rules, the nominalist alignment note, and the LevOS
extraction map. Losing it was the main risk in adopting v4 alone.

## Deliberately not copied

| Excluded | Reason |
|---|---|
| `dist/constraintbox-0.3.0-py3-none-any.whl` | build artifact; the repo does not carry built environments |
| `reference/existing_claimgate_review/` | a second copy of files already live at `claimgate_plugin/` |
| `provenance/source_material/gemini*.txt` | raw transcript, 220127 bytes, `sha256:3d5d7888f7e10aba6de5ca4fbe8b429d9d6976b29c318952adae56d69e30f5d9`; retained on the Desktop and inside the handoff archive |
| `__pycache__/`, `*.pyc` | generated |

## Change applied on landing

One defect was found and fixed before this directory was created. It is not a
style change and it is not cosmetic.

**`src/constraintbox/constraints.py` — the two solver backends disagreed on
legal input.**

`FiniteConstraintProblem.from_spec` deduplicated variable domains by `repr()`,
while `evaluate_constraint` compares with `==`. JSON `1` and `true` have
distinct reprs but are `==` in Python, as do `1` and `1.0`. Such domains passed
intake and were then read differently by each backend. The z3 backend also
resolved a constant to a domain address by repr-string lookup, so a float
constant could not address an integer domain value.

Reproduced before the fix, in both directions:

| Spec | enumeration | z3 |
|---|---|---|
| domain `[1, true]`, `a == true` | `BOUNDED_SAT` | `BOUNDED_UNSAT` |
| domain `[1, 1.0]`, `all_different(x, y)` | `BOUNDED_UNSAT` | `BOUNDED_SAT`, witness `{x: 1.0, y: 1}` |
| domain `[1]`, `v == 1.0` | `BOUNDED_SAT` | `BOUNDED_UNSAT` |

The second row is the serious one: z3 returned a bounded witness that the
system's own evaluator rejects.

The fix has two parts. Intake now rejects any domain whose values collide under
`==`, not merely under `repr`. The z3 backend now resolves addresses by `==`
against the domain, matching the enumeration backend. Because intake guarantees
pairwise-distinct domains, at most one address can match.

Regression: `tests/test_constraints_backend_parity.py`. Four of its ten tests
fail against the unmodified v4 source and all ten pass here — the test has
teeth rather than restating the fix. It also carries a seeded randomised
differential over the shared operator subset, which checks three properties:
the two backends return the same status, every z3 model satisfies the
enumeration evaluator, and every z3 `UNSAT` survives full enumeration. The
randomised part did not catch the original bug — its value pool contains no
`==`-colliding pairs — so it guards against future divergence rather than
this one.

## Findings recorded, not fixed

| Where | Finding | Severity |
|---|---|---|
| `src/constraintbox/parity.py` | `independent_families` counts `quimb` as independent of `numpy`, but quimb's default linear algebra is numpy. Not load-bearing in the retained receipt, where jax and numpy already supply two families. | latent |
| `src/constraintbox/numeric.py` | `isinstance(value, (int, float))` admits `bool`, so a values list of JSON booleans is accepted as numeric. | minor |
| `src/constraintbox/ledger.py` | `append` calls `verify()`, which re-reads the whole ledger, so appending n records is O(n²). | scaling |
| `src/constraintbox/estate.py` | A failing capability recorded `stderr_sha256` but never the stderr text, so a failure could not be diagnosed afterwards. This bit on the first darwin run: `quimb_tensor` came back `FAILED`, did not reproduce, and the message was gone. **Fixed** — non-READY receipts now retain bounded stdout/stderr text alongside the digests. The original quimb failure remains unexplained. | fixed |
| `src/constraintbox/estate.py` | A version mismatch returns early with a hardcoded `{"positive": False}` before the oracle comparison runs, so every `DRIFT` row reports `controls.positive = false` as a default rather than a measurement. Version drift and control outcome are conflated in one state. **Fixed 2026-07-26** — the early return is gone; a drifted capability now runs its full control battery and the drift reason and the control outcome are recorded separately. Guarded by `tests/test_estate_drift.py` (3 tests, teeth confirmed: reverting the early return in a throwaway copy fails all 3). The fix was inert in production until `config/sim_estate_v2.json` was re-pinned to the post-fix controller digest, also on 2026-07-26. | fixed |
| `src/constraintbox/constraints.py` | `all_different` compared with `set()`, which is hash-based, so a legal unhashable JSON array domain value raised a bare `TypeError` from enumeration while z3 returned a witness — the same repr-vs-`==` split one layer down, missed by the first pass of the fix because the fuzz pool held only hashable scalars. **Fixed**, pool widened. | fixed |
| `system_v8/julia_optional/*/Project.toml` | No `[compat]` section on any isolated optional project, so a routine update can re-pull a breaking transitive dependency — which is exactly how Metatheory broke in the first place. | real, open |
| `system_v5/julia_carrier/Manifest.toml` | Gitignored, so the verified QuantumOptics/Symbolics resolution is local-only and not reproducible from a fresh checkout. | real, open |
| `src/constraintbox/estate.py` | `passed = all(controls.values())` was vacuously true over whatever keys existed. `mutation` is only inserted for certain oracles and `severance` only when `block_import` is set, so capabilities reached READY with `all_required_controls_passed` having never run them — including `pymdp_fep`, which is `required: true`, missing `mutation`. Mutation is the one control separating a worker that computes from one that echoes a constant. **Fixed** — receipts now carry `controls_not_measured` and say `measured_controls_passed_others_not_run`. The exemptions remain legitimate; claiming they ran did not. | fixed |
| `src/constraintbox/estate.py` | The TLA replay control's middle conjunct was `sha256(replay_out).hexdigest() != ""` — true for every possible input including empty bytes. A tautology dressed as a digest comparison, making replay strictly weaker than the positive control beside it. **Fixed** — now compares replay output to the base run. **Correction 2026-07-27: the fix has no test.** Reverting it to the exact tautology in a throwaway copy produced zero new failures against the suite, which was 200 tests when that revert was run and is 220 now. The count is stale; the finding is not, and nothing added since guards this expression. This row previously cited `_nvidia_receipt` as the model the fix copied; that function is the weaker of the two — see the `_nvidia_receipt` row below. | fixed, **unguarded** |
| `src/constraintbox/numeric.py` | `isinstance(value, (int, float))` admitted JSON booleans, so `[true, true]` was reported as summing to 2. **Fixed** — booleans now rejected as a category error. | fixed |
| `src/constraintbox/ledger.py` | The retained head defaults to a sibling file next to the ledger it authenticates, and `verify()` re-derives every hash from the ledger's own bytes. Editing a record, re-chaining, and rewriting the sibling head yields a forged chain that verifies clean. The class docstring correctly disclaims being a signature and scopes the guarantee to "when its head is retained" — the defect is that the default constructor retains it nowhere separate. Deliberately NOT fixed: where the head should live is an infrastructure decision, not a code tweak. | real, open |
| `src/constraintbox/controller.py` | `AgentProposalProfile` blocks authority-bearing keys by exact membership after `casefold()`, so `"command "`, fullwidth `ｃｏｍｍａｎｄ`, and Cyrillic-es `сommand` pass. Deliberately NOT fixed: nothing in the repo reads proposal payload fields, and any exact-key consumer would miss the lookalike too. Weaker than its docstring, with no demonstrated escalation path. | real, open, low |
| `src/constraintbox/applicability.py` | `ApplicabilityRegistry` names the capabilities a claim type requires, but nothing wires it to `ConstraintBoxController.run()` or `EstateRunner.run_capability()` — zero references in `controller.py`. A declared requirement can sit disconnected from the decision it is supposed to gate. Found by codex. **STILL OPEN after 2026-07-26.** A `constraintbox applicability` CLI subcommand was added that day and reported as closing this row. It does not. Re-checked: `grep -rn "applicability\|ApplicabilityRegistry" src/constraintbox/controller.py src/constraintbox/estate.py` still exits 1. The only importers are `__init__.py` and `cli.py`. The module is now typeable by a human; it is still not load-bearing on any decision. | real, open |
| `workers/estate/capability_worker.py` | **The `dispatch` evidence field is a hardcoded string list in every worker.** `["quimb.qarray", "quimb.eigvalsh", ...]` are literals the author typed, not a record of calls made. `controls["dispatch"] = True` means only that the worker printed some strings, so the field cannot distinguish a real engine run from a numpy stand-in emitting the same list. This is the same failure the gate exists to catch, one layer down. Only `stablehlo_sha256` (a hash of compiled JAX IR) resists forgery among the passive witnesses. **Widened 2026-07-27: there is a second site this row did not name.** `estate.py:790` inside `_nvidia_receipt` assigns `"dispatch": True` as a bare literal in the controller itself, not in a worker. Measured: a two-line `/bin/sh` script named `nvidia-smi` reaches `READY` / `all_required_controls_passed`. `nvidia_device` is in both `required_capability_sets` routes for S4. | real, open |
| `src/constraintbox/estate.py` | **`all_required_controls_passed` is emitted at three sites; `controls_not_measured` can be written at one.** The claim is emitted at `estate.py:694` (`_tla_receipt`), `:807` (`_nvidia_receipt`) and `:1222` (`run_capability`); the honesty field is assigned only at `:1200`, inside `run_capability`'s tail. `_tla_receipt` and `_nvidia_receipt` return early and can never emit it, so those two capabilities can claim a full pass while silent about controls that never ran. The mechanism built to stop exactly that claim covers one emission site of three. Found by an independent reader 2026-07-27, reproduced. | real, open, high |
| `src/constraintbox/estate.py` | Severance was skipped whenever `block_import` was None, i.e. every engine running in a subprocess. `sever_env` was added to break the external binary and require failure. **The `julia_density` half of this is now void** — Julia was removed from Constraint Box by owner ruling and the capability is `UNTESTED` with `controls: {}`; no control runs for it. `sever_env` remains in the code with no current user. | superseded |
| `src/constraintbox/estate.py` | **Severance tests module reachability, not operation execution — it does not do the job claimed for it.** Demonstrated: a worker that does `import scipy`, touches `scipy.__name__`, then computes with stdlib `math` is indistinguishable from one that genuinely calls `scipy.linalg.expm`. Both give positive exit 0 and severance exit 1. The import exists only so severance has something to sever. Operation-level poisoning discriminates perfectly — replace the claimed function with one that raises, then **surviving is the failure**: the fake exits 0, the real one exits 1. The polarity inverts. **Partly implemented 2026-07-26** — `workers/estate/operation_poisoner.py` exists and `estate.py` runs it, but only for the two capabilities that declare `sever_operation`: `numpy_density` → `numpy.linalg.eigvalsh` and `scipy_channel` → `scipy.linalg.expm`. Every other capability has no operation control. Worse, `operation` is absent from `expected_controls`, so a capability without `sever_operation` does not even appear in `controls_not_measured` — the gap is silent. | partly fixed, open |
| `src/constraintbox/numeric.py` | The boolean-rejection fix has **no test**. Reverting `_is_number` to a bare `isinstance(value, (int, float))` restores the defect and the suite is unchanged. Re-confirmed 2026-07-26 against the current suite: reverting the guard in a throwaway copy produced **zero new failures** at 194 tests. The count in the original row (178) is stale; the finding is not. Other defences landed alongside it are equally unguarded — the enumeration was never completed, so treat the count as unknown rather than four. | real, open |

## Retained receipts do not describe this host

`receipts/` holds S1–S4 plus the wheel smoke and preflight records carried over
from the packaging host. They were generated under Python 3.12.13 against
`requirements/locks/*-linux.lock`, at `/tmp/constraintbox-estate-e*/bin/python`.
This machine is darwin/arm64 running Python 3.13.6. Those receipts are evidence
about the packaging host and nothing else. Host-valid receipts live in
`receipts/darwin/`.

Host-valid receipts live in `receipts/darwin/`.

**The "all carrying the current controller digest" claim in the earlier version
of this paragraph was false when written, and stayed false for a day.** The
receipts recorded controller `29c3dcac…`; `receipts/*.json` on the packaging
host recorded `c4233d49…`; the manifest pinned `a2916880…`; the controller on
disk hashed to something else again. Four digests, no agreement. Corrected
2026-07-26 by re-pinning the manifest and regenerating every darwin receipt from
the controller now on disk.

**The pin went stale again within a day, for the same reason as before.** The
2026-07-26 round left the manifest pinned at
`61e5d39dab1c084f78bdb54893f47001992c87e6a795a3ec054b748db890efc3`, and then a
later lane in that same round edited `estate.py` to fix the timeout defect. A pin
is data and does not follow the file it names. Re-pinned 2026-07-27 by the
closing lane; the two other digests in the manifest, `worker_sha256` and
`import_blocker_sha256`, were checked against disk first and were already
correct, so only the one stale value was edited.

**Then it went stale a THIRD time, the same day, by the same mechanism.** The
paragraph that stood here said: "Current state, measured 2026-07-27T05:45–05:46Z:
controller on disk, manifest pin, and all four estate receipts agree at
`9ce0edb4d109…`." That was true when written and was false within the hour. A
lane in the 2026-07-26/27 build round edited `estate.py` at 23:26 local to close
the mutation-timeout defect, which moved the controller to
`ff1fb8d1b9bbd5f52e034e0ad33a62000a50148944844d9032564baadb3256a7` and left the
`9ce0edb4…` pin behind it.

The consequence is not cosmetic. A stale controller pin short-circuits every
capability to `controller_source_digest_mismatch` with `controls: {}`, so no
control runs at all and the control fix that caused the staleness is invisible in
production. Measured directly: an S1 run against the stale pin returned empty
`controls` for every capability.

Current state, measured 2026-07-27T08:07Z: controller on disk, manifest pin, and
all four estate receipts agree at
`ff1fb8d1b9bbd5f52e034e0ad33a62000a50148944844d9032564baadb3256a7`, and
`controller_source_digest_mismatch` appears zero times in all four.
`DENSITY_PARITY.json` and `MAJOR_RUN_PREFLIGHT.json` carry no controller field
at all — their schemas have no such key — so the digest claim covers the four
estate receipts only. Do not read "all six receipts carry the digest".

**This recurrence is now guarded.** `tests/test_pins_current.py` recomputes each
of the three pinned digests and fails on a stale pin or a deleted pin key. It is
the first of the three pin refreshes to have any test behind it. It does not
guard `workers/estate/operation_poisoner.py`, which carries no pin — see the
findings row below.

All 20 manifest capabilities appear exactly once with a non-empty reason:
7 `READY`, 6 `DRIFT`, 2 `FAILED`, 2 `UNAVAILABLE`, 3 `UNTESTED` — unchanged in
distribution from the previous round. The earlier figure of 22 capabilities with
5 `UNTESTED` predates the removal of the two Julia capabilities from the
manifest. Tiers S1–S3 are `DRIFT` against the Linux locks, S4 is `FAILED` with
no NVIDIA device, parity is `FAILED` for want of a second independent READY
density family, and preflight is `PARKED`.

Two things visible in the regenerated receipts that were not visible before:

- **The DRIFT fix is live and reachable.** `numpy_density` and `scipy_channel`
  are `DRIFT` and each records six passing controls including `operation`. Before
  the fix a DRIFT row returned early with `{"positive": False}` and measured
  nothing. Version drift and control outcome are now separate facts.
- **Four capabilities never ran their mutation control** — `z3_finite`,
  `cvc5_finite`, `cotengra_path`, `pymdp_fep` — three of which are
  `required: true`. The receipts say so in `controls_not_measured`. Tier state
  and CLI exit code do not.

`receipts/darwin/HOST_ACCEPTANCE_REPORT.md` was **regenerated 2026-07-27** from
the six receipts above. The stale version claimed 22 capabilities, `julia_density`
READY "for the first time", a controller digest `ccba74624622b969` matching
nothing on disk, and stated that DRIFT rows never measure their controls — which
had stopped being true. It is still prose with **no checked-in generator**; it
now names the exact commands that produced each receipt it summarises, so a
reader can re-derive it, but nothing enforces that it stays current. It will go
stale again the next time the receipts move.

States recorded on the packaging host: S1 `READY`, S2 `DEGRADED`
(julia_density unavailable, not required), S3 `DEGRADED` (pykoopman, torch,
dimod unavailable or untested, none required), S4 `FAILED` (no NVIDIA device).

`MAJOR_RUN_PREFLIGHT` reports `READY` over two `DEGRADED` tiers. That is the
designed behaviour, not a defect: `major_run_preflight` accepts `DEGRADED` when
every capability marked `required: true` is `READY`.

## Changes landed 2026-07-26 / 27

Five build lanes plus a closing lane. Every row states whether a test guards the
change. A row with no test says so.

| # | Change | Files | Test guarding it | Status |
|---|---|---|---|---|
| 1 | DRIFT no longer short-circuits the control battery | `src/constraintbox/estate.py` | `tests/test_estate_drift.py`, 3 tests, teeth confirmed by revert | fixed, reachable |
| 2 | Controller digest re-pinned so the manifest matches the controller on disk | `config/sim_estate_v2.json`, `controller_sha256` only | none — a pin is data, not behaviour | landed |
| 3 | All six `receipts/darwin/` receipts regenerated against the re-pinned manifest | `S1/S2/S3_ACCEPTANCE.json`, `S4_BOOT.json`, `DENSITY_PARITY.json`, `MAJOR_RUN_PREFLIGHT.json` | none — receipts are outputs | landed |
| 4 | Four dead modules reachable from the CLI: `lease`, `discharge`, `evidence`, `applicability` | `src/constraintbox/cli.py`, `__init__.py` | `tests/test_cli_wiring.py`, 5 tests | reachable, **not** load-bearing |
| 5 | `constraintbox gate <receipt.json>` runs the ClaimGate chain. **Corrected: the exit table has five entries, not three.** `GATE_EXIT_CODES` in `gate.py` is now the single source of truth — ADMITTED 0, REFUSED 1, INSUFFICIENT_DEPTH 3, PARKED 4, EVALUATION_ERROR 5, with `GateError` staying at 2 | `src/constraintbox/gate.py`, `cli.py` | `tests/test_gate_entrypoint.py`, 9 tests, teeth confirmed by revert | landed |
| 6 | Julia reference removed from the evidence test fixture | `tests/test_evidence.py` | fixture rename only | landed |
| 7 | numpy containment regression: exit-expectation corrected from `0` to `{0,3}` | `claimgate_plugin/run_numpy_containment_regression.py` | none | landed, **runner still RED** |
| 8 | **Six** bypass fixtures captured, not four. e1–e4 on 2026-07-26 (prose claim, unexecuted operation, manufactured engine independence, lease/archive divergence); e5 and e6 on 2026-07-27 (nested input yields no disposition or ledger record; equivalent Unicode keys survive the duplicate-key guard) | `claimgate_plugin/fixtures/bypass2/`, `run_bypass2_regression.py` | the runner is the test | captured, **0 closed** |
| 9 | Subprocess timeout no longer scores the **severance** and **operation** controls as passing. A timeout returns `code=None, timed_out=True` rather than exit 124 | `src/constraintbox/estate.py` | `tests/test_estate_timeout.py`, 2 tests, teeth confirmed by revert | fixed for two controls of three — see the corrected row below |
| 10 | bypass2 runner polarity: it now fails on deviation in **either** direction, with distinct reason codes `HOLE_CLOSED_MOVE_TO_V1`, `HOLE_REOPENED`, `FIXTURE_MISSING`, `NO_FIXTURES_DECLARED` | `claimgate_plugin/run_bypass2_regression.py`, `fixtures/bypass2/bypass2_regression_v1.json` | the runner is the test; each reason code was fired by hand | landed, one guard dead — see below |
| 11 | Controller digest re-pinned a second time, `61e5d39d…` → `9ce0edb4…`, after change 9 edited `estate.py` and left the change-2 pin stale | `config/sim_estate_v2.json`, `controller_sha256` only | none — a pin is data, not behaviour | landed |
| 12 | All six `receipts/darwin/` receipts regenerated against the re-pinned manifest; all four estate receipts confirmed carrying `9ce0edb4…` | `S1/S2/S3_ACCEPTANCE.json`, `S4_BOOT.json`, `DENSITY_PARITY.json`, `MAJOR_RUN_PREFLIGHT.json` | none — receipts are outputs | landed |
| 13 | `receipts/darwin/HOST_ACCEPTANCE_REPORT.md` regenerated from those six receipts | `receipts/darwin/HOST_ACCEPTANCE_REPORT.md` | none — **still prose with no checked-in generator** | landed, will go stale again |
| 14 | Controller digest re-pinned a **third** time, `9ce0edb4…` → `ff1fb8d1…`, after a build lane edited `estate.py` and left the change-11 pin stale. `import_blocker_sha256` and `worker_sha256` were hashed against disk **before** editing and both already matched, so exactly one value changed | `config/sim_estate_v2.json`, `controller_sha256` only | `tests/test_pins_current.py` | landed |
| 15 | **`tests/test_pins_current.py` added — the check open decision 8 asked for.** One test, three subTests; asserts each pin key exists and each digest equals the file it names. Box root resolved from `Path(__file__).parents[1]` and the controller from `Path(estate.__file__)`, so it needs no git checkout and it follows the controller rather than a hardcoded path | `tests/test_pins_current.py` | it **is** the test; teeth confirmed by three reverts in a throwaway copy with `.git` absent — controller pin staled → FAIL, import-blocker pin staled → FAIL, `worker_sha256` key deleted → FAIL, control and restored copies both OK | fixed, guarded |
| 16 | All six `receipts/darwin/` receipts regenerated in a single quiet pass at 08:07Z against the re-pinned manifest. All four estate receipts confirmed carrying `ff1fb8d1…`; `controller_source_digest_mismatch` count is 0 in all four; controls are populated again for all 15 capabilities that reach an executable oracle | `S1/S2/S3_ACCEPTANCE.json`, `S4_BOOT.json`, `DENSITY_PARITY.json`, `MAJOR_RUN_PREFLIGHT.json` | none — receipts are outputs | landed |
| 17 | `receipts/darwin/HOST_ACCEPTANCE_REPORT.md` regenerated, then corrected: its first version was written against a receipt set that was replaced minutes later, and asserted three things that had stopped being true (the four timestamps, `quimb_tensor` FAILED, parity with no sources) | `receipts/darwin/HOST_ACCEPTANCE_REPORT.md` | none — **still prose with no checked-in generator**, and it went stale within minutes of being written, which is the third time this file has done so | landed, will go stale again |

### What these changes did not do

- Change 4 made four modules typeable. It did not wire any of them to a
  decision. `applicability.py` in particular is still orphaned — see the
  corrected row above.
- Change 7 fixed one runner defect. It turned no clause green. The regression
  still fails 7 of 7 clauses because `claim_policy_gate` cannot witness a torch
  leg, so the chain never reaches the seal. The containment rule is
  **unmeasured**, not refuted.
- Change 8 captured six bypasses. It closed none. All six are still `ADMITTED`.
  Twelve of the eighteen reported bypasses remain uncaptured, and the
  denominator 18 is itself unverified — the lane that extended the corpus could
  only account for about twelve candidates in the grouping it was handed. Of the
  four boundaries it measured, two reproduced and were captured (e5, e6) and two
  held and were deliberately not captured: the `request_id` directory-name guard
  accepts only a single plain component, and the payload byte bound is inclusive
  and exact with no off-by-one. That negative result is recorded here because it
  exists nowhere else.
- Change 9 fixed **two of three** timeout-vulnerable controls. See the corrected
  row below; the mutation control is still exposed and a code comment claims
  otherwise.
- Change 10 made the bypass2 runner safe to wire into CI. It did not wire it.
  Neither bypass runner has a CI caller — `grep` across `*.sh`, `Makefile`,
  `*.yml`, `*.yaml` finds zero. Six captured cases that nothing runs
  automatically are six cases that will rot.
- Changes 11 and 12 are a repeat of changes 2 and 3, one day later, for the same
  structural reason: a digest pin does not follow the file it names, and nothing
  in the repo checks the two against each other. This will happen again on the
  next `estate.py` edit unless a check is added.
- Changes 14 and 16 are that same repeat a third time. The prediction in the line
  above was correct and the interval was hours, not days. Change 15 is the check
  that was missing. It closes the recurrence for the three pinned files only,
  and only when something runs the suite — nothing in CI does.
- Change 15 does **not** guard `workers/estate/operation_poisoner.py`. That file
  has no pin in the manifest to check.

### The suite went green, and nobody owns the edit

`tests/test_cli_wiring.py:38` asserted the subcommand set exhaustively and
omitted `gate`, which `cli.py` registers. This file recorded that as an open
owner decision needing a one-line fix.

**The fix was made. `"gate"` is in the set literal now, and the suite is green
at 200.** No lane claimed it, and no lane's log contains a write to that file.
The edit is unattributed. That is worse than the red suite it resolved: an
unowned edit to a test is exactly the move the gate exists to catch, and it
landed inside the gate's own repository during a hardening round.

Counts, measured by the closing lane on 2026-07-27: 200 tests, 200 pass, exit 0,
before and after the pin change. Baseline for the round was 194. The passing
count has never gone below it.

## Findings recorded this session, not fixed

| Where | Finding | Severity |
|---|---|---|
| `src/constraintbox/estate.py:500, 1010, 1024` | **A subprocess timeout was recorded as the severance and operation controls passing.** A timeout returned exit `124`; both controls test `!= 0`. **Fixed 2026-07-26 for severance and operation.** A timeout now returns `code=None, timed_out=True`, both controls require `not X_timed_out`, and the timed-out control is named in `evidence["controls_timed_out"]`. Guarded by `tests/test_estate_timeout.py`; teeth confirmed by reverting each expression separately. A third vulnerable site was found during the fix and is **not** covered — see the row below. | fixed for severance and operation |
| `src/constraintbox/estate.py:1029, 1041, 1144-1148` | **The mutation control is still exposed to the timeout defect, and a comment now says it is not.** `controls_timed_out.append("mutation")` fires at `:1032`, but `controls["mutation"]` is only assigned inside the oracle allow-list at `:1041`, so for the `solver`, `path` and `fep` oracles there is no key to force false and `passed = all(controls.values())` skips it. The comment added by the fixing lane at `:1144-1148` reads "force the attempted control false… This keeps capability state and CLI disposition fail-closed". The block below it does one thing: assign `evidence["controls_timed_out"]`. It forces nothing. Measured on `z3_finite` (`required: true`, S1): capability `READY`, tier `READY`, real CLI `--enforce` exit `0`, with `mutation` listed in both `controls_timed_out` and `controls_not_measured`. Also hits `cotengra_path` (required, S2) and `pymdp_fep` (required, S3). **A comment claiming a check the code beside it does not run is the verdict-inflation pattern this gate exists to catch, introduced by the lane that was fixing that pattern.** The closing lane's own verifier initially scored this row CLOSED on the strength of the three quoted expressions without their enclosing `if` guard; an independent reader caught it. | real, open, high |
| `src/constraintbox/estate.py:957, 1029` | `controls["mutation"]` is only assigned for a fixed oracle set. For the `path`, `solver` and `fep` oracles it is never measured, and `passed = all(controls.values())` is taken over whichever keys exist. A `cotengra_path` worker that imports the library, never opens the fixture, and prints two constants reaches `READY` with CLI exit `0` under `--enforce`. The receipt is honest in prose — it records `controls_not_measured: ["mutation"]` — but the machine-readable surfaces, tier state and exit code, both say pass. Confirmed live in the 2026-07-27 receipts: four capabilities carry `controls_not_measured: ["mutation"]`, three of them `required: true`. | real, open |
| `src/constraintbox/estate.py:1136-1138` | **The operation control is defeated by inspection, and it is the control built to fix the weaker severance control.** `operation_poisoner.py` replaces the claimed function with one that raises, and the control is `not poison_timed_out and poison_code != 0` — surviving is the failure. But the severed function is trivially identifiable: `__name__` is `_severed`, `__qualname__` is `poison.<locals>._severed`, `__module__` is `__main__`. A worker that reads `__name__`, never calls the operation, and exits nonzero passes the control. Reproduced end to end: genuine worker and inspecting stand-in both reach `READY` / `all_required_controls_passed` with all six controls true and `evidence["operation_severed"]` naming `numpy.linalg.eigvalsh`. The poisoner's docstring considers only two worker classes — calls it and dies, or merely imported and survives — and scores the third, inspects and deliberately dies, as genuine. Owner decision: identification-resistant in-process poisoning is hard, so the honest alternative may be to stop claiming the operation executed and record it as unmeasured. | real, open, high |
| `src/constraintbox/estate.py:899-904` | The `path` oracle's `positive` control is `contraction_cost > 0 and max_size > 0`. Nothing in it derives from the fixture. Two printed constants satisfy it. | real, open |
| `tests/test_cli_wiring.py:55, 58` | **The test suite requires the parent git checkout, which contradicts the standalone mission.** Line 55 hardcodes the absolute interpreter path; line 58 does `shutil.copyfile(repo / ".git" / "index", …)`. Copying the package anywhere outside a checkout hard-errors rather than skipping: `FileNotFoundError: '/private/tmp/.git/index'` (reproduced). Writes are safe — the real object store is attached read-only — but a project whose purpose is to run without its parent cannot ship a suite that needs it. Also the reason suite runtime went ~13s to ~40s. **Sized 2026-07-27: this is a much smaller job than the row implies.** The full package copied outside any checkout runs `199/200`. Exactly one test blocks true standalone, `test_lease_issue_verify_and_denial_dispatch`, and it is not the exhaustive-subcommand assertion. | real, open, one test |
| `src/constraintbox/gate.py` | `constraintbox gate` was **not standalone**, and the row said only that. **Corrected 2026-07-27 to "made visible and made to park", not "closed".** Three measured states: (1) box-only copy with cwd inside the box → `ADMITTED` exit 0, `chain_root_inside_box: true`, tier0 running the box's own `claimgate_plugin/claimgate.mjs` — **the box does verify standalone in this case**; (2) box-only with cwd elsewhere → `PARKED` exit 4, `tier0_checker: null`, with a reason naming both paths it looked for; (3) in-repo → `chain_root` still resolves to `/Users/joshuaeisenhart/Codex-Ratchet` and tier0 still runs the repo-root `claimgate/claimgate.py`. Case 3 is not eliminated, only recorded. The cwd dependence is not fixable in `gate.py`: `claim_verify.py:38` falls back to `os.getcwd()` when no `.git` or `system_v8` is found above it, and `gate.py` deliberately replicates that walk so the receipt is honest about it. **The case that carries the mission — case 1 — has no test.** `tests/test_gate_standalone.py` holds one test and it asserts the PARK path. | real, open, partly visible |
| `src/constraintbox/gate.py` | tier2 and tier3 are **unmeasured**. Both registered gates point at `system_v8/` paths outside the box, and no fixture in `claimgate_plugin/fixtures` carries `claim_kind` `manifold_sim` or `quantum_claim` — all 159 are `field_only` or unregistered. They SKIP every time. Not broken, not proven. | unmeasured |
| `claimgate_plugin/claim_policy_gate.py:146` | Imports `witness_leg` from `claimgate_plugin/engine_witness.py`, whose own file header reads "FAILED CANDIDATE — PURGATORY. Do NOT import this from any gate." `SUPPORTED_ENGINES = ("jax", "julia")`, so a genuinely computing torch leg always reports `DECORATIVE_IMPORT`. This is the stage that blocks the numpy containment regression. Do not fix it by adding `"torch"` to the tuple — the purgatory header's stated root cause is that every control asks a process question, never whether the receipt's numbers came from the engine. **Escalated 2026-07-27: the import is production-reachable, not merely present.** `claim_policy_gate.py` is invoked from `hooks/post_receipt_gate.sh:123`, so the purgatory module sits in the fired-side chain, not on a shelf. | real, open, owner decision |
| `claimgate_plugin/run_bypass_regression.py` vs `run_bypass2_regression.py` | The two runners invert each other's exit convention by design. v1 exits 1 when an attack is still admitted; v2 exits 0 when every attack is still admitted. Wire both into CI and a fully vulnerable v2 result reads green. **Half corrected 2026-07-27.** v2 now fails on deviation in either direction against a recorded per-case expectation, so `exit 0` means "every case matched what was recorded", not "everything is still admitted". The inversion itself stands: a green v2 run over six still-open holes is still a green run. Neither runner is wired into CI, so the collision has never actually fired. | real, open, polarity fixed |
| `claimgate_plugin/run_bypass2_regression.py:379` | `COVERAGE_MISMATCH` is **dead code**. `rows.append` executes exactly once per `CASES` entry, unconditionally, so `len(rows) != len(CASES)` and `row_ids != declared_ids` can never be true. Verified empirically: duplicating a case id does not trip it. The coverage property is still carried, by the per-case `FIXTURE_MISSING` preflight and by `NO_FIXTURES_DECLARED`, both of which do fire — but one of the two coverage guards is inert. Either delete it or give it a real trigger, for example asserting every `RUNNERS` key is declared in `CASES`, which would catch a case being dropped from the table while its runner stays behind. | real, open, low |
| `claimgate_plugin/run_bypass2_regression.py:139, 148` | `chain()` reads the disposition from `json.loads(lines[-1])` and separately returns `receipt_sha256 = _sha(receipt)`. Every ledger line carries its own `receipt_sha256` and `receipt_path`; neither is read, so the runner reports a digest it never bound to the verdict. Measured against the real `chain()` body with a temp ledger: `admitted: true` reported with digest `d1519bc1…` while the line that produced the verdict carried `ffff…`. Lanes run in parallel and the git pre-commit hook fires the same chain, so a concurrent append in that window is realistic. | real, open |
| `claimgate_plugin/run_numpy_containment_regression.py` | Two copies now exist and have diverged by one hunk: the repo-root copy and `constraint_box/claimgate_plugin/`. The wider fact is that `constraint_box/claimgate_plugin/` is a full duplicate of the plugin, so two ClaimGates exist and have started to drift. Owner should name which is canonical before the box goes standalone. **The split widened during the 2026-07-26/27 round, not narrowed.** `run_bypass2_regression.py` and the entire `fixtures/bypass2/` corpus exist **only** in the repo-root copy. Eight files now differ. A corpus audit in the same round also measured the duplicate tree by mistake and reported its figures as the gate's — see the corpus row below. | real, open, widening |
| `claimgate_plugin/` corpus reachability | An earlier audit reported 84 modules, 18 reachable, 66 orphaned, 344 fixtures, 169 exercised. **All six figures are wrong.** Re-derived by row on 2026-07-27: the primary corpus has **91 modules — 19 production-reachable, 1 test-only, 71 orphaned (78%)** — and 340 fixtures after the Julia exclusion, of which 213 are exercised, 66 unexercised and 61 reachable only through an orphaned loader. The 84/344 figures are the **duplicate** tree at `constraint_box/claimgate_plugin/`; the audit measured the wrong directory. The substantive finding is that the hostile corpus is largely shelf-ware: 61 fixtures sit behind runners (`run_bypass_regression`, `run_bypass2_regression`, `run_numpy_containment_regression`, `run_typed_grammar_regression`, `gatecheck.mjs` manifests, `run_od_deck.sh`, `canfail_probe.py`) that no CI `run:` line and no hook stage invokes — they appear only in YAML comments. The fixture denominator is a judgment call, not a measurement: 340 excludes 9 Julia files on the standalone-box rule, 349 includes them on the Codex-Ratchet rule where Julia is Canon. Neither is 344. | real, open, owner decision |
| `claimgate_plugin/results/numpy_containment_regression_v1.json` | Records `"rule_proven": false`, which reads as "rule refuted". The measured state is "rule not reachable" — the chain never got to the seal. A labelling question. | minor |
| `claimgate_plugin/fixtures/bypass2/e4/reproduce.py:74` | Returns `"temporary_repo_cleaned": True` as a literal inside the `try`, before the `finally` that calls `rmtree`. Asserts an outcome that has not happened. Feeds no verdict; same pattern as the defects above. | cosmetic |
| the new subcommands | **Corrected 2026-07-27: there are SIX, not five.** `lease`, `discharge`, `evidence`, `applicability`, `gate` and `deps` all have tests and **zero production callers**. `deps` was added by the dependency-freshness lane after this row was written. Measured CLI list: `demo, doctor, deps, solve, estate, estate-parity, preflight, lease, discharge, evidence, applicability, gate`. The hook fires `claim_verify.py` directly at `post_receipt_gate.sh:153`. There are now two front doors onto the same chain and the Constraint Box one is decorative until a caller is named. `run_gate` and `GateError` are also absent from `__init__.py` — re-checked 2026-07-27, still absent, `__init__.py` imports nothing from `gate.py`. | real, open |
| `src/constraintbox/gate.py` | **The gate records two verdicts and never compares them.** `disposition` is derived from the chain's exit code; `chain_verdict` is read from the chain's stdout JSON. Reproduced: `disposition: ADMITTED` recorded beside `chain_verdict: REFUSED` with `required_unmet: ["tier0","tier4"]`, from a chain that printed REFUSED and exited 0. This is the project's own "the verdict must agree with the field beside it" rule, violated inside its own gate. Not reachable through the shipped chain — `claim_verify.py:274-282` assigns verdict and code as a pair — and the CLI does not expose `chain`, so a Python caller is required. A missing invariant, not a live bypass; one assert closes it. | latent |
| `src/constraintbox/gate.py` | A chain that exits 0 with no output yields `ADMITTED` with `required_tiers`, `verified_tiers`, `required_unmet` and `tier_results` all empty. **An ADMITTED receipt listing zero verified tiers should not be constructible.** Same injected-chain caveat as the row above: `claim_verify.py:41` runs every child with `capture_output=True`, so the shipped chain's children cannot pollute its stdout. | latent |
| `src/constraintbox/gate.py` | The receipt's `chain` field is the hardcoded constant `CHAIN_RELATIVE_PATH`, not the chain that actually ran. Verified by passing a stub: the receipt still reads `claimgate_plugin/claim_verify.py`. An injected chain leaves no trace, which is what makes the two rows above undiagnosable after the fact. | real, open |
| `src/constraintbox/gate.py:127` | **The documented exit 2 is not performed for a missing registry.** The docstring promises exit 2 for "usage or I/O failure before the chain starts (GateError)". `run_gate` guards `receipt.is_file()` and `chain_path.is_file()` with `GateError` but calls `_sha(registry_path)` unguarded. A box copy missing only `gate_registry.json` raises an uncaught `FileNotFoundError`: **exit 1, empty stdout**. Exit 1 is REFUSED in the same docstring's table, so a broken install is indistinguishable from a refused claim to any exit-code consumer. Reproduced by the closing lane in a throwaway copy. Directly relevant to the standalone mission. | real, open |
| `src/constraintbox/cli.py:292-299` | The `--output` write runs **before** `if exit_code: raise SystemExit(exit_code)`, so a write failure replaces the disposition exit code with 1. ADMITTED 0 → 1 is the safe direction, but INSUFFICIENT_DEPTH 3 → 1 and EVALUATION_ERROR 5 → 1 both mislabel as REFUSED. No false green. | real, open, low |
| `src/constraintbox/gate.py` | Chain exit 4 maps to `EVALUATION_ERROR` although `GATE_EXIT_CODES` defines `PARKED: 4`. Unreachable in the shipped chain, which emits only 0, 1, 2, 3. Dead-code inconsistency rather than a defect today. | latent, low |
| `src/constraintbox/estate.py:345, 383` | The interpreter version probe and the environment inventory have **no `TimeoutExpired` handler at all**. A timeout there raises and aborts the run rather than producing a receipt. It cannot false-pass a control — the `except Exception` at `:396` wraps only the JSON parse, not the subprocess — so it is outside the class of the timeout defect above, but it is an unhandled exception path rather than a designed one. | real, open, low |
| `config/sim_estate_v2.json` | **The manifest pins three source files and does not pin the operation poisoner.** `controller_sha256`, `import_blocker_sha256` and `worker_sha256` are checked by `estate.py` at run time and now by `tests/test_pins_current.py`. `workers/estate/operation_poisoner.py` — current digest `9779cb64a0f2f78c0be041123a386f76cdefee0bc1b9513a039fa73bc8ccb548` — has no pin and no check. It is the control built to defeat the import-only fake, the one control whose polarity inverts (surviving is the failure), and it can be edited with no integrity signal anywhere. Adding a fourth pin was deliberately out of scope for the closing round; it is a one-line manifest addition plus one line in the existing test. | real, open |
| `receipts/darwin/` | **Two writers regenerated the receipts concurrently and produced an internally inconsistent set.** `DENSITY_PARITY.json` was left bound, by its own `receipt_sha256` map, to `S1_ACCEPTANCE.json` and `S2_ACCEPTANCE.json` bytes that no longer existed on disk. Caught by hashing both files and comparing them against that map, then fixed by regenerating all six in one quiet pass. The lesson to keep: a parity receipt records the digests it consumed, so that map is the check that detects a concurrent regeneration. `git status --porcelain` does not detect it — these files were already dirty, and porcelain equality also failed to detect a 25-line ledger append in the previous round. Porcelain equality is not an integrity check for an already-dirty file. | real, open, process |
| `constraint_box/mmm/`, `tests/test_mmm.py` | **ATTRIBUTED — the deletion proposal below is withdrawn.** Written by a second workflow, `wf_7e83ab0a-48a` lane 1, launched by the assistant at 01:09 local while this workflow's closing round was still active. The detection was correct and valuable: the closing lane hashed a 00:57 snapshot against 01:02 disk state, found six markdown packs, `mmm/load.py` and `tests/test_mmm.py` named in no card of its own, and refused to absorb them silently. The cause was an orchestration error, not an unowned write — the assistant judged the first workflow finished from "no repo writes in 15 minutes" and launched the second on that heuristic. The close lane was still running. The same collision produced the concurrent receipt regeneration recorded two rows above. Do NOT run the proposed `rm -rf`: the loader has been independently verified to run under a non-Claude interpreter with stdlib-only imports, and all six tests were severance-checked and fail when their mechanism is broken. Standing lesson: quiet-for-N-minutes is not a release signal for a workflow that owns files. | resolved, process |
| `src/constraintbox/estate.py` — `quimb_tensor` | **Intermittent, and density parity depends on it.** `FAILED` with `positive_witness_failed` at 08:01Z, its retained stderr reporting a Numba cache locator error while importing `quimb/core.py`; `READY` with `all_required_controls_passed` at 08:07Z with no change to any input. Both outcomes observed inside one session. This is the second occurrence — the row above recording an earlier unexplained `quimb_tensor` FAILED that "did not reproduce" is the first, and it can now be cross-referenced rather than left unexplained. `DENSITY_PARITY.json` reads `sources: []` on the failing run and `sources: ["quimb_tensor"]` on the passing one. The parity state is `FAILED` either way but for different reasons, so the parity receipt is not a stable fact about this host. | real, open |

## Standalone status, measured

| Question | Measured answer |
|---|---|
| Does the unit suite pass in the repo? | Yes. 220/220, exit 0, measured three times on 2026-07-27. |
| Does it pass outside any git checkout? | Almost. One test, `test_lease_issue_verify_and_denial_dispatch`, hard-errors on `.git/index`. Re-confirmed 2026-07-27 in a throwaway copy with `.git` absent; `tests/test_pins_current.py` passes there. |
| Are the manifest pins checked against the files they name? | Yes, for three of four. `tests/test_pins_current.py` covers `controller_sha256`, `import_blocker_sha256` and `worker_sha256`. `workers/estate/operation_poisoner.py` has no pin to check. |
| Does `constraintbox gate` verify from a box-only copy? | Yes, when cwd is inside the box: ADMITTED off the box's own `claimgate_plugin/claimgate.mjs`. Untested. |
| …with cwd outside the box? | No, and it now says so: PARKED, exit 4, `tier0_checker: null`. |
| …in the repo? | It reaches outside the box. `chain_root` resolves to the repo root. Recorded in every receipt, not eliminated. |
| Is there any Julia in `src`, `config`, `workers`, `tests`? | No. `grep -rniE 'julia'` exits 1; no matching filenames. |
| Are the gate suites wired into CI? | No. Zero callers for either bypass runner. |

## Open decision for the owner

**Superseded 2026-07-26.** This row described the S2 profile marking
`julia_density` as `required: false`, and asked which profile Codex-Ratchet
should run under. The question is moot: Julia was removed from Constraint Box by
owner ruling, `julia_density` is no longer in `config/sim_estate_v2.json`, and
S2 now holds four capabilities, none of them Julia. Confirmed: zero Julia
references in `src`, `config`, `workers`, `tests`. Julia remains Canon for
Codex-Ratchet at large — `system_v5/julia_carrier` resolves and loads
QuantumOptics v1.2.6 — it is simply outside this box.

The live owner decisions are now:

1. ~~**The one-line test fix.**~~ **Done, but unattributed.** `"gate"` is in the
   exhaustive set and the suite is green at 200. No lane claimed the edit and no
   lane log contains a write to that file. Decide whether an unowned edit to a
   test inside this repository is acceptable, or whether it should be reverted
   and re-made under an owner.
2. **Name a production caller** for the five CLI subcommands, or accept that
   they are decorative. `run_gate` and `GateError` are still absent from
   `__init__.py`.
3. **Decide which ClaimGate is canonical** — the repo-root `claimgate_plugin/`
   or the duplicate inside `constraint_box/`. They have diverged further, not
   less: eight files now differ, `run_bypass2_regression.py` and all of
   `fixtures/bypass2/` exist only at the repo root, and one audit has already
   measured the wrong tree and reported it as the gate's.
4. **`engine_witness.py`.** A production gate is load-bearing on an artifact the
   repo itself marked inadmissible, and the import is reachable from
   `post_receipt_gate.sh:123`. Nothing downstream of it can be trusted until
   this is settled.
5. **The operation control.** It is defeated by inspection, and it was the fix
   for the weaker severance control. Either find identification-resistant
   poisoning, or stop claiming the operation executed and record it as
   unmeasured. Do not leave the claim standing.
6. **The mutation control's comment.** `estate.py:1144-1148` claims a fail-closed
   behaviour the block does not perform, for three `required: true` capabilities.
   Fix the code or delete the comment. Leaving both is the exact defect class
   this project exists to catch.
7. **Wire the gate suites into CI, or stop citing the corpus.** 61 hostile
   fixtures sit behind runners nothing invokes. The bypass2 polarity is now safe
   to wire; the wiring does not exist.
8. ~~**Add a pin check.**~~ **Done, and narrowed.** The controller digest went
   stale a **third** time on 2026-07-27, hours after the second, by the same
   mechanism. `tests/test_pins_current.py` now recomputes all three pinned
   digests and fails on a stale pin or a deleted pin key; teeth confirmed by
   three reverts in a throwaway copy. Two things remain open and the decision is
   not closed until they are answered:
   1. `workers/estate/operation_poisoner.py` carries **no pin at all**, so the
      control built to defeat the import-only fake has no integrity binding. Pin
      it, or state that it is deliberately unpinned.
   2. **Nothing in CI runs this suite.** The guard fires only when a human runs
      the tests. A check nobody runs is the same shape as the pin nobody
      compared — see decision 7, which is the same problem for the gate suites.

## Gate suite exit codes, 2026-07-27

Run by the closing lane from the repo-root `claimgate_plugin/`, which is the copy
carrying the newest work. No `--enforce` anywhere; the exit code is the verdict.

**Corrected 2026-07-27: this table listed six suites and there are eight.**
`run_slop_regression.py` and `run_standing_regression.py` were missing. Both were
built during the 2026-07-26/27 round and neither had been recorded here. Re-run
in full by the closing lane:

| Suite | Exit | Result |
|---|---|---|
| `run_bypass_regression.py` | 0 | 12/12 blocked |
| `run_typed_grammar_regression.py` | 0 | 8 cases, all non-admitting on the fired chain, control pair splits on the one field between them |
| `run_bypass2_regression.py` | 0 | 6/6 still ADMITTED, 0 closed, 0 fixture errors, 0 deviations |
| `run_numpy_containment_regression.py` | **1** | 7 unmet clauses, `blocking_stage=claim_policy`, stages `{intake:0, recompute_veto:0, tier0:0, claim_policy:1}` |
| `run_slop_regression.py` | 0 | 12/12 fixtures matched, 24/24 negative fixtures clean, 0 deviations |
| `run_standing_regression.py` | 0 | 3/3 MATCH; the three producer bands give effective tier sets of 1, 3 and 5 tiers for the same claim kind |
| `formal/chain_bmc_z3.py` | 0 | 3 non-vacuous properties hold; `NoSilentExit` self-declared **VACUOUS** — no guard erasure or structural mutation can produce a counterexample, so it restates the encoding |
| `formal/chain_bmc_cvc5.py` | 0 | all properties unsat; `guards_proven_load_bearing` non-empty for `NoAdmitWithoutAllChecks` only, empty for the other three |

Four things this table does not say.

The numpy containment `1` is the known `engine_witness` block, unchanged — the
containment rule is unmeasured, not refuted.

`run_bypass2_regression.py` exit 0 means "every case matched what was recorded",
and what is recorded is that all six bypasses are still ADMITTED. A green run
over six open holes is still a green run. Do not read exit 0 as "no bypass".

`run_slop_regression.py` exit 0 is measured over a **top-level** census only —
`PLUGIN.glob("*.py")`, which never descends into `claimgate_plugin/formal/`,
`bridge/`, `hooks/`, `constraint_box/adapters/` or `scripts/`. Run recursively
over real code the same gate reports **20 suspects**, not 1: S1 15, S2 1, S3 2,
S5 2, with nine S1 hits in `scripts/validate_smt_not_tautology.py` alone, all
inside its own `_selftest()`. The CI path added in the same round scans whatever
a diff touches, anywhere, so it consumes the wide surface while the regression
measured the narrow one.

The runners are not side-effect-free. `run_bypass2_regression.py` appends to
`claimgate_plugin/results/gate_ledger.jsonl` through the e1 hook fire. The
previous round took the ledger from 439 to 464 lines; **this** round took it from
466 to 491. Repeated CI runs will grow it monotonically. `git status --porcelain`
does not reveal this, because the file is already dirty.
