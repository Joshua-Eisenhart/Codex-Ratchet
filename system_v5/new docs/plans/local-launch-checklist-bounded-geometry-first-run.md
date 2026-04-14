# Local Launch Checklist — Bounded Geometry-First Automated Run

Use this checklist immediately before starting a real automated run.

## Fill these values
- run_duration =
- transport =

## Confirm files to load
- [ ] `new docs/LLM_CONTROLLER_CONTRACT.md`
- [ ] `new docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- [ ] `new docs/EXPLICIT_CONTROLLER_MODEL.md`
- [ ] `new docs/ANOMALOUS_COMPUTER_SCIENCE_TRANSLATION.md`
- [ ] `new docs/16_lego_build_catalog.md`
- [ ] `new docs/17_actual_lego_registry.md`
- [ ] `new docs/plans/sim_backlog_matrix.md`
- [ ] `new docs/plans/sim_truth_audit.md`
- [ ] `new docs/plans/tool_integration_maintenance_matrix.md`
- [ ] `new docs/plans/controller_maintenance_checklist.md`
- [ ] `new docs/plans/corrected-bounded-automation-plan.md`
- [ ] `new docs/plans/launch-ready-claude-worker-orchestration-spec.md`
- [ ] `new docs/plans/launch-ready-automated-run-manifest.md`
- [ ] `new docs/plans/launch-prompt-bounded-geometry-first-automated-run.md`
- [ ] `Makefile`

## Confirm active layer
- [ ] active layer is explicitly chosen from the live queue before launch
- [ ] recommended default = tool-capability foundation / counterpart-forging
- [ ] if a scientific fallback layer is chosen instead, the reason it beat the tool-capability lane is explicit
- [ ] no widening beyond this layer is implicitly queued

## Confirm allowed packet list
- [ ] exact bounded packet list is filled from live authority surfaces before launch
- [ ] if using the recommended default, the list primarily contains tool-capability packets and/or baseline-vs-canonical comparison closures
- [ ] if using the scientific fallback, the list stays bounded to `operator_geometry_compatibility`, `compound_operator_geometry`, or direct maintenance tied to them
- [ ] maintenance-only packets are tied directly to just-finished work

## Confirm forbidden packet classes
- [ ] reopening exhausted local-forging anchors without a named defect
- [ ] Carnot/Szilard broad engine packets
- [ ] extracted Carnot/Szilard lego packets
- [ ] graph/cell/persistence deepeners beyond this active layer
- [ ] bipartite/bridge packets
- [ ] axis packets
- [ ] flux packets
- [ ] broad packet sweeps
- [ ] open-ended autoresearch
- [ ] workers choosing alternate targets

## Confirm worker model
- [ ] Hermes = controller only
- [ ] Claude Code print-mode workers only (`claude -p`)
- [ ] no tmux/interactive swarm assumptions
- [ ] concurrency cap = 3
- [ ] file sets for parallel workers are non-overlapping

## Confirm canonical interpreter
- [ ] `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3`

## Confirm per-packet run pattern
- [ ] `system_v4/probes/cleanup_first_guard.py --context sim`
- [ ] `system_v4/probes/<sim>.py`
- [ ] `system_v4/probes/probe_truth_audit.py`
- [ ] `system_v4/probes/controller_alignment_audit.py`

## Confirm advancement gate
- [ ] all allowed packets must become `canonical by process` or honestly blocked
- [ ] truth/controller audits must be green
- [ ] maintenance must be caught up
- [ ] time remaining is NOT an advancement gate

## Confirm reporting contract
- [ ] first heartbeat only after real worker is confirmed alive
- [ ] heartbeat cadence = every 5 minutes if reporting is active
- [ ] heartbeat includes worker/process truth, not just helper truth

## Final go/no-go
- [ ] If any box above is not checked, do not launch
- [ ] If all boxes are checked, launch from `launch-prompt-bounded-geometry-first-automated-run.md`
