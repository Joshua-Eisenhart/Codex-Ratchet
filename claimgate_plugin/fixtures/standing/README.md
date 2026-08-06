# Producer-standing fixtures

These synthetic ledgers use the real `claimgate_gate_ledger_v1` key names, but
they intentionally do not carry valid hash chains. `producer_standing.py`
parses outcome records and does not verify ledger chaining; chain verification
belongs to `gate_ledger.py`.
