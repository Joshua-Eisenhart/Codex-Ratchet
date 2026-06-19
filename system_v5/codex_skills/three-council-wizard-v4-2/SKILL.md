---
name: three-council-wizard-v4-2
description: Legacy/provenance only. Do not use for current Wizard work; current Wizard is v4.3. Load only when the user explicitly asks to inspect historical v4.2 packet behavior, receipts, or migration evidence.
---

# Legacy Wizard v4.2 — provenance only

Current rule: **do not run v4.2 as Wizard**. Wizard is v4.3.

This skill is retained only so old receipts, old packet docs, and historical audits can be interpreted without rewriting history. It is not an active runtime, not a fallback, and not a post-v4.3 handoff step.

Use this file only when the current user request explicitly asks for:

- historical v4.2 receipt interpretation;
- migration comparison between old v4.2 packet surfaces and v4.3;
- cleanup of stale v4.2 docs without treating them as runnable.

If current work needs Wizard behavior, load `three-council-wizard-v4-3` and the v4.3 repo validator instead.
