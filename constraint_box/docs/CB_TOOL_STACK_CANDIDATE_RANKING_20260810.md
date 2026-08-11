# ConstraintBox tool-stack candidate ranking

Status: evidence-bound planning and inventory, 2026-08-10  
Scope: CB Light first; CB Heavy and simulation profiles remain separate.  
Claim ceiling: this records candidate usefulness, current local lifecycle evidence, and admission tests. It does **not** install, adopt, promote, release, or make an OS-portability claim for any tool.

## Decision in one sentence

Keep the *active* CB Light kernel small and composable—stdlib state/custody,
the five existing formal tools, the optional control-plane Pydantic/JSON Schema
boundary (outside the 91-row domain), and a proposed, not-yet-earned test-only
Hypothesis lane—while preserving the larger 91-row set as a mined, per-use
candidate domain rather than pretending it is a 91-tool runtime.

That is compatible with a large toolbox. A tool may be bound to a gate, a
wave-probe, a maintenance operation, and a falsifier in different runs. It
does **not** need to run in every wave, and neither a category label nor an
installed wheel makes it an integrated CB capability.

## Requirements this ranking obeys

The current owner direction is: lean, efficient, maintained/integrable, mostly
Python, easy to install, cheap enough for repeated/lateral probes, and actually
portable across macOS, Windows, and Linux. The preserved owner record also asks
for the complete considered set, usefulness-ranked explanations, and actual
integration rather than installed-package rhetoric. See the [owner record](OWNER_PROMPTS_VERBATIM_20260809.md), especially its August 9 portability,
large-small-library-set, and four-category inventory requirements.

Additional non-negotiable boundaries:

- **CB Light can run waves.** It does not need CB Heavy or a simulation engine
  to run a formal nested-wave fixture.
- A wave is a sequential barrier containing nested councils; skills, MMMs,
  formal agents, tools, and source packs can bind at lower levels. The
  [preserved wiki management-plane patch](</Users/joshuaeisenhart/wiki/projects/leviathan-current/nested-wave-council-management-plane-patch-2026-06-23.md>) calls this a work plane plus a resource/context/gate/receipt management plane. It is a preserved patch, not proof of a complete Lev runtime.
- Models, councils, and MMMs generate or critique bounded packets. A
  deterministic gate and receipt path decide what crosses the boundary; they
  do not declare scientific or semantic truth.
- One asset may have many roles. “Wave tool,” “gate tool,” and “maintenance
  tool” are invocation relations, not mutually exclusive tool categories.
- Local success is not portable adoption. The current required evidence target
  is a clean macOS/Linux/Windows × Python 3.12/3.13 matrix.
- CB Heavy profiles (JAX, PyTorch, Julia, QIT/topology/GPU tools) stay out of
  the Light runtime. CB may later call a public Heavy capability through a
  packet, never by ambient import or inherited environment state.

## Lifecycle language used below

| State | Meaning | Does not mean |
| --- | --- | --- |
| `PROPOSED_LIGHT` | Finite candidate identity is in the 91-row Light domain. | Installed, used, adopted, or portable. |
| `INSTALLED_CONTAINED_LOCAL` / import/provider verified | Exact local environment evidence exists. | A real consumer or an OS matrix exists. |
| `SELECTED_FOR_WORK` | The row satisfied the current static selection predicate. | Function integration, owner adoption, or release. |
| `FUNCTION_LINKED_LOCAL` | A bounded, real local consumer calls the tool and emits/consumes a receipt. | Full system, cross-platform, or semantic-truth proof. |
| `PORTABLE_ADOPTED` | Owner-approved, hash-bound clean install/import/operation evidence exists on the required matrix. | Release or CB Heavy authorization. |
| `HOLD` / `REFUSE` | A specific predicate or boundary failed. | Permanent rejection; repair may be possible. |

The status ledger deliberately reports multiple facts at once. For example, a
core package can be `PROPOSED_LIGHT`, locally installed, and selected for work,
while still having **zero portable adoption**.

## Current ground truth, not a target state

| Surface | Observed current fact | Ceiling |
| --- | --- | --- |
| Finite candidate domain | 91 proposed Light roots; 15 were excluded before the 91-root install. | A bounded inventory, not a list of adopted runtime dependencies. |
| Local contained evidence | 91/91 root install/import/provider facts are recorded for the contained local runtime and a separately generated clean local environment, both on macOS/CPython 3.13. | No Linux, Windows, or CPython 3.12 execution evidence. |
| Static current-work selection | 86 `SELECTED_FOR_WORK`, 5 `HOLD_MISSING_EVIDENCE`. | Selection is not integration or adoption. |
| Holds | `annotated-types`, `ecdsa`, `platformdirs`, `satispy`, `typing-extensions`. | Each has a recorded failed condition; none is silently promoted. |
| Formal core | `z3-solver`, `cvc5`, `sympy`, `rustworkx`, and `maude` are direct dependencies of the contained Light wheel and have local bounded core-contract exercises. | No portable adoption or claim that every decision must invoke all five. |
| Controller state | `sqlite3` is stdlib controller infrastructure; the current state writer and candidate evaluation path use it with explicit transaction/savepoint handling. | It is not one of the finite 91 candidate roots. |
| Typed control profile | `pydantic==2.12.5` and `jsonschema==4.26.0` are separate optional control-plane dependencies, not rows of the 91 domain. Fresh-wheel evidence exercises an installed local CLI and three refusal controls. | No membership, adoption, provider execution, or OS matrix. |
| Test/falsification candidate | `hypothesis==6.151.12` has a local candidate-install/probe receipt, including generated strict-envelope cases. | It is not a direct current Light runtime dependency or a function-linked gate consumer. |
| Adoption | Owner-approved adoption: 0. Portable adoption: 0. | Nothing below should be read as adopted or released. |

Primary local evidence: [row-level tool status ledger](../receipts/cb_light_tool_status_ledger_v1.json), [contained Light package definition](../light_runtime/pyproject.toml), [candidate control pins](../requirements/control_plane_candidates/cb_control_plane_candidate_pins_v1.txt), [candidate control-profile probe receipt](../receipts/cb_control_plane_candidate_install_probe_20260810.json), and [fresh wheel control-profile receipt](../receipts/CONTROL_PLANE_FRESH_WHEEL_PROFILE_20260810.json). The similarly named `CB_LIGHT_CURRENT_STATUS_20260811.md` is intentionally not temporal evidence for this August 10 report because its filename is forward-dated.

## Power ranking: likely near-term CB usefulness

The rank is an expected-usefulness order for the next earned integration steps,
not a vote to install a package or a claim that a lower-ranked tool is bad.
“M2M roles” are intentionally non-exclusive. Exact 91-row version strings
below are the `locked_version` fields in the [row-level ledger](../receipts/cb_light_tool_status_ledger_v1.json); Pydantic, jsonschema, and Hypothesis pins are from the [candidate pin file](../requirements/control_plane_candidates/cb_control_plane_candidate_pins_v1.txt) and the contained [package definition](../light_runtime/pyproject.toml).

| Rank | Asset | Current local lifecycle/evidence | M2M roles it can earn | Exact next proof before a stronger claim |
| ---: | --- | --- | --- | --- |
| 1 | `sqlite3` (stdlib) | Controller infrastructure; **function-linked local** in immutable state and candidate-evaluation paths. | Snapshot/selection state, receipt ledger, wave barrier state, replay query, maintenance audit. | Clean matrix transaction/replay tests, concurrent-writer control, and a public Light-only wave receipt; no package install is needed. |
| 2 | Pydantic 2.12.5 | **Function-linked local** optional profile: the installed `constraintbox control-plane` CLI strictly parses a packet, consumes a selection triple, and records a local evaluation; its fresh-wheel receipt includes three refusal controls. Not a 91-row member. | Strict `WaveRecipe`, probe packet, worker-result, receipt-envelope, provider-adapter packet. | Give the first wave fixture positive/unknown-field/type/capability/replay/severance tests through the same public route. |
| 3 | `jsonschema` 4.26.0 | **Function-linked local** optional-profile cross-check of the Pydantic-generated schema in the installed `constraintbox control-plane` CLI; the same fresh-wheel receipt records its bounded refusal controls. Not a 91-row member. | Independent packet-shape cross-check, external packet interchange, regression fixture validation. | Specify draft/version and format policy; prove disagreement/refusal controls rather than treating schema validity as semantic validity. |
| 4 | `rustworkx` 0.17.1 | `PROPOSED_LIGHT` + `SELECTED_FOR_WORK`; local core graph exercise. | Wave/council DAG, topological barrier, ancestor/child order check, cycle/collapse probe, maintenance dependency graph. | A Light-only `WaveRecipe` must reject a cycle, a child-before-parent settlement, and a missing prerequisite, then replay its topology witness. |
| 5 | `z3-solver` 4.16.0.0 | `PROPOSED_LIGHT` + selected; bounded local solver/witness exercise. | Finite gate decision, counterexample witness, worker-output constraint check, falsifier probe. | Bind one finite formula and its encoded-domain digest to a receipt; prove a one-field mutation flips SAT/UNSAT or yields a witness. |
| 6 | `cvc5` 1.3.3 | `PROPOSED_LIGHT` + selected; bounded local solver/witness exercise. | Independent implementation check for a declared finite formula, model/unsat-core diagnostics where configured, falsifier route. | Exercise the same fixed formula separately; report agreement/disagreement as a *formula result*, never as independent validation of an upstream premise. |
| 7 | Hypothesis 6.151.12 | Candidate install/probe only; test profile, no current Light membership or gate consumer. | Property-based negative packets, one-field mutations, state idempotency, provider-adapter contract fuzzing, regression shrinking. | Move it to a test-only consumer only after a failing generated case is preserved as a deterministic regression fixture and replayed by the public gate. |
| 8 | SymPy 1.14.0 | `PROPOSED_LIGHT` + selected; bounded local symbolic exercise. | Exact recomputation, normalization, finite polynomial/reference checks, falsifier algebra. | Use only in a declared symbolic claim profile; show a counterexample or exact recomputation changes a real gate disposition. |
| 9 | Maude 1.6.0 | `PROPOSED_LIGHT` + selected; bounded local rewrite exercise. | Ordered finite transition/rewrite checks, Mini-Lev transition probe, repair-route state witness. | Show a finite controller-defined rewrite fixture with an accepted and refused/unfinished state. Do not call it a general termination proof. |
| 10 | `packaging` 26.3 | 91-row selected candidate; active Light evidence is a bounded operation probe, not a proven consumer. | PEP 440 pin/range parsing, installer/profile admission, candidate/lock mismatch diagnostics. | One public installer or verification consumer plus invalid-version, prerelease, and profile-severance controls. |
| 11 | `grimp` 3.15 | 91-row selected candidate; current evidence is probe/test-level. | Import-boundary audit, Light/Heavy separation regression, source-set drift detector, maintenance mapping. | A Light-only source-boundary consumer that fails when a forbidden Heavy/legacy import edge is introduced. |
| 12 | `blake3` 1.0.9 | 91-row selected candidate; the active contained source has a bounded probe. Legacy scripts are not Light integration evidence. | Fast non-authoritative tree digest, probe corpus bucketing, duplicate artifact detection, maintenance acceleration. | Benchmark against stdlib SHA-256 on an actual large evidence tree; bind algorithm/version/domain separation so it never substitutes for the current authority digest. |
| 13 | `platformdirs` 4.11.1 | 91-row **HOLD**: probe structure and reason-specific negative controls are incomplete. | Per-OS state-root resolution, portable receipt location, installer/user-data conventions. | Repair its named hold, then execute actual macOS/Linux/Windows path tests. Do not make it a default storage authority first. |
| 14 | `fasteners` 0.20 | 91-row selected; bounded probe only. | Explicit inter-process lease in a non-SQLite resource, maintenance coordination, worker cache lock. | Demonstrate a real resource not already serialized by SQLite, including lost-holder/refusal/recovery controls. Otherwise do not duplicate SQLite concurrency machinery. |
| 15 | `clingo`, `gmpy2`, `formula`, `automaton`, `bitarray`, `regex` | 91-row selected candidates; per-tool operation probes only. `satispy` is on HOLD and must not be used as a pretend independent solver. | New bounded ASP/numeric/automaton/formula profiles, specialized falsifiers, compact finite representations. | Open a new claim profile first, write a separate encoding/reference test, then prove what new discriminating result it supplies beyond Z3/CVC5/enumeration. |
| 16 | PydanticAI | Not a current 91-row candidate, contained-Light direct dependency, or active contained-Light source consumer. This report did not evaluate any host-level installation. | Provider-worker adapter, typed model output, tool-call boundary, spend/timeout envelope, disposable research probe. | Admit only if a real provider adapter cannot be smaller. Use a fake provider, deny undeclared tools/capabilities, cap spend/time/retries, record model/provider/version/input/output digests, and prove the deterministic gate—not the framework—settles disposition. |
| 17 | Claude bridge, Luna Ultra, other model providers, skills, MMMs | External execution/context assets, not CB Python-library membership. No current CB-Light provider identity or portability claim is made here. | Diverse worker lanes, source/skill loading, MMM salience, cost-constrained probe generation, falsifier councils. | Receipt-bind provider/model identity, skill/MMM/source hashes, input diversity, tool permission set, cost/timeout, raw result, and gate outcome. A provider result cannot self-admit. |

### Important interpretation of the formal ranks

Z3/CVC5 agreement is useful **only** as a separately executed result over the
declared formula and bounded domain. It does not independently establish that
the source facts, translation, or claim framing were correct. A solver is a
precise formal tool, not an oracle. The same applies to SymPy and Maude:
invoke the tool required by the particular contract rather than forcing all
five into every wave.

Pydantic is the strongest near-term addition because it already has a narrow,
exercised consumer. Its job is strict envelope validation—not solving the
constraint or declaring the worker output true. Pydantic’s strict mode rejects
many coercions that default validation permits; that is exactly the desired
packet boundary, not a semantic evaluator. [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)

`jsonschema` is a useful independent shape cross-check, but JSON Schema
formats are not automatically validation obligations. The contract must state
whether a `FormatChecker` is enabled and include a negative control. [jsonschema validation docs](https://python-jsonschema.readthedocs.io/en/stable/)

Hypothesis is an efficient falsification tool: it generates values over stated
properties and can shrink failures. It cannot prove the property specification
is adequate, so every generated failure must be retained as a replayable
fixture. [Hypothesis documentation](https://hypothesis.readthedocs.io/en/latest/)

PydanticAI is compelling as a future typed provider adapter because it exposes
agent loops, model/provider integrations, tools, approvals, structured output,
and evaluation surfaces. Those are reasons to isolate it behind a bounded
adapter—not reasons to put it inside CB Light’s deterministic kernel. [Pydantic AI overview](https://ai.pydantic.dev/)

## Many-to-many capability/use ledger

The data model should record a binding, not classify a tool permanently:

```text
AssetBinding(
  run_id, wave_id?, council_id?, member_id?,
  asset_id, distribution_or_provider_version, source_or_config_digest,
  purpose, invocation_mode, input_digest, permission_set,
  expected_contract, raw_result_digest, gate_disposition, receipt_id
)
```

`?` means a relation may be absent. A maintenance action can use an asset with
no wave; a wave member can bind several assets; the same asset can be used by
different councils or deterministic gates in the same run. Mark the relation
as `declared`, `bound_reference`, `invoked`, or `verified_result`—never infer
`invoked` from a registry, import, or prompt.

| Asset family | Possible concurrent roles | Authority boundary |
| --- | --- | --- |
| SQLite + hashes + canonical JSON | Gate state, receipt index, replay, maintenance audit, wave barrier ledger. | Retains and checks state; it does not decide scientific truth. |
| Pydantic + `jsonschema` | Public packet parser, worker-result envelope, hook/provider boundary, replay schema cross-check. | Shape/type/capability enforcement only; deterministic formal rules decide semantics. |
| Z3/CVC5 + bounded enumeration | Gate predicate, counterexample finder, falsifier check, independent implementation comparison. | Decide only the encoded finite relation; record `unknown`/disagreement rather than fabricate success. |
| Rustworkx | Wave DAG, nested-council topology, scheduling barrier, source/dependency graph maintenance. | Proves a declared graph property, not that a council’s prose is correct. |
| SymPy + Maude | Exact symbolic recompute, finite rewrite/transition observation, repair-route check. | Contract-specific deterministic work; do not expand a bounded result to a universal claim. |
| Hypothesis + test harness tools | Adversarial packet generation, mutation/severance/replay regression, load/order tests. | Test evidence only; a green randomized run is not adoption. |
| `packaging`, `grimp`, `platformdirs`, `blake3`, `fasteners` | Installer verification, source-boundary audit, portable path policy, large-artifact hashing, rare non-SQLite leases. | Maintenance/support aids remain dormant until a real consumer and role-specific negatives exist. |
| Skills/MMMs/Claude/Luna/provider adapters | Context preparation, diverse proposal/falsifier work, source analysis, model/tool execution. | They may propose packets and their own evidence; a deterministic gate + receipt plane alone permits downstream effect. |
| CB Heavy/Sim Engine profiles | External workload capability, evidence-producing executor, optional stress/falsification target. | CB Light may call a public packet capability later; Heavy is neither required for a Light wave nor imported into its environment. |

This also resolves the apparent tension between “use low-cost tools freely” and
“stay lean”: make cheap tools *available and selectable*, but choose invocation
by the operation’s declared contract and record it. Repeated inexpensive
falsification can scale laterally; unconditional calls to every installed
package are bloat and make receipts less informative.

## Complete current 91-row domain, preserved without overclaiming

The rows below are the exact current ledger set, grouped by their existing
candidate-role labels. Those labels are inventory descriptors, **not exclusive
future role assignments**. Every row is proposed; the parenthetical `HOLD`
labels identify the five not selected for current work. The current table does
not establish an active consumer for every selected item.

| Candidate-role label in ledger | Exact rows | Selection count |
| --- | --- | ---: |
| `core_deterministic_runtime` | `z3-solver`, `cvc5`, `sympy`, `rustworkx`, `maude` | 5/5 selected |
| `schema-contract-serialization` | `annotated-types` **(HOLD)**, `attrs`, `cattrs`, `cbor2`, `cerberus`, `email-validator`, `fastjsonschema`, `frozendict`, `lark`, `marshmallow`, `msgpack`, `parso`, `portion`, `protobuf`, `tomli`, `tomlkit`, `typeguard`, `typing-extensions` **(HOLD)**, `validators`, `voluptuous` | 18/20 selected |
| `solvers-logic-automata` | `automaton`, `bitarray`, `clingo`, `formula`, `gmpy2`, `regex`, `satispy` **(HOLD)** | 6/7 selected |
| `hash-sign-ledger-storage` | `argon2-cffi`, `cachetools`, `checksumdir`, `dictdiffer`, `ecdsa` **(HOLD)**, `GitPython`, `mmh3`, `peewee`, `pickledb`, `PyJWT`, `python-ulid`, `ruamel.yaml`, `tinydb`, `uuid6` | 13/14 selected |
| `hash_integrity` | `blake3`, `xxhash` | 2/2 selected |
| `test-repro-bounded` | `coverage`, `dirty-equals`, `freezegun`, `more-itertools`, `pluggy`, `pyfakefs`, `pytest-benchmark`, `pytest-randomly`, `pytest-timeout`, `pytest-xdist`, `python-Levenshtein`, `responses`, `testfixtures`, `vcrpy` | 14/14 selected |
| `static-analysis-drift` + `static_audit` | `asttokens`, `flake8-simplify`, `isort`, `pyflakes`, `rope`, `unidiff`, `vulture`, `grimp` | 8/8 selected |
| `text-similarity-drift` + `text_drift` | `arrow`, `ast-comments`, `beautifulsoup4`, `bleach`, `charset-normalizer`, `html2text`, `markdown-it-py`, `markdown2`, `mistune`, `soupsieve`, `tinycss2`, `Unidecode`, `w3lib`, `xmltodict` | 14/14 selected |
| `portability` | `platformdirs` **(HOLD)** | 0/1 selected |
| `concurrency_control` | `fasteners` | 1/1 selected |
| `package_semantics` | `packaging` | 1/1 selected |
| `subprocess_control` | `plumbum` | 1/1 selected |
| `bounded_retry` | `stamina` | 1/1 selected |
| `audit_telemetry` | `structlog` | 1/1 selected |
| `mutation_tool` | `patch-ng` | 1/1 selected |

The 15 pre-install exclusions were `backoff`, `cyclonedx-python-lib`, `distro`,
`import-linter`, `pexpect`, `pip-audit`, `portalocker`, `psutil`,
`python-json-logger`, `python-statemachine`, `RestrictedPython`, `rfc8785`,
`tenacity`, `transitions`, and `whatthepatch`. Their current disposition is a
metadata-bar failure before the 91-root install—not a claim that they can never
be reconsidered if a named consumer changes the evidence.

### Deliberate non-promotions and de-duplication rules

- Keep **one** primary strict packet system: Pydantic, with `jsonschema` as the
  declared independent cross-check. Do not add `attrs`, `marshmallow`,
  `cerberus`, `voluptuous`, `fastjsonschema`, or `typeguard` to the public
  control path merely because they are present candidates. A concrete missing
  contract must justify each one.
- Keep stdlib SQLite as the receipt/state store. Do not promote `peewee`,
  `tinydb`, or `pickledb` without a data model SQLite cannot meet.
- Keep canonical SHA-256/stdlib custody digest authoritative. `blake3` may earn
  a performance/bucketing role, not an ambiguous replacement for the receipt
  identity algorithm.
- Do not add a lock abstraction simply because it exists. SQLite’s currently
  exercised explicit transaction/savepoint route is the default; prove an
  independently locked non-SQLite resource before using `fasteners`.
- Do not add `clingo`, `gmpy2`, or a solver wrapper to create a decorative
  “third opinion.” A new formal tool must bring a new bounded encoding and a
  discriminating positive/negative result. `satispy` remains a hold rather than
  false evidence of independent solving.
- Do not use an ORM, generic agent framework, queue, cache, or telemetry
  package as a substitute for a missing deterministic contract.

## Exact next admission tranches and falsification tests

### Tranche A — first Light-only formal wave (no new package)

Use SQLite + Pydantic + `jsonschema` + Rustworkx + the necessary subset of
Z3/CVC5/enumeration. Add a typed `WaveRecipe` / `CouncilRecipe` / `ProbePacket`
and produce a single fixture with nested councils and a deterministic barrier.

Required controls:

1. Valid topology reaches the barrier and writes a SQLite receipt.
2. A cycle, missing child receipt, parent/child ordering violation, and
   undeclared capability each refuse before state advancement.
3. One finite solver formula has an input/domain/formula digest, a witness or
   unsat reason, and an explicit deliberately mutated control.
4. Each worker packet carries source/skill/MMM/model/provider references, but
   no worker can choose promotion or mutate settlement state directly.
5. Replay from retained bytes recreates the same topology, packet digests, and
   final deterministic disposition.
6. The receipt reports exactly which assets were *invoked*, not a list of all
   packages installed in the environment.

Mini-LevOS is a controller/transition concern for this tranche, not a new
third-party dependency. Use a public Light-only interface and do not import a
legacy or Heavy private path merely to make the fixture run.

### Tranche B — property-based falsification (Hypothesis, test profile only)

Bind Hypothesis to the actual public gate, not a duplicate toy validator:

- generate legal and illegal packet shapes, duplicate identities, wrong
  capability, stale selection triple, one-field source-digest mutation, and
  invalid child topology;
- seed and record the run, preserve any minimized counterexample as a checked-in
  deterministic replay fixture;
- show that a severed Pydantic or `jsonschema` validation edge changes the
  public outcome to `HOLD`/`REFUSE`, rather than merely failing a unit helper.

This earns a test-only consumer. It does not make Hypothesis a resident
per-wave runtime dependency unless a future bounded workload truly requires it.

### Tranche C — maintenance consumers only when needed

1. `packaging`: exact candidate-pin/version/range verifier with a malformed
   range and wrong-profile negative.
2. `grimp`: Light/Heavy import-boundary enforcement with an injected forbidden
   edge control.
3. `platformdirs`: first repair the existing hold, then record the three real
   OS locations and their no-escape/same-app/different-app controls.
4. `blake3`: only after an evidence-tree performance case exceeds an agreed
   threshold; retain SHA-256 as the custody identity.

### Tranche D — optional provider adapter (PydanticAI only on demand)

Open this only after the deterministic wave fixture is real and a concrete
provider worker needs more than the bridge/adapter already supplies. The
admission package must demonstrate:

- fake/offline provider success plus time, spend, tool-permission, network, and
  malformed-structured-output refusal controls;
- strict Pydantic envelope on every model/tool result;
- provider/model/version/config/seed/input/context/output/cost digests;
- provider loss, retry exhaustion, and output-schema failure that leave the
  SQLite gate state safe; and
- a positive proof that PydanticAI is severable: disabling it blocks only the
  optional worker adapter, never the deterministic gate or a local formal wave.

Luna Ultra can be one such provider identity if and when its actual endpoint,
model/version identifier, cost policy, and executable adapter are supplied.
It is not a Python-package admission, and it must not be represented as a
current integration merely because it is desired for future waves.

### Tranche E — portability is a separate promotion gate

For every candidate that reaches `FUNCTION_LINKED_LOCAL`, run from a fresh
environment on each required target:

```text
macOS, Linux, Windows × CPython 3.12, 3.13
  -> exact lock/resolution + pip check
  -> package/provider/import-origin evidence
  -> positive operation
  -> named negative/boundary/severance/replay control
  -> source/policy/receipt digest comparison
```

Publish a per-cell result. A wheel tag, package metadata, or another OS’s
success is only candidate evidence. This is especially important for native
formal tools: cvc5’s own Python documentation explicitly calls out a Windows
CLANG environment for a source-build route, so actual target execution—not an
assumed universal wheel—is the standard. [cvc5 Python API](https://cvc5.github.io/docs/latest/api/python/python.html)

## Research-backed tool boundaries

- [Z3’s guide](https://microsoft.github.io/z3guide/docs/logic/intro/) describes
  satisfiability over logical theories; encode the finite relation carefully and
  retain the model/witness. Do not treat a satisfiable check as a fact checker.
- [cvc5’s Python API](https://cvc5.github.io/docs/latest/api/python/python.html)
  supports a direct Python solver route. Its role here is an independently run
  implementation check, not a voting council member.
- [SymPy](https://docs.sympy.org/latest/) is a symbolic-mathematics library;
  constrain its use to exact, declared transformations and avoid evaluating
  untrusted expression strings.
- [Rustworkx](https://www.rustworkx.org/api/index.html) exposes directed graph
  and topological-sort APIs, which fit topology witnesses and cycle controls.
- [Maude Python bindings](https://fadoss.github.io/maude-bindings/) begin with
  `init()` and accept module input; that supports a bounded rewrite fixture,
  not a universal termination result.
- Python’s [sqlite3 transaction documentation](https://docs.python.org/3/library/sqlite3.html)
  distinguishes implicit and explicit transaction control. CB’s state writer
  must continue to preserve its explicit transaction/savepoint assertions in
  every portability cell.

## Source hierarchy and refresh rule

This document ranks only against the current direct owner direction, active
contained-Light source/receipts, and the indexed wiki’s explicitly labelled
patch material. It intentionally does not use historical “all tools installed”
reports as proof of present integration. Candidate metadata (release recency,
wheel size, dependency count) must be refreshed against the package source
before any future admission; the local candidate registry is evidence of a
previous assessment, not an evergreen portability or maintenance guarantee.

Before changing any row’s lifecycle, require the corresponding source hash,
exact interpreter, import/provider origin, positive/negative/boundary/replay/
severance evidence, and a real downstream consumer receipt. That preserves the
large research surface without turning it into a bloated or falsely integrated
runtime.
