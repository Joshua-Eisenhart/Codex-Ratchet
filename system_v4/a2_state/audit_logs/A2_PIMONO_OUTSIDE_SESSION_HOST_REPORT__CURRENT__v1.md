# Pi-mono Outside Session Host Report

- generated_utc: `2026-03-21T12:22:01Z`
- status: `ok`
- cluster_id: `SKILL_CLUSTER::outside-control-shell-session-host`
- first_slice: `outside-control-shell-operator`
- source_family: `pi-mono`
- target_surface_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/reference_repos/other/pi-mono/packages/coding-agent/test/fixtures/large-session.jsonl`
- audit_only: `True`
- observer_only: `True`
- do_not_promote: `True`

## Session Header
- id: `d703a1a9-1b7b-4fb1-b512-c9738b1fe617`
- timestamp: `2025-11-20T23:33:50.805Z`
- cwd: `/Users/badlogic/workspaces/pi-mono`
- provider: `anthropic`
- modelId: `claude-sonnet-4-5`
- thinkingLevel: `off`
- declared_keys: `['cwd', 'id', 'modelId', 'provider', 'thinkingLevel', 'timestamp', 'type']`
- version_present: `False`
- branch_reference_present: `False`

## Entry Counts
- message: `914`
- model_change: `1`
- session: `1`
- thinking_level_change: `103`

## Message Counts
- assistant: `453`
- toolResult: `373`
- user: `88`

## Assistant Stop Reasons
- aborted: `21`
- error: `1`
- stop: `65`
- toolUse: `366`

## Interactive Shell Capability
- rpc_mode_documented: `True`
- get_state_documented: `True`
- steer_documented: `True`
- follow_up_documented: `True`
- interactive_shell_example_present: `True`

## Mom Boundary
- doc_present: `True`
- workspace_layout_documented: `True`
- boundary_only: `True`

## Recommended Next Actions
- Keep the pi-mono slice report-only and read-only until a later host/session operator is justified.
- Treat mom as a workspace-boundary source only; do not treat it as canonical control state.
- Use this report as evidence for later outside-shell planning, not as proof of runtime integration.

## Issues
- none
