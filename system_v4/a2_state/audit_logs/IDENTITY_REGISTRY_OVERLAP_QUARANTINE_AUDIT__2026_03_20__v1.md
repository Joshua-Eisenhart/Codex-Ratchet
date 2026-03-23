# IDENTITY_REGISTRY_OVERLAP_QUARANTINE_AUDIT__2026_03_20__v1

generated_utc: 2026-03-20T20:49:27Z
owner_path: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/identity_registry_v1.json
owner_before_node_count: 13481
owner_before_edge_count: 95106
owner_after_edge_count: 0
quarantined_edge_count: 95106
affected_node_count: 7392

## Quarantine Rule
- All current `IDENTITY_OVERLAP` edges are treated as lexical suggestion edges, not canonical identity facts.
- The identity owner surface keeps nodes but drops heuristic overlap edges.
- Quarantined edges move into `identity_registry_overlap_suggestions_v1.json` as a non-canonical suggestion surface.

## Top Shared Token Patterns
- 3276: ['family', 'note', 'slice', 'update']
- 2815: ['dispatch', 'packet', 'worker']
- 2095: ['bearing', 'extract', 'source']
- 1946: ['note', 'promotion', 'selective']
- 1535: ['entropy', 'high', 'intake']
- 1129: ['handoff', 'launch', 'worker']
- 986: ['note', 'promotion', 'selective', 'trio']
- 963: ['extract', 'plan', 'upgrade']
- 954: ['backup', 'doc', 'index']
- 837: ['controller', 'handoff', 'launch']

## Non-Claims
- This pass does not infer a smaller semantic subset of overlap edges as canonical identity facts.
- This pass does not redesign the identity registry builder.
- This pass does not claim the quarantined suggestion surface is authoritative.
