# ConstraintBox gate index

This document indexes 139 gate records from the ConstraintBox source inventory. It separates declarations, production call paths, controls, tools, and status. `exists` means source evidence only.

## Inventory summary

Lane 1 counted 139 gates, 119 invoked rows, 20 not-invoked rows, and 55 rows with negative controls. Its kind counts are proposal_reason_code 44, construction_invariant 30, runtime_invariant 30, module_gate_candidate 20, gate_operations 11, and contract_identifier 4. The source command `rg -o 'cb:[a-z0-9-]+' constraint_box/src/constraintbox/gate_operations.py | sort -u` returned 11 executable IDs.

## Complete gate table

| gate_id | defined_at | kind | what it checks | invoked from | core tool | negative control | ladder status |
|---|---|---|---|---|---|---|---|
| cb:z3-request-gate | constraint_box/src/constraintbox/gate_operations.py:56 | gate_operations | finite constraint via dual_solve z3 result | NOT_INVOKED (rg found no production call site) | z3 | yes | exists |
| cb:cvc5-request-gate | constraint_box/src/constraintbox/gate_operations.py:95 | gate_operations | finite constraint via dual_solve cvc5 result | NOT_INVOKED (rg found no production call site) | cvc5 | yes | exists |
| cb:rustworkx-workflow-gate | constraint_box/src/constraintbox/gate_operations.py:134 | gate_operations | policy topology structure and reachability | NOT_INVOKED (rg found no production call site) | rustworkx | yes | exists |
| cb:sympy-exact-gate | constraint_box/src/constraintbox/gate_operations.py:213 | gate_operations | exact flow budget arithmetic and DAG facts | agentrun.py:1087-1091 | sympy | yes | exists |
| cb:maude-transition-gate | constraint_box/src/constraintbox/gate_operations.py:251 | gate_operations | one-rewrite transition and terminal reachability facts | agentrun.py:1087-1091 | maude | yes | exists |
| cb:boundary-contract-gate | constraint_box/src/constraintbox/gate_operations.py:289 | gate_operations | boundary profile separation | NOT_INVOKED (rg found no production call site) | none | yes | exists |
| cb:flow-termination-gate | constraint_box/src/constraintbox/gate_operations.py:334 | gate_operations | budget-free cycle/termination property | NOT_INVOKED (rg found no production call site) | none | yes | exists |
| cb:false-green-check-gate | constraint_box/src/constraintbox/gate_operations.py:384 | gate_operations | receipt authority and false-green diagnostics | NOT_INVOKED (rg found no production call site) | none | yes | exists |
| cb:gate-weakening-detection | constraint_box/src/constraintbox/gate_operations.py:445 | gate_operations | ledger weakening, evidence lowering, fixture removal, hash mismatch | NOT_INVOKED (rg found no production call site) | none | yes | exists |
| cb:strict-receipt-consumer-gate | constraint_box/src/constraintbox/gate_operations.py:507 | gate_operations | artifact tree byte integrity and derived aggregate recomputation | NOT_INVOKED (rg found no production call site) | none | yes | exists |
| cb:release-gate | constraint_box/src/constraintbox/gate_operations.py:565 | gate_operations | composed release ceiling checks G-A through G-D | NOT_INVOKED (rg found no production call site) | none | yes | exists |
| agentrun:PROPOSAL_NOT_STRICT_JSON_OBJECT | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | strict JSON object intake | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROPOSAL_ROOT_FIELDS | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | proposal root field schema | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROPOSAL_ID_INVALID | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | proposal id format | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROPOSAL_CANDIDATE_INVALID | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | candidate object shape | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROPOSAL_CANDIDATE_FIELDS | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | candidate field schema | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROPOSAL_CLAIM_ENUM | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | requested claim enum | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROPOSAL_EVIDENCE_REF_INVALID | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | evidence reference format | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROPOSAL_FALSIFIERS_INVALID | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | falsifier list shape | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:EVIDENCE_REF_MISMATCH | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | candidate evidence ref equals tool receipt ref | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:EVIDENCE_REF_MISSING | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | candidate evidence ref presence | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROPOSAL_CLAIM_MISSING | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | candidate requested claim presence | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:CLAIM_CEILING_EXCEEDED | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | requested claim equals allowed ceiling | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:SMT_PROPOSAL_UNSAT | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | SMT proposal admission | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:DISCHARGE_NOT_PASS | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | policy discharge status | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:RELEASE_SAFETY_VETO | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | independent release safety conjunction | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROVIDER_TOOL_USE | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | provider output has no tool use | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROVIDER_RECEIPT_REJECTED | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | provider receipt admission | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROVIDER_STATUS_<status> | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | provider status equals success | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:CONTROLLER_<blocked-reason> | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | controller decision is ELIGIBLE | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:MODEL_RESOLVED_MISMATCH | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | resolved model refines requested slug | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:MODEL_RESOLVED_UNAVAILABLE | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | resolved model is present | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:SMT_UNAVAILABLE_OR_DIVERGENT | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | z3/cvc5/enumeration settlement | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROVIDER_OUTPUT_MISSING | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | provider output exists | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROVIDER_OUTPUT_EXCEEDS_BOUND | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | provider output within bound | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROVIDER_EVENT_INVALID | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | provider event schema | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROVIDER_EVENT_TYPE_FORBIDDEN | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | provider event type allowlist | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROVIDER_ITEM_TYPE_FORBIDDEN | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | provider item type allowlist | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| agentrun:PROVIDER_AGENT_MESSAGE_COUNT | constraint_box/src/constraintbox/agentrun.py:880 | proposal_reason_code | provider agent message count | constraint_box/src/constraintbox/agentrun.py:880-930 | none | yes | exists |
| user_request:goal_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | proposal_reason_code | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | none | yes | exists |
| user_request:deliverable_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | proposal_reason_code | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | none | yes | exists |
| user_request:scope_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | proposal_reason_code | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | none | yes | exists |
| user_request:assumptions_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | proposal_reason_code | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | none | yes | exists |
| user_request:evidence_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | proposal_reason_code | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | none | yes | exists |
| user_request:actions_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | proposal_reason_code | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | none | yes | exists |
| user_request:external_tests_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | proposal_reason_code | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | none | yes | exists |
| user_request:claim_boundary_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | proposal_reason_code | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | none | yes | exists |
| user_request:authority_field_rejection | constraint_box/src/constraintbox/user_request.py:321-337 | proposal_reason_code | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | none | yes | exists |
| user_request:schema_shape_rejection | constraint_box/src/constraintbox/user_request.py:321-337 | proposal_reason_code | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | none | yes | exists |
| minilev:duplicate_node_signal_transition | constraint_box/src/constraintbox/mini_levos.py:849-1019 | proposal_reason_code | reason-code predicate | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | yes | exists |
| minilev:signal_terminal_mapping | constraint_box/src/constraintbox/mini_levos.py:849-1019 | proposal_reason_code | reason-code predicate | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | yes | exists |
| minilev:all_nodes_reachable | constraint_box/src/constraintbox/mini_levos.py:849-1019 | proposal_reason_code | reason-code predicate | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | yes | exists |
| minilev:nonretry_edges_dag | constraint_box/src/constraintbox/mini_levos.py:849-1019 | proposal_reason_code | reason-code predicate | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | yes | exists |
| minilev:every_node_reaches_terminal | constraint_box/src/constraintbox/gate_operations.py:1031-1234 | proposal_reason_code | reason-code predicate | constraint_box/src/constraintbox/agentrun.py:1087-1091 | none | yes | exists |
| claimgate:chain-verdict-path | claimgate_plugin/hooks/post_receipt_gate.sh:80-200 | proposal_reason_code | reason-code predicate | claimgate_plugin/hooks/pre_commit_gate_receipts.sh:46-57; claimgate_plugin/hooks/post_receipt_gate.sh:80-200 | none | yes | exists |
| cb:claimgate-chain | constraint_box/src/constraintbox/boundary_contract.py:44 | contract_identifier | metadata/contract identifier for ClaimGate chain boundary | constraint_box/src/constraintbox/gate.py:326 | none | unchecked | exists |
| cb:cpython-controller-runtime | constraint_box/src/constraintbox/boundary_contract.py:35 | contract_identifier | metadata/contract identifier for CPython runtime boundary | NOT_INVOKED | none | unchecked | exists |
| cb:external-sim-validation-adapter | constraint_box/src/constraintbox/boundary_contract.py:45 | contract_identifier | metadata/contract identifier for contained external sim adapter | NOT_INVOKED | none | unchecked | exists |
| cb:minilev-runtime | constraint_box/src/constraintbox/boundary_contract.py:44 | contract_identifier | metadata/contract identifier for MiniLev runtime boundary | constraint_box/src/constraintbox/gate.py:326 | none | unchecked | exists |
| cb:foundation-custody-gate-v2 | constraint_box/src/constraintbox/cb_foundation_custody_gate_v2.py:128 | module_gate_candidate | receipt schema, hash mappings, tooling record, paired genealogy block | NOT_INVOKED (rg found no production call site) | none | unchecked | exists |
| cb:independence-gate | constraint_box/src/constraintbox/cb_independence_gate.py:105 | module_gate_candidate | declared runtime dependency set versus exercised third-party imports | NOT_INVOKED (rg found no production call site) | none | unchecked | exists |
| cb:layer-purity-and-canaries | constraint_box/src/constraintbox/cb_layer_purity_and_canaries.py:235 | module_gate_candidate | layer import purity and mutation canary response changes | NOT_INVOKED (rg found no production call site) | none | unchecked | exists |
| cb:release-ceiling-gate | constraint_box/src/constraintbox/cb_release_gate.py:38 | module_gate_candidate | composed release ceiling gate over custody/strict/recompute conditions | constraint_box/src/constraintbox/gate_operations.py:565-598 | none | unchecked | exists |
| cb:semantic-drift-gate | constraint_box/src/constraintbox/semantic_drift_gate.py:59 | module_gate_candidate | packet structural/semantic drift and self-issued verdict separation | NOT_INVOKED (rg found no production call site) | none | unchecked | exists |
| cb:strict-receipt-consumer-v1 | constraint_box/src/constraintbox/strict_receipt_consumer.py:95 | module_gate_candidate | file index, declarations, recomputed aggregates, refusal of stored verdicts | NOT_INVOKED (v2 is referenced by gate_operations) | none | unchecked | exists |
| cb:strict-receipt-consumer-v2 | constraint_box/src/constraintbox/strict_receipt_consumer_v2.py:144 | module_gate_candidate | receipt digest, declared file containment, manifest hashes, producer verdict refusal | constraint_box/src/constraintbox/gate_operations.py:507-557 | none | unchecked | exists |
| cb:seal-artifact-scope | constraint_box/src/constraintbox/seal_artifact_scope.py:28 | module_gate_candidate | artifact scope/manifest seal CLI checks | NOT_INVOKED (rg found no production call site) | none | unchecked | exists |
| cb:gate-integrity-ast | constraint_box/src/constraintbox/gate_integrity_ast.py:55 | module_gate_candidate | AST gate source integrity and weakening findings | NOT_INVOKED (rg found no production call site) | none | unchecked | exists |
| cb:gate-weakening-detector | constraint_box/src/constraintbox/gate_weakening_detector.py:201 | module_gate_candidate | comparison of current/previous gate ledgers for weakening | constraint_box/src/constraintbox/gate_operations.py:445-498 | none | unchecked | exists |
| claimgate:artifact-binding | claimgate_plugin/artifact_binding.py:371 | module_gate_candidate | numeric leaf to artifact dependence and coverage | NOT_INVOKED by CB production call sites | none | unchecked | exists |
| claimgate:receipt-grammar | claimgate_plugin/receipt_grammar.py:649 | module_gate_candidate | evaluator-owned typed receipt grammar and evidence provenance | claimgate_plugin/hooks/post_receipt_gate.sh:104-123 | none | unchecked | exists |
| claimgate:claim-policy | claimgate_plugin/claim_policy_gate.py:33 | module_gate_candidate | content-derived numeric claim policy and engine requirement | claimgate_plugin/hooks/post_receipt_gate.sh:121-130 | none | unchecked | exists |
| claimgate:claim-verify | claimgate_plugin/claim_verify.py:100 | module_gate_candidate | registry-resolved tier verification and calibration identity | claimgate_plugin/hooks/post_receipt_gate.sh:156-168 | none | unchecked | exists |
| claimgate:recompute-veto | claimgate_plugin/recompute_veto.py:1 | module_gate_candidate | recompute claimed aggregates from raw receipt content | claimgate_plugin/hooks/post_receipt_gate.sh:89-101 | none | unchecked | exists |
| claimgate:three-engine-seal | claimgate_plugin/three_engine_seal.py:1 | module_gate_candidate | three-engine artifact/receipt seal | claimgate_plugin/hooks/post_receipt_gate.sh:136-153 | none | unchecked | exists |
| claimgate:ratchet-floor | claimgate_plugin/ratchet_floor.py:1 | module_gate_candidate | floor regression and unknown-key policy | claimgate_plugin/hooks/post_receipt_gate.sh:177-200 | none | unchecked | exists |
| claimgate:gate-integrity | claimgate_plugin/gate_integrity.py:249 | module_gate_candidate | hash manifest and uncovered chain-reference detection | NOT_INVOKED by post_receipt_gate chain | none | unchecked | exists |
| claimgate:formal-chain-bmc-z3 | claimgate_plugin/formal/chain_bmc_z3.py:38 | module_gate_candidate | bounded model check of stage progression | claimgate_plugin/run_all_gates.py:61-64 | z3 | unchecked | exists |
| claimgate:formal-chain-bmc-cvc5 | claimgate_plugin/formal/chain_bmc_cvc5.py:20 | module_gate_candidate | bounded model check of stage progression | claimgate_plugin/run_all_gates.py:67-70 | cvc5 | unchecked | exists |
| minilev:construction:policy_exact_type | constraint_box/src/constraintbox/mini_levos.py:850 | construction_invariant | policy exact type | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:registrations_tuple | constraint_box/src/constraintbox/mini_levos.py:852 | construction_invariant | registrations tuple | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:policy_collections_tuples | constraint_box/src/constraintbox/mini_levos.py:860 | construction_invariant | policy collections tuples | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:identifiers_valid | constraint_box/src/constraintbox/mini_levos.py:861 | construction_invariant | identifiers valid | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:positive_budgets | constraint_box/src/constraintbox/mini_levos.py:870 | construction_invariant | positive budgets | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:retry_nonnegative | constraint_box/src/constraintbox/mini_levos.py:871 | construction_invariant | retry nonnegative | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:hard_bounds | constraint_box/src/constraintbox/mini_levos.py:894 | construction_invariant | hard bounds | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:claim_ceiling | constraint_box/src/constraintbox/mini_levos.py:896 | construction_invariant | claim ceiling | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:unique_hooks | constraint_box/src/constraintbox/mini_levos.py:902 | construction_invariant | unique hooks | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:flow_node_types | constraint_box/src/constraintbox/mini_levos.py:909 | construction_invariant | flow node types | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:unique_nodes | constraint_box/src/constraintbox/mini_levos.py:913 | construction_invariant | unique nodes | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:registered_hooks | constraint_box/src/constraintbox/mini_levos.py:915 | construction_invariant | registered hooks | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:entry_node | constraint_box/src/constraintbox/mini_levos.py:918 | construction_invariant | entry node | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:exact_hook_node_binding | constraint_box/src/constraintbox/mini_levos.py:920 | construction_invariant | exact hook node binding | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:lease_type | constraint_box/src/constraintbox/mini_levos.py:924 | construction_invariant | lease type | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:lease_node_hook_match | constraint_box/src/constraintbox/mini_levos.py:927 | construction_invariant | lease node hook match | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:terminal_set | constraint_box/src/constraintbox/mini_levos.py:937 | construction_invariant | terminal set | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:required_nodes | constraint_box/src/constraintbox/mini_levos.py:943 | construction_invariant | required nodes | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:transition_type | constraint_box/src/constraintbox/mini_levos.py:953 | construction_invariant | transition type | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:transition_source | constraint_box/src/constraintbox/mini_levos.py:955 | construction_invariant | transition source | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:transition_signal | constraint_box/src/constraintbox/mini_levos.py:957 | construction_invariant | transition signal | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:transition_target | constraint_box/src/constraintbox/mini_levos.py:959 | construction_invariant | transition target | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:duplicate_transition | constraint_box/src/constraintbox/mini_levos.py:962 | construction_invariant | duplicate transition | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:terminal_signal_mapping | constraint_box/src/constraintbox/mini_levos.py:971 | construction_invariant | terminal signal mapping | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:retry_target_bounded_node | constraint_box/src/constraintbox/mini_levos.py:978 | construction_invariant | retry target bounded node | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:positive_terminal_gate_pass | constraint_box/src/constraintbox/mini_levos.py:983 | construction_invariant | positive terminal gate pass | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:retry_gate_only | constraint_box/src/constraintbox/mini_levos.py:997 | construction_invariant | retry gate only | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:exhaustive_transition_map | constraint_box/src/constraintbox/mini_levos.py:1008 | construction_invariant | exhaustive transition map | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:nonretry_dag | constraint_box/src/constraintbox/mini_levos.py:1013 | construction_invariant | nonretry dag | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:construction:reachability_and_terminal_reachability | constraint_box/src/constraintbox/mini_levos.py:1016 | construction_invariant | reachability and terminal reachability | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | none | unchecked | exists |
| minilev:runtime:ledger_path_unused | constraint_box/src/constraintbox/mini_levos.py:1759 | runtime_invariant | ledger path unused | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:execution_lease_guard_pairing | constraint_box/src/constraintbox/mini_levos.py:1768 | runtime_invariant | execution lease guard pairing | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:initial_context_object | constraint_box/src/constraintbox/mini_levos.py:1826 | runtime_invariant | initial context object | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:reserved_controller_metadata | constraint_box/src/constraintbox/mini_levos.py:1827 | runtime_invariant | reserved controller metadata | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:initial_context_bound | constraint_box/src/constraintbox/mini_levos.py:1833 | runtime_invariant | initial context bound | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:runtime_identity_before | constraint_box/src/constraintbox/mini_levos.py:1836 | runtime_invariant | runtime identity before | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:visit_budget | constraint_box/src/constraintbox/mini_levos.py:1867 | runtime_invariant | visit budget | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:hook_identity | constraint_box/src/constraintbox/mini_levos.py:1872 | runtime_invariant | hook identity | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:hook_result_type | constraint_box/src/constraintbox/mini_levos.py:1920 | runtime_invariant | hook result type | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:authorized_signal | constraint_box/src/constraintbox/mini_levos.py:1924 | runtime_invariant | authorized signal | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:canonical_hook_output | constraint_box/src/constraintbox/mini_levos.py:1931 | runtime_invariant | canonical hook output | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:controller_authority_paths | constraint_box/src/constraintbox/mini_levos.py:1947 | runtime_invariant | controller authority paths | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:update_keys | constraint_box/src/constraintbox/mini_levos.py:1956 | runtime_invariant | update keys | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:hook_output_bound | constraint_box/src/constraintbox/mini_levos.py:1971 | runtime_invariant | hook output bound | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:context_bound | constraint_box/src/constraintbox/mini_levos.py:1979 | runtime_invariant | context bound | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:retry_budget | constraint_box/src/constraintbox/mini_levos.py:1990 | runtime_invariant | retry budget | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:step_budget | constraint_box/src/constraintbox/mini_levos.py:1995 | runtime_invariant | step budget | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:runtime_identity_stability | constraint_box/src/constraintbox/mini_levos.py:2002 | runtime_invariant | runtime identity stability | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:required_nodes_executed | constraint_box/src/constraintbox/mini_levos.py:2024 | runtime_invariant | required nodes executed | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:event_bound | constraint_box/src/constraintbox/mini_levos.py:2072 | runtime_invariant | event bound | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:event_persistence | constraint_box/src/constraintbox/mini_levos.py:2075 | runtime_invariant | event persistence | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:terminal_exists | constraint_box/src/constraintbox/mini_levos.py:2095 | runtime_invariant | terminal exists | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:ledger_verification | constraint_box/src/constraintbox/mini_levos.py:2097 | runtime_invariant | ledger verification | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:receipt_bound | constraint_box/src/constraintbox/mini_levos.py:2150 | runtime_invariant | receipt bound | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:receipt_self_verification | constraint_box/src/constraintbox/mini_levos.py:2154 | runtime_invariant | receipt self verification | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:embedded_policy_validation | constraint_box/src/constraintbox/mini_levos.py:2242 | runtime_invariant | embedded policy validation | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:receipt_schema_keys | constraint_box/src/constraintbox/mini_levos.py:2180 | runtime_invariant | receipt schema keys | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:receipt_identity_fields | constraint_box/src/constraintbox/mini_levos.py:2190 | runtime_invariant | receipt identity fields | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:receipt_ledger_binding | constraint_box/src/constraintbox/mini_levos.py:2210 | runtime_invariant | receipt ledger binding | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |
| minilev:runtime:receipt_digest_binding | constraint_box/src/constraintbox/mini_levos.py:2230 | runtime_invariant | receipt digest binding | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | none | unchecked | exists |

## proposal_reason_code (44)

| gate_id | defined_at | what it checks | invoked from | status |
|---|---|---|---|---|
| agentrun:PROPOSAL_NOT_STRICT_JSON_OBJECT | constraint_box/src/constraintbox/agentrun.py:880 | strict JSON object intake | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROPOSAL_ROOT_FIELDS | constraint_box/src/constraintbox/agentrun.py:880 | proposal root field schema | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROPOSAL_ID_INVALID | constraint_box/src/constraintbox/agentrun.py:880 | proposal id format | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROPOSAL_CANDIDATE_INVALID | constraint_box/src/constraintbox/agentrun.py:880 | candidate object shape | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROPOSAL_CANDIDATE_FIELDS | constraint_box/src/constraintbox/agentrun.py:880 | candidate field schema | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROPOSAL_CLAIM_ENUM | constraint_box/src/constraintbox/agentrun.py:880 | requested claim enum | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROPOSAL_EVIDENCE_REF_INVALID | constraint_box/src/constraintbox/agentrun.py:880 | evidence reference format | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROPOSAL_FALSIFIERS_INVALID | constraint_box/src/constraintbox/agentrun.py:880 | falsifier list shape | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:EVIDENCE_REF_MISMATCH | constraint_box/src/constraintbox/agentrun.py:880 | candidate evidence ref equals tool receipt ref | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:EVIDENCE_REF_MISSING | constraint_box/src/constraintbox/agentrun.py:880 | candidate evidence ref presence | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROPOSAL_CLAIM_MISSING | constraint_box/src/constraintbox/agentrun.py:880 | candidate requested claim presence | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:CLAIM_CEILING_EXCEEDED | constraint_box/src/constraintbox/agentrun.py:880 | requested claim equals allowed ceiling | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:SMT_PROPOSAL_UNSAT | constraint_box/src/constraintbox/agentrun.py:880 | SMT proposal admission | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:DISCHARGE_NOT_PASS | constraint_box/src/constraintbox/agentrun.py:880 | policy discharge status | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:RELEASE_SAFETY_VETO | constraint_box/src/constraintbox/agentrun.py:880 | independent release safety conjunction | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROVIDER_TOOL_USE | constraint_box/src/constraintbox/agentrun.py:880 | provider output has no tool use | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROVIDER_RECEIPT_REJECTED | constraint_box/src/constraintbox/agentrun.py:880 | provider receipt admission | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROVIDER_STATUS_<status> | constraint_box/src/constraintbox/agentrun.py:880 | provider status equals success | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:CONTROLLER_<blocked-reason> | constraint_box/src/constraintbox/agentrun.py:880 | controller decision is ELIGIBLE | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:MODEL_RESOLVED_MISMATCH | constraint_box/src/constraintbox/agentrun.py:880 | resolved model refines requested slug | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:MODEL_RESOLVED_UNAVAILABLE | constraint_box/src/constraintbox/agentrun.py:880 | resolved model is present | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:SMT_UNAVAILABLE_OR_DIVERGENT | constraint_box/src/constraintbox/agentrun.py:880 | z3/cvc5/enumeration settlement | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROVIDER_OUTPUT_MISSING | constraint_box/src/constraintbox/agentrun.py:880 | provider output exists | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROVIDER_OUTPUT_EXCEEDS_BOUND | constraint_box/src/constraintbox/agentrun.py:880 | provider output within bound | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROVIDER_EVENT_INVALID | constraint_box/src/constraintbox/agentrun.py:880 | provider event schema | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROVIDER_EVENT_TYPE_FORBIDDEN | constraint_box/src/constraintbox/agentrun.py:880 | provider event type allowlist | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROVIDER_ITEM_TYPE_FORBIDDEN | constraint_box/src/constraintbox/agentrun.py:880 | provider item type allowlist | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| agentrun:PROVIDER_AGENT_MESSAGE_COUNT | constraint_box/src/constraintbox/agentrun.py:880 | provider agent message count | constraint_box/src/constraintbox/agentrun.py:880-930 | exists |
| user_request:goal_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | exists |
| user_request:deliverable_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | exists |
| user_request:scope_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | exists |
| user_request:assumptions_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | exists |
| user_request:evidence_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | exists |
| user_request:actions_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | exists |
| user_request:external_tests_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | exists |
| user_request:claim_boundary_explicit | constraint_box/src/constraintbox/user_request.py:321-337 | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | exists |
| user_request:authority_field_rejection | constraint_box/src/constraintbox/user_request.py:321-337 | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | exists |
| user_request:schema_shape_rejection | constraint_box/src/constraintbox/user_request.py:321-337 | reason-code predicate | constraint_box/src/constraintbox/user_request.py:321-337 | exists |
| minilev:duplicate_node_signal_transition | constraint_box/src/constraintbox/mini_levos.py:849-1019 | reason-code predicate | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:signal_terminal_mapping | constraint_box/src/constraintbox/mini_levos.py:849-1019 | reason-code predicate | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:all_nodes_reachable | constraint_box/src/constraintbox/mini_levos.py:849-1019 | reason-code predicate | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:nonretry_edges_dag | constraint_box/src/constraintbox/mini_levos.py:849-1019 | reason-code predicate | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:every_node_reaches_terminal | constraint_box/src/constraintbox/gate_operations.py:1031-1234 | reason-code predicate | constraint_box/src/constraintbox/agentrun.py:1087-1091 | exists |
| claimgate:chain-verdict-path | claimgate_plugin/hooks/post_receipt_gate.sh:80-200 | reason-code predicate | claimgate_plugin/hooks/pre_commit_gate_receipts.sh:46-57; claimgate_plugin/hooks/post_receipt_gate.sh:80-200 | exists |

## construction_invariant (30)

| gate_id | defined_at | what it checks | invoked from | status |
|---|---|---|---|---|
| minilev:construction:policy_exact_type | constraint_box/src/constraintbox/mini_levos.py:850 | policy exact type | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:registrations_tuple | constraint_box/src/constraintbox/mini_levos.py:852 | registrations tuple | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:policy_collections_tuples | constraint_box/src/constraintbox/mini_levos.py:860 | policy collections tuples | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:identifiers_valid | constraint_box/src/constraintbox/mini_levos.py:861 | identifiers valid | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:positive_budgets | constraint_box/src/constraintbox/mini_levos.py:870 | positive budgets | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:retry_nonnegative | constraint_box/src/constraintbox/mini_levos.py:871 | retry nonnegative | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:hard_bounds | constraint_box/src/constraintbox/mini_levos.py:894 | hard bounds | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:claim_ceiling | constraint_box/src/constraintbox/mini_levos.py:896 | claim ceiling | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:unique_hooks | constraint_box/src/constraintbox/mini_levos.py:902 | unique hooks | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:flow_node_types | constraint_box/src/constraintbox/mini_levos.py:909 | flow node types | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:unique_nodes | constraint_box/src/constraintbox/mini_levos.py:913 | unique nodes | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:registered_hooks | constraint_box/src/constraintbox/mini_levos.py:915 | registered hooks | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:entry_node | constraint_box/src/constraintbox/mini_levos.py:918 | entry node | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:exact_hook_node_binding | constraint_box/src/constraintbox/mini_levos.py:920 | exact hook node binding | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:lease_type | constraint_box/src/constraintbox/mini_levos.py:924 | lease type | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:lease_node_hook_match | constraint_box/src/constraintbox/mini_levos.py:927 | lease node hook match | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:terminal_set | constraint_box/src/constraintbox/mini_levos.py:937 | terminal set | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:required_nodes | constraint_box/src/constraintbox/mini_levos.py:943 | required nodes | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:transition_type | constraint_box/src/constraintbox/mini_levos.py:953 | transition type | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:transition_source | constraint_box/src/constraintbox/mini_levos.py:955 | transition source | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:transition_signal | constraint_box/src/constraintbox/mini_levos.py:957 | transition signal | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:transition_target | constraint_box/src/constraintbox/mini_levos.py:959 | transition target | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:duplicate_transition | constraint_box/src/constraintbox/mini_levos.py:962 | duplicate transition | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:terminal_signal_mapping | constraint_box/src/constraintbox/mini_levos.py:971 | terminal signal mapping | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:retry_target_bounded_node | constraint_box/src/constraintbox/mini_levos.py:978 | retry target bounded node | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:positive_terminal_gate_pass | constraint_box/src/constraintbox/mini_levos.py:983 | positive terminal gate pass | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:retry_gate_only | constraint_box/src/constraintbox/mini_levos.py:997 | retry gate only | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:exhaustive_transition_map | constraint_box/src/constraintbox/mini_levos.py:1008 | exhaustive transition map | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:nonretry_dag | constraint_box/src/constraintbox/mini_levos.py:1013 | nonretry dag | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |
| minilev:construction:reachability_and_terminal_reachability | constraint_box/src/constraintbox/mini_levos.py:1016 | reachability and terminal reachability | constraint_box/src/constraintbox/mini_levos.py:1763-1767 | exists |

## runtime_invariant (30)

| gate_id | defined_at | what it checks | invoked from | status |
|---|---|---|---|---|
| minilev:runtime:ledger_path_unused | constraint_box/src/constraintbox/mini_levos.py:1759 | ledger path unused | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:execution_lease_guard_pairing | constraint_box/src/constraintbox/mini_levos.py:1768 | execution lease guard pairing | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:initial_context_object | constraint_box/src/constraintbox/mini_levos.py:1826 | initial context object | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:reserved_controller_metadata | constraint_box/src/constraintbox/mini_levos.py:1827 | reserved controller metadata | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:initial_context_bound | constraint_box/src/constraintbox/mini_levos.py:1833 | initial context bound | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:runtime_identity_before | constraint_box/src/constraintbox/mini_levos.py:1836 | runtime identity before | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:visit_budget | constraint_box/src/constraintbox/mini_levos.py:1867 | visit budget | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:hook_identity | constraint_box/src/constraintbox/mini_levos.py:1872 | hook identity | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:hook_result_type | constraint_box/src/constraintbox/mini_levos.py:1920 | hook result type | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:authorized_signal | constraint_box/src/constraintbox/mini_levos.py:1924 | authorized signal | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:canonical_hook_output | constraint_box/src/constraintbox/mini_levos.py:1931 | canonical hook output | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:controller_authority_paths | constraint_box/src/constraintbox/mini_levos.py:1947 | controller authority paths | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:update_keys | constraint_box/src/constraintbox/mini_levos.py:1956 | update keys | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:hook_output_bound | constraint_box/src/constraintbox/mini_levos.py:1971 | hook output bound | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:context_bound | constraint_box/src/constraintbox/mini_levos.py:1979 | context bound | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:retry_budget | constraint_box/src/constraintbox/mini_levos.py:1990 | retry budget | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:step_budget | constraint_box/src/constraintbox/mini_levos.py:1995 | step budget | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:runtime_identity_stability | constraint_box/src/constraintbox/mini_levos.py:2002 | runtime identity stability | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:required_nodes_executed | constraint_box/src/constraintbox/mini_levos.py:2024 | required nodes executed | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:event_bound | constraint_box/src/constraintbox/mini_levos.py:2072 | event bound | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:event_persistence | constraint_box/src/constraintbox/mini_levos.py:2075 | event persistence | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:terminal_exists | constraint_box/src/constraintbox/mini_levos.py:2095 | terminal exists | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:ledger_verification | constraint_box/src/constraintbox/mini_levos.py:2097 | ledger verification | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:receipt_bound | constraint_box/src/constraintbox/mini_levos.py:2150 | receipt bound | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:receipt_self_verification | constraint_box/src/constraintbox/mini_levos.py:2154 | receipt self verification | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:embedded_policy_validation | constraint_box/src/constraintbox/mini_levos.py:2242 | embedded policy validation | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:receipt_schema_keys | constraint_box/src/constraintbox/mini_levos.py:2180 | receipt schema keys | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:receipt_identity_fields | constraint_box/src/constraintbox/mini_levos.py:2190 | receipt identity fields | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:receipt_ledger_binding | constraint_box/src/constraintbox/mini_levos.py:2210 | receipt ledger binding | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |
| minilev:runtime:receipt_digest_binding | constraint_box/src/constraintbox/mini_levos.py:2230 | receipt digest binding | constraint_box/src/constraintbox/mini_levos.py:1825-2164 | exists |

## module_gate_candidate (20)

| gate_id | defined_at | what it checks | invoked from | status |
|---|---|---|---|---|
| cb:foundation-custody-gate-v2 | constraint_box/src/constraintbox/cb_foundation_custody_gate_v2.py:128 | receipt schema, hash mappings, tooling record, paired genealogy block | NOT_INVOKED (rg found no production call site) | exists |
| cb:independence-gate | constraint_box/src/constraintbox/cb_independence_gate.py:105 | declared runtime dependency set versus exercised third-party imports | NOT_INVOKED (rg found no production call site) | exists |
| cb:layer-purity-and-canaries | constraint_box/src/constraintbox/cb_layer_purity_and_canaries.py:235 | layer import purity and mutation canary response changes | NOT_INVOKED (rg found no production call site) | exists |
| cb:release-ceiling-gate | constraint_box/src/constraintbox/cb_release_gate.py:38 | composed release ceiling gate over custody/strict/recompute conditions | constraint_box/src/constraintbox/gate_operations.py:565-598 | exists |
| cb:semantic-drift-gate | constraint_box/src/constraintbox/semantic_drift_gate.py:59 | packet structural/semantic drift and self-issued verdict separation | NOT_INVOKED (rg found no production call site) | exists |
| cb:strict-receipt-consumer-v1 | constraint_box/src/constraintbox/strict_receipt_consumer.py:95 | file index, declarations, recomputed aggregates, refusal of stored verdicts | NOT_INVOKED (v2 is referenced by gate_operations) | exists |
| cb:strict-receipt-consumer-v2 | constraint_box/src/constraintbox/strict_receipt_consumer_v2.py:144 | receipt digest, declared file containment, manifest hashes, producer verdict refusal | constraint_box/src/constraintbox/gate_operations.py:507-557 | exists |
| cb:seal-artifact-scope | constraint_box/src/constraintbox/seal_artifact_scope.py:28 | artifact scope/manifest seal CLI checks | NOT_INVOKED (rg found no production call site) | exists |
| cb:gate-integrity-ast | constraint_box/src/constraintbox/gate_integrity_ast.py:55 | AST gate source integrity and weakening findings | NOT_INVOKED (rg found no production call site) | exists |
| cb:gate-weakening-detector | constraint_box/src/constraintbox/gate_weakening_detector.py:201 | comparison of current/previous gate ledgers for weakening | constraint_box/src/constraintbox/gate_operations.py:445-498 | exists |
| claimgate:artifact-binding | claimgate_plugin/artifact_binding.py:371 | numeric leaf to artifact dependence and coverage | NOT_INVOKED by CB production call sites | exists |
| claimgate:receipt-grammar | claimgate_plugin/receipt_grammar.py:649 | evaluator-owned typed receipt grammar and evidence provenance | claimgate_plugin/hooks/post_receipt_gate.sh:104-123 | exists |
| claimgate:claim-policy | claimgate_plugin/claim_policy_gate.py:33 | content-derived numeric claim policy and engine requirement | claimgate_plugin/hooks/post_receipt_gate.sh:121-130 | exists |
| claimgate:claim-verify | claimgate_plugin/claim_verify.py:100 | registry-resolved tier verification and calibration identity | claimgate_plugin/hooks/post_receipt_gate.sh:156-168 | exists |
| claimgate:recompute-veto | claimgate_plugin/recompute_veto.py:1 | recompute claimed aggregates from raw receipt content | claimgate_plugin/hooks/post_receipt_gate.sh:89-101 | exists |
| claimgate:three-engine-seal | claimgate_plugin/three_engine_seal.py:1 | three-engine artifact/receipt seal | claimgate_plugin/hooks/post_receipt_gate.sh:136-153 | exists |
| claimgate:ratchet-floor | claimgate_plugin/ratchet_floor.py:1 | floor regression and unknown-key policy | claimgate_plugin/hooks/post_receipt_gate.sh:177-200 | exists |
| claimgate:gate-integrity | claimgate_plugin/gate_integrity.py:249 | hash manifest and uncovered chain-reference detection | NOT_INVOKED by post_receipt_gate chain | exists |
| claimgate:formal-chain-bmc-z3 | claimgate_plugin/formal/chain_bmc_z3.py:38 | bounded model check of stage progression | claimgate_plugin/run_all_gates.py:61-64 | exists |
| claimgate:formal-chain-bmc-cvc5 | claimgate_plugin/formal/chain_bmc_cvc5.py:20 | bounded model check of stage progression | claimgate_plugin/run_all_gates.py:67-70 | exists |

## gate_operations (11)

| gate_id | defined_at | what it checks | invoked from | status |
|---|---|---|---|---|
| cb:z3-request-gate | constraint_box/src/constraintbox/gate_operations.py:56 | finite constraint via dual_solve z3 result | NOT_INVOKED (rg found no production call site) | exists |
| cb:cvc5-request-gate | constraint_box/src/constraintbox/gate_operations.py:95 | finite constraint via dual_solve cvc5 result | NOT_INVOKED (rg found no production call site) | exists |
| cb:rustworkx-workflow-gate | constraint_box/src/constraintbox/gate_operations.py:134 | policy topology structure and reachability | NOT_INVOKED (rg found no production call site) | exists |
| cb:sympy-exact-gate | constraint_box/src/constraintbox/gate_operations.py:213 | exact flow budget arithmetic and DAG facts | agentrun.py:1087-1091 | exists |
| cb:maude-transition-gate | constraint_box/src/constraintbox/gate_operations.py:251 | one-rewrite transition and terminal reachability facts | agentrun.py:1087-1091 | exists |
| cb:boundary-contract-gate | constraint_box/src/constraintbox/gate_operations.py:289 | boundary profile separation | NOT_INVOKED (rg found no production call site) | exists |
| cb:flow-termination-gate | constraint_box/src/constraintbox/gate_operations.py:334 | budget-free cycle/termination property | NOT_INVOKED (rg found no production call site) | exists |
| cb:false-green-check-gate | constraint_box/src/constraintbox/gate_operations.py:384 | receipt authority and false-green diagnostics | NOT_INVOKED (rg found no production call site) | exists |
| cb:gate-weakening-detection | constraint_box/src/constraintbox/gate_operations.py:445 | ledger weakening, evidence lowering, fixture removal, hash mismatch | NOT_INVOKED (rg found no production call site) | exists |
| cb:strict-receipt-consumer-gate | constraint_box/src/constraintbox/gate_operations.py:507 | artifact tree byte integrity and derived aggregate recomputation | NOT_INVOKED (rg found no production call site) | exists |
| cb:release-gate | constraint_box/src/constraintbox/gate_operations.py:565 | composed release ceiling checks G-A through G-D | NOT_INVOKED (rg found no production call site) | exists |

## contract_identifier (4)

| gate_id | defined_at | what it checks | invoked from | status |
|---|---|---|---|---|
| cb:claimgate-chain | constraint_box/src/constraintbox/boundary_contract.py:44 | metadata/contract identifier for ClaimGate chain boundary | constraint_box/src/constraintbox/gate.py:326 | exists |
| cb:cpython-controller-runtime | constraint_box/src/constraintbox/boundary_contract.py:35 | metadata/contract identifier for CPython runtime boundary | NOT_INVOKED | exists |
| cb:external-sim-validation-adapter | constraint_box/src/constraintbox/boundary_contract.py:45 | metadata/contract identifier for contained external sim adapter | NOT_INVOKED | exists |
| cb:minilev-runtime | constraint_box/src/constraintbox/boundary_contract.py:44 | metadata/contract identifier for MiniLev runtime boundary | constraint_box/src/constraintbox/gate.py:326 | exists |

## Enforcement surfaces

| surface | defined at | reachable gates | status | observation |
|---|---|---|---|---|
| CLI | constraint_box/src/constraintbox/cli.py:169-392 | none | unchecked | mandated help command failed: No module named constraintbox |
| legacy/core CLI parser | constraint_box/src/constraintbox/core_cli.py:11-17 | none | exists | source parser exposes doctor, exercise; not reached by mandated module invocation |
| git hooks in .git/hooks | .git/hooks/pre-commit:1 (only non-sample executable hook found by find) | none | unchecked | sample hooks plus pre-commit; content not fully inspected for gate calls |
| shipped ClaimGate hooks | claimgate_plugin/hooks/post_receipt_gate.sh:80-200; pre_commit_gate_receipts.sh:22-57 | claimgate:receipt-grammar, claimgate:claim-policy, claimgate:recompute-veto, claimgate:three-engine-seal, claimgate:claim-verify, claimgate:ratchet-floor | exists | intake -> recompute -> tier0 -> policy -> seal -> verify -> floor -> ledger; pre-commit fires post-receipt gate for staged ratchet receipts |
| MiniLev FlowNode kinds | constraint_box/src/constraintbox/mini_levos.py:96-100 | minilev:construction:*, minilev:runtime:*, cb:sympy-exact-gate, cb:maude-transition-gate | exists | PROPOSAL, GATE, HOOK, TOOL |
| root Makefile targets | Makefile:11-412 | claimgate:*, cb:* | exists | targets enumerated by rg; no target execution performed |
| constraint_box Makefile targets | constraint_box/Makefile:1-34 | cb:* | exists | help, verify-install, install-gates, install-full, test, clean; no target execution performed |
| gate proof script | constraint_box/scripts/prove_gates_fire.py:1 | cb:z3-request-gate, cb:cvc5-request-gate, cb:rustworkx-workflow-gate, cb:sympy-exact-gate, cb:maude-transition-gate, cb:boundary-contract-gate, cb:flow-termination-gate, cb:false-green-check-gate, cb:gate-weakening-detection, cb:strict-receipt-consumer-gate, cb:release-gate, agentrun:PROPOSAL_NOT_STRICT_JSON_OBJECT, agentrun:PROPOSAL_ROOT_FIELDS, agentrun:PROPOSAL_ID_INVALID, agentrun:PROPOSAL_CANDIDATE_INVALID, agentrun:PROPOSAL_CANDIDATE_FIELDS, agentrun:PROPOSAL_CLAIM_ENUM, agentrun:PROPOSAL_EVIDENCE_REF_INVALID, agentrun:PROPOSAL_FALSIFIERS_INVALID, agentrun:EVIDENCE_REF_MISMATCH, agentrun:EVIDENCE_REF_MISSING, agentrun:PROPOSAL_CLAIM_MISSING, agentrun:CLAIM_CEILING_EXCEEDED, agentrun:SMT_PROPOSAL_UNSAT, agentrun:DISCHARGE_NOT_PASS, agentrun:RELEASE_SAFETY_VETO, agentrun:PROVIDER_TOOL_USE, agentrun:PROVIDER_RECEIPT_REJECTED, agentrun:PROVIDER_STATUS_<status>, agentrun:CONTROLLER_<blocked-reason>, agentrun:MODEL_RESOLVED_MISMATCH, agentrun:MODEL_RESOLVED_UNAVAILABLE, agentrun:SMT_UNAVAILABLE_OR_DIVERGENT, agentrun:PROVIDER_OUTPUT_MISSING, agentrun:PROVIDER_OUTPUT_EXCEEDS_BOUND, agentrun:PROVIDER_EVENT_INVALID, agentrun:PROVIDER_EVENT_TYPE_FORBIDDEN, agentrun:PROVIDER_ITEM_TYPE_FORBIDDEN, agentrun:PROVIDER_AGENT_MESSAGE_COUNT, user_request:goal_explicit, user_request:deliverable_explicit, user_request:scope_explicit, user_request:assumptions_explicit, user_request:evidence_explicit, user_request:actions_explicit, user_request:external_tests_explicit, user_request:claim_boundary_explicit, user_request:authority_field_rejection, user_request:schema_shape_rejection, minilev:duplicate_node_signal_transition, minilev:signal_terminal_mapping, minilev:all_nodes_reachable, minilev:nonretry_edges_dag, minilev:every_node_reaches_terminal, claimgate:chain-verdict-path | exists | receipt records 55 result rows; script not rerun because write scope is repo receipts |
| ClaimGate formal BMC runners | claimgate_plugin/formal/chain_bmc_z3.py:38; chain_bmc_cvc5.py:20 | claimgate:formal-chain-bmc-z3, claimgate:formal-chain-bmc-cvc5 | exists | listed in run_all_gates.py, not executed |
| gate assertion tests | constraint_box/tests/test_process_ratchet.py:170-175; constraint_box/tests/test_gate_entrypoint.py:62 | cb:z3-request-gate, cb:claimgate-chain, cb:minilev-runtime | exists | test modules found by rg; test suite not executed |

## Gates with no production call path

These 20 rows were marked `NOT_INVOKED`. The proof harness can call a gate without making it production-reachable.

| gate_id | file:line | kind |
|---|---|---|
| cb:z3-request-gate | constraint_box/src/constraintbox/gate_operations.py:56 | gate_operations |
| cb:cvc5-request-gate | constraint_box/src/constraintbox/gate_operations.py:95 | gate_operations |
| cb:rustworkx-workflow-gate | constraint_box/src/constraintbox/gate_operations.py:134 | gate_operations |
| cb:boundary-contract-gate | constraint_box/src/constraintbox/gate_operations.py:289 | gate_operations |
| cb:flow-termination-gate | constraint_box/src/constraintbox/gate_operations.py:334 | gate_operations |
| cb:false-green-check-gate | constraint_box/src/constraintbox/gate_operations.py:384 | gate_operations |
| cb:gate-weakening-detection | constraint_box/src/constraintbox/gate_operations.py:445 | gate_operations |
| cb:strict-receipt-consumer-gate | constraint_box/src/constraintbox/gate_operations.py:507 | gate_operations |
| cb:release-gate | constraint_box/src/constraintbox/gate_operations.py:565 | gate_operations |
| cb:cpython-controller-runtime | constraint_box/src/constraintbox/boundary_contract.py:35 | contract_identifier |
| cb:external-sim-validation-adapter | constraint_box/src/constraintbox/boundary_contract.py:45 | contract_identifier |
| cb:foundation-custody-gate-v2 | constraint_box/src/constraintbox/cb_foundation_custody_gate_v2.py:128 | module_gate_candidate |
| cb:independence-gate | constraint_box/src/constraintbox/cb_independence_gate.py:105 | module_gate_candidate |
| cb:layer-purity-and-canaries | constraint_box/src/constraintbox/cb_layer_purity_and_canaries.py:235 | module_gate_candidate |
| cb:semantic-drift-gate | constraint_box/src/constraintbox/semantic_drift_gate.py:59 | module_gate_candidate |
| cb:strict-receipt-consumer-v1 | constraint_box/src/constraintbox/strict_receipt_consumer.py:95 | module_gate_candidate |
| cb:seal-artifact-scope | constraint_box/src/constraintbox/seal_artifact_scope.py:28 | module_gate_candidate |
| cb:gate-integrity-ast | constraint_box/src/constraintbox/gate_integrity_ast.py:55 | module_gate_candidate |
| claimgate:artifact-binding | claimgate_plugin/artifact_binding.py:371 | module_gate_candidate |
| claimgate:gate-integrity | claimgate_plugin/gate_integrity.py:249 | module_gate_candidate |
## How to check this yourself

Run these commands from the repository root:

```sh
rg -n 'run_formal_flow_gates|gate_z3_request|gate_cvc5_request|gate_rustworkx_workflow|gate_boundary_contract|gate_strict_receipt_consumer|gate_release|gate_false_green|gate_weakening' constraint_box/src/constraintbox --glob '*.py'
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 -m json.tool constraint_box/receipts/gate_fire_proof_v1.json
```
