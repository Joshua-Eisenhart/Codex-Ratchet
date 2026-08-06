# Hostile Test Matrix

| ID | Attempt | Expected |
|---|---|---|
| H01 | duplicate JSON key | `BLOCKED` |
| H02 | `NaN`/Infinity | `BLOCKED` |
| H03 | array root where object required | `BLOCKED` |
| H04 | unknown task supplies `profile_id` | `BLOCKED` |
| H05 | proposal contains nested `verdict` under `digest` | `BLOCKED` |
| H06 | proposal supplies command/tolerance/promotion | `BLOCKED` |
| H07 | worker source digest changed | `BLOCKED` |
| H08 | worker exits nonzero | `BLOCKED` |
| H09 | worker times out | `PARKED` |
| H10 | output artifact missing/malformed | `BLOCKED` |
| H11 | NumPy claim mismatches independent recomputation | `BLOCKED` |
| H12 | reduction order changes result | `PARKED` |
| H13 | finite state count exceeds bound | `PARKED` |
| H14 | Z3 missing or returns unknown | `PARKED` |
| H15 | prune branch with nonempty fibre | refused |
| H16 | merge branches with different continuation outcomes | refused |
| H17 | merge has no active probes | refused |
| H18 | empty Ratchet demand | `HOLD` |
| H19 | candidate probe contracts differ | `HOLD` |
| H20 | candidates lack verified nest | `HOLD` |
| H21 | mutate transition to break quotient congruence | witness returned |
| H22 | mutate ledger record | verification fails |
| H23 | complex path amplitudes cancel | histories remain stored |
| H24 | diagonalize history-pair field | off-diagonal loss is measurable |

The initial automated suite covers H01–H07, H11–H24 except an actual Z3 run.
H08–H10 need additional worker fixtures before the capability profile can be
called mature.
