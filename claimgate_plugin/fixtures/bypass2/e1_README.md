# E1 — prose-only quantitative claim

This canonical-looking receipt puts its only quantitative assertion in English
prose and contains no numeric JSON scalars or wholly numeric strings.

- Should happen: the claim should require evidence and be refused or parked.
- Current behavior: `post_receipt_gate.sh` records `PASS`; `claim_verify.py`
  reports `VERIFIED`.
- Exact reach: `claim_policy_gate._numbers_in_claim_positions()` walks JSON
  scalar shape, and `claim_policy_gate.evaluate()` treats zero detected numbers
  plus zero declared engines as exempt. The fired hook does not invoke
  `receipt_grammar.py`, whose typed `claim` role would park prose.

This fixture captures the world/receipt mismatch. It does not close it.
