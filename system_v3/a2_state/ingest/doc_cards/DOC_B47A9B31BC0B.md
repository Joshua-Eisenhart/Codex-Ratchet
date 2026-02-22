## PURPOSE
- "# PURPOSE"
- "BOOT_ID: BOOTPACK_THREAD_B_v3.5.2"

## HARD_FENCES
- "Each user message must be exactly one of:"
- "- AXIOM_HYP IDs must be structural-neutral."
- "- Count or construction words are forbidden in AXIOM_HYP IDs."
- "="
- "A newly ACCEPTED PROBE_HYP must be referenced by at least one ACCEPTED SPEC_HYP"
- "Default: SIM_EVIDENCE SIM_ID must equal the target ID to kill."
- "Thread B never runs simulations."
- "- Not forbidden; forbidden as primitive use until CANONICAL_ALLOWED via term pipeline."
- "RULE BR-0D1 DERIVED_ONLY_SCAN (HARD, DETERMINISTIC)"
- "RULE BR-0D2 DERIVED_ONLY_PERMISSION (HARD)"
- "No permanent forbidden words."
- "RULE EV-000 SIM_SPEC_SINGLE_EVIDENCE (HARD)"
- "A SPEC_HYP whose SPEC_KIND is SIM_SPEC must include exactly one:"
- "Functionals do not define truth; they provide measurements."
- "# EXPLICITLY FORBIDDEN ASSUMPTIONS"
- "All future axes must be defined using only admitted structures."
- "All future constructions MUST respect this stratification."
- "Cross-stratum back-dependence is forbidden."
- "Functionals measure. They do not select."
- "# FORBIDDEN GLOBAL ASSUMPTIONS"

## CONTAINERS
- BEGIN: BOOTPACK_THREAD_B v3.5.2, EXPORT_BLOCK vN, SIM_EVIDENCE v1, THREAD_S_SAVE_SNAPSHOT v2, EXPORT_BLOCK v1, EXPORT_BLOCK v2, EXPORT_BLOCK v3, EXPORT_BLOCK v4, EXPORT_BLOCK v5, EXPORT_BLOCK v6, EXPORT_BLOCK v7, EXPORT_BLOCK v8, REPORT
- END: EXPORT_BLOCK vN, SIM_EVIDENCE v1, THREAD_S_SAVE_SNAPSHOT v2, BOOTPACK_THREAD_B v3.5.2, SIM_EVIDENCE, EXPORT_BLOCK v1, EXPORT_BLOCK, EXPORT_BLOCK v2, EXPORT_BLOCK v3, EXPORT_BLOCK v4, EXPORT_BLOCK v5, EXPORT_BLOCK v6, EXPORT_BLOCK v7, EXPORT_BLOCK v8, REPORT
- REQUIRED_FIELDS: BOOT_ID, AUTHORITY, ROLE, MODE, STYLE, DEFAULT_FLAGS, EXPORT_ID, TARGET, PROPOSAL_TYPE, CONTENT, SIM_ID, CODE_HASH_SHA256, OUTPUT_HASH_SHA256, METRIC, SURVIVOR_LEDGER, PARK_SET, TERM_REGISTRY, EVIDENCE_PENDING, PROVENANCE, TERM_DRIFT_BAN, INIT SURVIVOR_LEDGER, INIT PARK_SET, INIT TERM_REGISTRY, INIT EVIDENCE_PENDING, INIT ACCEPTED_BATCH_COUNT, INIT UNCHANGED_LEDGER_STREAK, AXIOM_HYP, PROBE_HYP, SPEC_HYP_ACTIVE, SPEC_HYP_PENDING_EVIDENCE

## ALLOWED_SPEC_KINDS
- TERM_DEF
- LABEL_DEF
- MATH_DEF
- CANON_PERMIT
- SIM_SPEC
- SPEC_BIND
- ASSUMPTION_SET

## FORBIDDEN_PRIMITIVES
- "- Count or construction words are forbidden in AXIOM_HYP IDs."
- "2.5) DERIVED-ONLY TERM GUARD (v3.5.2)"
- "- Set of TERM_LITERAL strings treated as “derived-only primitives”."
- "- Not forbidden; forbidden as primitive use until CANONICAL_ALLOWED via term pipeline."
- "If a derived-only literal t appears in any line outside the allowed contexts above:"
- "No permanent forbidden words."
- "Functionals do not define truth; they provide measurements."
- "# EXPLICITLY FORBIDDEN ASSUMPTIONS"
- "Cross-stratum back-dependence is forbidden."
- "Functionals measure. They do not select."
- "# FORBIDDEN GLOBAL ASSUMPTIONS"

## ROLE_IN_SYSTEM
- A2: "STRATUM A2 — STATE SPACES"
- A1: "STRATUM A1 — STRUCTURAL CARRIERS"
- A0: "ROLE: A0"
- B: "(B) ARTIFACT_MESSAGE:"

## OPEN_QUESTIONS
- NONE_MARKED_OPEN
