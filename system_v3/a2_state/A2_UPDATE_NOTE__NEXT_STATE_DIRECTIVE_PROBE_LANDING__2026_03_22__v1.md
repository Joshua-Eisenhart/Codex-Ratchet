# A2 Update Note — Next-State Directive Probe Landing

Date: 2026-03-22
Surface class: `DERIVED_A2`
Status: active maintenance note

Source-bound basis:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.md`

Bounded update:
- `SKILL_CLUSTER::next-state-signal-adaptation` now has a second bounded landed slice:
  - `a2-next-state-directive-signal-probe-operator`
- current graph / registry truth is:
  - `113` active registry skills
  - `113` graphed `SKILL` nodes
  - `0` missing
  - `0` stale
- current bounded probe result is:
  - `attention_required`
  - witness corpus entries are still intent/context-heavy
  - no real post-action next-state candidates are currently recorded
- current next step is:
  - `record_real_post_action_witnesses_first`

Controller consequence:
- keep this lane audit-only / nonoperative / non-runtime-live
- do not widen it into improver-context or live-learning claims yet
- preserve the result as a real lane insight: the blocker is witness quality, not missing source-family mapping
