---
name: cb-goodhart-regime-cell
description: Split regressional, extremal, causal, and adversarial Goodhart checks without collapsing them into one proxy-risk score.
---

# Goodhart regime cell

`scripts/split_regimes.py` accepts an exact JSON payload bound to canonical
`operation_id` `cb-goodhart-regime-cell.v1` and a consistent nonempty
`target`/`target_id`. It preserves four-regime observations, refuses any
collapsed score or null/empty regime, and never selects a winner, activates a
route, promotes an artifact, calls a provider, or writes a file.
