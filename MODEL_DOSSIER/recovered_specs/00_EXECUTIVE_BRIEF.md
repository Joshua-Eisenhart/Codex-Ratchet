# Executive Brief

**ClaimGate** is trust infrastructure for AI-generated work.

The first wedge is a GitHub-native PR trust gate:

```text
AI or human opens a PR
→ ClaimGate extracts/validates the claim
→ deterministic gates check scope, evidence, falsifiers, reruns, hashes, and overclaims
→ wide LLM lanes propose better claims/tests/falsifiers at the gates
→ gates decide admission
→ receipts preserve the decision
→ GitHub required checks can block merge
```

The product is deliberately concrete. It does not sell Free Energy Principle, QIT, political theory, personality theory, or an AI OS. Those are internal sources of design pressure. The product promise is:

> Don’t merge AI code on vibes. Require claims, evidence, falsifiers, and receipts.

## Why now

AI coding tools make plausible PRs cheap. Human trust, evidence, and accountability become the bottleneck.

Existing tools review code, run static analysis, or orchestrate agents. ClaimGate governs whether the PR's **claim** is allowed to count.

## Design inputs

- deterministic gates, finite witness discipline, process order,
  anti-flattening, graveyard/receipt logic;
- graph/event/receipt surfaces, lifecycle routing, and product execution.

## First deliverable

A dependency-free CLI + GitHub App scaffold that blocks or admits PRs based on claim cards and effect envelopes.
