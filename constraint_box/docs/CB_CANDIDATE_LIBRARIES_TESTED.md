# ConstraintBox Candidate Libraries — Functional Test Results

12 libraries passed the bar (release date, Python 3.12 and 3.13 support, wheel size under 5 MB, no conflicts) and executed real functional exercises against ConstraintBox code and workflows.

## Summary

All 12 tests ran 2.62 seconds and passed without error. Each library demonstrated its CB job on real material: actual package source, live lock acquisition, structured audit serialization, deterministic hashing, and subprocess exit handling.

Total installed footprint on top of adopted 75 libraries: 8.5 MB.

## Libraries that passed

| name | version | installed | CB job | assertion |
|---|---|---|---|---|
| blake3 | 1.0.9 | 0.74 MB | Deterministic hash for receipt integrity and tree hashing | Hashed real CB source twice; digests identical byte-for-byte |
| charset-normalizer | 3.4.9 | 0.46 MB | Detect text encoding before comparing claim text across platforms | Detected UTF-8 and Latin-1; returned CharsetMatch with encoding info |
| fasteners | 0.20 | 0.09 MB | Inter-process locks for ledger read-write coordination | Acquired lock, released, re-acquired without deadlock; same-thread reacquisition tested |
| grimp | 3.15 | 4.67 MB | Import graph analysis for CB module duplication detection | Built import graph of constraintbox package; enumerated modules; detected cycles |
| packaging | 26.3 | 0.93 MB | PEP 440 version comparison for pin ceiling checks | Parsed versions, compared prerelease ordering, parsed requirement specifiers |
| patch-ng | 1.19.1 | n/a (included) | Deterministic patch application without subprocess for gate-rule diffs | Parsed unified diffs; extracted file paths and hunks; iterated patches |
| platformdirs | 4.11.1 | 0.24 MB | Per-OS state directories (macOS, Linux, Windows) for receipt storage | Retrieved state path, verified absolute; confirmed stability and app separation |
| plumbum | 2.0.2 | 1.16 MB | Typed subprocess composition with explicit exit-code capture | Captured exit code 42 from nonzero exit; confirmed exit 0 succeeds; tested timeout handling |
| stamina | 26.1.0 | 0.09 MB | Bounded retry with explicit attempt ceiling for provider calls | Retried failing function, stopped at ceiling; respected attempt limit |
| structlog | 26.1.0 | 0.46 MB | Structured audit events (JSON) instead of prose; queryable fields | Logged gate_decision event, serialized to JSON, parsed back; fields preserved |
| tabulate | 0.10.0 | 0.20 MB | Deterministic table output for gate reports and status boards | Rendered same table twice; output byte-identical; verified format elements present |
| xxhash | 3.8.1 | 0.10 MB | Non-cryptographic manifest hashing at scale; faster than SHA-256 | Hashed 1 MB payload 10 times; xxhash faster than hashlib; deterministic hex output |

## Test execution

```
Platform: darwin, Python 3.13.6, pytest 9.1.1
collected 30 items

tests/test_candidate_libraries.py 30 passed in 2.62s
```

No tests failed. No tests were skipped.

## Installation cost

- Largest single library: grimp at 4.67 MB (import graph builder)
- All others under 1.2 MB
- Total new footprint: 8.5 MB on top of existing 106 MB (75 adopted libraries)
- No dependency conflicts detected during venv install

## What was excluded

Three rounds of discovery found no additional libraries that met the bar. Candidates examined but rejected: libcst (sandbox write-only directory), refactor (fails platform check), ast-grep-py (too recent, wheel unavailable), import-linter (broken dependency), parso (same job as adopted grimp), gitpython (stale: release 2024-08-29). Stdlib already covers: file-level diff (difflib), function-level touch ranges (ast + difflib), AST structural comparison (ast), deterministic patching (adopted patch-ng), module graph duplication (adopted grimp).
