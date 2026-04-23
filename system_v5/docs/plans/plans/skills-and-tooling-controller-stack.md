# Skills and Tooling Controller Stack

Goal: define which parts of the overall sim-build program should live in Hermes skills, which should live in runtime code/validators/maintenance surfaces, and where external reference repos are immediately useful.

## Current live surfaces checked
- Hermes built-in skill: `claude-code`
- Hermes built-in skill: `codex`
- Local repo: `/Users/joshuaeisenhart/Desktop/codex-autoresearch`
- Local repo: `/Users/joshuaeisenhart/GitHub/hermes-agent-self-evolution`

## Core split

### A. Skills are relevant for controller/process behavior
Use skills for:
- bounded Claude Code orchestration
- bounded Codex CLI orchestration
- lane-separated batch control
- truth-audit workflow
- wiki ingest + lego-ledger upkeep
- recurring maintenance loops
- parallel workstream routing with one controller truth surface

### B. Skills are not the tool integration itself
Deep PyTorch / graph / proof / topology integration must live in:
- sim code
- result manifests
- validators
- truth audits
- recurring maintenance docs/checklists
- actual reruns and result files

So skills are the controller layer around the real integration work, not a substitute for it.

## External repo classification

### 1. `hermes-agent-self-evolution`
Status now:
- `reference_only`
- `method_mine`

Useful now for:
- improving Hermes skills
- improving Hermes prompts/tool descriptions
- designing evaluation loops for controller quality

Not useful yet for:
- direct runtime integration into Codex Ratchet
- overriding repo-local process authority
- replacing bounded local skill design

### 2. `lev.here.now/constraints/` + `lev-os/leviathan`
Status now:
- `reference_only`
- `method_mine`
- `parallel-project constraint source`

Useful now for:
- mining controller/runtime principles like contract-first, explicit ownership routing, fractal config discipline, and finitude/non-commutation framing
- borrowing health/reporting/runtime-discipline ideas for on-demand Telegram-controlled Hermes runs
- mining graph/runtime architecture ideas from Leviathan without importing its whole stack

Not useful yet for:
- replacing repo-local sim authority
- flattening Leviathan constraints into Codex Ratchet ontology claims
- bypassing the current repo's geometry-first build order and truth-label regime

### 3. `codex-autoresearch`
Status now:
- `active integration target` for workflow ideas
- `method_mine` for modify/verify/decide loops

Useful now for:
- measurable unattended improvement loops
- foreground/background run modes
- artifact/state semantics (`research-results.tsv`, `autoresearch-state.json`)
- keep/discard/refine/pivot loop design
- skill-level acceptance gates and end-to-end smoke testing
- parallel experiment control ideas

Not sufficient by itself for:
- proving geometry/tool integration depth
- replacing repo-local truth labels or process rules

## Immediate skill implications

### Existing Hermes skills worth keeping
- `claude-code`
- `codex`

### Repo-targeted controller skills
Current repo-targeted controller skills now include:
1. `sim-controller-batch`
   - use for any bounded batch touching sims, docs, ledger, and wiki at once
   - role: controller owns queue, truth labels, and scope discipline

2. `wiki-ingest-and-lego-maintenance`
   - use for new docs, changed docs, or material sim-result updates
   - role: keep `16`, `17`, and wiki concept pages synchronized

3. `truth-audit-and-tool-maintenance`
   - use before/after meaningful sim batches
   - role: truth-label audit, stale canonical cleanup, tool-role coverage checks

Remaining likely gap:
4. `bounded-autoresearch-for-maintenance`
   - use for measurable maintenance problems with clear verify/guard gates
   - role: adapt codex-autoresearch patterns without importing its whole worldview

## What to import from `codex-autoresearch`
Import as patterns, not as authority:
- modify -> verify -> decide loop
- one atomic change per iteration
- keep/discard logging
- explicit verify vs guard split
- foreground vs background modes
- resume/state artifacts
- refine/pivot escalation after repeated discards
- end-to-end smoke gates for skill behavior

## What not to import blindly
- any workflow that widens scope beyond the bounded sim lane
- any assumption that one repo-local metric captures the whole problem
- any artifact naming/runtime behavior that conflicts with current repo conventions
- any autonomy boundary that bypasses repo-local truth labels or maintenance surfaces

## Runtime/tooling implications outside skills
Need real repo surfaces for:
- tool integration maintenance matrix
- controller maintenance checklist
- stale result/classification cleanup
- validator coverage for tool-role contracts
- rerun-driven truth audits
- per-lane backlog matrix

## Recommended next sequence
1. Patch/audit Hermes `codex` skill against `codex-autoresearch` ✅
2. Patch/audit Hermes `claude-code` skill against the actual sim-controller needs
3. Create repo-targeted controller/maintenance skills ✅
4. Create the maintenance docs/checklists those skills operate on ✅ partially
5. Add an on-demand Telegram/manual-run controller pattern
6. Only then decide whether to run bounded autoresearch loops for maintenance/integration work

## Bottom line
- `hermes-agent-self-evolution` is useful now as a method mine for improving Hermes skills.
- `codex-autoresearch` is useful now as a more operational pattern source for measured modify/verify/decide loops.
- Skills matter for controller behavior and maintenance discipline.
- Deep PyTorch/graph/proof integration still has to be earned in the sims, manifests, validators, and reruns themselves.
