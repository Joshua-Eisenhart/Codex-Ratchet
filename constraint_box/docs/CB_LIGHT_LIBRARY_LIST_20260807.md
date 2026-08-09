# CB LIGHT — THE COMPLETE PYTHON LIBRARY LIST

Every library laid out for ConstraintBox light across this session, by
tier and job. `env` = present in `~/.local/share/codex-ratchet/envs/main`.
`wired` = imported by `constraint_box/` source today.

---

## TIER 1 — CORE (load-bearing; CB cannot reach a verdict without these)

| # | Library | Job | env | wired |
|---|---|---|---|---|
| 1 | **z3-solver** | SMT decision, bounded satisfiability, erased controls | yes | yes |
| 2 | **cvc5** | independent second decider; AGREE or UNRESOLVED | yes | yes |
| 3 | **sympy** | exact symbolic recompute (ClaimGate R5 contract) | yes | yes |
| 4 | **rustworkx** | graph/DAG: cycles, topological order, reachability | yes | yes |
| 5 | **maude** | rewriting logic, state transitions, severance controls | yes | yes |

Declared in `pyproject.toml` as core dependencies. Enumeration (stdlib)
acts as the third decider beside z3 and cvc5.

## TIER 1b — DECLARED EXTRA, CONTROL-ONLY BY LAW

| # | Library | Job | env | wired |
|---|---|---|---|---|
| 6 | **numpy** | numeric convenience | yes | yes |

`three_engine_seal.py` hard-rejects numpy, scipy and mpmath as
`load_bearing`. They may compute; they may never seal.

## TEST TIER — dev closure only, never in the runtime closure

| # | Library | Job | env | wired |
|---|---|---|---|---|
| 7 | **hypothesis** | property-based adversarial input; a FINDER, frozen examples ship | yes | yes |
| 8 | **pytest** | harness | yes | no |
| 9 | **mutmut** | mutation testing — does the suite detect injected faults | no | no |

## TIER 2 — FORMAT AND CONTRACT

| # | Library | Job | env | wired |
|---|---|---|---|---|
| 10 | **msgspec** | strict receipt decode, typed errors (0.06 ms; 3 canaries refused) | yes | **no** |
| 11 | **jsonschema** | receipt contracts validated at write time | yes | **no** |
| 12 | **rfc8785** | JCS canonical JSON before hashing (9 KB, frozen spec) | no | no |
| 13 | **cel-python** | declarative gate rules as data, not code | no | no |
| 14 | **icontract** | pre/postconditions on gate functions | no | no |
| 15 | **beartype** | O(1) runtime type enforcement at CB boundaries | yes | **no** |

## TIER 2 — RANGE, UNITS, EXACTNESS (the constraint box itself)

| # | Library | Job | env | wired |
|---|---|---|---|---|
| 16 | **portion** | admissible-range membership; unfalsifiable-box detection (27 KB) | no | no |
| 17 | **pint** | units and dimensional consistency | no | no |
| 18 | **mpmath** | arbitrary precision — CONTROL-ONLY by the seal | yes | no |

## TIER 2 — CUSTODY, ATTESTATION, SIGNING

| # | Library | Job | env | wired |
|---|---|---|---|---|
| 19 | **pygit2** | lease tree hashing without subprocess (65x faster, identical id) | no | no |
| 20 | **cryptography** | receipt signing; the Lev authority seam | yes | **no** |
| 21 | **PyNaCl** | ed25519 alternative to cryptography | no | no |
| 22 | **in-toto** | supply-chain attestation: steps, materials, products, links | no | no |
| 23 | **securesystemslib** | in-toto's crypto layer | no | no |
| 24 | **filelock** | lease mutual exclusion (96 KB) | yes | **no** |
| 25 | **cyclonedx-python-lib** | SBOM per run, recorded in the receipt | no | no |

## TIER 2 — ARCHITECTURE, DEAD CODE, LINT

| # | Library | Job | env | wired |
|---|---|---|---|---|
| 26 | **import-linter** | ArchFence in Python: import contracts, layer boundaries | no | no |
| 27 | **grimp** | the import graph behind import-linter | no | no |
| 28 | **vulture** | dead-code / orphan detection (26 KB) | no | no |
| 29 | **ruff** | dev-tier determinism on the codebase | no | no |
| 30 | **tree-sitter** | multi-language scanning for boundary rules | no | no |

## TIER 2 — DIFF, HASH, STORE, SERIALIZE

| # | Library | Job | env | wired |
|---|---|---|---|---|
| 31 | **deepdiff** | structural receipt diffing: what changed, not just that it did | no | no |
| 32 | **blake3** | fast hashing of large artifact trees | no | no |
| 33 | **xxhash** | manifest-scale hashing, non-crypto — manifests ONLY, never receipts | yes | **no** |
| 34 | **lmdb** | crash-safe append-only ledger if sqlite proves insufficient (97 KB) | no | no |
| 35 | **orjson** | fast JSON where canonical form is not required | yes | **no** |
| 36 | **zstandard** | evidence-tree compression | no | no |
| 37 | **pyroaring** | compressed sets for tracked-set / orphan detection at scale | no | no |
| 38 | **jsonlines** | strict JSONL for ledgers — STALE (1070 days), stdlib replaces it | no | no |

## TIER 2 — ENVIRONMENT AND DEPENDENCY

| # | Library | Job | env | wired |
|---|---|---|---|---|
| 39 | **uv** | pinned resolution and lockfiles | no | no |
| 40 | **packaging** | PEP 440 version comparison | yes | no |
| 41 | **pip-audit** | dependency integrity | no | no |

## TIER 2 — SOLVER-ADJACENT AND GRAPH

| # | Library | Job | env | wired |
|---|---|---|---|---|
| 42 | **python-sat** | lightweight SAT when full SMT is unnecessary | no | no |
| 43 | **networkx** | pure-python graph where rustworkx is not wired | yes | yes |
| 44 | ~~PySMT~~ | solver-agnostic layer — **REJECTED: 773 days stale, no requires-python** | no | no |

## STDLIB TIER — zero install, the cheapest and most overlooked

`sqlite3` (ledger, receipt index, registry) · `hashlib` `hmac` `secrets`
(artifact binding, hash chains) · `difflib` (near-duplicate, ClaimGate G4)
· `ast` `tokenize` `symtable` (import-boundary scanning) · `zipfile`
`tarfile` (deterministic packaging, fixed timestamps) · `resource`
`signal` `subprocess` (bounded execution, timeouts, severance) ·
`statistics` (R3 baseline honesty) · `fractions` `decimal` (exact
arithmetic) · `tomllib` (pins without a dependency) ·
`importlib.metadata` (versions into receipts) · `random.Random(seed)`
(deterministic fixtures) · `unittest.mock` (severance simulation) ·
`dataclasses` `enum` `contextvars` (typed receipts without pydantic) ·
`itertools` `re` `pathlib` `json` `time`.

**16 of 21 already imported by CB source.** Unused: `difflib`,
`statistics`, `tokenize`, `symtable`, `decimal`.

## VENDORED MICRO-CAPABILITIES — not dependencies

Small stdlib routines CB owns and tests, used as the **recompute leg**
to audit sim claims at small N: Hopfield recall (30/30 in 0.19 s),
finite-map attractor/basin census, energy-landscape enumeration,
interval membership (portion's job in one line). Source material to
vendor from, never to depend on: `qclib`, `solvOR`, `Newt`.

---

## TOTALS

- **44 third-party candidates** across all tiers; 5 core, 1 control-only,
  3 test-tier, 34 secondary, 1 rejected.
- **16 present** in the project environment.
- **7 wired** into CB source today: z3, cvc5, sympy, rustworkx, maude,
  hypothesis, networkx.
- **8 present but unwired** — the zero-install gap: msgspec, jsonschema,
  cryptography, filelock, xxhash, orjson, beartype, mpmath.
- **21 stdlib modules** in the light tier, 16 already used.

CB light measured: **183.5 MB, ~0.6 s import.**
CB heavy (18 sim lanes, all present): **1,158.7 MB, ~10.6 s import.**
Ratio **6.3x disk, 17x import time.**
