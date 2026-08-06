# E6 — equivalent Unicode keys survive the duplicate-key guard

- Should happen: two spellings a normalising reader cannot tell apart should
  not both survive a guard whose ceiling claims the snapshot is unambiguous.
- Current behavior: both survive; `canonical_json` emits both.
- Exact reach: `intake.parse_json_value`'s `no_duplicates` object-pairs hook
  compares keys with Python string equality, and `canonical_json` sorts and
  emits the resulting dict unchanged.
- Distinctness: this is the duplicate-key guard in `intake.py`. It is NOT the
  separate registered row about `AgentProposalProfile` matching reserved key
  names by exact membership after `casefold()` — that row is already recorded
  and is a different function.

The fixture builds NFC and NFD spellings at runtime and includes an identical-key
control. It records the current gap; it does not close it.
