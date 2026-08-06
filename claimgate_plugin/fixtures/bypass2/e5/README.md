# E5 — nested input yields no disposition

- Should happen: every accepted input yields a disposition and a ledger line,
  or is rejected before evaluation.
- Current behavior: a 4006-byte well-formed input yields neither.
- Exact reach: `ConstraintBoxController.run()` line 309 calls
  `profile.evaluate()` with no exception handling, while the three sibling
  paths at lines 264, 277 and 295 each build a `DecisionRecord`;
  `intake.parse_json_value` catches only `UnicodeDecodeError` and
  `json.JSONDecodeError`.
- Distinctness: no existing fixture reaches `controller.run()` at all — e1
  fires the hook chain, e2 the estate CLI, e3 estate-parity, e4 the lease
  helpers.

The fixture compares a depth-200 control with a depth-2000 input for all three
profiles. It records the current gap; it does not close it.
