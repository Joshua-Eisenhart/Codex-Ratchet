# Launch-Ready Automated Run Manifest

Status: READY-TO-FILL MANIFEST TEMPLATE FOR THE NEXT ACTUAL AUTOMATED RUN

Use this file as the final pre-launch contract. It combines:
- corrected bounded automation rules
- Claude worker orchestration rules
- live controller maintenance rules

Important:
- duration is a runtime parameter only
- duration must never be encoded into the run name or treated as a scope-expansion license

## 1. Runtime parameter block

- run_duration: <set at launch>
- transport: <local | telegram | other>
- transport affects reporting only, not logic
- active_layer: <must be filled before launch>
- advancement_gate: <must be filled before launch>

## 2. Controller contract

Controller:
- Hermes only
- Hermes owns:
  - order discipline
  - queue discipline
  - truth labels
  - health reporting
  - maintenance closure

Workers:
- bounded Claude Code print-mode workers (`claude -p`)
- no worker chooses its own target
- no worker owns truth or promotion language

Current machine constraint:
- `claude` available
- `tmux` unavailable
- approved worker model = parallel bounded Claude print-mode workers only

## 3. Hard process rules

1. Order is load-bearing.
2. Layer bounds are real.
3. One worker = one bounded packet.
4. Geometry-first on the constrained side.
5. Tool integration must happen inside the order.
6. Out-of-order or out-of-scope work counts as failure.

## 4. Active layer for the next automated run

Declared active layer:
- fill explicitly before launch from the live queue

Recommended default for the next relaunch:
- tool-capability foundation / counterpart-forging layer

Secondary fallback layer:
- successor-hardening / first pairwise-coupling layer

Meaning:
- stay inside bounded per-tool capability probes, bounded tool-native counterpart packets, or bounded baseline-vs-canonical comparison closures when the default tool-capability layer is chosen
- do not reopen already-canonical local-forging anchors during this run unless a concrete process defect is named before launch
- do not widen into later layers during this run unless the explicit advancement gate is met

## 5. Allowed packet list for the next run

Controller may choose only from the following packet classes, in this order:

Primary packet classes for the recommended relaunch:
1. one bounded z3 / cvc5 / sympy capability packet
2. one bounded rustworkx / PyG / XGI capability packet
3. one bounded TopoNetX / GUDHI capability packet
4. one bounded clifford / e3nn / geomstats capability packet
5. one bounded baseline-vs-canonical comparison packet when the pair already exists

Secondary scientific fallback packets:
6. `operator_geometry_compatibility`
7. `compound_operator_geometry`

Allowed maintenance-only packets:
8. direct truth-surface patch tied to just-finished packet
9. direct tool-depth/manifest coherence patch tied to just-finished packet
10. direct registry/wiki patch tied to just-finished packet

Notes:
- `nested_torus_geometry`, `fiber_loop_law`, `base_loop_law`, `berry_holonomy`, and `local_operator_action` are already process-canonical local anchors for the exhausted prior launch slice and should not be reopened in this run unless a process-specific defect is explicitly named before launch.
- `hopf_map_s3_to_s2`, `hopf_fiber_equivalence`, `hopf_connection_form`, `weyl_chirality_pair`, and `chiral_density_bookkeeping` are also already process-canonical local anchors and should remain closed unless a direct defect is named.
- if a packet in this list lacks a direct probe, the worker must report that and stop; no substitution without explicit controller approval.
- the packet classes above are illustrative seed classes, not an exhaustive claim that only those exact examples are valid; the launch controller must still derive the exact bounded packet list from the full live queue, registry, and tool-capability surfaces.

## 6. Forbidden packet classes for this run

Forbidden by default:
- reopening exhausted local-forging anchors without a named defect
- Carnot/Szilard broad engine packets
- extracted Carnot/Szilard lego packets
- graph/cell/persistence deepeners beyond this active layer
- bipartite/bridge packets
- axis packets
- flux packets
- broad packet sweeps
- open-ended autoresearch
- workers choosing alternate targets because they look useful

## 7. Concurrency rule

Default max active workers: set from live machine facts and file isolation at launch.

Current machine guidance:
- if the next relaunch uses print-mode-only Claude workers on this 10-core machine and file sets remain non-overlapping, the cap may be raised above 3 for isolated tool-capability waves
- use a lower cap whenever Hermes cannot still audit every touched artifact/doc directly

Valid split examples:
- Worker A: one tool-capability packet on a proof/symbolic file set
- Worker B: one tool-capability packet on a graph/topology file set
- Worker C: maintenance-only after A or B lands

Invalid split examples:
- two workers touching the same truth surface at once
- one worker changing a sim while another claims truth outcomes from it
- one worker on a packet and another on that packet's maintenance row simultaneously

## 8. Worker prompt contract

Every worker prompt must include:
1. exact read order
2. exact bounded target
3. exact file set allowed to touch
4. exact rerun command using Makefile interpreter
5. exact audit commands
6. allowed claim vocabulary only
7. explicit non-goals / forbidden widening
8. stop rules

Required stop language:
- if no direct probe exists, report the missing direct packet and stop
- do not substitute a nearby packet unless controller explicitly allowed it
- do not promote beyond the bounded claim set

## 9. Exact rerun/audit commands

Canonical interpreter:
- `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3`

Per-packet run pattern:
- `system_v4/probes/cleanup_first_guard.py --context sim`
- `system_v4/probes/<sim>.py`
- `system_v4/probes/probe_truth_audit.py`
- `system_v4/probes/controller_alignment_audit.py`

## 10. Hermes reconciliation procedure

After each worker exits, Hermes must:
1. reread touched sim file(s) if code changed
2. reread touched result JSON(s)
3. verify the rerun command matched the assigned bounded target
4. verify `probe_truth_audit.py` output
5. verify `controller_alignment_audit.py` output
6. assign truth label
7. patch live surfaces only if evidence clearly justifies it

Worker output alone is never sufficient.

## 11. Heartbeat / reporting contract

Heartbeat payload must include:
- wall-clock time
- active layer
- currently active workers
- current packets
- last successful result file(s)
- health state: healthy / blocked / degraded
- whether maintenance closure is caught up or lagging

Default cadence:
- immediate first heartbeat after real worker is confirmed alive
- then every 5 minutes if transport/reporting is active

Truth rule:
- do not let heartbeat-alive imply work-alive unless real worker/process check confirms it

## 12. Blocked / stop behavior

Hermes must stop a packet immediately if:
- worker changes target
- worker widens into forbidden lanes
- worker produces no result path
- worker repeats the same failed move twice without a new hypothesis
- worker touches forbidden files
- maintenance lags behind by more than one packet

If a packet blocks:
- record explicit blocker
- either move to the next allowed packet in the SAME active layer
- or stop the run if the layer cannot progress honestly

## 13. Advancement gate

Hermes may leave the current active layer only if:
- every allowed packet for this run is either:
  - `canonical by process`, or
  - honestly blocked with explicit blocker evidence
- truth/controller audits are green
- maintenance surfaces are caught up

Time remaining is not an advancement reason.

## 14. Success condition for the run

The run is successful only if:
- it stays inside the declared active layer
- it follows the declared packet order and stop rules
- it does not substitute nearby useful work for requested packet order
- every promoted claim is tied to rerun + truth audit + controller audit
- transport never changes logic
- advancement only happens because the gate was met, not because time remained

## 15. Fill-before-launch section

Before the next actual automated launch, fill these exact values:
- run_duration = <value>
- transport = <value>
- active_layer = <fill from live queue; recommended default = tool-capability foundation / counterpart-forging>
- allowed_packets = <fill exact bounded packet list at launch; use the tool-capability lane by default and successor-hardening only as fallback>
- forbidden_packets = [reopening exhausted local-forging anchors without named defect, Carnot/Szilard packets, bridge/axis/flux, broad sweeps, open-ended autoresearch, and any packet outside the declared active layer]
- advancement_gate = all allowed packets canonical-by-process or honestly blocked, with audits green and maintenance caught up
- concurrency_cap = <fill from live machine facts and file-set isolation>
