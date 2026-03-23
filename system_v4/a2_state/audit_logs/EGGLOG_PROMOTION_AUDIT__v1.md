# EGGLOG PROMOTION AUDIT — v1

> **Date**: 2026-03-22T04:12:10.630285
> **Status**: GENERATED

## Overview
Evaluation of promotion rules across `a2_low_control_graph_v1.json` and `promoted_subgraph.json` using `egglog` equality saturation.

## Saturation Report
```
RunReport { iterations: [IterationReport { rule_set_report: RuleSetReport { changed: true, rule_reports: {"(rule ((__main___node_in _n (__main___Graph_LOW_CONTROL ))\n       (__main___node_in _n (__main___Graph_PROMOTED )))\n      ((__main___confirmed _n))\n         )": [RuleReport { plan: None, search_and_apply_time: 159.333µs, num_matches: 46 }], "(rule ((__main___edge_in _a _b _g))\n      ((__main___connected _a _b))\n         )": [RuleReport { plan: None, search_and_apply_time: 289.458µs, num_matches: 1532 }], "(rule ((__main___degree _n (__main___Graph_LOW_CONTROL ) _d)\n       (>= _d 3))\n      ((__main___qualifies_kernel _n))\n         )": [RuleReport { plan: None, search_and_apply_time: 523.791µs, num_matches: 83 }], "(rule ((__main___edge_in _a _b _g))\n      ((__main___connected _b _a))\n         )": [RuleReport { plan: None, search_and_apply_time: 261.834µs, num_matches: 1532 }], "(rule ((__main___authority _n 'CROSS_VALIDATED')\n       (__main___connected _n _other))\n      ((__main___bridge_eligible _n))\n         )": [RuleReport { plan: None, search_and_apply_time: 83ns, num_matches: 0 }]}, search_and_apply_time: 1.297625ms, merge_time: 734.459µs }, rebuild_time: 322.459µs }, IterationReport { rule_set_report: RuleSetReport { changed: false, rule_reports: {"(rule ((__main___node_in _n (__main___Graph_LOW_CONTROL ))\n       (__main___node_in _n (__main___Graph_PROMOTED )))\n      ((__main___confirmed _n))\n         )": [RuleReport { plan: None, search_and_apply_time: 42ns, num_matches: 0 }, RuleReport { plan: None, search_and_apply_time: 42ns, num_matches: 0 }, RuleReport { plan: None, search_and_apply_time: 41ns, num_matches: 0 }, RuleReport { plan: None, search_and_apply_time: 41ns, num_matches: 0 }], "(rule ((__main___edge_in _a _b _g))\n      ((__main___connected _a _b))\n         )": [RuleReport { plan: None, search_and_apply_time: 41ns, num_matches: 0 }], "(rule ((__main___degree _n (__main___Graph_LOW_CONTROL ) _d)\n       (>= _d 3))\n      ((__main___qualifies_kernel _n))\n         )": [RuleReport { plan: None, search_and_apply_time: 83ns, num_matches: 0 }, RuleReport { plan: None, search_and_apply_time: 41ns, num_matches: 0 }], "(rule ((__main___authority _n 'CROSS_VALIDATED')\n       (__main___connected _n _other))\n      ((__main___bridge_eligible _n))\n         )": [RuleReport { plan: None, search_and_apply_time: 41ns, num_matches: 0 }, RuleReport { plan: None, search_and_apply_time: 41ns, num_matches: 0 }], "(rule ((__main___edge_in _a _b _g))\n      ((__main___connected _b _a))\n         )": [RuleReport { plan: None, search_and_apply_time: 0ns, num_matches: 0 }]}, search_and_apply_time: 2.958µs, merge_time: 244.208µs }, rebuild_time: 0ns }], updated: true, search_and_apply_time_per_rule: {"(rule ((__main___node_in _n (__main___Graph_LOW_CONTROL ))\n       (__main___node_in _n (__main___Graph_PROMOTED )))\n      ((__main___confirmed _n))\n         )": 159.499µs, "(rule ((__main___edge_in _a _b _g))\n      ((__main___connected _a _b))\n         )": 289.499µs, "(rule ((__main___degree _n (__main___Graph_LOW_CONTROL ) _d)\n       (>= _d 3))\n      ((__main___qualifies_kernel _n))\n         )": 523.915µs, "(rule ((__main___authority _n 'CROSS_VALIDATED')\n       (__main___connected _n _other))\n      ((__main___bridge_eligible _n))\n         )": 165ns, "(rule ((__main___edge_in _a _b _g))\n      ((__main___connected _b _a))\n         )": 261.834µs}, num_matches_per_rule: {"(rule ((__main___node_in _n (__main___Graph_LOW_CONTROL ))\n       (__main___node_in _n (__main___Graph_PROMOTED )))\n      ((__main___confirmed _n))\n         )": 46, "(rule ((__main___edge_in _a _b _g))\n      ((__main___connected _a _b))\n         )": 1532, "(rule ((__main___degree _n (__main___Graph_LOW_CONTROL ) _d)\n       (>= _d 3))\n      ((__main___qualifies_kernel _n))\n         )": 83, "(rule ((__main___edge_in _a _b _g))\n      ((__main___connected _b _a))\n         )": 1532, "(rule ((__main___authority _n 'CROSS_VALIDATED')\n       (__main___connected _n _other))\n      ((__main___bridge_eligible _n))\n         )": 0}, search_and_apply_time_per_ruleset: {"": 1.300583ms}, merge_time_per_ruleset: {"": 978.667µs}, rebuild_time_per_ruleset: {"": 322.459µs} }
```

## Discovered Facts
- **Total Qualified for Kernel (degree >= 3 in LOW_CONTROL)**: 83
- **Total Confirmed (in both LOW_CONTROL and PROMOTED)**: 46
- **Total Bridge Eligible (authority CROSS_VALIDATED & connected)**: 0

### Qualified for Kernel (Sample)
- `A2_1::KERNEL::deterministic_dual_replay::1724f48536df4a3d`
- `A2_2::REFINED::a0_budget_and_truncation::4745e5fd4d283ec6`
- `A2_2::REFINED::a0_export_block_compilation::0689ed62233c4265`
- `A2_2::REFINED::a1_anti_classical_leakage::702a223de5c2c206`
- `A2_2::REFINED::a1_strategy_v1_schema::d471f02fe871cb95`
- `A2_2::REFINED::a1_thread_boot_eight_hard_rules::305bb4ebdc28de2b`
- `A2_2::REFINED::a2_canonical_schemas::531d4fa6f8e1bb8f`
- `A2_2::REFINED::a2_controller_dispatch_first::935c20466384198e`
- `A2_2::REFINED::a2_entropy_reduction_mission::befe40027c55382a`
- `A2_2::REFINED::a2_thread_boot_nine_hard_rules::eb81d871409b8f0f`
- `A2_2::REFINED::axes_master_spec_canon::f2cba58ef00962fc`
- `A2_2::REFINED::axis_foundation_companion::6c80c870b389efc1`
- `A2_2::REFINED::base_constraints_ledger_bc01_to_bc12::116c7150b19458fe`
- `A2_2::REFINED::canon_geometry_constraint_manifold::f1ddcf9da0ce2187`
- `A2_2::REFINED::compile_ready_candidate_object::960197abd31777b4`
- `A2_2::REFINED::conformance_fixture_matrix_contract::5c8fd5d491ab0f05`
- `A2_2::REFINED::constraint_ladder_contracts::3e27ccf2fe15f144`
- `A2_2::REFINED::constraint_manifold_formal_derivation::e2a796f27a003a3d`
- `A2_2::REFINED::directed_extraction_answers_zip_and_scale::20e586417906132d`
- `A2_2::REFINED::eight_phase_gate_pipeline::ef4f09488be01e1d`
- ... (and 63 more)

### Confirmed Nodes (Sample)
- `A2_1::KERNEL::deterministic_dual_replay::1724f48536df4a3d`
- `A2_2::REFINED::DETERMINISTIC_KERNEL_PIPELINE::030ebc838121b473`
- `A2_2::REFINED::a0_budget_and_truncation::4745e5fd4d283ec6`
- `A2_2::REFINED::a0_export_block_compilation::0689ed62233c4265`
- `A2_2::REFINED::a1_anti_classical_leakage::702a223de5c2c206`
- `A2_2::REFINED::a1_strategy_v1_schema::d471f02fe871cb95`
- `A2_2::REFINED::a1_thread_boot_eight_hard_rules::305bb4ebdc28de2b`
- `A2_2::REFINED::a2_canonical_schemas::531d4fa6f8e1bb8f`
- `A2_2::REFINED::a2_controller_dispatch_first::935c20466384198e`
- `A2_2::REFINED::a2_entropy_reduction_mission::befe40027c55382a`
- `A2_2::REFINED::a2_thread_boot_nine_hard_rules::eb81d871409b8f0f`
- `A2_2::REFINED::axes_master_spec_canon::f2cba58ef00962fc`
- `A2_2::REFINED::axis_foundation_companion::6c80c870b389efc1`
- `A2_2::REFINED::base_constraints_ledger_bc01_to_bc12::116c7150b19458fe`
- `A2_2::REFINED::canon_geometry_constraint_manifold::f1ddcf9da0ce2187`
- `A2_2::REFINED::compile_ready_candidate_object::960197abd31777b4`
- `A2_2::REFINED::conformance_fixture_matrix_contract::5c8fd5d491ab0f05`
- `A2_2::REFINED::constraint_ladder_contracts::3e27ccf2fe15f144`
- `A2_2::REFINED::constraint_manifold_formal_derivation::e2a796f27a003a3d`
- `A2_2::REFINED::content_redundancy_lint::0bb2761bf47387ae`
- ... (and 26 more)

### Bridge Eligible Nodes (Sample)

