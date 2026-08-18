---
name: cb-strategy-portfolio-cell
description: Emit direct, alternative, reframe, back, wildcard, and stop strategy proposals without ranking or selecting one.
---

# Strategy portfolio cell

`scripts/portfolio.py` accepts an exact JSON card with canonical `operation`
and `operation_id` (both `cb-strategy-portfolio-cell.v1`), a nonblank
`target`, and all six required branches: `direct`, `alternative`, `reframe`,
`back`, `wildcard`, and `stop`. Unknown or case-variant keys refuse. Branches
must remain distinct, or use exact `{proposal,distinguisher}` objects to make
otherwise equal proposals explicit.

The deterministic output schema is `constraintbox.strategy-portfolio.v1`.
It is a proposal-only portfolio: it contains no winner, ranking, vote,
authority, activation, or promotion decision.  Missing branches hold;
authority-shaped or malformed input is refused structurally.  All receipts
carry canonical target/operation bindings, a claim ceiling,
`promotion_allowed: false`, `writes_performed: false`, and a self-digest.
