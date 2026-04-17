# Launch Prompt — Bounded Geometry-First Automated Run

Use this prompt verbatim as the launch instruction for the next actual automated run.
Replace only the runtime parameter values.

## Runtime parameters to fill
- <RUN_DURATION>
- <TRANSPORT>

## Launch prompt

Run for <RUN_DURATION> from the live queue using the corrected bounded automation contract.

System root:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5

Read first:
1. /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/LLM_CONTROLLER_CONTRACT.md
2. /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/ENFORCEMENT_AND_PROCESS_RULES.md
3. /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/EXPLICIT_CONTROLLER_MODEL.md
4. /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/ANOMALOUS_COMPUTER_SCIENCE_TRANSLATION.md
5. /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/16_lego_build_catalog.md
6. /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/17_actual_lego_registry.md
7. /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/plans/sim_backlog_matrix.md
8. /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/plans/sim_truth_audit.md
9. /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/plans/tool_integration_maintenance_matrix.md
10. /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/plans/controller_maintenance_checklist.md
11. /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/plans/corrected-bounded-automation-plan.md
12. /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/plans/launch-ready-claude-worker-orchestration-spec.md
13. /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/plans/launch-ready-automated-run-manifest.md
14. /Users/joshuaeisenhart/Desktop/Codex Ratchet/Makefile

Transport:
- <TRANSPORT>
- transport changes reporting only, not run logic

Controller contract:
- Hermes is the only controller
- Claude Code workers are bounded print-mode workers only
- no worker chooses its own target
- no worker owns truth or promotion language
- on this machine, use parallel Claude Code print-mode workers only; do not assume tmux or interactive Claude terminal swarms

Hard process rules:
- order is load-bearing
- layer bounds are real
- one worker = one bounded packet
- geometry-first on the constrained side
- tool integration must happen inside the order
- out-of-order or out-of-scope work counts as failure

Active layer for this run:
- <fill from live queue at launch>
- recommended default: tool-capability foundation / counterpart-forging layer
- secondary fallback: successor-hardening / first pairwise-coupling layer

Allowed packet list for this run, in order:
1. <fill exact bounded tool-capability packet list from live authority surfaces>
2. <fill direct baseline-vs-canonical comparison closures if the pair exists>
3. if the tool-capability lane is honestly blocked, `operator_geometry_compatibility`
4. if the tool-capability lane is honestly blocked, `compound_operator_geometry`
5. direct truth-surface patch tied to a just-finished packet
6. direct tool-depth/manifest coherence patch tied to a just-finished packet
7. direct registry/wiki patch tied to a just-finished packet

Already canonical-by-process local anchors that should NOT be reopened unless a process defect is explicitly found:
- nested_torus_geometry
- fiber_loop_law
- base_loop_law
- berry_holonomy
- local_operator_action
- hopf_map_s3_to_s2
- hopf_fiber_equivalence
- hopf_connection_form / transport anchor
- weyl_chirality_pair
- chiral_density_bookkeeping
- pauli_generator_basis / left_right_asymmetry

Forbidden packet classes for this run:
- reopening exhausted local-forging anchors without a named defect
- Carnot/Szilard broad engine packets
- extracted Carnot/Szilard lego packets
- graph/cell/persistence deepeners beyond the active successor-hardening layer
- bipartite/bridge packets
- axis packets
- flux packets
- broad packet sweeps
- open-ended autoresearch
- workers choosing alternate targets because they look useful

Concurrency:
- maximum active workers = 3
- use parallel workers only when file sets do not overlap
- maintenance worker may run only on non-overlapping maintenance surfaces tied to just-finished packets

Worker prompt contract:
Each worker must receive:
1. exact read order
2. exact bounded target lego
3. exact file set allowed to touch
4. exact rerun command using Makefile interpreter
5. exact audit commands
6. allowed claim vocabulary only
7. explicit non-goals / forbidden widening
8. stop rules

Required stop language for all workers:
- if no direct probe exists, report the missing direct packet and stop
- do not substitute a nearby packet unless controller explicitly allows it
- do not promote beyond the bounded claim set

Canonical interpreter:
- /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3

Per-packet run pattern:
- system_v4/probes/cleanup_first_guard.py --context sim
- system_v4/probes/<sim>.py
- system_v4/probes/probe_truth_audit.py
- system_v4/probes/controller_alignment_audit.py

Hermes reconciliation procedure after each worker:
1. reread touched sim file(s) if code changed
2. reread touched result JSON(s)
3. verify rerun command matched assigned bounded target
4. verify probe_truth_audit.py output
5. verify controller_alignment_audit.py output
6. assign truth label
7. patch live surfaces only if evidence clearly justifies it

Worker output alone is never sufficient.

Heartbeat/reporting contract:
- immediate first heartbeat after real worker is confirmed alive
- then every 5 minutes if reporting is active
- include: wall-clock time, active layer, active workers, current packets, last successful result files, health state, closure state
- do not let heartbeat-alive imply work-alive unless real worker state confirms it

Blocked/stop behavior:
- stop a packet immediately if worker changes target, widens into forbidden lanes, produces no result path, repeats the same failed move twice without a new hypothesis, touches forbidden files, or maintenance lags behind by more than one packet
- if blocked, move only to the next allowed packet in the SAME active layer, or stop if the layer cannot progress honestly

Advancement gate:
- do NOT leave the current active layer unless every allowed packet for this run is either canonical by process or honestly blocked with explicit blocker evidence, while truth/controller audits are green and maintenance is caught up
- time remaining is not a gate

Success condition:
- the run is successful only if it stays inside the declared active layer, follows the declared packet order and stop rules, does not substitute nearby useful work for the requested packet order, and only advances when the gate is met

Required launch acknowledgement format:
- run_duration
- transport
- active_layer
- allowed packet list
- forbidden packet classes
- worker model
- concurrency cap
- confirmed real worker/session IDs

Required closeout format:
1. Primary task(s) chosen
2. Exact commands/sims run
3. Files/results changed
4. Truth-label outcomes
5. Tool integration / maintenance findings
6. Blockers
7. Next bounded move
8. Which exact step failed or stopped the run, if any
