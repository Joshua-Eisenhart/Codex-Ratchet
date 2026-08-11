# CodexRatchet Formal-Assurance and Cloud-Science Architecture

**Version:** proposed v2  
**Date:** 2026-07-24  
**Scope:** sim-engine estate, ClaimGate, Ratchet, external LevOS integration, formal methods, maintenance, and local/cloud science execution  
**Promotion:** `promotion_allowed: false`

This document compares the proposed “Julia → JAX → NumPy → SMT → ClaimGate → Lev” layout with the current repository implementation and replaces it with a stricter, claim-specific architecture.

It is not a report declaring the system complete. It is a proposed operating architecture, a repair ledger, and a set of executable acceptance boundaries.

---

## 0. Status vocabulary used here

| Status | Meaning |
|---|---|
| `OWNER_LOCKED` | Explicit project rule supplied by the owner |
| `REPO_MEASURED` | Directly observed in the audited local repository branch or a machine receipt |
| `REPO_REPORTED` | Claimed by repository documentation but not freshly reproduced in this audit |
| `PROPOSED` | Recommended architecture or tool placement; not yet implemented |
| `OPEN` | A live choice requiring a discriminator |
| `BLOCKED` | Cannot legitimately advance with the present evidence |
| `SUPERSEDED` | Historical design retained only as provenance |
| `UNKNOWN` | Not established |

These labels are deliberately separate from mathematical truth, scientific support, software execution, and governance admission.

---

## 1. Executive decision

The pasted layout has the right **isolation instinct** but the wrong **authority abstraction**.

The improved system is not a fixed six-stage conveyor belt and not a global ranking of programming libraries. It is a deterministic, typed graph of obligations selected by a frozen science contract.

```text
                    OWNER-LOCKED ROOT CONSTRAINTS
                                  |
                backend-neutral model + science contract
                                  |
                         ClaimGate preflight
                                  |
                     deterministic lane planner
                                  |
              external LevOS bridge supervises execution
                                  |
        +-------------------------+-------------------------+
        |                         |                         |
   numeric lanes             formal lanes             search lanes
 Julia / JAX / controls   SMT / proof / TLA+     GPU / tensor / learned
        |                         |                         |
        +--------------- immutable evidence ---------------+
                                  |
                         ClaimGate postflight
                                  |
                  validated candidates and negatives
                                  |
                  Ratchet relative finite comparison
                                  |
          survivors / antichain / Purgatory / next obligation
```

The responsibility boundaries are:

| Component | May do | Must not do |
|---|---|---|
| LLM or council | Propose candidates, attacks, encodings, repairs, and experiment designs | Self-certify, choose MSS, change frozen contracts, or declare scientific truth |
| Science Module | Deterministically compile a frozen contract into an execution DAG and run it | Select the winning ontology or silently omit an obligation |
| Julia/JAX/PyTorch/NumPy | Compute only the observables assigned to their declared lanes | Acquire universal authority because a library is installed |
| Formal tools | Decide or bound explicitly encoded obligations | Inflate a bounded encoded result into an unrestricted claim |
| ClaimGate | Validate schemas, provenance, execution evidence, obligation polarity, and policy | Compute MSS, decide ontology, or treat agreement as truth |
| Ratchet | Compare admitted finite candidates under shared demands and nested orders | Prove absolute MSS, ratchet root constraints, or replace incomparability with a convenient scalar |
| External LevOS bridge | Enforce the actual host path, process isolation, and allowed effects without modifying LevOS | Become the source of scientific truth |

---

## 2. Comparison with the pasted layout

| Pasted proposal | Audit decision | Corrected rule |
|---|---|---|
| One heavy runtime owns the machine at a time | **Keep as a local default** | On the 16 GB M1, serialize heavy runtimes by default. It is a resource policy, not a law of the scientific model or of cloud execution. |
| DLPack / zero-copy is dead | **Narrow** | Keep zero-copy out of the trusted artifact boundary because it couples memory lifetimes and weakens replay. It may still be used inside one untrusted performance job. DLPack does not inherently reverse axes; layout, strides, ownership, and device semantics must be explicit. |
| Julia is canonical | **Rename** | Julia is the current reference-semantic implementation. “Reference” does not mean it automatically wins disagreements or defines nature. |
| JAX is the workhorse | **Keep** | JAX x64 is the normal dense/batched numerical workhorse and primary NVIDIA search lane. |
| NumPy satellites are arbiters | **Correct** | NumPy/SciPy are controls, analysts, and candidate compilers. They may veto through a counterexample but do not arbitrate admission or MSS. |
| NumPy restoration needs no gate change | **Reject** | Containment code partly agrees, but workflow wording, strict parsing, authority rules, stage selection, metadata-only status, and post-hoc exemptions all require repair. |
| SMT is only supportive | **Correct** | SMT may be load-bearing for a particular finite obligation. It is not a numerical engine and needs no fake Julia/JAX pair when the claim is purely exact and finite. |
| PyTorch is globally authoritative | **Reject** | PyTorch authority is claim-specific. It is normally a learned/search proposer; it becomes load-bearing only for a task that actually requires it and still cannot certify its own output. |
| Every GPU number needs a CPU cross-check | **Refine** | Require exact-small overlap, same-backend CPU/GPU parity, and an independent implementation on declared overlap. Very large outputs use post-commit challenges rather than impossible full CPU repetition. |
| Reactant.jl supplies a same-GPU independent Julia witness | **Reject as independence** | Reactant and JAX share XLA compiler infrastructure. Reactant is a useful accelerator but not an independent failure domain from JAX/XLA. |
| PyTorch Geometric is the renesting machinery | **Demote** | PyG may learn or score rewrite proposals. Authoritative typed graph rewriting belongs in Catlab/AlgebraicRewriting, Metatheory, Maude, Alloy, or a compact deterministic kernel. |
| Autograd gives an exact topological-stress gradient | **Correct** | Autograd differentiates the implemented floating computation graph. It is not an exact symbolic proof of the intended geometry or physics. |
| ClaimGate → Lev decides | **Split responsibilities** | ClaimGate validates evidence; Ratchet compares candidates; the external LevOS bridge enforces the actual host execution path and permitted effects. |
| Fixed Julia → JAX → NumPy → SMT chain | **Replace** | Compile a claim-specific typed DAG. A TLA+ protocol claim should not be forced through PySINDy; an exact SMT claim should not invent numeric-engine work. |
| `numeric_engine_required=false` can exempt a run | **Freeze earlier** | An exemption is valid only when fixed in the signed pre-run contract. A numeric result cannot retroactively relabel itself nonnumeric after failing the seal. |
| Target hybrid maps rather than known contractions | **Keep** | GPU search is justified where basin structure is genuinely open: switching, memory, coupled engines, renesting, or history-dependent dynamics. |
| Sample the fuzz on history space, not only density matrices | **Keep** | If the intended object contains \(j\ne k\) history-pair coherence, sampling only \(\rho\) destroys the very distinctions under test. |

---

## 3. Rules inherited from the model

These rules must be enforced in data schemas and execution logic, not left as prose instructions to an LLM.

### 3.1 Nominalist and constraint-first rules

1. Every executable object has a finite carrier, explicit identifiers, declared maps, and a representation bound.
2. A solver may decide only the encoded finite obligation.
3. The Ratchet compares candidates relative to a declared demand packet and probe family.
4. MSS is relative to the compared candidate set and orders. It is never absolutely proven.
5. Root constraints are not candidates and cannot be ratcheted by their own mechanism.
6. Negative candidates and failed repairs remain first-class evidence.
7. Incomparable survivors remain plural. A weighted scalar score cannot silently erase the antichain.
8. An absent distinction, skipped gate, or empty metric floor is not a pass.

### 3.2 Scientific-engine identity rules

The Type-1 and Type-2 scientific engines are not Julia, JAX, PyTorch, or NumPy.

Their backend-neutral semantic contract must carry:

- four topologies;
- eight flux terrains;
- sixteen stage bindings;
- four oriented loops;
- two independent engine types;
- stage adjacency;
- loop direction;
- selected run start;
- operator family;
- Axis-6 sign and composition action;
- terrain/operator equations;
- initial and boundary conditions;
- history/record carrier where used;
- requested observables;
- falsifiers;
- claim ceiling.

The loops are cyclic:

- cyclic rotation preserves loop identity;
- selected starting stage is a run coordinate;
- reversing orientation creates a distinct traversal;
- changing adjacency creates a distinct loop;
- science-method interpretation may prefer a start but must not rewrite the cycle’s mathematical identity.

The semantic digest must therefore hash both:

```text
cycle_identity = canonical_oriented_cycle_modulo_rotation
run_coordinate = {start_stage, direction, initial_state, boundary_conditions}
```

Axis 6 must be an explicit signed operation in the contract. It must not be reduced to a decorative up/down label or only to prose about function order.

### 3.3 No hidden entropy soup

Hartley/Rényi-0 capacity, von Neumann entropy, Shannon record entropy, coherent information, extension-fibre capacity, Spohn production, graded coherence, and other typed quantities remain separate coordinates unless a particular map between them is explicitly defined and tested.

### 3.4 History-pair preservation

For a channel-history family \(K_j\), the history object

\[
D(j,k)=\operatorname{Tr}\!\left(K_j\rho_0K_k^\dagger\right)
\]

contains diagonal probabilities and off-diagonal interference. A density-matrix output can be a quotient that forgets distinctions in \(D(j,k)\).

Any “jk fuzz” or uncollapsed-history experiment must therefore declare whether its carrier is:

- a finite possibility set;
- a diagonal history distribution;
- a full history-pair matrix;
- a density operator;
- an extension fibre over a quotient.

These cannot be substituted for one another because they have similar dimensions.

### 3.5 Nonassociativity preservation

Every nonassociative computation must carry an explicit bracket tree:

\[
[A,B,C]_\star=(A\star B)\star C-A\star(B\star C).
\]

The bracket-tree digest is part of the semantic contract. Generic parallel reductions may not reassociate a nonassociative product. A compiler-generated reassociation is a semantic failure even when the numerical output appears stable.

---

## 4. The improved sim-engine estate

### 4.1 Roles, not a single ranking

| Lane | Current default role | Claim-specific authority | Principal prohibition |
|---|---|---|---|
| Native Julia CPU | Reference semantics, exact-small carriers, topology, intervals, independent observables | Numeric reference for declared arrows; exact carrier authority where explicitly assigned | Does not automatically win a disagreement |
| JAX x64 CPU/CUDA | Dense and batched numerical workhorse, differentiable search | Numeric workhorse for declared arrows | Search output is not a proof |
| NumPy/SciPy | Exact-small controls, analysis, serialization, baseline algorithms | Counterexample/veto and control authority only | Never hidden core dynamics or solo promotion |
| PySINDy/PyDMD/Koopman | Candidate AST and reduced-model proposal generation | Proposal only until independently checked | Residual fit is not discovery of a law |
| PyTorch | Learned proposal models, graph learning, irregular search, task-specific training | Only for a named learned/search claim after an acceptance gate | No global scientific authority |
| Symbolics.jl/SymPy | Canonical expressions and obligation generation | Symbolic support | Simplification is not certification |
| Z3/cvc5/Bitwuzla | Exact finite logical obligations | Load-bearing for the exact obligation encoded | No continuum or ontology inflation |
| Lean 4 | Small trusted theorem kernel for stable finite definitions and lemmas | Proof authority for the checked theorem under declared axioms | Does not select the model’s root premises |
| TLC/Apalache/TLAPS | State-machine safety, bounded temporal checking, deductive protocol proofs | Protocol assurance | Does not prove numerical physics |
| Interval/reachability tools | Validated continuous enclosures and hybrid reachability | Bound authority for declared domains and tolerances | No unbounded extrapolation |
| Annealing/tensor tools | Bounded candidate search or contraction | Search/comparator only unless an independently checkable certificate is emitted | No “quantum oracle” claim |

### 4.2 Claim-specific authority matrix

Replace the current global `AUTHORITATIVE = (...)` tuple with a registry keyed by claim type.

| Claim type | Required evidence | Optional lanes | What can admit it to Ratchet comparison |
|---|---|---|---|
| Dense open-system trajectory | Independent native Julia and JAX construction; typed observable parity | NumPy exact-small control | ClaimGate verifies both implementations and hostile mutations |
| JAX CPU/GPU parity | Same JAX program, fixed fixture, device evidence, tolerance budget | Julia reference on small overlap | Platform parity only, not implementation independence |
| Learned graph-rewrite proposer | PyTorch/PyG held-out performance and ablation | JAX reimplementation of score | Only proposed rewrites; deterministic rewrite kernel settles validity |
| Finite existence claim | SAT witness checked by independent executable predicate | Z3 and cvc5 cross-check | Valid witness under the frozen finite domain |
| Finite impossibility claim | UNSAT plus proof object where supported; independent encoding/mutation | Second solver | Checked certificate and nonvacuity controls |
| Bit-vector/floating-point semantics | Bitwuzla or suitable SMT logic plus independent concrete controls | Z3/cvc5 where supported | Exact encoded machine-semantics result |
| Nonlinear real bound | Interval enclosure and/or reachability; dReal as bounded support | JAX search for candidates | Declared bounded result; \(\delta\)-SAT remains approximate |
| Workflow safety | TLA+ spec, TLC finite checks, Apalache bounded/invariant checks, runtime trace conformance | TLAPS for stable lemmas | Protocol property only |
| Stable finite mathematical lemma | Lean proof under recorded imports and axioms | SMT-generated witness imported only after checking | Lean kernel acceptance |
| Tensor-network cloud result | Exact-small Julia/JAX reference; contraction error and path receipt; cloud attestation | cuTensorNet acceleration | Bounded observable with declared approximation error |

No library is authoritative “in general.”

### 4.3 Capability maturity

Every library or lane advances separately:

1. `AVAILABLE`
2. `EXERCISED`
3. `INTEGRATED`
4. `LOAD_BEARING_FOR_<CLAIM_TYPE>`
5. `AUTHORITATIVE_FOR_<OBLIGATION_TYPE>`

An import check proves only `AVAILABLE`.

---

## 5. Stronger formal-assurance stack

No one formal tool covers the whole system. The correct stack is divided by the semantic object being checked.

### 5.1 Tool placement

| Layer | Recommended tools | Exact job | Important limit |
|---|---|---|---|
| Strict data/schema | Duplicate-rejecting JSON parser, JSON Schema, CUE, canonical JSON | Types, required fields, closed objects, units, finite values, contract unification | CUE is for configuration/schema, not the model’s nonassociative multiplication |
| Finite SAT/SMT | Z3 + cvc5 | Integer, real, array, datatype, sequence, set, and finite structural obligations | Agreement can preserve a shared encoding bug |
| Machine arithmetic | Bitwuzla | Bit-vectors, arrays, floating point, uninterpreted functions | It proves encoded machine semantics, not the intended physical interpretation |
| Proof-producing SMT | cvc5 Alethe/LFSC/CPC output plus an independent checker | Checkable UNSAT evidence and proof-step accounting | Unsupported rules or trust steps must be recorded; “proof emitted” is not enough |
| Pure SAT certificates | LRAT/FRAT-capable solver and checker | Independently checkable propositional UNSAT | Requires a sound, recorded translation from the original obligation |
| Theorem kernel | Lean 4 | Stable finite definitions: partitions, refinement, cyclic equivalence, associators, selected bridge lemmas | A theorem is conditional on imports and axioms; it does not prove owner premises |
| Protocol model checking | TLA+ + TLC | Explicit finite state exploration and counterexample traces | State explosion; bounded model is not full implementation conformance |
| Symbolic temporal checking | Apalache | SMT-backed bounded model checking and inductiveness checking | Bounded/experimental; not a replacement for TLC or proof |
| Deductive temporal proof | TLAPS | Proofs of stable TLA+ safety/liveness lemmas | Use after the protocol stops changing; TLAPS is not a model checker |
| Rewrite semantics | Catlab/AlgebraicRewriting or Metatheory; Maude | Typed graph rewrites, executable rewrite logic, strategy/order exploration | A learned score may rank rewrites but cannot define valid rewriting |
| Bounded relational countermodels | Alloy 6 | Small-scope structure and relation counterexamples | “No counterexample in scope” is not a general theorem |
| Validated continuous dynamics | IntervalArithmetic.jl, ReachabilityAnalysis.jl | Enclosures, reachable sets, bounded safety | Susceptible to enclosure growth; domain must be explicit |
| Nonlinear real decision support | dReal | Exact UNSAT or bounded \(\delta\)-SAT for nonlinear real formulas | \(\delta\)-SAT is not exact SAT |
| Supply-chain provenance | in-toto, SLSA provenance, Sigstore/Cosign | Bind source, build, container, and artifact lineage | Provenance proves origin/process, not scientific truth |

### 5.2 What to add first

| Priority | Addition | Reason |
|---|---|---|
| 1 | TLA+ CLI/TLC plus Apalache in an isolated formal-protocol environment | The largest current gap is control-state correctness: promotion, retries, stale generations, Purgatory, and cloud handoff |
| 2 | cvc5 proof production plus an independent proof checker | Converts some UNSAT results from trusted solver assertions into checkable evidence |
| 3 | Bitwuzla | Stronger bit-vector and floating-point obligations for bounded representation and actual machine arithmetic |
| 4 | Extend the existing Lean microcore | The repository already contains a load-bearing Lean result; build on it instead of starting another theorem-prover branch |
| 5 | IntervalArithmetic.jl + ReachabilityAnalysis.jl acceptance fixtures | Needed before serious continuous/hybrid and Navier–Stokes-style bounded claims |
| 6 | Maude and Alloy bounded fixtures | Needed for graph rewrite order, renesting, and small structural countermodels |
| 7 | in-toto/SLSA/Cosign | Needed before cloud artifacts become promotion-bearing evidence |

Do not install all of these into one runtime. Give each a pinned profile and a known-answer acceptance fixture.

---

## 6. SMT obligation protocol

The present code globally treats `SAT` as rejection and `UNSAT` as continuation. That is wrong outside one specific counterexample query.

### 6.1 Obligation envelope

Every solver call must be preceded by a frozen obligation record:

```yaml
schema_id: cr.obligation.v2
obligation_id: sha256:...
statement_digest: sha256:...
semantic_contract_digest: sha256:...
logic: QF_BV
domain_bounds:
  n: 16
polarity: prove_nonexistence
expected_status: UNSAT
witness_schema: null
counterexample_schema: cr.counterexample.v1
resource_limits:
  wall_seconds: 120
  memory_mib: 2048
encodings:
  - encoder_id: native_z3_v2
  - encoder_id: native_cvc5_v2
proof_requirement:
  format: alethe
  checker: pinned-independent-checker
mutation_controls:
  - erase_one_demand
  - invert_one_constraint
  - replace_mechanism_with_tautology
```

### 6.2 Result semantics

| Obligation | SAT means | UNSAT means | ClaimGate action |
|---|---|---|---|
| Existence | A candidate witness may exist | No witness exists in the encoded finite domain | SAT succeeds only after witness re-evaluation |
| Nonexistence | A counterexample refutes the claim | The encoded finite nonexistence claim holds | UNSAT succeeds only with nonvacuity and certificate policy |
| Safety violation search | A violating trace exists | No violating trace exists within the checked scope | Preserve SAT trace as valuable negative evidence |
| Equivalence | A distinguishing model may exist, depending on encoding | No distinguishing model exists in scope | Interpretation comes from the frozen polarity |
| Optimization bound | A better model may exist | No better model exists within the exact bound | Do not infer a global optimum outside the bound |

`UNKNOWN`, timeout, OOM, parser failure, unsupported logic, or unchecked proof output yields `PARK`, never `PASS`.

### 6.3 Independence requirements

Running one generated SMT-LIB file through two solvers is useful but does not test the translator.

Higher-tier obligations require:

1. two independently implemented encoders where practical;
2. canonical normalized semantic AST comparison before solver lowering;
3. polarity controls that must flip;
4. demand-erasure controls that must weaken or alter the result;
5. an independently checked proof object for critical UNSAT claims;
6. concrete witness replay for SAT claims.

### 6.4 SMT’s proper relationship to the Ratchet

SMT can determine facts such as:

- whether a finite candidate violates a frozen constraint;
- whether a demanded distinction is collapsed;
- whether a bounded rewrite preserves declared invariants;
- whether a shorter finite word satisfies a coverage property;
- whether a finite associator or commutator witness exists.

SMT cannot establish:

- absolute MSS;
- the correct ontology;
- an unrestricted continuum theorem from a discretization;
- that the Ratchet’s root constraints are uniquely forced.

---

## 7. TLA+ plan

TLA+ belongs in the control plane, not inside the scientific equations.

### 7.1 Separate specifications

Do not write one giant “CodexRatchet universe” specification. Use small composable modules.

| Module | State being modeled | Required invariants |
|---|---|---|
| `ClaimLifecycle.tla` | Draft → frozen → dispatched → evidenced → checked → compared | No self-promotion; contract immutable after freeze; no pass without evidence |
| `ArtifactProtocol.tla` | Generation IDs, hashes, commitment, challenge, finalization | No stale generation; no valid final artifact after partial write; committed bytes cannot change |
| `RatchetTick.tla` | Candidate set, demands, partitions, antichain, Purgatory | Root constraints immutable; comparisons share the same contract; negatives preserved |
| `CloudJob.tla` | Queue, lease, worker, retry, timeout, cancellation | At-most-one accepted finalization; bounded retries; no late result overwrites newer generation |
| `LevBridge.tla` | External supervisor, child process, event evidence, effect authorization | No direct LevOS source mutation; no effect without a valid policy token |
| `Maintenance.tla` | Production lock, candidate lock, regression, promotion, rollback | No dependency promotion without full applicable regression |

### 7.2 Verification ladder

1. **TLC:** exhaust finite small configurations and retain counterexample traces.
2. **Apalache:** run bounded symbolic checks and inductiveness queries.
3. **Runtime conformance:** production components emit events in the same vocabulary; a trace checker rejects impossible transitions.
4. **TLAPS:** prove only stable safety/liveness lemmas after the state machine settles.

### 7.3 TLA+ claim ceiling

A passing model check means:

> No counterexample was found for the stated invariant in the declared model and checked scope.

It does not mean:

- the Python/Node/Rust implementation conforms automatically;
- the numerical science is correct;
- liveness holds without declared fairness;
- an infinite-state property has been proven by a finite TLC run.

---

## 8. ClaimGate v2

ClaimGate should become a small deterministic evidence kernel surrounded by untrusted adapters.

### 8.1 Two gates, not one

#### Preflight

Before compute:

- parse with duplicate-key rejection;
- validate a closed schema;
- reject NaN and infinities;
- freeze the semantic contract;
- freeze claim ceiling, obligations, polarities, metrics, units, tolerances, and cost limits;
- compile the required lane DAG;
- issue a run generation and challenge authority;
- record the exact source/dirty digest.

#### Postflight

After compute:

- verify every required node ran;
- recompute content hashes;
- verify parent/child generation links;
- verify actual executables, locks, devices, process lineage, and termination;
- check metric identity, dtype, shape, units, and tolerance budget;
- check SAT/UNSAT against each obligation’s polarity;
- verify proof objects and concrete witnesses;
- run hostile and deletion controls;
- emit a signed decision receipt.

The producer cannot set `promotion_allowed`, `all_pass`, or its own final verdict.

### 8.2 Distinct status axes

Never collapse these into one `PASS` boolean:

```text
execution_status:
  NOT_STARTED | RUNNING | COMPLETED | TIMEOUT | OOM | INFRA_ERROR

evidence_status:
  INVALID | PARTIAL | COMPLETE | TAMPERED

obligation_status:
  SAT | UNSAT | UNKNOWN | DELTA_SAT | PROOF_CHECKED | NOT_APPLICABLE

candidate_status:
  SUPPORTED_IN_SCOPE | REFUTED_IN_SCOPE | UNRESOLVED | NOT_EVALUATED

governance_status:
  BLOCK | PARK | ADMISSIBLE_TO_RATCHET
```

A valid counterexample can have:

```text
execution_status = COMPLETED
evidence_status = COMPLETE
candidate_status = REFUTED_IN_SCOPE
governance_status = ADMISSIBLE_TO_RATCHET
```

That keeps negative science rather than confusing “candidate failed” with “run invalid.”

### 8.3 Required implementation corrections

The audited session branch currently contains:

- a global `AUTHORITATIVE = ("julia", "jax", "torch", "pytorch")`;
- a fixed Julia/JAX/PySINDy/Z3 stage list;
- global SAT-bad/UNSAT-good logic;
- ordinary JSON parsing;
- a hard-coded personal Python path;
- a metadata-only scientific-looking pass;
- an N/A path for non-object JSON;
- CI wording that says “no NumPy” although contained NumPy is owner-restored;
- `|| true` and `continue-on-error` in CI paths;
- N/A-ok validation paths.

Replace these with:

1. `claim_type_matrix_v2.yaml`;
2. `obligation_registry_v2.yaml`;
3. contract-selected DAG nodes;
4. strict canonical parsing;
5. environment-resolved executable digests;
6. `TRANSPORT_OK` for metadata-only checks;
7. fail-closed expected-schema behavior;
8. explicit informational versus gating CI jobs;
9. predeclared optional nodes rather than inferred N/A.

### 8.4 Recommended implementation language

Do not block progress on a rewrite, but move the smallest trusted core toward a memory-safe compiled executable such as Rust:

- no network;
- no plugin loading;
- closed schemas;
- deterministic canonicalization;
- verifier adapters invoked as child processes;
- signed decision output;
- reproducible build.

Python, Node, Julia, and LLM-produced code remain outside the trusted core.

---

## 9. Ratchet integration

### 9.1 Input boundary

The Ratchet receives:

- validated candidate semantic digests;
- declared demand and probe contracts;
- typed observations;
- exact obstruction and counterexample records;
- valid negative candidates;
- lineage and Purgatory identifiers.

It does not receive:

- arbitrary prose;
- backend self-verdicts;
- untyped scalar scores;
- silently changed probes;
- evidence from different contracts merged into one comparison.

### 9.2 Relative comparison

For a finite candidate-induced partition \(\pi\) and demanded distinctions \(D\), let

\[
L_D(\pi)
\]

measure demanded distinctions collapsed by the partition. Admissible candidates satisfy the declared zero-loss condition. The MSS frontier retains coarsest surviving partitions under refinement and preserves incomparable candidates.

This mechanism should remain distinct from general Pareto ranking. A typed Pareto frontier may be a separate diagnostic, but it must not silently replace the owner’s partition-refinement MSS rule.

### 9.3 Nested towers

The Ratchet compares compatible nested candidate towers, not isolated layer labels stripped from their context.

Each result must record:

- the full candidate tower digest;
- the projection being compared;
- restriction/extension maps;
- demand/probe contract;
- branch lineage;
- unresolved competing towers.

### 9.4 Purgatory

Purgatory must separate:

| Archive class | Meaning |
|---|---|
| `INVALID_EVIDENCE` | Execution or provenance failed; candidate not scientifically evaluated |
| `VALID_COUNTEREXAMPLE` | Candidate refuted in the declared scope |
| `VALID_BUT_DOMINATED` | Evidence valid; candidate loses the current relative comparison |
| `BLOCKED_OBLIGATION` | Evidence valid but a required obligation remains unresolved |
| `SUPERSEDED_CONTRACT` | Result belongs to an older demand/probe/schema version |

Re-offer is triggered by a changed demand, probe, capacity, or contract. It must not mutate the historical record.

---

## 10. External LevOS bridge

The bridge remains outside the LevOS checkout.

### 10.1 Correct role

The bridge:

- launches the deterministic dispatcher through the permitted LevOS path;
- records process and event lineage;
- verifies the actual command executed;
- snapshots or hashes the LevOS source before and after;
- fails closed if host evidence is absent;
- enforces effect permissions;
- does not edit the LevOS repository.

### 10.2 Bridge receipt

```yaml
schema_id: cr.lev_bridge_receipt.v2
levos_commit: ...
levos_tree_before: sha256:...
levos_tree_after: sha256:...
bridge_policy_digest: sha256:...
session_id: ...
event_ids: [...]
child_process_tree_digest: sha256:...
science_contract_digest: sha256:...
claim_gate_preflight_digest: sha256:...
effect_set: [...]
write_attempts_blocked: [...]
exit_status: ...
```

If `levos_tree_before != levos_tree_after`, the bridge blocks unless the owner separately authorized a LevOS change. The CodexRatchet integration path itself never grants that authority.

---

## 11. Science Module

The Science Module is a deterministic experiment compiler and dispatcher. It is not an LLM agent.

### 11.1 Inputs

```yaml
science_contract:
  model_digest: ...
  candidate_set_digest: ...
  claim_type: ...
  claim_ceiling: ...
  demands: ...
  probes: ...
  falsifiers: ...
  observables: ...
  metrics: ...
  obligations: ...
  resource_budget: ...
  required_lanes: ...
  optional_lanes: ...
```

### 11.2 Outputs

- a typed execution DAG;
- immutable job bundles;
- artifact manifests;
- solver obligations and proof receipts;
- candidate and negative evidence packets;
- a complete cost/resource record;
- no self-verdict.

### 11.3 Example DAGs

#### Dense engine dynamics

```text
contract
  ├─ Julia native reference
  ├─ JAX x64 implementation
  ├─ NumPy exact-small control
  ├─ Julia/JAX parity comparator
  ├─ hostile mutations
  └─ ClaimGate postflight
```

#### Exact finite constraint

```text
contract
  ├─ semantic AST
  ├─ independent Z3 encoding
  ├─ independent cvc5 encoding + proof
  ├─ proof checker
  ├─ polarity mutations
  └─ ClaimGate postflight
```

#### Cloud learned rewrite proposal

```text
contract
  ├─ PyTorch/PyG proposal search on GPU
  ├─ deterministic typed rewrite parser
  ├─ Catlab/Maude/Alloy validity checks
  ├─ Julia/JAX observable settlement on survivors
  ├─ ClaimGate postflight
  └─ Ratchet comparison
```

The fixed Julia → JAX → PySINDy → Z3 path remains as one interoperability fixture, not the universal science pipeline.

---

## 12. Cloud GPU architecture

Cloud GPU is a hostile, untrusted compute worker that returns candidate evidence.

### 12.1 Trust boundaries

The cloud worker must not possess:

- ClaimGate decision keys;
- Ratchet authority;
- repository write credentials;
- LevOS trust roots;
- the ability to change the frozen contract;
- the seed used to choose later audit challenges.

### 12.2 Job isolation

Each job uses:

- pinned OCI image digest;
- read-only input bundle;
- isolated writable output directory;
- network denied by default;
- scoped short-lived credentials only when unavoidable;
- fixed wall-time, RAM, VRAM, disk, and cost limits;
- source and dependency lock digests;
- actual GPU UUID and driver/runtime evidence;
- deterministic seed policy;
- explicit nondeterminism declaration where deterministic kernels are unavailable.

### 12.3 Three different checks

Do not call all of these “independence.”

| Check | What it catches | What it does not catch |
|---|---|---|
| Same JAX fixture on CPU and GPU | Device/backend parity, dtype and kernel differences | Shared implementation or semantic bug |
| Native Julia versus native JAX | Independent implementation disagreement | Shared fixture or model-spec error |
| Same artifact reproduced on a second provider/runner | Infrastructure/provider corruption | Shared source/model error |

### 12.4 Commit–challenge protocol

Full CPU reproduction of a huge GPU run is often impossible. Use delayed challenges:

1. GPU worker executes the frozen job.
2. Outputs are chunked and hashed into a Merkle tree.
3. Worker returns the root commitment before seeing the audit challenge.
4. Trusted local control generates challenge indices.
5. Worker returns selected chunks and Merkle inclusion proofs.
6. Local Julia/JAX independently recompute the challenged subproblems.
7. ClaimGate verifies inclusion, recomputation, and challenge timing.
8. High-tier claims additionally require a separate provider or runner.

This does not prove every unchallenged byte correct. The claim level must record challenge coverage and sampling risk.

### 12.5 Good first cloud targets

1. JAX CPU-x64 to NVIDIA parity on a settled small fixture.
2. Hybrid/piecewise engine maps with record-mediated switching.
3. Coupled two-engine fields where contraction no longer settles the question.
4. Full \(D(j,k)\) history-space searches rather than only \(\rho\)-space.
5. Tensor-network contraction paths with exact-small reference values.
6. Factor-graph searches with treewidth and approximation receipts.
7. Candidate generation for major-problem bounded fixtures.

### 12.6 Poor cloud targets

- accelerating a map already proven to have one global fixed point;
- running more random seeds to promote a weak claim;
- treating PyTorch/JAX agreement on one shared builder as independence;
- calling a GPU search a proof;
- claiming a quantum advantage without matched classical cost controls;
- using Reactant/JAX shared XLA output as two independent witnesses.

---

## 13. Major-problem science tracks

The Science Module should enforce a level ladder:

| Level | Requirement | GPU role |
|---|---|---|
| P0 — translation | Exact accepted problem statement, definitions, reductions, and declared finite subproblem | None required |
| P1 — bounded fixture | Known-answer controls, adversarial negatives, exact-small verifier | Optional speedup |
| P2 — candidate mechanism | New invariant/decomposition/dynamics versus strong baselines | Search and proposal generation |
| P3 — scaling/convergence | Resource curves, stability, numerical error and approximation bounds | Large sweeps |
| P4 — formal bridge | Machine-checkable lemma connecting finite work toward the original problem | Candidate/certificate generation only |
| P5 — external validation | Independent expert and machine reproduction | Reproduction support |

No number of P2/P3 GPU runs automatically creates a P4 bridge.

### Recommended campaign pattern

```text
LLM proposes invariant
  -> bounded compiler validates syntax
  -> GPU searches/evaluates
  -> exact-small and hostile controls
  -> formal obligation generator
  -> solver/proof checker
  -> ClaimGate validates
  -> Ratchet compares with rivals
  -> failed candidate enters Purgatory
```

The “special seam” is the formal bridge obligation, not the numerical score.

---

## 14. Artifact and provenance system

### 14.1 Representations

| Object | Representation |
|---|---|
| Tables and scalar time series | Arrow IPC or Parquet with strict schema |
| Dense arrays | Zarr or NPY/NPZ inside a manifest bundle |
| Candidate equation/model | Canonical typed AST |
| SMT obligation | Canonical semantic AST plus solver-specific SMT-LIB |
| TLA+ run | Spec/module digests, configuration, tool version, trace/counterexample |
| Proof | Proof format, proof bytes, checker digest, trust-step inventory |
| Run envelope | Strict canonical JSON |

### 14.2 Mandatory manifest fields

- schema ID and fingerprint;
- semantic contract and obligation digests;
- source commit and dirty-tree digest;
- generation and parent digests;
- actual executable path and binary hash;
- environment lock and container digest;
- dtype, precision, shape, axes, units, order/strides;
- seeds and nondeterminism flags;
- CPU/GPU identity;
- driver/runtime/library versions;
- input/output/intermediate/Merkle hashes;
- process tree and exit reason;
- wall, CPU, RAM, VRAM, I/O, compilation, synchronization, and cost;
- scientific, evidence, obligation, and governance statuses as separate fields.

### 14.3 Provenance

Use:

- in-toto-style step attestations;
- SLSA-compatible provenance for builds and containers;
- Sigstore/Cosign signatures for finalized job bundles and evidence.

Signatures bind identity and bytes. They do not certify the mathematics.

---

## 15. LLM cheat and bias threat model

| Failure pattern | Why an LLM tends to do it | Mechanical defense |
|---|---|---|
| Familiar-object substitution | Replaces a strange carrier with a known set, density matrix, Ising model, or scalar | Closed semantic schema; carrier digest; deletion test for lost distinctions |
| Version averaging | Reconciles conflicting v4–v8 descriptions into a smooth story | Branch/authority labels; conflict ledger; no automatic merge |
| Stage-list normalization | Treats a loop as a linear list or changes its start | Cycle identity modulo rotation plus separate start/direction |
| Axis-6 erasure | Keeps the label but drops the signed mathematical action | Axis-6 term in the semantic AST and mutation test |
| Jungian labels inside formal equations | Lets interpretive language replace the mathematical carrier | Formal equations use neutral identifiers; interpretations live in a separate mapping table |
| Hidden NumPy workhorse | Computes in NumPy and wraps output with JAX/Julia headers | Process isolation, import kill, native graph witness, asymmetric kernel mutation |
| Shared-builder false independence | Julia and JAX consume the same precomputed matrices/results | Shared constants allowed; native construction required; delete intermediate builders |
| Global backend authority | Promotes a library because it appears in a hard-coded tuple | Claim-specific authority registry |
| Post-hoc exemption | Marks a failed numeric run “nonnumeric” | Freeze exemptions in preflight contract |
| SAT/UNSAT polarity laundering | Treats all SAT as bad and all UNSAT as good | Per-obligation polarity and witness schemas |
| Solver tautology | Encodes a trivial statement unrelated to the mechanism | Semantic mutation, demand erasure, independent encoders |
| Metadata-only promotion | Passes hashes and labels without running science | Metadata result is `TRANSPORT_OK`, never scientific admission |
| N/A laundering | Missing evidence becomes “not applicable” | Applicability fixed before run; missing required node parks/blocks |
| Metric renaming | Changes `accuracy` to `accuracy_v2` to escape a floor | Locked metric registry; unknown near-match keys rejected |
| NaN comparison bypass | Floating comparisons with NaN return misleading booleans | Recursive finite-value validation |
| Duplicate-key overwrite | Parser accepts the last of conflicting verdict fields | Duplicate-rejecting parser |
| GPU identity lie | Claims CUDA while executing CPU | Device UUID, kernel/runtime evidence, hostile forced-CPU control |
| More-runs-equals-proof | Converts volume of samples into epistemic promotion | Promotion ladder requires a new certificate class, not a run count |
| Learned rewrite becomes law | PyG proposal score is treated as valid topology | Deterministic rewrite grammar and whole-state settlement |
| Nonassociative reassociation | Optimizer changes bracket order | Explicit bracket-tree digest and ordered kernels |
| History quotient collapse | Samples \(\rho\) while claiming full \(D(j,k)\) fuzz | Carrier-type check and off-diagonal deletion witness |
| Tuned falsifier | Threshold chosen after seeing the result | Preflight locks thresholds and negative controls |
| Mock-to-real drift | Transport canary is described as physics | Payload class is immutable and ClaimGate parks any mock node |
| LLM self-verdict | Producer writes `all_pass: true` | Producer verdict fields ignored or rejected |

---

## 16. Maintenance and update system

“Regularly updated” must not mean changing the production environment immediately before a major run.

### 16.1 Locks

Maintain for every lane:

- one frozen production lock;
- one candidate-upgrade lock;
- one last-known-good rollback lock;
- machine-produced SBOM and capability receipt.

### 16.2 Before every major run

| Gate | Required evidence |
|---|---|
| Repository | Intended branch/commit, dirty digest, submodule/plugin state |
| Contract | Model, cycle, Axis-6, carrier, obligations, claims, falsifiers frozen |
| Binaries | Paths and hashes; no personal hard-coded interpreter path |
| Dependencies | Lock digests and acceptance fixtures for activated libraries |
| Device | CPU/GPU identity, precision, driver/runtime, RAM/VRAM/disk headroom |
| Protocol | TLC/Apalache checks for applicable state machines |
| Numeric | Julia/JAX native fixtures and typed parity |
| Formal | Solver self-tests, polarity tests, proof checker, interval controls |
| Containment | NumPy/PyTorch/search lanes confined to declared roles |
| Serialization | Close/reopen, corruption, truncation, stale-generation controls |
| Host | External LevOS bridge/session/event evidence when required |
| Cloud | OCI digest, credentials, network policy, cost cap, commit–challenge plan |
| Governance | ClaimGate preflight result; no missing required nodes |

Outcome:

- `RUN`
- `PARK`
- `BLOCK`

There is no “run anyway and explain later” state for a promotion-bearing job.

### 16.3 Cadence

| Cadence | Action |
|---|---|
| Every major run | Full activated-lane preflight |
| Weekly | Read-only version, vulnerability, and driver drift inventory |
| Monthly or campaign boundary | Candidate-lock upgrades and full regression |
| After JAX/Julia/CUDA/driver changes | CPU/GPU parity and performance requalification |
| After ClaimGate/Ratchet protocol changes | TLC/Apalache and runtime trace-conformance suite |
| Before high-cost cloud campaign | Budgeted dry run, exact-small fixture, hostile worker test |

---

## 17. Repository-specific repair ledger

The following items were directly observed in local branch
`session/r0-three-engine-probes` at commit
`fe9673568ec1b95553b44fe6b455c54ee2063320`.

| Repair | Priority | Acceptance condition |
|---|---|---|
| Consolidate intended session work with the GitHub default branch | P0 | One owner-approved branch/commit is named as current; CI runs there |
| Replace global backend authority tuple | P0 | Claim-specific registry tests show PyTorch cannot authorize unrelated claims |
| Rename “no NumPy” workflow and comments | P0 | Contained NumPy passes; load-bearing NumPy fails |
| Remove hard-coded local Python path | P0 | Executable resolved from frozen environment and hashed |
| Strict duplicate/finite JSON parser | P0 | Duplicate, NaN, infinity, and non-object hostile receipts reject |
| Replace fixed stage list with contract DAG | P0 | Numeric, exact-formal, and protocol fixtures each invoke only required nodes |
| Fix SMT polarity | P0 | SAT-existence and UNSAT-nonexistence fixtures both succeed correctly; inversions fail |
| Demote metadata-only pass | P0 | CI emits `TRANSPORT_OK`; cannot satisfy scientific admission |
| Remove or isolate `|| true`, `continue-on-error`, and N/A-ok gates | P0 | Required jobs fail closed; informational jobs are visibly non-gating |
| Preserve schedule-tournament rejection as apparatus evidence only | P0 | No schedule conclusion is drawn from a degenerate/invalid reference fixture |
| Add TLA+ protocol estate | P1 | Claim lifecycle and artifact protocol pass TLC/Apalache hostile traces |
| Add proof-producing cvc5 path | P1 | Checked UNSAT proof, trust-step inventory, mutation controls |
| Extend Lean microcore | P1 | Cyclic-loop equivalence, partition refinement, and selected finite lemmas compile |
| Add supply-chain attestation | P2 | Cloud job source/container/artifacts form a verifiable provenance chain |
| Add cloud commit–challenge | P2 | Forced tampering and precomputed-response attacks reject |
| Add deterministic renesting grammar | P3 | PyG proposals cannot execute until typed rewrite and whole-state checks pass |

The connected GitHub default branch visible during this audit lagged the local session branch. Until the intended changes are consolidated, GitHub CI cannot be assumed to enforce the current architecture.

---

## 18. Proposed repository layout

```text
system_v9/
  contracts/
    model/
      engine_spec_v2.schema.json
      manifold_candidate_v2.schema.json
    science/
      science_contract_v2.schema.json
      claim_type_matrix_v2.yaml
      obligation_registry_v2.yaml
      metric_registry_v2.yaml
  claimgate/
    core/
    adapters/
    policies/
    hostile_tests/
  ratchet/
    partition_kernel/
    nested_tower/
    purgatory/
    tests/
  science_module/
    planner/
    local_runner/
    cloud_runner/
    artifact_store/
    challenge/
  formal/
    tla/
      ClaimLifecycle.tla
      ArtifactProtocol.tla
      RatchetTick.tla
      CloudJob.tla
      LevBridge.tla
    lean/
    smt/
      semantic_ast/
      z3_encoder/
      cvc5_encoder/
      bitwuzla_encoder/
      proof_checkers/
    rewriting/
    intervals/
  sim/
    julia_reference/
    jax_workhorse/
    numpy_controls/
    pytorch_proposers/
  bridge/
    levos_external/
  env/
    julia-reference/
    jax-cpu/
    numpy-satellite/
    formal-smt/
    formal-tla/
    cloud-jax-cuda/
    cloud-pytorch/
    cloud-specialists/
  provenance/
  maintenance/
  receipts/
```

Do not call this `system_v9` merely because the directory exists. Version promotion occurs only after owner selection and migration tests.

---

## 19. Adoption sequence

### Phase 0 — authority and branch freeze

1. Name the owner-approved current branch/commit.
2. Freeze `claim_type_matrix_v2`.
3. Freeze the engine semantic digest fields.
4. Preserve old versions without merging their semantics.

### Phase 1 — ClaimGate containment

1. Strict parser and canonicalization.
2. Contract-selected DAG.
3. Per-obligation polarity.
4. Distinct status axes.
5. Remove metadata/N/A/`|| true` promotion paths.
6. Rewrite CI wording around contained NumPy.

### Phase 2 — protocol formalization

1. `ClaimLifecycle.tla`.
2. `ArtifactProtocol.tla`.
3. TLC exhaustive small-state fixtures.
4. Apalache bounded/invariant checks.
5. Runtime event trace conformance.

### Phase 3 — proof lane

1. cvc5 proof output and independent checker.
2. Bitwuzla machine-arithmetic fixtures.
3. Independent encoders and semantic mutations.
4. Lean microcore extension.

### Phase 4 — provenance and cloud

1. OCI job schema.
2. in-toto/SLSA/Cosign provenance.
3. JAX CPU/GPU parity pilot.
4. Merkle commit–challenge.
5. Second-runner reproduction policy.

### Phase 5 — open scientific mechanisms

1. Hybrid/piecewise basin searches.
2. History-pair fuzz experiments.
3. Coupled engine-field searches.
4. Deterministic graph renesting.
5. Tensor/factor contraction scaling.

### Phase 6 — major-problem campaigns

Start only after P0/P1 fixtures, claim ceilings, proof-lane interfaces, and cloud evidence paths are functioning.

---

## 20. Acceptance tests for the architecture

The architecture is not integrated until all of these are machine-tested.

1. A contained NumPy analysis runs and cannot change a scientific verdict directly.
2. A NumPy-hidden workhorse with JAX headers is rejected.
3. A PyTorch-only numeric schedule receipt is rejected for a claim requiring independent numeric witnesses.
4. A PyTorch graph proposer is accepted as a proposal while its invalid rewrite is rejected by the deterministic rewrite kernel.
5. A SAT existence witness is accepted after replay.
6. A SAT counterexample refutes but does not invalidate the run.
7. An UNSAT claim with a broken proof is parked.
8. An SMT tautology passes the solver but fails semantic mutation.
9. A duplicate-key receipt is rejected before object construction.
10. A NaN metric is rejected.
11. A metadata-only receipt cannot enter Ratchet comparison.
12. A cyclic rotation preserves loop identity while a reversed direction changes it.
13. An Axis-6 sign mutation changes the semantic digest and demanded observable.
14. A nonassociative bracket mutation changes the bracket-tree digest and result.
15. A density-only run cannot claim full history-pair coverage.
16. A stale cloud generation cannot overwrite a newer result.
17. A cloud worker cannot predict the post-commit challenge.
18. A forged GPU claim fails device evidence.
19. A partial artifact cannot finalize.
20. A missing optional node is allowed only when predeclared optional.
21. A missing required node parks or blocks.
22. A valid negative candidate is preserved in Purgatory.
23. An LLM-written `all_pass: true` is ignored or rejected.
24. A LevOS-path claim without real session/event evidence blocks.
25. The LevOS checkout remains byte-identical after external-bridge runs.

---

## 21. Final target layout

The best compact description is:

> **Owner-frozen contracts define the model and obligations. ClaimGate preflight freezes the run. A deterministic Science Module dispatches isolated, claim-specific local or cloud lanes under an external LevOS supervisor. Julia and JAX provide independent numerical implementations where the claim requires them; NumPy analyses and vetoes without becoming a hidden workhorse; PyTorch proposes learned candidates only where earned; SMT, proof, temporal, rewrite, and interval tools certify only their explicitly encoded obligations. ClaimGate validates the returned evidence, and the Ratchet performs finite relative comparison without proving absolute MSS.**

That is stronger than:

```text
Julia → JAX → NumPy → SMT → ClaimGate → Lev
```

because it prevents a fixed pipeline, a library name, a cloud device, or an LLM narrative from silently becoming authority.

---

## 22. Primary external references

- TLA+ tools and TLC: <https://github.com/tlaplus/tlaplus>
- Apalache symbolic TLA+ checker: <https://apalache-mc.org/>
- cvc5 proof production: <https://cvc5.github.io/docs-ci/docs-main/proofs/proofs.html>
- Bitwuzla supported theories: <https://bitwuzla.github.io/docs/index.html>
- Lean 4 theorem proving: <https://docs.lean-lang.org/theorem_proving_in_lean4/>
- Lean axioms and trust boundary: <https://lean-lang.org/doc/reference/latest/Axioms/>
- Maude strategies and model checking: <https://maude.ucm.es/strategies/>
- Alloy 6: <https://alloytools.org/>
- ReachabilityAnalysis.jl: <https://juliareach.github.io/ReachabilityAnalysis.jl/>
- dReal: <https://dreal.github.io/>
- CUE configuration and validation: <https://cuelang.org/docs/introduction/>
- in-toto: <https://in-toto.io/>
- SLSA specification: <https://slsa.dev/spec/v1.2/>
- Sigstore/Cosign container signing: <https://docs.sigstore.dev/cosign/signing/signing_with_containers/>

