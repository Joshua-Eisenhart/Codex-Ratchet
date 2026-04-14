# Controller Maintenance Closure Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build the missing maintenance-closure layer so bounded controller runs can update the live control surfaces from fresh result artifacts and audit outputs instead of leaving truth/queue/wiki state partially manual.

**Architecture:** Add one repo-local control-plane script, `system_v4/probes/maintenance_closure.py`, that reads fresh result JSONs plus `probe_truth_audit_results.json` and `controller_alignment_audit_results.json`, computes honest truth-label deltas for explicitly targeted legos, and patches only directly stale markdown surfaces. Keep this first wave narrow: no Telegram transport redesign, no broad controller rewrite, no scientific packet widening, and no automatic wiki editing in v1.

**Tech Stack:** Python stdlib, existing result JSON artifacts, existing audit JSON artifacts, markdown patching via structured string replacement, pytest for control-plane tests.

---

## Design constraints

- Use the Makefile interpreter as authority:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/Makefile`
- Status labels must remain exactly:
  - `exists`
  - `runs`
  - `passes local rerun`
  - `canonical by process`
- The new closure script must not infer broader lane completion from one packet.
- The new closure script must patch only explicitly targeted rows or explicitly targeted markdown sections.
- The new closure script must fail closed when the fresh artifact or fresh audits do not justify promotion.
- The new closure script must not edit wiki pages in v1.
- The new closure script must not invent new queue packets.

## Scope for v1

### In scope
- Create a closure script that can update these live surfaces when explicitly targeted:
  - `system_v5/new docs/plans/sim_truth_audit.md`
  - `system_v5/new docs/plans/sim_backlog_matrix.md`
  - `system_v5/new docs/plans/tool_integration_maintenance_matrix.md`
  - `system_v5/new docs/17_actual_lego_registry.md`
- Read these machine surfaces as inputs:
  - `system_v4/probes/a2_state/sim_results/probe_truth_audit_results.json`
  - `system_v4/probes/a2_state/sim_results/controller_alignment_audit_results.json`
  - target packet result JSON(s)
- Add tests for truthful promotion/demotion decisions.
- Add a dry-run mode that prints proposed edits without writing.

### Out of scope for v1
- Full Hermes runtime class
- Telegram transport changes beyond optional future call sites
- launchd scheduling changes
- auto-wiki editing
- automatic batch selection from all queue surfaces
- scientific sim edits except when needed to create stable test fixtures

---

## Proposed file changes

### Create
- `system_v4/probes/maintenance_closure.py`
- `system_v4/tests/test_maintenance_closure.py`

### Modify
- `system_v4/probes/live_queue_controller.py`
- `docs/plans/overnight_8h_run.sh`
- `system_v5/new docs/plans/run_overnight_8h_controller.sh`
- `telegram_bot.py`
- `system_v5/new docs/plans/controller_maintenance_checklist.md`
- optionally `system_v5/new docs/plans/on-demand-telegram-runner.md`

---

## Data contract for `maintenance_closure.py`

### CLI shape

```bash
$PYTHON system_v4/probes/maintenance_closure.py \
  --result-json system_v4/probes/a2_state/sim_results/density_hopf_geometry_results.json \
  --lego-id hopf_map_s3_to_s2 \
  --truth-row "explicit Hopf-map packet (`hopf_map_s3_to_s2`)" \
  --backlog-row B4 \
  --registry-row hopf_map_s3_to_s2 \
  --write
```

### Required inputs
- `--result-json`
- at least one explicit target surface selector:
  - `--truth-row`
  - `--backlog-row`
  - `--registry-row`
  - `--tool-row`

### Optional inputs
- `--lego-id`
- `--notes-fragment`
- `--dry-run`
- `--write`
- `--allow-noop`

### Required behavior
1. Read the target result JSON.
2. Read fresh audit outputs.
3. Derive the honest truth label from artifact + audits.
4. Re-read each target markdown surface immediately before patching.
5. Patch only the targeted row(s).
6. Print a compact closure report:
   - result path
   - derived truth label
   - surfaces touched
   - whether write or dry-run
   - blocked reason if no patch justified

---

## Truth-label derivation rules for v1

`maintenance_closure.py` should implement a small explicit decision function.

### Rule 1: `exists`
Use only when the result JSON exists but no fresh rerun/audit evidence is supplied.

### Rule 2: `runs`
Use when the artifact exists and the target packet clearly executed, but passing sections or fresh audit evidence are missing.

### Rule 3: `passes local rerun`
Use when all of the following hold:
- result JSON exists
- artifact indicates passing bounded checks
- fresh `probe_truth_audit.py` passed
- fresh `controller_alignment_audit.py` passed
- but artifact classification/process fields do not justify `canonical by process`

### Rule 4: `canonical by process`
Use only when all of the following hold:
- passing bounded checks
- `classification: canonical`
- complete non-empty `tool_manifest.reason` fields
- `tool_integration_depth` present
- at least one honest non-baseline load-bearing tool
- fresh `probe_truth_audit.py` passed
- fresh `controller_alignment_audit.py` passed

### Explicit non-promotion rule
If the artifact says `classification: classical_baseline`, the highest honest label is not `canonical by process`.

---

## Row-targeting strategy

### Truth surface
Patch exact anchor row text in:
- `system_v5/new docs/plans/sim_truth_audit.md`

Approach:
- find the row by the exact row label string passed in `--truth-row`
- replace only the `Runs`, `Passes local rerun`, `Canonical by process`, and `Notes` columns
- do not rewrite the whole table

### Backlog surface
Patch exact queue row in:
- `system_v5/new docs/plans/sim_backlog_matrix.md`

Approach:
- find the row by batch/priority key passed in `--backlog-row`
- update only `Current state` and `Next bounded move`
- preserve lane order and neighboring rows

### Registry surface
Patch exact lego row in:
- `system_v5/new docs/17_actual_lego_registry.md`

Approach:
- find the row by registry lego id passed in `--registry-row`
- update only the status / owner-result / note cells justified by the fresh artifact

### Tool matrix surface
Patch only when the closure target explicitly changes honest tool-depth framing.

---

## Task breakdown

### Task 1: Add failing tests for truth-label derivation

**Objective:** Lock the promotion rules before implementation.

**Files:**
- Create: `system_v4/tests/test_maintenance_closure.py`

**Step 1: Write failing tests**
Include at minimum:
- canonical artifact + clean audits -> `canonical by process`
- classical_baseline artifact + clean audits -> `passes local rerun`
- canonical artifact with empty manifest reason -> `passes local rerun`
- canonical artifact + failing audit -> blocked/no promotion

**Step 2: Run tests to verify failure**
Run:
```bash
PY=$(awk -F':=' '/^PYTHON[[:space:]]*:=[[:space:]]*/{print $2; exit}' Makefile | xargs)
"$PY" -m pytest system_v4/tests/test_maintenance_closure.py -q
```
Expected: FAIL because `maintenance_closure.py` does not exist yet.

**Step 3: Commit**
```bash
git add system_v4/tests/test_maintenance_closure.py
git commit -m "test: add failing maintenance closure truth-label tests"
```

### Task 2: Create minimal `maintenance_closure.py` skeleton

**Objective:** Make the new control-plane entrypoint importable and testable.

**Files:**
- Create: `system_v4/probes/maintenance_closure.py`

**Step 1: Implement CLI skeleton**
Add:
- arg parsing
- JSON readers
- markdown readers
- `derive_truth_label(...)`
- `main()`

**Step 2: Re-run the targeted tests**
Run:
```bash
PY=$(awk -F':=' '/^PYTHON[[:space:]]*:=[[:space:]]*/{print $2; exit}' Makefile | xargs)
"$PY" -m pytest system_v4/tests/test_maintenance_closure.py -q
```
Expected: some tests still fail, but import/entrypoint now works.

**Step 3: Commit**
```bash
git add system_v4/probes/maintenance_closure.py system_v4/tests/test_maintenance_closure.py
git commit -m "feat: add maintenance closure skeleton"
```

### Task 3: Implement truthful promotion logic

**Objective:** Make truth-label derivation match repo process rules.

**Files:**
- Modify: `system_v4/probes/maintenance_closure.py`
- Modify: `system_v4/tests/test_maintenance_closure.py`

**Step 1: Implement artifact checks**
Add helpers for:
- manifest completeness
- non-empty reasons
- load-bearing tool presence
- summary pass detection
- audit pass detection

**Step 2: Run tests**
Run:
```bash
PY=$(awk -F':=' '/^PYTHON[[:space:]]*:=[[:space:]]*/{print $2; exit}' Makefile | xargs)
"$PY" -m pytest system_v4/tests/test_maintenance_closure.py -q
```
Expected: PASS for truth-label tests.

**Step 3: Commit**
```bash
git add system_v4/probes/maintenance_closure.py system_v4/tests/test_maintenance_closure.py
git commit -m "feat: implement maintenance closure truth-label derivation"
```

### Task 4: Add markdown row patchers in dry-run mode

**Objective:** Produce exact targeted diffs without writing yet.

**Files:**
- Modify: `system_v4/probes/maintenance_closure.py`
- Modify: `system_v4/tests/test_maintenance_closure.py`

**Step 1: Implement targeted row patch helpers**
Helpers should support:
- truth table row replacement
- backlog row replacement
- registry row replacement

**Step 2: Add tests using small fixture markdown strings**
Verify only one row changes.

**Step 3: Run tests**
Run:
```bash
PY=$(awk -F':=' '/^PYTHON[[:space:]]*:=[[:space:]]*/{print $2; exit}' Makefile | xargs)
"$PY" -m pytest system_v4/tests/test_maintenance_closure.py -q
```
Expected: PASS.

**Step 4: Commit**
```bash
git add system_v4/probes/maintenance_closure.py system_v4/tests/test_maintenance_closure.py
git commit -m "feat: add targeted markdown row patchers"
```

### Task 5: Enable real-file dry-run against one known row

**Objective:** Prove the script can read real repo surfaces and propose the correct edit.

**Files:**
- Modify: `system_v4/probes/maintenance_closure.py`

**Step 1: Add dry-run output format**
Print:
- old row
- new row
- surface path
- write decision

**Step 2: Run one real dry-run**
Suggested command:
```bash
PY=$(awk -F':=' '/^PYTHON[[:space:]]*:=[[:space:]]*/{print $2; exit}' Makefile | xargs)
"$PY" system_v4/probes/maintenance_closure.py \
  --result-json system_v4/probes/a2_state/sim_results/g_structure_tower_results.json \
  --lego-id g_structure_tower \
  --truth-row "g-structure support-manifold anchor" \
  --dry-run
```
Expected: no promotion to `canonical by process`; proposal should stay at `passes local rerun`.

**Step 3: Commit**
```bash
git add system_v4/probes/maintenance_closure.py
git commit -m "feat: add maintenance closure dry-run reporting"
```

### Task 6: Add write mode with fail-closed safeguards

**Objective:** Allow real writes only when explicit targets are supplied.

**Files:**
- Modify: `system_v4/probes/maintenance_closure.py`
- Modify: `system_v4/tests/test_maintenance_closure.py`

**Step 1: Require `--write` for file changes**
No implicit writes.

**Step 2: Require exact row selectors**
Fail if target row not found.

**Step 3: Add tests for safety behavior**
- missing row selector -> fail
- row not found -> fail
- `--dry-run` + `--write` together -> fail

**Step 4: Run tests**
Run:
```bash
PY=$(awk -F':=' '/^PYTHON[[:space:]]*:=[[:space:]]*/{print $2; exit}' Makefile | xargs)
"$PY" -m pytest system_v4/tests/test_maintenance_closure.py -q
```
Expected: PASS.

**Step 5: Commit**
```bash
git add system_v4/probes/maintenance_closure.py system_v4/tests/test_maintenance_closure.py
git commit -m "feat: add fail-closed write mode for maintenance closure"
```

### Task 7: Wire closure into `live_queue_controller.py`

**Objective:** Make the existing controller able to close touched rows instead of stopping at audits.

**Files:**
- Modify: `system_v4/probes/live_queue_controller.py`

**Step 1: Add optional per-step closure metadata**
For each hardcoded packet, allow:
- result path
- truth row label
- backlog row key
- registry row key

**Step 2: After successful packet + passing audits, call `maintenance_closure.py --dry-run` first**
In v1, keep this dry-run-only until one real row is validated.

**Step 3: Run targeted tests or a bounded smoke check**
If no direct controller tests exist, run:
```bash
PY=$(awk -F':=' '/^PYTHON[[:space:]]*:=[[:space:]]*/{print $2; exit}' Makefile | xargs)
"$PY" -m pytest system_v4/tests/test_telegram_bot.py -q
```
Expected: PASS.

**Step 4: Commit**
```bash
git add system_v4/probes/live_queue_controller.py system_v4/probes/maintenance_closure.py
git commit -m "feat: wire maintenance closure dry-run into live queue controller"
```

### Task 8: Consolidate overnight runner behavior around one closure path

**Objective:** Stop overnight scripts from diverging on cleanup and post-run closure semantics.

**Files:**
- Modify: `docs/plans/overnight_8h_run.sh`
- Modify: `system_v5/new docs/plans/run_overnight_8h_controller.sh`

**Step 1: Add cleanup guard to the canonical runner**
`docs/plans/overnight_8h_run.sh` should call `cleanup_first_guard.py` before new sim execution.

**Step 2: Make both scripts call the same closure command path**
Prefer one helper invocation pattern after audits.

**Step 3: Run shell syntax checks**
Run:
```bash
bash -n docs/plans/overnight_8h_run.sh
bash -n "system_v5/new docs/plans/run_overnight_8h_controller.sh"
```
Expected: no syntax errors.

**Step 4: Commit**
```bash
git add docs/plans/overnight_8h_run.sh "system_v5/new docs/plans/run_overnight_8h_controller.sh"
git commit -m "chore: align overnight runners on cleanup and closure flow"
```

### Task 9: Update transport path to reference the closure-capable controller

**Objective:** Keep Telegram transport aligned with the actual controller path.

**Files:**
- Modify: `telegram_bot.py`
- Modify: `system_v4/tests/test_telegram_bot.py`

**Step 1: Preserve existing `handle_live_queue_run(...)` behavior**
Do not redesign command parsing.

**Step 2: Add a small note in the started message if closure mode is enabled**
Only if trivial.

**Step 3: Run tests**
Run:
```bash
PY=$(awk -F':=' '/^PYTHON[[:space:]]*:=[[:space:]]*/{print $2; exit}' Makefile | xargs)
"$PY" -m pytest system_v4/tests/test_telegram_bot.py -q
```
Expected: PASS.

**Step 4: Commit**
```bash
git add telegram_bot.py system_v4/tests/test_telegram_bot.py
git commit -m "test: keep telegram live queue path aligned with closure-capable controller"
```

### Task 10: Promote from dry-run closure to one real write-backed row

**Objective:** Validate one end-to-end control-surface patch in repo reality.

**Files:**
- Modify: `system_v4/probes/maintenance_closure.py`
- Potentially modify one directly stale target row in a live surface via the script

**Step 1: Pick one narrow stale row only**
Good candidate pattern:
- artifact and audits already justify a row-level change
- broader lane summary does not need rewriting

**Step 2: Run real closure command with `--write`**
Then rerun:
```bash
PY=$(awk -F':=' '/^PYTHON[[:space:]]*:=[[:space:]]*/{print $2; exit}' Makefile | xargs)
"$PY" system_v4/probes/probe_truth_audit.py
"$PY" system_v4/probes/controller_alignment_audit.py
```
Expected: both pass after the markdown patch.

**Step 3: Commit**
```bash
git add system_v4/probes/maintenance_closure.py system_v5/new\ docs/plans/sim_truth_audit.md system_v5/new\ docs/plans/sim_backlog_matrix.md system_v5/new\ docs/17_actual_lego_registry.md
git commit -m "feat: close one controller-maintenance row end-to-end"
```

---

## Verification checklist

- [ ] `maintenance_closure.py` exists and is runnable with the Makefile interpreter
- [ ] truth-label derivation is test-covered
- [ ] dry-run mode shows one-row-only proposals
- [ ] write mode is fail-closed
- [ ] `live_queue_controller.py` can invoke closure logic
- [ ] overnight runners share the same cleanup/closure model
- [ ] Telegram path still works
- [ ] fresh `probe_truth_audit.py` passes
- [ ] fresh `controller_alignment_audit.py` passes

---

## Recommended implementation order

1. Tasks 1-6 only
2. validate one real dry-run on a known row
3. only then wire controller and runner surfaces
4. only after one successful real write-backed row consider a thin Hermes class

---

## Why this order

This closes the biggest real automation gap first:
- runs already happen
- audits already happen
- truth/backlog/wiki surfaces already exist
- what is missing is the deterministic row-level closeout layer

That means maintenance closure should be built before a larger controller rewrite.
