# ConstraintBox tool and integration index

This document lists the five core tools, candidate extensions, external integrations, and CLI surface. `yes` means a severance receipt changed an exercised result; it does not prove correctness or coverage.

## Core tools

The five required dependencies are declared at `constraint_box/pyproject.toml:9-13`.

| tool | version | call sites | dependent gates | severance receipt | load-bearing |
|---|---|---|---|---|---|
| z3-solver | >=4.16.0.0,<4.17.0.0 | constraints.py:186; dualsolve.py:322; flow_termination.py:306 | cb:z3-request-gate; cb:flow-termination-gate | receipts/severance_v1/severance_z3-solver.json | yes |
| cvc5 | >=1.3.3,<1.4.0 | dualsolve.py:212 | cb:cvc5-request-gate; agentrun.py:710-730 | receipts/severance_v1/severance_cvc5.json | yes |
| sympy | >=1.14.0,<1.15.0 | gate_operations.py:913; symbolic.py:823 | cb:sympy-exact-gate | receipts/severance_v1/severance_sympy.json | yes |
| rustworkx | >=0.17.0,<0.18.0 | flow_termination.py:191; workflow_graph.py:709-969 | cb:flow-termination-gate; workflow profile | receipts/severance_v1/severance_rustworkx.json | yes |
| maude | ==1.6.0 | _maude_worker.py:539; maude_rewrite.py:230 | cb:maude-transition-gate | receipts/severance_v1/severance_maude.json | yes |

The summary at `constraint_box/receipts/severance_v1/severance_summary.json:9-43` reports cvc5 14 changed fields, z3 14, rustworkx 3, sympy 2, and Maude 2. Its claim ceiling excludes correctness, platform support, resolver success, whole-suite coverage, and promotion.

## Extended candidate library set

These packages come from `constraint_box/requirements/candidates/cb-light-extended.in`. The file is a candidate inventory, not installation or use evidence.

| package | version | stated use | where used | load-bearing | receipt |
|---|---|---|---|---|---|
| argon2-cffi | 25.1.0 | Argon2 key derivation binding credentials to ledger entries | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| cachetools | 7.1.7 | Memoization of receipt validation results on hot paths | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| checksumdir | 1.3.0 | Deterministic directory-tree hash binding receipts to artifact collect | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| dictdiffer | 0.10.0 | Structural dict diff for receipt change detection | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| ecdsa | 0.19.2 | ECDSA signing for receipt attestation without the full cryptography st | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| GitPython | 3.1.58 | Read git objects to audit evidence-tree commit hashes without subproce | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| mmh3 | 5.2.1 | MurmurHash3 non-cryptographic hashing for manifest-scale tree hashing | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| peewee | 4.3.0 | Small ORM for SQL ledger persistence | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| pickledb | 1.6 | JSON key-value store for receipt index and registry | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| PyJWT | 2.13.0 | JWT sign and verify for lightweight receipt attestation | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| python-ulid | 4.0.1 | Sortable ULIDs for chronologically ordered ledger entry IDs | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| ruamel.yaml | 0.19.1 | Round-trip YAML preserving comments for byte-identical config replay | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| tinydb | 4.9.0 | Embedded JSON document store for append-only receipt logs | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| uuid6 | 2025.0.1 | RFC 9562 v6/v7 sortable UUIDs for receipt entry ordering | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| annotated-types | 0.8.0 | Reusable constraint markers (Range, Len, MultipleOf, Pattern) for typi | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| attrs | 26.1.0 | Typed receipt classes with validators and no boilerplate | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| cattrs | 26.1.0 | Typed structure/unstructure converters for attrs receipt classes | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| cbor2 | 6.1.4 | CBOR binary serialization with canonical encoding; receipt hashes stab | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| cerberus | 1.3.8 | Dict schema validation for gate proposals before admission | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| email-validator | 2.3.0 | RFC-compliant email validation for receipt author fields | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| fastjsonschema | 2.22.1 | Compiles JSON Schema to fast validators; refuses receipts that violate | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| frozendict | 2.4.7 | Immutable dict for receipt content after validation and hashing | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| lark | 1.3.1 | Parser generator for bounded gate-rule DSLs | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| marshmallow | 4.3.1 | Schema validation and deserialization; receipts conform to declared st | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| msgpack | 1.2.1 | Compact binary receipt serialization without JSON canonicalization ove | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| parso | 0.8.7 | Python parser with error recovery for static gate-code and prompt-code | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| portion | 2.6.2 | Interval membership testing; computed values fall within declared admi | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| protobuf | 7.35.1 | Binary protocol buffers for compact versioned receipt serialization; s | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| tomli | 2.4.1 | Pure-Python TOML reading backport for pinned manifests | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| tomlkit | 0.15.1 | Round-trip TOML preserving structure and comments for inspectable cano | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| typeguard | 4.6.0 | Runtime type checking at gate function boundaries; rejects mistyped pr | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| typing-extensions | 4.16.0 | Typing backports enabling constraint annotations across supported Pyth | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| validators | 0.35.0 | Composable field validators (URL, IP, email) for receipt fields | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| voluptuous | 0.16.0 | Declarative dict/list validation; refuses malformed receipts before wr | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| automaton | 3.4.0 | Finite state machine constraints on gate sequencing and state validity | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| bitarray | 3.10.1 | Compact boolean arrays for SAT/CSP assignment and clause bookkeeping | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| clingo | 5.8.1 | Answer Set Programming decider orthogonal to SMT and enumeration | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| formula | 6.0.0 | Formula parsing and solving with exact arithmetic for constraint expre | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| gmpy2 | 2.3.1 | Exact arbitrary-precision arithmetic for gates that refuse rounding er | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| regex | 2026.7.19 | Enhanced regex engine for formal-language membership constraints | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| satispy | 1.4 | Unified wrapper over SAT solvers; extra verifier lane for satisfiabili | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| asttokens | 3.0.2 | AST-to-token mapping for precise source locations in drift reports | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| flake8-simplify | 0.30.0 | Flags complexity-increasing patterns in gate submissions | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| isort | 8.0.1 | Import order and boundary checking for module layout drift | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| pyflakes | 3.4.0 | Detects unused names, imports, redefinitions; no dead logic paths in g | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| rope | 1.14.0 | Static import and usage analysis via refactoring engine | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| unidiff | 1.0.0 | Unified-diff parsing; reject patches that touch gate rules or assertio | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| vulture | 2.16 | Dead code detection; unreferenced definitions rejected | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| coverage | 7.15.4 | Path coverage measurement as evidence of gate test adequacy | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| dirty-equals | 0.11 | Structural equality tolerant of field order for receipt assertions | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| freezegun | 1.5.5 | Frozen time for reproducible time-sensitive gate tests | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| more-itertools | 11.1.0 | Deterministic batching and windowing iteration utilities | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| pluggy | 1.6.0 | Minimal hook and plugin framework for extending gate behavior | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| pyfakefs | 6.2.0 | Hermetic in-memory filesystem for I/O gate tests | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| pytest-benchmark | 5.2.3 | Reproducible timing statistics for gate latency regressions | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| pytest-randomly | 4.1.0 | Seed control and test-order randomization to expose order dependence | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| pytest-timeout | 2.4.0 | Hard time ceilings; bounded-execution proof for gate tests | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| pytest-xdist | 3.8.0 | Parallel test execution; gates behave under concurrency | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| python-Levenshtein | 0.27.4 | Fast edit distance for near-duplicate receipt and claim comparison | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| responses | 0.26.2 | HTTP mocking for deterministic gate tests | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| testfixtures | 12.3.0 | Fixtures (TempDirectory, LogCapture, ShouldRaise) for deterministic sc | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| vcrpy | 8.3.0 | Record and replay HTTP for hermetic tests of network-touching gates | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| arrow | 1.4.0 | Timestamp parsing and normalization for time-sensitive claim drift | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| ast-comments | 1.3.0 | AST parse preserving comments for prompt-code analysis | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| beautifulsoup4 | 4.15.0 | HTML and XML parsing for complex prompt extraction | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| bleach | 6.4.0 | Tag stripping and sanitization before HTML claim comparison | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| html2text | 2025.4.15 | HTML-to-text so markup noise cannot disguise drift | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| markdown-it-py | 4.2.0 | CommonMark-strict markdown parsing for markup drift | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| markdown2 | 2.5.5 | Markdown variant conversion where mistune misses extensions | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| mistune | 3.3.4 | Markdown parsing for structural change detection | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| soupsieve | 2.9.2 | CSS selectors for targeted HTML prompt comparison | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| tinycss2 | 1.5.1 | CSS parsing to detect style changes without whitespace false positives | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| Unidecode | 1.4.0 | ASCII transliteration so accented variants compare equal | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| w3lib | 2.4.1 | URL and percent-encoding normalization for comparison | requirements/candidates/cb-light-extended.in | no; candidate only | none |
| xmltodict | 1.0.4 | XML-to-dict for element-wise structural comparison | requirements/candidates/cb-light-extended.in | no; candidate only | none |

## External integrations

| integration | where used | load-bearing | receipt or boundary |
|---|---|---|---|
| ClaimGate | claimgate_plugin/hooks/post_receipt_gate.sh:80-200; pre_commit_gate_receipts.sh:22-57 | not established | no runtime rerun |
| Lev OS / FlowMind | lev-main/crates/lev-flowmind-compiler; lev-main/core/eval; lev-main/.lev/validation-gates.yaml | not established | source inspection; no build/eval run |
| Codex dispatch path | constraint_box/src/constraintbox/agentrun.py:1087-1091; 710-730 | SMT source path only | import rerun failed |
| CB package install | constraint_box/pyproject.toml:1-31; editable .pth | no; prerequisite | ModuleNotFoundError |
| gate proof harness | constraint_box/scripts/prove_gates_fire.py:1; receipts/gate_fire_proof_v1.json:1 | no production path | receipt exists; not rerun |
| ClaimGate formal BMC | claimgate_plugin/formal/chain_bmc_z3.py:38; chain_bmc_cvc5.py:20 | not established | listed, not executed |

## Install situation

The mandated interpreter reports `ModuleNotFoundError: No module named constraintbox` for `-m constraintbox` and direct import. The editable `.pth` points to a missing worktree. Scripts can mask this by inserting `constraint_box/src`, including `constraint_box/scripts/prove_gates_fire.py:37-38`. The repair command is:

```sh
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 -m pip install -e constraint_box/src
```

The repair was not run in this audit.

## CLI subcommands

The parser defines these names at `constraint_box/src/constraintbox/cli.py:169-392`. The module invocation failed, so these are `exists`, not `runs`.

| subcommand | source | load-bearing | receipt |
|---|---|---|---|
| demo | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| doctor | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| runtime list | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| runtime inspect | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| runtime verify | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| run | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| request | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| box | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| capability-box | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| capability-suite | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| integrated-workload | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| admit-sim-evidence | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| shared-affine-parity | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| observe-lev-eval | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| repair-plan | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| repair-outcome | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| advise | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| engine-test | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| deps | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| mmm | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| solve | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| crosscheck | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| estate | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| cr-slice | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| exploratory-ijk | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| candidate-world | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| manifold-foundation | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| estate-parity | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| preflight | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| lease issue | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| lease verify | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| discharge | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| evidence seal | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| evidence verify | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| applicability | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| formal list | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| formal run | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| formal temporal | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| gate | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| sim run | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
| ratchet tick | constraint_box/src/constraintbox/cli.py:169-392 | not established | none; import blocked |
## How to check this yourself

Run these commands from the repository root:

```sh
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 -m constraintbox --help
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 -c "import constraintbox"
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 -m pip install -e constraint_box/src
```
