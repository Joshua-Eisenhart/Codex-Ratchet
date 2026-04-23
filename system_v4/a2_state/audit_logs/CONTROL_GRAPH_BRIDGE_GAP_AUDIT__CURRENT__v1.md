# Control Graph Bridge Gap Audit

- generated_utc: `2026-03-21T23:26:53Z`
- status: `ok`
- audit_only: `True`
- do_not_promote: `True`
- authoritative_graph: `system_v4/a2_state/graphs/system_graph_a2_refinery.json`

## Bridge Status
- `SKILL -> KERNEL_CONCEPT`: missing (0 edges)
- `SKILL -> EXECUTION_BLOCK`: missing (0 edges)
- `SKILL -> B_OUTCOME`: missing (0 edges)
- `SKILL -> B_SURVIVOR`: missing (0 edges)
- `SKILL -> SIM_EVIDENCED`: missing (0 edges)
- `B_OUTCOME -> KERNEL_CONCEPT`: missing (0 edges)
- `SIM_EVIDENCED -> KERNEL_CONCEPT`: missing (0 edges)
- `SIM_EVIDENCED -> B_SURVIVOR`: present (67 edges)
- `B_SURVIVOR -> KERNEL_CONCEPT`: weak_signal (1 edges)
- `B_OUTCOME -> EXECUTION_BLOCK`: present (401 edges)

## Recommended Next Actions
- Build a bounded skill-to-kernel bridge audit or projection follow-on before claiming the graph connects skills to the control substrate.
- Build a bounded witness-to-kernel bridge audit so B/SIM evidence can be traced into kernel/control surfaces more honestly.
- Keep the current PyG view read-only until these bridge families are stronger than isolated or absent signals.
- Do not widen training claims until bridge families exist beyond SKILL-to-SKILL and kernel-only relation islands.

## Issues
- none
