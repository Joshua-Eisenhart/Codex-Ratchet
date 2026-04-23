# A1_CARTRIDGE_GRAPH_AUDIT__2026_03_20__v1

generated_utc: 2026-03-20T10:18:59Z
build_status: FAIL_CLOSED
materialized: False
node_count: 0
edge_count: 0

## Included Terms
- none

## Blocked Terms
- none

## Selection Contract
- included_node_rule: Include only materialized A1_STRIPPED nodes whose exact stripped term is currently treated by cartridge doctrine as packageable fuel rather than witness-only or deferred.
- edge_rule: Materialize only PACKAGED_FROM edges from A1_CARTRIDGE to A1_STRIPPED. Do not promote COMPILED_FROM or infer internal strategy/dependency topology.
- exact_term_gate: family-level cartridge PASS is insufficient; the exact stripped term must pass

## Non-Claims
- This pass does not promote family-level cartridge PASS into exact-term packageability.
- This pass does not materialize internal cartridge strategy edges.
- This pass does not promote downstream A0 COMPILED_FROM edges into cartridge-owner doctrine.
