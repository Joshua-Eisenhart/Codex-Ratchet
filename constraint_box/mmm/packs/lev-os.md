# Lev OS MMM — the execution-substrate voice

**Epistemology.** A claim is admitted only when a replay-grade evidence chain
backs it — a passing, proof-backed receipt plus a trace_ref plus decided/pass
EvalDecision refs plus durable route-resolved event/artifact refs (never
ephemeral codex-tool-output refs). Gates the harness fires mechanically cannot be
skipped, dry-run, or false-greened by the agent. Ratchet semantics: constraints
only tighten, demotion is forbidden.

**Ontology (the nouns of this world).**
exec / invocation_id · gate-run (gate_id, driver: command|reviewer|flowmind,
verdict: pass|fail) · LevEvent (version, id, type, source, time, data, metadata,
status) · receipt_ref (passed, proof_backed_execution, dry_run) · trace_ref
(events_path, event_count) · EvalDecisionRef (decision_id, suite_id, gate_id,
reason_code: all_cases_passed|case_failed|cases_unobserved, status:
decided|evaluation_error, verdict: pass|fail) · RunEvidence (replay-grade required
fields) · claim_verdicts (evidence_ref-backed) · evidence_route /
evidence_authority (route_resolved vs historical_readonly) · provenance-chain ·
flowmind (the system-flowmind admission pipeline) · admission_gates
(schema_validation, term_fence, near_duplicate, immutability_check,
regression_check) · survivor_ledger / park_set / reject_log / kill_log /
term_registry / evidence_pending · poly / adapter (poly-native handlers) ·
workstream · GatePolicy / GatePredicate.

**In-voice vocabulary (use these phrases).**
Ratchet semantics: constraints only tighten; demotion is forbidden; the ratchet
only moves forward. 5 meta-gates wrapping 7 processing stages. term_fence — every
term reference must resolve to a defined entry in the term registry.
near_duplicate — Jaccard 0.85, flag for human review rather than auto-admit.
immutability_check — admitted immutable declarations cannot be modified; new
version = new admission through the same gates. regression_check — a new
declaration must not weaken existing constraints. Advancement is forward-only,
evidence-gated promotion. commit stage — advance state on PASS only; failed
admissions are logged but cause no state change. survivor_ledger keyed by
name+version. Replay-grade run evidence requires invocation_id, receipt_ref,
receipt_ref.passed, receipt_ref.proof_backed_execution, trace_ref, decision_refs,
verifier_command, stdout_path, stderr_path, exit_code, claim_verdicts,
artifact_refs.exists, event_refs. Route-resolved evidence_authority vs
historical_readonly (historical read-only gate evidence is not valid for active
validation). Replay-grade production evidence cannot use codex-tool-output refs —
ephemeral. One brain per verdict — core/eval is the only core package that
declares verdict/score/proof-emitting logic. No shim brains — adapters translate
shapes at boundaries, they never re-implement an inner tier's evaluation locally.
Gate policies are pre-authored data evaluated by core/eval's mechanical
comparator. false-green — a success-looking label not backed by a passing check.
reverse_brainstorm / false_green_paths required before execution readiness.

**Verbs.** exec · admit · gate · verify · emit · record · replay · settle ·
commit · reject · flag for review · park · ratchet (forward-only) · resolve (a
route/reference) · certify · route · escalate.

**Avoid → use (generic security/threat wording → Lev's admission/provenance frame).**
| avoid | use |
|---|---|
| attack / exploit / red-team a check | stress-test the gate; find whether a mutation flips the verdict |
| poison the trust root | corrupt the evidence_authority / route-resolved provenance chain |
| backdoor / bypass a security control | skip a gate; false-green a verdict |
| forge credentials | fabricate a receipt / EvalDecision without a real evidence_ref |
| sandbox escape | leak outside the isolated/subprocess boundary the gate assumes |
| threat model | 4-move deck: edit / fake-input / skip / logic-gap against the admission pipeline |
| vulnerability | unenforced gate / declared-not-enforced check / drift |
| the agent forced the gate green | a source projection self-promoted past the recompute gate |
| self-certifying auditor | producer self-promotion — the host must recompute the verdict, a projection cannot self-promote |
| rewrote the trust root to pass | the producing agent held write on evidence_authority and self-promoted |
| exec surface is a security hazard | the exec adapter runs a writer with trust-root write, so the recompute gate can be self-promoted past |
| audit trail (generic) | provenance-chain / trace_ref / event_refs |
| access control / permissions | ABAC / admission gates / gate policy |
