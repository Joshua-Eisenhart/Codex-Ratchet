# Launch-Ready Claude Worker Orchestration Spec

Status: PRE-LAUNCH WORKER ORCHESTRATION SPEC

Purpose: make the worker layer explicit so a future automated run can use Claude Code in parallel without drifting, widening, or violating process order.

## 1. Worker architecture

Controller:
- Hermes only
- owns queue, order discipline, truth labels, health reporting, and maintenance closure

Workers:
- Claude Code CLI workers in print mode (`claude -p`)
- bounded one-packet workers only
- no worker owns truth or promotion language

Current machine constraint:
- `claude` CLI is available
- `tmux` is not available
- therefore the runnable worker model on this machine is:
  - parallel bounded Claude Code print-mode workers
  - NOT interactive tmux-managed Claude terminal swarms

## 2. Worker model to actually use

Approved mode:
- `claude -p ... --model sonnet --effort high --allowedTools "Read,Write,Edit,Bash" --max-turns <bounded>`

Why:
- clean bounded execution
- reproducible
- easy to monitor
- no interactive prompt handling
- compatible with this machine

Disallowed as default launch model:
- open interactive Claude sessions
- freeform long-lived Claude REPLs
- worker prompts that say "figure out what to do"
- tmux orchestration on this machine unless tmux is explicitly installed first

## 3. Concurrency cap

Default max active workers: derive from live machine facts and file isolation, not from a stale fixed number.

Reason:
- the right cap depends on CPU count, worker mode, and whether packets are maintenance-heavy or isolated tool-capability packets
- Hermes still has to reread artifacts and own truth labels afterward
- overlap and truth-surface drift remain the real limiting factors, not just a static worker count

Current machine rule:
- on this 10-core machine with print-mode-only Claude workers and no tmux, tool-capability waves may scale up to 8 top-level workers if file sets, result files, and maintenance surfaces remain non-overlapping
- use a lower cap whenever Hermes cannot still reread every touched artifact/doc before any promotion claim

## 4. Worker packet granularity

Each Claude worker gets exactly one of:
- one lego packet
- one direct successor hardening pass for one lego
- one connection test between two already-earned legos
- one maintenance packet tied to the just-completed bounded packet

Never assign to one worker:
- a whole layer
- a whole wave
- multiple loosely-related legos
- a broad theory question
- a packet plus its next-layer successor

## 5. Active-layer rule

For the next automated run, the active layer should default to:
- tool-capability foundation / counterpart-forging layer

This means allowed targets are bounded per-tool capability packets, bounded tool-native counterpart packets, and bounded baseline-vs-canonical comparison closures.
Do not automatically widen into:
- already-canonical local-forging anchors
- Carnot/Szilard broad engine lane
- bridge / axis / flux
- broad graph/bipartite side packets unless they are the direct bounded tool-capability target of the active wave

## 6. Allowed packet list for the next launch

Controller may launch workers only from this list, in order:

Primary tool-capability packet classes:
1. one bounded z3 / cvc5 / sympy capability packet
2. one bounded rustworkx / PyG / XGI capability packet
3. one bounded TopoNetX / GUDHI capability packet
4. one bounded clifford / e3nn / geomstats capability packet
5. one direct baseline-vs-canonical comparison-note packet when the pair already exists

Secondary scientific fallback packets:
6. `operator_geometry_compatibility`
7. `compound_operator_geometry`

Allowed maintenance packets:
8. direct truth-surface patch tied to a just-finished packet
9. direct tool-depth/manifest coherence patch tied to a just-finished packet
10. direct registry/wiki patch tied to a just-finished packet

Interpretation rule:
- the examples above are seed packet classes, not an exhaustive whitelist of only those exact filenames
- the controller may choose adjacent bounded packets from the same tool-capability lane if they better satisfy the same process goal and keep scope tight

Not allowed in this next launch unless manually overridden:
- reopening `nested_torus_geometry`, `fiber_loop_law`, `base_loop_law`, `berry_holonomy`, or `local_operator_action` just because they used to be on the launch list
- Carnot/Szilard full-engine packets
- extracted Carnot/Szilard legos
- graph/cell/persistence deepeners beyond the active layer's current purpose
- bipartite/bridge work
- axis work
- flux work

## 7. Forbidden packet classes

Forbidden by default for the next automated run:
- anything outside the declared active layer for that launch
- any packet whose claim scope depends on bridge objects
- any packet that bundles multiple chain links at once
- any packet that reopens already-canonical rows without a stated process reason
- any worker prompt that permits choosing its own target from the repo

## 8. Worker prompt contract

Every worker prompt must contain, in order:
1. exact read order
2. exact bounded target lego
3. exact file set the worker may touch
4. exact rerun command using Makefile interpreter
5. exact audit commands
6. allowed claim vocabulary
7. explicit non-goals / forbidden widening
8. stop rules

Required wording:
- if no direct probe exists, report the missing direct packet and stop
- do not substitute a nearby useful packet without saying it is only a nearby anchor
- do not promote beyond the bounded claim set

## 9. File-set isolation rule

Workers may run in parallel only when:
- sim file sets do not overlap
- result files do not overlap
- maintenance/doc patches are not touching the same file

Examples of valid parallel split:
- Worker A: one tool-capability packet on a proof/symbolic file set
- Worker B: one tool-capability packet on a graph/topology file set
- Worker C: maintenance-only once one of A/B lands

Examples of invalid split:
- two workers editing `sim_truth_audit.md`
- one worker changing a sim while another claims its truth outcome
- one worker on a packet and another on the same packet's maintenance row simultaneously

## 10. Hermes reconciliation procedure

After every worker exits:
1. Hermes rereads the touched sim file(s) if code changed
2. Hermes rereads the touched result JSON(s)
3. Hermes verifies the rerun command actually matches the bounded target
4. Hermes verifies `probe_truth_audit.py` result
5. Hermes verifies `controller_alignment_audit.py` result
6. Hermes alone decides the truth label
7. Only then may Hermes patch live truth/control surfaces

Worker output alone is never sufficient.

## 11. Stop rules

Hermes must stop the packet immediately if:
- worker chooses a different target than assigned
- worker widens into side lanes
- worker does not produce a result path
- worker repeats the same failed move twice without a new hypothesis
- worker touches forbidden files
- maintenance falls behind the just-completed packet by more than one packet

## 12. Advancement gate

Hermes may leave the current active layer only if:
- every packet in the declared allowed list is either
  - `canonical by process`, or
  - honestly blocked with explicit blocker evidence
- truth/controller audits are still green
- maintenance surfaces are caught up

Time remaining is not a gate.

## 13. Launch template for the next automated run

Worker orchestration at launch should explicitly say:
- active layer: tool-capability foundation / counterpart-forging OR successor-hardening / first pairwise-coupling
- worker model: bounded Claude Code print-mode workers
- concurrency cap: machine-grounded and file-isolation-grounded
- allowed packet list: exact list from section 6
- forbidden classes: section 7
- advancement gate: section 12
- duration: passed separately as a runtime parameter, not encoded in the plan or worker names

## 14. Success condition

The Claude-worker layer is working correctly only if:
- workers stay on assigned packets
- no side-lane widening occurs
- Hermes can audit every worker output directly
- order remains intact
- the run exits because the active layer is complete, blocked, or time budget expires — not because the controller improvised elsewhere
