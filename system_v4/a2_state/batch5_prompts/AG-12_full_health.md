# AG-12: Full System Health Report

## Task
Run full system health:
1. `python3 system_v4/probes/run_all_sims.py`
2. `python3 system_v4/skills/probe_graph_materializer.py`
3. `python3 system_v4/skills/evidence_witness_bridge.py`
4. `python3 system_v4/skills/intent-compiler/heartbeat_daemon.py --no-codex`

Write: `system_v4/a2_state/audit_logs/A2_FULL_SYSTEM_HEALTH__v1.md` with: token inventory, KILL analysis, graph stats, workstream status, constraint coverage.
