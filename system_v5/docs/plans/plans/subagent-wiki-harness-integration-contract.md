# Subagent + Wiki Harness Integration Contract

Status: DRAFT CONTROL CONTRACT
Date: 2026-04-20
Purpose: make the new multi-part process explicit so Hermes can use bounded workers, voice-lens audits, the wiki harness, and the repo control surfaces together without collapsing them into one blurry run story.

## 1. What this contract is for
This contract covers the missing `M-05` surface in `system_v5/docs/plans/lanes.md`:
- subagents
- worker models
- voice/lens audits
- wiki harness coordination
- controller reconciliation
- process smoke tests

This is a control-plane contract.
It does not admit new sim stages.
It does not replace the hard build order.

## 2. Checked live machine facts
- canonical interpreter: `~/.local/share/codex-ratchet/envs/main/bin/python3`
- `claude` present: `/usr/local/bin/claude` (`2.1.112`)
- `codex` present: `/usr/local/bin/codex` (`0.118.0`)
- `tmux` absent
- `mngr` absent
- `omc` absent
- `omx` absent
- logical CPU count: `10`

Checked Claude CLI capability fact:
- `claude auth status --text` reports an authenticated Claude CLI session

These facts mean:
- Hermes can use bounded CLI workers directly
- Hermes cannot honestly assume a tmux-managed swarm/manager layer on this machine
- direct Hermes-tracked process ownership is the current default

## 3. Keep these process surfaces separate

### A. Build-stage sim lanes
- `T`, `TI`, `C`, `NC`, `B`, `S`
- these track sim-stage work only
- they do not absorb controller/harness debt

### B. Maintenance overlay
- `M-01` truth / integrity verification
- `M-02` hygiene / repository maintenance
- `M-03` controller / harness contract governance
- `M-04` runtime / CLI worker prerequisites
- `M-05` subagent + wiki harness integration
- `M` is orthogonal to the build-stage lanes and never authorizes stage promotion

### C. Execution surface
- Hermes = controller
- bounded CLI workers = execution helpers
- worker choice does not itself change lane status or truth labels

### D. Wiki-builder surface
- separate from the sim runner
- tranche-based
- may use bounded independent workers only for non-overlapping concept clusters

### E. Shared reconciliation surface
These stay Hermes-owned unless a single-worker pass is explicitly bounded that way:
- `~/wiki/index.md`
- `~/wiki/log.md`
- `~/wiki/concepts/topic-map.md`
- `~/wiki/concepts/current-research-overlays.md`
- repo lane/status/control surfaces that summarize multiple packets

### F. Low-entropy routing surface
- `hermes-current/` remains the front door for current frame, provenance, intentions, and authority routing
- it is a routing/control spine, not proof of repo state by itself

### G. Skill/procedure surface
- skills help with orchestration, read order, maintenance, and bounded workflows
- skills are not the deep proof/graph/torch/topology integration itself

## 4. Controller / worker split

### Hermes owns
- lane selection
- tranche selection
- worker launch approval
- file/result isolation checks
- truth labels
- status reporting
- closeout wording
- shared-surface reconciliation
- refusal when a worker packet widens scope

### Workers own
- one bounded packet only
- one local file/result scope only
- one declared question only

Workers do not own:
- promotion language
- final lane status
- shared routing/log surfaces
- changing the active layer by narrative substitution

## 5. Two worker families

### Family 1: Functional workers
Use for real bounded work packets.
Examples:
- one tool-capability packet
- one tool-integration packet
- one maintenance packet tied to a just-finished packet
- one wiki concept-cluster pass

### Family 2: Voice-lens audit workers
Use to preserve plurality and catch collapse.
These do not execute the packet. They audit the packet/process from distinct reasoning stances.

Current useful lenses:
- `🦉 Hume` — speak from what is observed, checked, or directly supported; keep inference conditional; prefer particulars, ordinary language, and nominalist clarity over abstraction and system-jargon drift
- `🧨 Popper` — likely failure modes and falsifier tests
- `🦋 Zhuangzi` — distinct live packetizations that should not be collapsed

Voice-lens workers are for:
- process design review
- packet selection review
- post-run diagnosis
- status-surface pressure tests

Voice-lens workers are not for:
- choosing targets alone
- patching repo files by default
- overwriting Hermes reconciliation

## 6. Packet schema for all worker types
Every worker packet should declare:
- surface: `build | maintenance | execution | wiki | lens-audit`
- packet id / lane id
- exact goal
- exact read order
- exact allowed file set
- exact forbidden widening
- exact verification step
- exact stop rule
- who reconciles the output

If a proposed packet cannot fill those fields, it is not ready.

## 7. When to use voice-lens workers
Run lens workers when one of these is true:
- the user explicitly asks for multiple readings
- the process “works sometimes and not others” and the failure is likely control-plane, not single-packet-local
- a summary is collapsing build-stage, maintenance, worker, and wiki realities into one story
- Hermes is about to change a control surface that affects multiple lanes

Default lens-audit bundle for process questions:
1. `🦉 Hume` audit
2. `🧨 Popper` audit
3. `🦋 Zhuangzi` audit
4. Hermes synthesis

Reporting rule:
- if Hermes says multiple lanes or lenses ran, the reply should say which ones actually ran
- if some were only proposed or implied, say that plainly
- do not present a proposed lane/lens bundle as if it already executed
- if subagents ran, report each one in plain English with: actual work done, files changed or `none`, and the concrete result or evidence path
- in user-facing summaries, prefer ordinary language first and internal lane codes second
- use nominalist claim language: `supports`, `does not yet support`, `survived this test`, `blocked by`; avoid inflated closure words unless the stronger label was actually earned

## 8. Current admitted worker model

### Default admitted now
- Hermes controller
- bounded non-overlapping CLI workers
- Claude print-mode = fully specified default contract
- Codex CLI = installed and usable, but not yet launch-ready parity with Claude

Checked utilization receipt:
- `system_v5/docs/plans/plans/claude-worker-utilization-receipt.md`
- direct `claude -p` print-mode workers are the proved Claude execution path right now
- Claude-routed `delegate_task` ACP remains ambiguous and is not yet treated as the proved primary Claude path
- `system_v5/docs/plans/plans/gemini-worker-utilization-receipt.md`
- Gemini CLI headless `-p` + `--approval-mode plan` is also proved for a 3-worker read-only smoke, but remains supportive/overflow rather than primary

### Not admitted by default now
- tmux-managed swarms
- `mngr`/`omc`/`omx` managed worker layers
- open-ended worker prompts
- workers choosing their own targets from the repo

## 9. Wiki harness interaction rule
When a task touches the wiki harness:
1. read the Hermes spine first
2. classify whether the task is:
   - repo build/control work
   - wiki builder work
   - a bridge between them
3. keep concept-local edits separate from shared-route reconciliation
4. let Hermes reconcile shared wiki surfaces after worker completion
5. do not let wiki maintenance become fake proof of repo state

## 10. Reconciliation rule
After any worker or lens batch, Hermes should reconcile in this order:
1. reread touched local files/results
2. verify isolation held
3. verify the bounded question was actually answered
4. update the appropriate local truth surface
5. only then patch shared status/routing surfaces
6. if different lenses still disagree, preserve the split explicitly instead of smoothing it away

## 11. Process smoke tests
These are the minimum useful tests for the new process itself.

### Checked already
1. lane-claim smoke
- `scripts/claim_lane.py claim <lane_id> <owner>` / release path works on the live lanes file

2. worker prerequisite smoke
- `claude` and `codex` present
- manager/swarm tools absent
- direct CLI worker model is the honest default

3. voice-lens audit smoke
- `🦉 Hume`, `🧨 Popper`, and `🦋 Zhuangzi` audits can run in parallel on the same process question and return distinct useful outputs

4. direct Claude worker smoke
- initial 3 parallel direct `claude -p` workers succeeded
- tuned launcher probes then succeeded at `4/4`, `6/6`, `8/8`, and `10/10` for bounded read-only extraction tasks
- 1 direct `claude -p` Opus `max` synthesis worker succeeded
- see `system_v5/docs/plans/plans/claude-worker-utilization-receipt.md`

5. direct Gemini worker smoke
- `gemini -p` headless mode works in this environment
- 3 parallel Gemini read-only workers succeeded under `--approval-mode plan`
- see `system_v5/docs/plans/plans/gemini-worker-utilization-receipt.md`

### Next process falsifier tests
6. live-surface selector test
- verify the controller actually chooses work from the declared live control surfaces rather than only from fallback batch rotation

7. closure writeback test
- verify maintenance closure targets the live `system_v5/docs/plans/plans/...` surfaces rather than stale paths

8. heartbeat truth test
- verify run reporting tracks a real worker/process state rather than only a launched controller pid

9. worker parity test
- verify Codex has an explicit bounded-launch contract parallel to the Claude launch-ready contract

10. wiki shared-surface isolation test
- verify concept-local worker edits and Hermes shared-surface reconciliation stay separated

11. Claude scaling test
- now that `10/10` direct Claude read-only packets succeeded, the next falsifier is not raw scale but whether the same success holds for write-producing or mixed maintenance packets without losing Hermes reread/reconciliation discipline

## 12. Stop rules
Stop and report instead of widening if:
- a worker needs overlapping files with another live worker
- a lens audit is being treated as execution proof
- a wiki worker is about to edit shared routing surfaces without explicit assignment
- a functional worker proposes a nearby packet instead of the assigned one
- a control-surface summary would hide unresolved differences between build, maintenance, execution, and wiki surfaces

## 13. Success condition for M-05
`M-05` is not “done” because the contract file exists.
`M-05` is working when:
1. the contract exists
2. the default worker model matches live machine facts
3. one bounded functional worker packet can be launched and reconciled under this contract
4. one bounded lens-audit batch can be launched and reconciled under this contract
5. one wiki concept-cluster pass can run under the non-overlap + Hermes-reconciliation rule
6. the resulting closeout stays readable and does not collapse the surfaces into one story

## 13A. Claude-first utilization policy

If multiple Claude workers are available:
- default to `sonnet` with `xhigh` or `high` for most bounded packet workers
- reserve one `opus` / `opus-4-7` `max` worker for the hardest packet, synthesis, or arbitration

If only one Claude worker is effectively available:
- use `opus` / `opus-4-7` `max` on the hardest/highest-leverage packet

GPT-5.4 usage for now:
- keep available as overflow/supportive capacity
- use for secondary falsifier audits, controller summarization, or non-primary side work
- but maximize Claude first

Scaling rule:
- direct `claude -p` read-only probes are now proved at `3`, `4`, `6`, `8`, and `10` parallel workers on this machine
- `10` is now a proved operating cap for this safer read-only extraction packet family
- this still does not automatically prove `10` as the right default for write-producing or mixed maintenance packets
- for file-read + structured-output extraction tasks, prefer `--max-turns 5` over `3`; the first 4-way failure was `error_max_turns`, not a proved rate cap

## 14. Non-goals
This contract does not:
- authorize later sim stages
- fix truth/hygiene/controller blockers by itself
- replace the hard build guardrail
- make the wiki builder and sim runner the same lane
- treat lens output as promotion evidence

## 15. One-sentence summary
Use Hermes as the single controller over distinct build, maintenance, execution, wiki, and lens-audit surfaces; allow bounded non-overlapping workers inside those surfaces; reconcile only at explicit Hermes-owned joins so the process can be integrated and tested without collapsing into one misleading story.
