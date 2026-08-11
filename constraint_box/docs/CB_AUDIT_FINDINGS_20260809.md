# ConstraintBox audit findings for 2026-08-09

This document consolidates five read-only lanes. It contains 25 raw findings and 24 unique defects because lanes 2 and 5 independently found the same provisional rustworkx defect. No production source was edited.

## Findings

### 1. Rustworkx workflow gate emits ACYCLIC_REACHABLE without checking cycles or reachability

- Severity: `critical`
- Location: `constraint_box/src/constraintbox/gate_operations.py:170-195`
- Threat move: `logic-gap`
- Lane evidence: lane 2, lane 5
- What is wrong: The positive branch only checks that entry_node is named and terminal values are strings, then emits ACYCLIC_REACHABLE while the source says the full check is pending. A genuinely cyclic FlowPolicy and an acyclic control returned the same verdict, reason, and output hash.
- How checked: Command: PYTHONPATH=/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/src /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 /private/tmp/claude-501/-Users/joshuaeisenhart-Codex-Ratchet/b1e33759-f392-47e0-8f05-c6ce7250426c/scratchpad/codex_lanes/lane2_probe.py. Output: rustworkx acyclic ACYCLIC_REACHABLE structural_validation_passed 4012b10016245da99733f0a6c4db7b87670c37b12e67f09d4b6204762ed4b649; rustworkx cyclic ACYCLIC_REACHABLE structural_validation_passed 4012b10016245da99733f0a6c4db7b87670c37b12e67f09d4b6204762ed4b649. Source evidence: gate_operations.py:171-194 contains only minimal checks and the provisional verdict.
- Concrete fix: Construct the rustworkx graph and independently compute cycle and terminal-reachability facts before emitting ACYCLIC_REACHABLE; return a distinct failure verdict for either violation and add the cyclic/acyclic differential control to the gate test.

### 2. The AST gate-integrity checker is exported but has no production call path

- Severity: `critical`
- Location: `constraint_box/src/constraintbox/__init__.py:120-125`
- Threat move: `edit-checker`
- Lane evidence: lane 3
- What is wrong: gate_integrity_ast.py is imported into the package namespace, but the repository search found no production call to GateIntegrityChecker or its checker methods outside the module itself. Therefore an LLM can alter a checker module without this AST gate being invoked by a CB production operation. The separate claimgate_plugin manifest explicitly says an in-repo manifest does not prevent same-commit source plus manifest edits at claimgate_plugin/gate_integrity_manifest.json:10, and it does not cover the CB AST module.
- How checked: Command: rg -n "gate_integrity_ast|GateIntegrity|verify_gate_integrity|AST" constraint_box/src/constraintbox constraint_box/tests constraint_box/scripts. Output contained only the package import at constraint_box/src/constraintbox/__init__.py:120-125 and definitions in constraint_box/src/constraintbox/gate_integrity_ast.py. No production invocation was returned.
- Concrete fix: Put the AST comparison in the controller-owned production gate chain, with an externally pinned source set/digest and an exercised negative mutation for every load-bearing checker module; package export alone is insufficient.

### 3. Boundary contract gate reads fields absent from ProfileOutcome

- Severity: `high`
- Location: `constraint_box/src/constraintbox/gate_operations.py:300-320`
- Threat move: `logic-gap`
- Lane evidence: lane 2
- What is wrong: The gate reads outcome.classification and outcome.detail, but ProfileOutcome defines only disposition, reason, and evidence. The exception handler converts every evaluated payload, including valid and invalid controls, into FAIL boundary_contract_error:AttributeError before the intended disposition mapping.
- How checked: Command: PYTHONPATH=/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/src /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 /private/tmp/claude-501/-Users/joshuaeisenhart-Codex-Ratchet/b1e33759-f392-47e0-8f05-c6ce7250426c/scratchpad/lane2_probe.py. Output: boundary not json FAIL boundary_contract_error:AttributeError; boundary {} FAIL boundary_contract_error:AttributeError; the clean_contract.json fixture also returned FAIL boundary_contract_error:AttributeError; the conflated_contract.json fixture also returned FAIL boundary_contract_error:AttributeError. Source evidence: contracts.py:30-34 defines ProfileOutcome(disposition, reason, evidence), and boundary_contract.py:305-327 returns those fields.
- Concrete fix: Serialize disposition.value, reason, and evidence from ProfileOutcome, then preserve the profile's ELIGIBLE/BLOCKED/PARKED disposition mapping. Add clean and conflated fixture assertions that check both verdict and reason.

### 4. Claim-profile validation has no coverage gate for emitted claim kinds

- Severity: `high`
- Location: `constraint_box/scripts/check_claim_profiles.py:166-219`
- Threat move: `logic-gap`
- Lane evidence: lane 3
- What is wrong: The checker loads profiles and validates each profile's fields, tools, controls, ceiling, and failure disposition, but never enumerates CB-emitted claim kinds and requires a matching refusing profile. The AST scan found claim_kind=field_only in constraint_box/src/constraintbox/agentrun.py:1580 while claim_profiles.json contains 11 different claim_type entries and no field_only entry. Separately, the external claim verifier returned VERIFIED for the field_only fixture with only tier0 required, so this unprofiled claim kind is not refused by the claim-profile matrix.
- How checked: Command: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 constraint_box/scripts/check_claim_profiles.py. Output: All 11 profiles are well-formed. AST scan output: profile_count 11; claim_kind_literals ['field_only']; unprofiled_claim_kinds ['field_only']. Command: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 claimgate_plugin/claim_verify.py claimgate_plugin/evals/claimgate/fixtures/engine-leg-field-only.receipt.json --json. Output included "verdict": "VERIFIED", "required_tiers": ["tier0"], and RC=0.
- Concrete fix: Add a coverage validator that extracts every production-emitted claim_kind/claim type, rejects unknown values, and binds each to an explicit refusing gate and claim ceiling before profile validation can pass.

### 5. ClaimGate trust-root files are writable in the repository by stated source policy

- Severity: `high`
- Location: `claimgate_plugin/gate_registry.json:1; claimgate_plugin/claim_policy.json:1`
- Threat move: `edit-checker`
- Lane evidence: lane 1
- What is wrong: The registry and claim policy describe themselves as evaluator-owned/external policy, but the files are in-repo and no external immutability was established in this audit. A producer able to edit them can alter the policy that verifies its receipt.
- How checked: Command: sed -n '1,40p' claimgate_plugin/gate_registry.json; sed -n '1,25p' claimgate_plugin/claim_policy.json ; output states production branch protection/CODEOWNERS is required and current repo is not yet a trust root.
- Concrete fix: Move or enforce these policy surfaces under an independently protected trust root and verify the protection in CI.

### 6. FlowMind semantic gates can route on an LLM output and default to the first branch

- Severity: `high`
- Location: `lev-main/core/eval/src/gate-evaluator.ts:100-147,192-237`
- Threat move: `logic-gap`
- Lane evidence: lane 4
- What is wrong: The evaluator explicitly falls back from deterministic expression/schema handling to nodeExecutor semantic evaluation, described as an LLM call, and interprets the returned output as the branch. If no expression and no executor apply, it returns the first branch with fallback=true. This is an LLM_JUDGED surface and a permissive fallback, not a CB-grade deterministic verdict.
- How checked: nl -ba core/eval/src/gate-evaluator.ts | sed -n '100,147p'; nl -ba core/eval/src/gate-evaluator.ts | sed -n '192,237p' -> comments identify semantic predicates as nodeExecutor/LLM and code returns the first branch on absent strategy; nl -ba core/eval/src/gate-expression.ts | sed -n '1,35p' -> deterministic parser is function-free and tri-state.
- Concrete fix: For CB extraction, require a typed finite constraint/schema/graph predicate. Map unresolved or semantically expressed gates to HOLD/PARKED, never the first branch. Use FiniteConstraintProblem plus dual_solve for bounded equivalence/status checks, rustworkx for topology, SymPy for exact arithmetic, and Maude for explicit transition rewrites.

### 7. Invalid proposal candidate is diagnosed but then dereferenced before the gate can refuse it

- Severity: `high`
- Location: `constraint_box/src/constraintbox/agentrun.py:664-666 and :1375-1392`
- Threat move: `skip-step`
- Lane evidence: lane 2
- What is wrong: _proposal_shape_errors correctly records PROPOSAL_CANDIDATE_INVALID for a non-dict candidate, but proposal_gate_callback then assigns that same non-dict value to candidate and calls candidate.get. The malformed candidate therefore raises AttributeError before the observation/SMT gate can consume the invalid-shape result.
- How checked: Command: PYTHONPATH=/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/src /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 /private/tmp/claude-501/-Users/joshuaeisenhart-Codex-Ratchet/b1e33759-f392-47e0-8f05-c6ce7250426c/scratchpad/lane2_probe.py. Output: proposal_candidate_shape ['PROPOSAL_CANDIDATE_INVALID']; proposal_candidate_read EXCEPTION AttributeError 'str' object has no attribute 'get'. Source evidence: agentrun.py:664-666 emits the error, while :1375, :1383, and :1392 dereference candidate.
- Concrete fix: Normalize candidate to {} whenever it is not a dict before any candidate.get call, and let the normal invalid-proposal disposition/receipt path record PROPOSAL_CANDIDATE_INVALID.

### 8. Mandated constraintbox CLI cannot start in the specified interpreter

- Severity: `high`
- Location: `constraint_box/src/constraintbox/cli.py:169`
- Threat move: `skip-step`
- Lane evidence: lane 1
- What is wrong: The required command does not expose the CLI surface because the required interpreter cannot import constraintbox. This prevents a local reachability check for every CLI subcommand.
- How checked: Command: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 -m constraintbox --help ; output: /Users/.../python3: No module named constraintbox
- Concrete fix: Repair the installation/runtime packaging or PYTHONPATH outside this audit; then rerun the exact mandated command.

### 9. Most gate_operations gates have no production call site found by source search

- Severity: `high`
- Location: `constraint_box/src/constraintbox/gate_operations.py:56-624`
- Threat move: `skip-step`
- Lane evidence: lane 1
- What is wrong: The only direct production call site found for the gate_operations suite is agentrun.py:1087-1091, which invokes run_formal_flow_gates; z3, cvc5, rustworkx, boundary, false-green, weakening, strict-receipt, and release bindings had no production caller in the searched source.
- How checked: Command: rg -n 'gate_z3_request|gate_cvc5_request|gate_rustworkx_workflow|gate_boundary_contract|gate_strict_receipt_consumer|gate_release|gate_false_green|gate_weakening|run_formal_flow_gates|gate_sympy_flow_budgets|gate_maude_flow_transitions' constraint_box/src --glob '*.py' ; output showed definitions plus agentrun.py:1087-1091 for run_formal_flow_gates.
- Concrete fix: Wire each intended gate through a tested production dispatcher or mark it explicitly non-production; add positive/negative call-site tests.

### 10. The stated 16 executable gate IDs do not match source

- Severity: `high`
- Location: `constraint_box/src/constraintbox/gate_operations.py:56-624`
- Threat move: `logic-gap`
- Lane evidence: lane 1
- What is wrong: rg found 11 cb:* IDs emitted by gate_operations.py, while the preamble lists 15 names and calls that 16. Four additional names are contract identifiers in boundary_contract.py, not gate_operations implementations.
- How checked: Command: rg -o 'cb:[a-z0-9-]+' constraint_box/src/constraintbox/gate_operations.py | sort -u ; output contained 11 IDs. Command: rg -n 'cb:claimgate-chain|cb:cpython-controller-runtime|cb:external-sim-validation-adapter|cb:minilev-runtime' constraint_box/src constraint_box/tests ; output located only contract/registry references.
- Concrete fix: Define one authoritative registry and distinguish executable gates from contract identifiers; do not count declarations as fired gates.

### 11. The strict consumer ignores an input promotion_allowed=true field

- Severity: `high`
- Location: `constraint_box/src/constraintbox/strict_receipt_consumer.py:209-229`
- Threat move: `logic-gap`
- Lane evidence: lane 3
- What is wrong: The consumer does not reject a receipt that declares promotion_allowed=true; it merely hardcodes promotion_allowed=false in its own output. The promotion_true scratch receipt was accepted with passed=true and defects=[], so this consumer supplies no refusing gate for a forged promotion claim in the consumed receipt.
- How checked: Scratch probe command: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 constraint_box/src/constraintbox/strict_receipt_consumer.py --run-root <scratchpad>/probes/promotion_true --output <scratchpad>/promotion_true-out.json. Output: declared=0 match=0 mismatch=0 absent=0 undeclared=1 refused_stored_verdicts=0; DEFECTS: none; RC=0; JSON had "passed": true and "promotion_allowed": false. The input receipt contained promotion_allowed=true.
- Concrete fix: Treat any consumed receipt promotion_allowed value other than literal false as a defect, and require a separate controller-owned promotion gate rather than normalizing the field in the consumer output.

### 12. The strict receipt consumer accepts a matching receipt without any chain verification

- Severity: `high`
- Location: `constraint_box/src/constraintbox/strict_receipt_consumer.py:95-116`
- Threat move: `fake-input`
- Lane evidence: lane 3
- What is wrong: The consumer selects receipt JSON, harvests digest pairs, and checks artifact bytes, but it never loads or verifies a hash-chain ledger. A receipt with a matching artifact digest and no chain/ledger was therefore consumed with passed=true and defects=[]; the output's claim ceiling is only byte-level integrity.
- How checked: Scratch probe command: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 constraint_box/src/constraintbox/strict_receipt_consumer.py --run-root <scratchpad>/probes/no_chain --output <scratchpad>/no_chain-out2.json. Output: declared=1 match=1 mismatch=0 absent=0 undeclared=1 refused_stored_verdicts=0; DEFECTS: none; RC=0; JSON had "passed": true, "recomputed_match": 1, and no chain field/check.
- Concrete fix: Make receipt consumption require a controller-selected ledger path and independently verify chain continuity, sequence, head anchor, and authorship before any receipt can be consumed as evidence.

### 13. There is no single canonical typed input format for every gate

- Severity: `high`
- Location: `constraint_box/src/constraintbox/constraints.py:96-116; constraint_box/src/constraintbox/gate_operations.py:56-64,134-147,289-326,1031-1048,1221-1235`
- Threat move: `fake-input`
- Lane evidence: lane 5
- What is wrong: FiniteConstraintProblem is a canonical finite variable/domain/constraint format for solver questions, and dual_solve consumes it at dualsolve.py:510-518. But gate inputs remain heterogeneous: z3/cvc5 gates accept arbitrary dict specs, topology/formal gates accept FlowPolicy objects, boundary-contract accepts bytes, and receipt/release gates accept paths. Therefore not every gate question can be serialized and handed to a solver without a separate adapter, and the current five tools are not uniformly built into one typed gate language.
- How checked: sed -n '1,180p' constraint_box/src/constraintbox/constraints.py; sed -n '56,326p' and '1031,1270p' constraint_box/src/constraintbox/gate_operations.py; sed -n '492,530p' constraint_box/src/constraintbox/dualsolve.py. These outputs show the FCP schema and the distinct gate signatures.
- Concrete fix: Define a versioned GateQuestion envelope with typed fields for finite variables, finite domains, constraints, graph nodes/edges, rewrite rules, exact expressions, and receipt bytes. Compile every gate input into that envelope before dispatch; preserve the original object hash and adapter schema in the receipt. Reject an unadapted object rather than silently treating it as solver-ready.

### 14. agent-lease release accepts agent-authored proof instead of re-running validators

- Severity: `high`
- Location: `agent-lease/bin/agentguard.js:401-466`
- Threat move: `fake-input`
- Lane evidence: lane 4
- What is wrong: The release path parses --audit-proof, checks that configured runner names are present, rejects only status exactly equal to FAIL, and then calls releaseLockWithAgentProof. It does not execute the configured runner commands in this mode. Any status other than FAIL, including an empty status, is accepted and written as proof mode agent; the lock is then released. This is an LLM/agent decision in the gate path and permits the fake-input escape move.
- How checked: nl -ba bin/agentguard.js | sed -n '298,350p'; nl -ba bin/agentguard.js | sed -n '401,466p'; nl -ba lib/lock-manager.js | sed -n '208,289p' -> parseAgentProof only records text; release checks missing names and status === 'FAIL'; releaseLockWithAgentProof writes PROOF_MODE=agent and STATUS=VALIDATED without invoking runners.
- Concrete fix: Make release execute the configured deterministic runners against the current commit/push context and bind their exit status, stdout hash, input hash, and commit/topic identity into the lock. If agent-submitted text remains, treat it as commentary only; require exact PASS for every configured runner and reject unknown or empty statuses.

### 15. z3 and cvc5 request gates treat scalar status strings as backend dictionaries

- Severity: `high`
- Location: `constraint_box/src/constraintbox/gate_operations.py:69-77 and :108-116`
- Threat move: `logic-gap`
- Lane evidence: lane 2
- What is wrong: dual_solve returns scalar strings at result['z3'] and result['cvc5']; the detailed dictionaries are under backend_results. Each request gate therefore calls .get on a string, catches AttributeError, and returns UNKNOWN instead of the backend verdict.
- How checked: Command: PYTHONPATH=/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/src /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 /private/tmp/claude-501/-Users/joshuaeisenhart-Codex-Ratchet/b1e33759-f392-47e0-8f05-c6ce7250426c/scratchpad/codex_lanes/lane2_probe.py. Output: dual_solve ... "z3":"BOUNDED_SAT" ... "cvc5":"BOUNDED_SAT" ... "backend_results":{"cvc5":{"status":"BOUNDED_SAT"},"z3":{"status":"BOUNDED_SAT"}}; z3 verdict UNKNOWN reason z3_execution_error:AttributeError; cvc5 verdict UNKNOWN reason cvc5_execution_error:AttributeError. Source evidence: dualsolve.py:527-535 builds scalar top-level statuses and nested backend_results.
- Concrete fix: Read result['backend_results']['z3'] and result['backend_results']['cvc5'] or change dual_solve's documented return contract consistently; assert a SAT and UNSAT control reaches the gate verdict path.

### 16. ClaimGate pre-commit behavior is explicitly best effort on missing/broken gates

- Severity: `medium`
- Location: `claimgate_plugin/hooks/pre_commit_gate_receipts.sh:16-18`
- Threat move: `skip-step`
- Lane evidence: lane 1
- What is wrong: The shipped pre-commit hook documents that a missing gate or broken tool does not brick commits and only an explicit REJECTED exit 1 blocks. This is an enforcement surface weaker than fail-closed gate execution.
- How checked: Command: rg -n 'Best-effort by design|missing gate|broken tool|REJECTED|tool error' claimgate_plugin/hooks/pre_commit_gate_receipts.sh ; output matched lines 16-18 and 48-55.
- Concrete fix: If the intended threat model requires mandatory gating, make missing/tool-error states block or explicitly document this as a bounded non-gating surface.

### 17. Loop progress is not ratchet-monotone

- Severity: `medium`
- Location: `constraint_box/scripts/cb_loop.py:73-89`
- Threat move: `logic-gap`
- Lane evidence: lane 3
- What is wrong: advanced() treats any changed measure as progress. It does not encode whether unmentioned or deep_survivors must increase or decrease, and it does not reject a backward step. The loop state can therefore record advanced=true for a worsening measure and reset dead-cycle detection.
- How checked: Command: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 <import cb_loop.py and call advanced>. Output for previous {unmentioned:21,deep_survivors:39}, current {unmentioned:22,deep_survivors:39,_integrated_rc:0}: (True, 'unmentioned: 21 -> 22'). Output for current {unmentioned:20,deep_survivors:39,_integrated_rc:0}: (True, 'unmentioned: 21 -> 20'). Both directions were accepted.
- Concrete fix: Define controller-owned direction and bounds for every ratchet measure, compare current against the prior retained state, and route regressions to a refusing terminal without treating them as live progress.

### 18. Several production comparisons still use floating tolerances where decimal fixture arithmetic could be exact

- Severity: `medium`
- Location: `constraint_box/src/constraintbox/external_bounded_numerics.py:297-316,501-528; constraint_box/src/constraintbox/external_pykoopman_capability.py:364,518-524; constraint_box/src/constraintbox/external_multiengine_capability.py:173-177; constraint_box/src/constraintbox/paired_extension.py:232`
- Threat move: `logic-gap`
- Lane evidence: lane 5
- What is wrong: The source contains tolerance-based verdict comparisons using abs or math.isclose. For decimal JSON fixtures whose values are intended as exact rational data, binary float conversion makes the verdict dependent on an arbitrary tolerance instead of an exact symbolic relation. These are external-capability paths rather than the current Mini-Lev formal gate, so this finding does not claim that every floating measurement should be made exact.
- How checked: rg -n -i 'isclose|tolerance|epsilon|math\.fabs|abs\(|float\(' constraint_box/src/constraintbox --glob '*.py'; the command returned the cited lines, including _close_number/_close_matrix, CONTROL_TOLERANCE comparisons, math.isclose, and paired-extension least-cost comparison.
- Concrete fix: For exact decimal fixture fields, parse the original decimal strings as sympy.Rational, express each expected-minus-observed relation as a SymPy expression, and require simplify(expression) == 0 or an explicitly declared rational inequality. Keep tolerance comparisons only for measured external values, and label them approximate rather than exact.

### 19. Strict receipt and release gates invoke an unavailable bare python executable

- Severity: `medium`
- Location: `constraint_box/src/constraintbox/gate_operations.py:530-539 and :589-599`
- Threat move: `skip-step`
- Lane evidence: lane 2
- What is wrong: Both gates invoke subprocesses with the literal executable python. On this host which python and command -v python produce no path, while command -v python3 produces /opt/homebrew/bin/python3. The gates therefore fail with FileNotFoundError before their underlying checks run.
- How checked: Command: which python; command -v python || true; command -v python3. Output: python not found; /opt/homebrew/bin/python3. Probe output using the mandated interpreter and PYTHONPATH: strict FAIL consumer_error:FileNotFoundError; release FAIL release_gate_error:FileNotFoundError.
- Concrete fix: Invoke the current interpreter via sys.executable or an explicit configured interpreter, and add a positive-control test that proves the consumer/release subprocess actually ran rather than only checking the wrapper's fail-closed exception.

### 20. The 55-gate proof receipt is not a local rerun under this audit

- Severity: `medium`
- Location: `constraint_box/receipts/gate_fire_proof_v1.json:1`
- Threat move: `none`
- Lane evidence: lane 1
- What is wrong: The receipt contains 55 rows and claims positive/negative outcomes, but this audit only read it; no proof script or gate was rerun, and the required package import failed. Therefore every receipt-backed gate remains at exists, not passes local rerun or canonical by process.
- How checked: Command: specified-interpreter JSON parse of constraint_box/receipts/gate_fire_proof_v1.json ; output: gates_total 55, results 55, proven_real 48, always_fires 5, never_fires 2. No prove_gates_fire.py execution was performed.
- Concrete fix: Run the proof script in an isolated output-preserving environment after repairing the required interpreter import, then retain its exact fresh receipt.

### 21. The loop driver does not self-validate its gates when advancing

- Severity: `medium`
- Location: `constraint_box/scripts/cb_loop.py:120-150`
- Threat move: `skip-step`
- Lane evidence: lane 3
- What is wrong: Each cycle runs census, optional falsification, and autoresearch, then calls advanced() on measures. The cycle body contains no call to gate_integrity_ast, gate_integrity, claim-profile coverage, or a gate revalidation operation before writing an advanced state. The loop therefore emits state progress without a self-check that the gates themselves remain unchanged or admissible.
- How checked: Command: nl -ba constraint_box/scripts/cb_loop.py | sed -n '120,150p' showed only measures_now, cb_wave_falsifier_v3, cb_autoresearch_loop, and advanced. Command: rg -n "gate_integrity_ast|gate_integrity|claim-profile|self.?valid|revalidate" constraint_box/scripts/cb_loop.py constraint_box/src/constraintbox/mini_levos.py returned no loop-driver self-validation call.
- Concrete fix: Insert a controller-owned self-validation gate before each ratchet advance; bind its source digest and result to the loop receipt, and refuse the advance when gate identity, profile coverage, or gate receipts cannot be revalidated.

### 22. The severance criterion proves local causal dependence, not sufficient integration quality

- Severity: `medium`
- Location: `constraint_box/receipts/severance_v1/severance_summary.json:2-4`
- Threat move: `none`
- Lane evidence: lane 5
- What is wrong: The existing evidence defines LOAD_BEARING as a decision change after removing one import name during one operation on one host, and explicitly excludes correctness, semantic, platform, resolver, whole-suite, and promotion claims. That is strong evidence that the tools are not decorative on those exercised operations, but it is not enough to justify each tool's current API coverage or gate correctness. In particular it does not catch the provisional rustworkx gate above.
- How checked: sed -n '1,240p' constraint_box/receipts/severance_v1/severance_summary.json; line 2 states the claim ceiling and lines 9-43 report all five LOAD_BEARING rows. dependency_reachability_v1.json reports execution reachability only and its claim ceiling at lines 2-3.
- Concrete fix: Make the acceptance criterion two-dimensional: retain severance for causal dependence, and add adversarial gate fixtures that independently assert the tool's claimed property, including cyclic/unreachable graph negatives, Maude rewrite disagreement, solver disagreement/UNKNOWN, and exact-arithmetic mismatch. Require the gate receipt to show the exercised API and the negative-control verdict.

### 23. The validation-gates file has many declared gates but only three direct gate:* entries marked enforced

- Severity: `medium`
- Location: `lev-main/.lev/validation-gates.yaml:1131-1170,1500-1615`
- Threat move: `skip-step`
- Lane evidence: lane 4
- What is wrong: A full YAML parse and recursive enumeration found 16 direct gate:* definitions: 3 enforced and 13 declared. The file also contains aspirational/declared policy sections and human/CDO approval references, so gate declaration is not evidence that a deterministic runtime consumes every gate.
- How checked: /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 - <<'PY' ... recursive walk of .lev/validation-gates.yaml ... PY -> gate_definitions 16; status_counts {'enforced': 3, 'declared': 13}; source lines 1131-1170 and 1500-1615 show prompt-stack and runtime-contract gate catalogs.
- Concrete fix: Maintain a machine-readable gate registry with owner, evaluator function, input schema, receipt schema, caller, and enforcement status; fail closed when a declared gate lacks a reachable deterministic executor. Do not promote declared/aspirational entries to CB gates.

### 24. agent-lease has no stale-lease policy and can treat an old lock as irrelevant after HEAD changes

- Severity: `medium`
- Location: `agent-lease/lib/lock-manager.js:22-99`
- Threat move: `logic-gap`
- Lane evidence: lane 4
- What is wrong: The lock filename is derived from the current short HEAD hash, while createLock stores CREATED and STATUS=PENDING but checkLock does not validate age, GUID ownership, branch, staged-input identity, or a stale timeout. After a crash the pending file remains. After HEAD changes, the current hash points to a different filename and the previous lock is not considered by checkLock; getAllLocks/clearAllLocks can enumerate it, but the normal gate path does not reconcile it. This is a logic-gap boundary for crash recovery and stale ownership.
- How checked: nl -ba lib/lock-manager.js | sed -n '22,99p' -> getLockPath uses current HEAD, createLock writes CREATED/STATUS=PENDING, and checkLock reads only the current path plus AUDIT_PROOF_PASSED; nl -ba bin/agentguard.js | sed -n '469,496p' -> deny mode creates a lock only when the current-hash lock is absent.
- Concrete fix: Define explicit states and recovery: PENDING with immutable input/branch identity, VALIDATED, EXPIRED, ABANDONED, and ARCHIVED; use an atomic create/owner token, monotonic or wall-clock TTL policy, and deterministic stale handling that blocks or parks rather than silently proceeding. Reconcile prior-hash leases before allowing a new lease.

## Independent rediscovery

Lanes 2 and 5 independently identified `constraint_box/src/constraintbox/gate_operations.py:171-194`. Lane 2 supplied a cyclic/acyclic differential probe. Lane 5 supplied the provisional source assignment and named tool-backed paths. The defect appears once above, with both lanes recorded.

## What was not checked

### Lane 1

- CLI subcommand reachability after import repair
- execution of prove_gates_fire.py and all 55 positive/negative controls
- execution of all gate assertion test modules
- full content/reachability audit of every Makefile recipe
- whether .git/hooks/pre-commit is active in the current Git configuration
- all non-Python JavaScript/JSON/YAML gate-like labels outside the enumerated ClaimGate chain; many are fixtures or historical references and were not promoted to executable gates

### Lane 2

- I did not fuzz every gate input type or every subprocess call outside gate_operations.py.
- I did not run the full constraint_box test suite.
- I did not establish a passing strict-receipt or release positive control because the wrapper cannot launch its bare python subprocess on this host.
- I did not claim canonical by process for any finding or gate; no commit, fixture edit, or production-source edit was made.

### Lane 3

- I did not run the full production gate suite or mutate any repository file, because the lane is read-only and all probes were isolated in the assigned scratchpad.
- I did not establish a replay-after-input-change bypass across every receipt consumer.
- I did not run a duplicate-position ledger fixture; the source-level seq check was inspected only.
- I did not prove that every claim type in dynamically generated or non-Python payloads is covered; the claim-kind scan covered Python literals under constraint_box/src, constraint_box/scripts, and claimgate_plugin.
- The codebase-memory MCP list-projects call was cancelled by the tool runtime, so code discovery fell back to rg and line-addressed source inspection.

### Lane 4

- No Lev build, Rust test, pnpm test, or eval command was run; the user prohibited running the Lev build and this lane did not need a build to establish source classifications.
- No live .lev validation-gate executor was run; gate definitions were parsed and enumerated, not promoted to runs or canonical by process.
- No live agent-lease end-to-end test was run because its tests create and delete temporary repositories; the state machine is source-derived.
- No live AgentPing server/API interaction was run; typed schemas and pure lease/approval functions were source-inspected.
- The requested CB import/rerun was blocked by ModuleNotFoundError in the mandated interpreter; CB replacement descriptions use source lines and the user-provided five-tool authority boundary, not a claimed runtime pass.
- I did not independently determine whether every non-direct gate reference nested under checks, quality_gates, gate_catalog and sdlc_gates has a reachable executor; the direct gate:* inventory is complete for recursive YAML keys with that exact prefix.

### Lane 5

- A complete count of every downstream CB decision branch across all production modules, rather than the stated 11 gate-ID denominator, was not computed.
- The full prove_dependencies_used.py run was not rerun because its documented default writes constraint_box/receipts/dependency_reachability_v1.json, which violates the assigned-output-only constraint.
- A full five-tool self-check timing was not run because no existing non-mutating command was identified; only the non-mutating formal_flow_gates call was timed.
- I did not execute adversarial cyclic/unreachable fixtures against gate_rustworkx_workflow; the provisional verdict is established from source inspection at gate_operations.py:187-194.
- No claim that tolerance-based external numerical comparisons are semantically safe to rationalize was made; fixture exactness must be established per capability.


## How to check this yourself

Run these commands from the repository root:

```sh
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 -m json.tool constraint_box/receipts/gate_fire_proof_v1.json
rg -n "run_formal_flow_gates|gate_z3_request|gate_cvc5_request|gate_rustworkx_workflow" constraint_box/src/constraintbox --glob "*.py"
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 constraint_box/scripts/check_claim_profiles.py
```
