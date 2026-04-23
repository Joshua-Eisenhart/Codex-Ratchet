# SYSTEM_UPGRADE_PLAN_EXTRACT_PASS8

STATUS: EXTRACTION ONLY
MODE: VERBATIM / DENSE AGGREGATION
NOTE: NO SYNTHESIS, NO FIXES

---

SECTION: A1 MODES AND LLM FAILURE VECTORS

- A1 modes discussed as REAL behavioral constraints, not labels.
- Modes explicitly tied to:
  - hallucination
  - drift
  - smoothing
  - narrative bias
  - helpfulness bias
- Mode changes are NONCOMMUTATIVE.
- System intent is to make mode changes explicit and detectable.
- Deterministic enforcement of mode change may not be possible.
- Confirmation of mode change is required even if deterministic enforcement fails.
- Mode control described metaphorically as “horse reins.”

AMBIGUITIES / UNRESOLVED:
- Whether deterministic confirmation of mode change is achievable.
- How many retries allowed for failed mode change.
- Whether mode confirmation is binary or graded.

CONFLICTS:
- Desire for deterministic guarantees vs acknowledgment that LLM mode control may remain probabilistic.

UNSPECIFIED — DO NOT INFER

---

END OF PASS 8
