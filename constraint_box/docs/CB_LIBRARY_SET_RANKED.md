# CB light — the library set, ranked by use

Generated 2026-08-09 from `config/cb_light_library_candidates.json`.

75 libraries. All install clean together, all import, all publish for macOS, Linux and Windows (67 pure Python, 8 binary with all three platforms). Total installed cost 107 MB.

Download figures are monthly from PyPI, as the adoption signal — the test for whether something is a standard tool or an abandoned one. Blank means the API did not return a figure, not that it is unused.


## Tier 0 — the core five

Declared in `pyproject.toml` as CB's only hard dependencies and in `config/core_tool_registry_v9.json` at `integration_level: function_level_receipt`. Every one publishes for macOS, Linux and Windows. All six `cb:*-gate` identifiers are now bound to real operations that emit an execution receipt.

| tool | installed | size | platforms | source | what CB uses it for |
|---|---|---|---|---|---|
| `z3-solver` | 4.16.0.0 | 41.14 MB | lin/mac/win | `constraints.py` | SMT decision over finite enumerated domains. Bounded satisfiability, counterexample witnesses, and the erased-control polarity flip that proves a proof is load-bearing rather than a tautology. |
| `cvc5` | 1.3.3 | 13.74 MB | lin/mac/win | `constraints.py` | The independent second decider. Its whole value is being a different implementation: agreement means something, and disagreement raises definite_status_disagreement instead of a silent wrong answer. |
| `sympy` | 1.14.0 | 6.30 MB | pure python | `symbolic.py` | Exact symbolic recompute. Backs ClaimGate's R5 contract, so a number in a receipt can be re-derived rather than asserted. Now wired to the mini-lev budgets as cb:sympy-exact-gate. |
| `rustworkx` | 0.17.1 | 3.10 MB | lin/mac/win | `workflow_graph.py` | Graphs and DAGs on the real FlowPolicy: cycles, topological order, reachability, acyclicity. Runs in the run path via mini_lev_topology.py and writes a topology witness into every receipt. |
| `maude` | 1.6.0 | 3.95 MB | lin/mac/win | `maude_rewrite.py` | Rewriting logic. The mini-lev transition relation is a rewrite system; maude checks that every signal sequence reaches a terminal and no non-terminal is a dead end. Now wired as cb:maude-transition-gate. |

Combined: 68.2 MB, five packages, one `pip install`.

CORRECTION (2026-08-09, external audit): an earlier draft said CB "cannot reach a verdict without"
all five. That is too strong. A verdict invokes the tools that ITS claim profile requires. A bounded
symbolic-polynomial receipt must not imply Maude ran; a transition receipt must not imply SymPy
decided it. Maude's earned ceiling in particular is a bounded observation of a controller-defined
rewrite transition, not proof that every possible signal sequence terminates.


## Tier 0b — the stdlib tier

Zero install and zero version risk. NOT uniformly cross-platform, which an earlier draft claimed:
`resource` is Unix-only and has no Windows build, and its limits vary between Unix platforms.
A capability matrix is needed here, not a blanket portability claim. 21 modules; 16 are already imported by CB source. Anything below that duplicates a third-party candidate should win on principle.

| module | what CB uses it for |
|---|---|
| `sqlite3` | ledger, receipt index, registry. Transactional, queryable, crash-safe, on every platform, zero install. Does what peewee, tinydb and pickledb do in tier 7, better. |
| `hashlib / hmac / secrets` | artifact binding and hash chains. The evidence-recomputed-from-bytes rule rests on these. |
| `difflib` | near-duplicate and ClaimGate G4. Covers what most of the abandoned string-distance packages were for. |
| `ast / tokenize / symtable` | import-boundary scanning and gate-code analysis without a dependency. |
| `zipfile / tarfile` | packaging. Fixed timestamps alone do NOT make an archive deterministic: file order, permissions, compression settings, ownership metadata and format flags all matter. Hash the canonical manifest and the raw artifact bytes separately. |
| `resource / signal / subprocess` | bounded execution, timeouts, severance controls. NOT portable: `resource` is Unix-only, so Windows needs a different mechanism or a declared capability gap. |
| `fractions / decimal` | exact arithmetic where floating point would let a gate pass on a rounding error. |
| `statistics` | R3 baseline honesty. |
| `tomllib` | read pins without adding a dependency. |
| `importlib.metadata` | installed versions recorded into the receipt. |
| `random.Random(seed)` | deterministic fixtures that replay. |
| `unittest.mock` | severance simulation — prove a gate fails closed when a dependency is cut. |
| `dataclasses / enum / contextvars` | typed receipts without pydantic. |
| `itertools / re / pathlib / json / time` | the everyday floor. |

Unused so far: `difflib`, `statistics`, `tokenize`, `symtable`, `decimal`.


## Tier 1 — Gate the receipt

Fires on every run. These decide whether a receipt or proposal is admitted at write time. If CB only ever adopted one tier, this is it.

| library | version | size | downloads/mo | what CB uses it for |
|---|---|---|---|---|
| `typing-extensions` | 4.16.0 | 0.04 MB | 1,871M | Typing backports enabling constraint annotations across supported Pythons |
| `attrs` | 26.1.0 | 0.06 MB | 915M | Typed receipt classes with validators and no boilerplate |
| `annotated-types` | 0.8.0 | 0.01 MB | 913M | Reusable constraint markers (Range, Len, MultipleOf, Pattern) for typing.Annotated fields |
| `fastjsonschema` | 2.22.1 | 0.03 MB | 150M | Compiles JSON Schema to fast validators; refuses receipts that violate schema at write time |
| `marshmallow` | 4.3.1 | 0.05 MB | 121M | Schema validation and deserialization; receipts conform to declared structure or fail at write time |
| `typeguard` | 4.6.0 | 0.04 MB | 74M | Runtime type checking at gate function boundaries; rejects mistyped proposals before entry |
| `cattrs` | 26.1.0 | 0.07 MB | 72M | Typed structure/unstructure converters for attrs receipt classes |
| `validators` | 0.35.0 | 0.04 MB | 30M | Composable field validators (URL, IP, email) for receipt fields |
| `frozendict` | 2.4.7 | 0.12 MB | 19M | Immutable dict for receipt content after validation and hashing |
| `cerberus` | 1.3.8 | 0.03 MB | 6M | Dict schema validation for gate proposals before admission |
| `portion` | 2.6.2 | 0.03 MB | 2M | Interval membership testing; computed values fall within declared admissible ranges at write time |
| `voluptuous` | 0.16.0 | 0.03 MB | — | Declarative dict/list validation; refuses malformed receipts before write |

## Tier 2 — Decide

Independent deciders beside z3, cvc5 and bounded enumeration. Their value is being a different implementation, so agreement means something.

| library | version | size | downloads/mo | what CB uses it for |
|---|---|---|---|---|
| `gmpy2` | 2.3.1 | 1.7 MB | 577K | Exact arbitrary-precision arithmetic for gates that refuse rounding error |
| `clingo` | 5.8.1 | 3.46 MB | 143K | Answer Set Programming decider orthogonal to SMT and enumeration |
| `satispy` | 1.4 | 0.01 MB | — | REMOVED: a wrapper over other solvers adds no independence, so agreement with it is circular. Independence requires a genuinely separate implementation. |
| `bitarray` | 3.10.1 | 0.4 MB | — | Compact boolean arrays for SAT/CSP assignment and clause bookkeeping |
| `formula` | 6.0.0 | 2.13 MB | — | Formula parsing and solving with exact arithmetic for constraint expressions |
| `automaton` | 3.4.0 | 0.02 MB | — | Finite state machine constraints on gate sequencing and state validity |
| `regex` | 2026.7.19 | 0.88 MB | — | Enhanced regex engine for formal-language membership constraints |

## Tier 3 — Bind evidence to bytes

Receipts, hash chains, custody. CB recomputes evidence from bytes rather than trusting what a producer declared; these are how.

| library | version | size | downloads/mo | what CB uses it for |
|---|---|---|---|---|
| `PyJWT` | 2.13.0 | 0.03 MB | 690M | JWT sign and verify for lightweight receipt attestation |
| `cbor2` | 6.1.4 | 0.51 MB | 87M | CBOR binary serialization with canonical encoding; receipt hashes stable across platforms without JSON escaping |
| `argon2-cffi` | 25.1.0 | 0.01 MB | 73M | Argon2 key derivation binding credentials to ledger entries |
| `mmh3` | 5.2.1 | 0.13 MB | 70M | MurmurHash3 non-cryptographic hashing for manifest-scale tree hashing |
| `ecdsa` | 0.19.2 | 0.14 MB | 57M | ECDSA signing for receipt attestation without the full cryptography stack |
| `uuid6` | 2025.0.1 | 0.01 MB | 17M | RFC 9562 v6/v7 sortable UUIDs for receipt entry ordering |
| `python-ulid` | 4.0.1 | 0.01 MB | 10M | Sortable ULIDs for chronologically ordered ledger entry IDs |
| `dictdiffer` | 0.10.0 | 0.02 MB | 9M | Structural dict diff for receipt change detection |
| `checksumdir` | 1.3.0 | 0.01 MB | 734K | Deterministic directory-tree hash binding receipts to artifact collections |
| `msgpack` | 1.2.1 | 0.41 MB | — | Compact binary receipt serialization without JSON canonicalization overhead |
| `protobuf` | 7.35.1 | 0.42 MB | — | Binary protocol buffers for compact versioned receipt serialization; schema executable via codegen |
| `GitPython` | 3.1.58 | 0.21 MB | — | Read git objects to audit evidence-tree commit hashes without subprocess |

## Tier 4 — Catch a weakened gate

Detect mechanically that a check became more permissive, an assertion vanished, or a module duplicates one that exists. This is the live failure mode.

| library | version | size | downloads/mo | what CB uses it for |
|---|---|---|---|---|
| `asttokens` | 3.0.2 | 0.03 MB | 140M | AST-to-token mapping for precise source locations in drift reports |
| `parso` | 0.8.7 | 0.1 MB | 139M | Python parser with error recovery for static gate-code and prompt-code analysis |
| `pyflakes` | 3.4.0 | 0.06 MB | 63M | Detects unused names, imports, redefinitions; no dead logic paths in gate code |
| `unidiff` | 1.0.0 | 0.02 MB | 56M | Unified-diff parsing; reject patches that touch gate rules or assertions |
| `rope` | 1.14.0 | 0.2 MB | 2M | Static import and usage analysis via refactoring engine |
| `flake8-simplify` | 0.30.0 | 0.03 MB | 391K | Flags complexity-increasing patterns in gate submissions |
| `vulture` | 2.16 | 0.03 MB | — | Dead code detection; unreferenced definitions rejected |
| `isort` | 8.0.1 | 0.09 MB | — | Import order and boundary checking for module layout drift |
| `ast-comments` | 1.3.0 | 0.01 MB | — | AST parse preserving comments for prompt-code analysis |

## Tier 5 — Prove the gate fires

A gate that never fires on a targeted control is decorative. These generate adversarial input and bound execution.

| library | version | size | downloads/mo | what CB uses it for |
|---|---|---|---|---|
| `more-itertools` | 11.1.0 | 0.07 MB | 339M | Deterministic batching and windowing iteration utilities |
| `coverage` | 7.15.4 | 0.26 MB | 323M | Path coverage measurement as evidence of gate test adequacy |
| `freezegun` | 1.5.5 | 0.02 MB | 60M | Frozen time for reproducible time-sensitive gate tests |
| `vcrpy` | 8.3.0 | 0.04 MB | 26M | Record and replay HTTP for hermetic tests of network-touching gates |
| `pytest-benchmark` | 5.2.3 | 0.04 MB | 13M | Reproducible timing statistics for gate latency regressions |
| `testfixtures` | 12.3.0 | 0.07 MB | 3M | Fixtures (TempDirectory, LogCapture, ShouldRaise) for deterministic scaffolding |
| `dirty-equals` | 0.11 | 0.03 MB | 3M | Structural equality tolerant of field order for receipt assertions |
| `pytest-timeout` | 2.4.0 | 0.01 MB | — | Hard time ceilings; bounded-execution proof for gate tests |
| `pytest-randomly` | 4.1.0 | 0.01 MB | — | Seed control and test-order randomization to expose order dependence |
| `pytest-xdist` | 3.8.0 | 0.04 MB | — | Parallel test execution; gates behave under concurrency |
| `pyfakefs` | 6.2.0 | 0.23 MB | — | Hermetic in-memory filesystem for I/O gate tests |
| `responses` | 0.26.2 | 0.03 MB | — | HTTP mocking for deterministic gate tests |
| `pluggy` | 1.6.0 | 0.02 MB | — | Minimal hook and plugin framework for extending gate behavior |

## Tier 6 — Detect drift in claims and prompts

Whether an argument has drifted from what was admitted. Markup and encoding noise must not disguise a real change.

| library | version | size | downloads/mo | what CB uses it for |
|---|---|---|---|---|
| `markdown-it-py` | 4.2.0 | 0.09 MB | 610M | CommonMark-strict markdown parsing for markup drift |
| `beautifulsoup4` | 4.15.0 | 0.1 MB | 438M | HTML and XML parsing for complex prompt extraction |
| `xmltodict` | 1.0.4 | 0.01 MB | 124M | XML-to-dict for element-wise structural comparison |
| `tinycss2` | 1.5.1 | 0.03 MB | 110M | CSS parsing to detect style changes without whitespace false positives |
| `arrow` | 1.4.0 | 0.07 MB | 78M | Timestamp parsing and normalization for time-sensitive claim drift |
| `mistune` | 3.3.4 | 0.06 MB | 78M | Markdown parsing for structural change detection |
| `bleach` | 6.4.0 | 0.16 MB | 76M | Tag stripping and sanitization before HTML claim comparison |
| `Unidecode` | 1.4.0 | 0.22 MB | 31M | ASCII transliteration so accented variants compare equal |
| `html2text` | 2025.4.15 | 0.03 MB | 15M | HTML-to-text so markup noise cannot disguise drift |
| `python-Levenshtein` | 0.27.4 | 0.01 MB | 13M | Fast edit distance for near-duplicate receipt and claim comparison |
| `markdown2` | 2.5.5 | 0.05 MB | — | Markdown variant conversion where mistune misses extensions |
| `soupsieve` | 2.9.2 | 0.04 MB | — | CSS selectors for targeted HTML prompt comparison |
| `w3lib` | 2.4.1 | 0.02 MB | — | URL and percent-encoding normalization for comparison |

## Tier 7 — Store and config

Weakest tier. stdlib sqlite3 and tomllib already do most of this, transactionally, on every platform, for free.

| library | version | size | downloads/mo | what CB uses it for |
|---|---|---|---|---|
| `cachetools` | 7.1.7 | 0.02 MB | 335M | Memoization of receipt validation results on hot paths |
| `tomlkit` | 0.15.1 | 0.05 MB | 324M | Round-trip TOML preserving structure and comments for inspectable canonical pins |
| `email-validator` | 2.3.0 | 0.03 MB | 237M | RFC-compliant email validation for receipt author fields |
| `peewee` | 4.3.0 | 0.17 MB | 49M | Small ORM for SQL ledger persistence |
| `tinydb` | 4.9.0 | 0.02 MB | 7M | Embedded JSON document store for append-only receipt logs |
| `pickledb` | 1.6 | 0.0 MB | 30K | JSON key-value store for receipt index and registry |
| `tomli` | 2.4.1 | 0.27 MB | — | Pure-Python TOML reading backport for pinned manifests |
| `ruamel.yaml` | 0.19.1 | 0.11 MB | — | Round-trip YAML preserving comments for byte-identical config replay |
| `lark` | 1.3.1 | 0.11 MB | — | Parser generator for bounded gate-rule DSLs |

---

# Not yet adopted — candidates checked against the same bar

27 further libraries were checked against PyPI. The bar: released within 548 days, declares `requires-python` admitting 3.12 and 3.13, wheels for all three platforms or pure Python, largest wheel under 5 MB, at most 3 declared runtime dependencies.


## These pass the bar and could be added now

| library | version | days since release | what it would give CB |
|---|---|---|---|
| `plumbum` | 2.0.2 | 18 | typed subprocess composition with explicit exit-code handling |
| `blake3` | 1.0.9 | 47 | fast tree hashing for large evidence directories |
| `xxhash` | 3.8.1 | 33 | non-cryptographic manifest hashing |
| `charset-normalizer` | 3.4.9 | 32 | detect encoding before comparing claim text |
| `grimp` | 3.15 | 36 | the import graph behind import-linter |
| `fasteners` | 0.20 | 362 | inter-process locks and read-write locks for the ledger |
| `patch-ng` | 1.19.1 | 107 | apply patches deterministically without shelling out |
| `tabulate` | 0.10.0 | 157 | deterministic table output for gate reports |
| `stamina` | 26.1.0 | 117 | opinionated bounded retry built on tenacity |
| `structlog` | 26.1.0 | 64 | structured, machine-parseable audit events instead of prose logs |
| `packaging` | 26.3 | 4 | PEP 440 version comparison for pin checks |
| `platformdirs` | 4.11.1 | 1 | correct per-OS state locations on all three platforms |

## These fail the bar, and why

| library | verdict | what it would have given CB |
|---|---|---|
| `RestrictedPython` | 5 runtime dependencies | compile untrusted proposal code with a restricted builtins set |
| `pexpect` | stale, 987 days; no requires-python declared | drive a subprocess deterministically and capture exactly what it emitted |
| `psutil` | 38 runtime dependencies | process and resource introspection; prove a worker stayed inside its memory and CPU ceiling |
| `rfc8785` | stale, 680 days; 9 runtime dependencies | JCS canonical JSON so hashes are stable across implementations |
| `import-linter` | 7 runtime dependencies | declare and enforce layer boundaries between CB modules |
| `portalocker` | 12 runtime dependencies | cross-platform advisory file locking for lease exclusion |
| `whatthepatch` | stale, 630 days | parse unified diffs to decide whether a patch touches a gate |
| `backoff` | stale, 1403 days | decorator-level bounded backoff |
| `tenacity` | 5 runtime dependencies | bounded retry with declared stop conditions; a provider call cannot retry forever |
| `python-statemachine` | 5 runtime dependencies | declarative state machine with transition validation |
| `transitions` | no requires-python declared | explicit finite state machine with guards; mini-lev flow policies as data |
| `python-json-logger` | 18 runtime dependencies | JSON log records that a gate can consume |
| `cyclonedx-python-lib` | 8 runtime dependencies | SBOM per run recorded into the receipt |
| `distro` | stale, 958 days | identify the host distribution into the receipt |
| `pip-audit` | 23 runtime dependencies | dependency vulnerability check as a gate |

---

## Dropped from the installed set, with reasons

| library | reason |
|---|---|
| `pddl` | requires lark<1.2.0, conflicts with lark==1.3.1 which CB keeps for gate-rule DSLs |
| `faker` | 19 MB; hypothesis already generates adversarial input and is wired |
| `datasketch` | pulls scipy+numpy = 132 MB; stdlib difflib covers near-duplicate |
| `html-sanitizer` | pulls lxml = 20 MB |
| `pdfplumber` | pulls pdfminer.six+pillow = 25 MB; CB gates receipts, not PDFs |

## Keeping it current

```
make cb-libs-check          # report what has drifted
make cb-libs-refresh        # re-resolve every candidate against live PyPI
make cb-libs-install-test   # prove the set still resolves and imports
```

Run `refresh` every month or two. The 548-day bar means a library that stops being maintained falls out on its own — that is how `fuzzywuzzy` (2020) and `abydos` (2020) were already removed.

