# Ratchet mechanics

This is a structural map of every part of the ratchet as it is actually built and run in
this repo, checked against `ROOT/` and `system_v7/constraint_core/RATCHET_SPEC.md`. It sets
out what each part is, what it is built from, and how far it has been checked — nothing
more.

## Bottom line

The ratchet's core logic — partition, `L_D`, coarseness, frontier, purgatory — is real code,
not prose, and every self-test and self-check reran clean in this session. Two bundles
(`ratchet_contract` core, `ratchet_contract/bridge_validation`) have been through a
fresh-context adversarial audit and came back `CLEAN`, with every finding either fixed or
named as an open caveat. Since the current commit (`d419077`, 2026-07-20 21:32), the
trace-to-partition bridge has also flowed once on two small real (non-toy) carriers — a
qutip 2-qubit density matrix and a classical finite relation — through the whole pipeline,
not only toys. Three things still cap every claim at practice: the pool-level fuel gate
(Principle Zero) currently returns `HOLD` on the only candidate pool that exists; the
SMT-relational bridge is not yet an independent decider, only a gated echo of the same
Python recursion; and no engine adapter (Julia, JAX, or PyTorch) is wired — the one live
numeric substrate today is qutip, called directly, bypassing that interface. Count:
2 audited-clean bundles (18 individual checks) against 7 named open gaps. Detail below.

## Owner's root claim, in one paragraph

`ROOT/ROOT_CARD.md` outranks everything below it: "This directory holds OWNER VERBATIM
only. It outranks every spec, pack, wiki concept, memory file, and machine-generated draft
in this repository." Its own words: MSS, ratchet, tower, nesting, nested ratchet, and
replicators "are all the 'same thing' stated in different ways" — one minimal evolving
persistent structure that ratchets, nests, and replicates
(`OWNER_VOICE_ratchet_core_20260704.md`). The nesting law: "everything has to run on
density matrices if it is the MSS... though there might be deeper MSS under them. and they
run on that. then all the math is CONSTRAINED by the previous rungs." Everything below this
section is the machine engineering built to test that claim. `ROOT_CARD.md` is explicit that
"the kernel/pawl/purgatory vocabulary of the July pack lineage is machine draft, not owner
spec. Usable as engineering, never citable as doctrine." Read what follows in that light: it
describes what the engineering currently does, not a restatement of the owner's model.

## How to read "degree working" below

This repo's status ladder is fixed by `CLAUDE.md`: `exists < runs < passes local rerun <
canonical by process`, and a lower label never implies a higher one. `canonical by process`
needs a `SIM_TEMPLATE`, a tool manifest, and a `classification` field; none of the
ratchet-mechanics components carry those (they are infrastructure and contract code, not
registered probes). So every row below caps at `passes local rerun`, at best.

Layered on top of that ladder, this repo separately tracks a fresh-context adversarial audit
as its own fact, tagged `audited CLEAN` where one exists, and `HOLD` where a gate's own
honest verdict is `HOLD` rather than a defect. `audited CLEAN` is not a fifth rung above
`canonical by process` — it answers a different question (did an independent reviewer try
to break this and fail) from the ladder's question (has this gone through the
sim-registration pipeline).

Every claim below marked "fresh, this session" was rerun as part of this task, not taken on
a prior report's word. See the verification log near the end for the full list.

## Table 1: every part of the ratchet

| Part | Formula / definition | Degree working | Code file |
|---|---|---|---|
| Kernel (finite process tick) | Declared root form: `A_r = {p ∈ P_r : C_r(p, M_r(p))}`, `F_{r,i} = Min_⪯i(A_r)` (`ROOT/ROOT_RATCHET_KERNEL_pack178.md`). As implemented (current process authority): `run_packet()` chains `generate_observations` → `build_demand_families` → `explore_candidate_population` → `compute_frontier_cache` → `execute_schedules` (`RATCHET_SPEC.md` v0.5) | Self-test, passes local rerun (fresh, this session: `PASS order_open_ratchet_v0_5`). Runs on generated combinatorial fixtures only; has never called Julia, JAX, or PyTorch | `system_v7/constraint_core/ratchet/ratchet_engine.py` |
| `L_D` coface (entropy-geometry coface) | `L_D(π) = \|{(x,y) ∈ D : π(x)=π(y)}\|` — one quantity, two readings: geometrically, a demanded edge collapsed inside a block; informationally, a demanded distinction left unresolved (`RATCHET_SPEC.md` §3) | Self-test, passes local rerun (fresh, same run as the kernel row). Ported byte-for-byte into `gates.py`, where it is audited `CLEAN` | `ratchet_engine.py` (`collapsed_demand_edges` field per behaviour row); `ratchet_contract/gates.py` (`collapsed_demand_edges()`) |
| Partition-coarseness MSS | `π ⪯ ρ` when every block of `ρ` lies inside one block of `π` (`π` is no more discriminating than `ρ`); `M(D) = min_⪯ Surv(D)` (`RATCHET_SPEC.md` §6) | Audited `CLEAN`, passes local rerun (fresh, this session). `AUDIT_VERDICT.md`: "4 boolean guards over `partition_coarser` only... no score/count/weighted sum" | `ratchet_engine.py` (`_partition_coarser`, `compute_frontier_cache`); `gates.py` (`partition_coarser`); `ratchet_contract/mss.py` (`pairwise_mss`) |
| Survivors | `Surv(D) = {π : L_D(π) = 0}` — every candidate that preserves every demanded distinction in the active family set | Passes local rerun (fresh, both homes, this session). Also exercised on 2 real, non-toy carriers in the first real-carrier run: 1 survivor | `ratchet_engine.py` (filter inside `compute_frontier_cache`); `mss.py` (`frontier()`'s `survivors`) |
| Frontier-antichain | `F_r = Min_⪯(S_r)` — the coarsest survivors; incomparable minima all stay; no scalar picks one (`ROOT/RATCHET_KERNEL_AND_BOUNDARIES_pack178.md`) | Passes local rerun (fresh, this session). Real-carrier antichain currently has 1 member — the rival left the comparison at eligibility/thickening, before the coarseness stage was reached, so this is not a case of a scalar excluding an incomparable minimum | `ratchet_engine.py` (`frontier` list); `mss.py` (`frontier()`'s `antichain`) |
| Purgatory | Records with an immutable context fingerprint, a named failure stage, and a re-entry condition (`ROOT/RATCHET_KERNEL_AND_BOUNDARIES_pack178.md`; `RATCHET_SPEC.md` §7's `UNRESOLVED_GATE__DIG_CONTINUES`) | Audited `CLEAN`, passes local rerun. Demonstrated on a real carrier: `classical_relational_exec_pkg` landed in purgatory, `failed_at: persistence_demand`, with a named `re_entry_condition` | `mss.py` (`frontier()`'s `purgatory`, `_RE_ENTRY_CONDITIONS`) |
| Branches / re-merge | Two branches inducing the same partition digest re-merge into one — convergence is basin evidence inside the packet, never a canonical path (`RATCHET_SPEC.md` §4) | Audited `CLEAN`, passes local rerun (fresh, this session; `toy_quotient_respecting`/`toy_amnesiac` merge into one branch) | `mss.py` (`frontier()`'s `branches`) |
| Fuel gate + 6 slots + Principle Zero | 4 mechanical checks: required slots, real diversity, provenance present, executable enough. 6 required slots: `incumbent`, `minimal_rival`, `structural_rival`, `order_nesting_rival`, `countermodel`, `ablation_control` | `HOLD`, passes local rerun (fresh, this session: exit 1, `HOLD_INSUFFICIENT_FUEL`, matching the documented state exactly). Self-verified against a synthetic complete pool (exit 0) and a single-slot-removed pool (flips back to `HOLD`, naming the removed slot) — not yet through a fresh-context adversarial audit | `fuel_gate/fuel_adequacy_gate.py` |
| Execution contract + identity gate + thicken-D | `CandidatePackage` (8 required methods). `IDENTITY_GATE`: `π_probes == π_reidentify` → `PASS` (a=a iff a~b, earned); strictly finer → `FAIL` (unearned); strictly coarser → `HOLD` (new probe needed). Thicken-D: `persistence_gate`/`evolvability_gate`/`extension_gate` push `D` through a continuation and re-check with the same kernel | Audited `CLEAN`, passes local rerun (fresh, this session). 2 findings from the 2026-07-20 audit (F1, F2), both fixed the same day and now demonstrated firing inside `selfcheck.json` itself | `ratchet_contract/contract.py`, `ratchet_contract/gates.py` |
| The two bridges | Action-predictive: `h ~_C h'` iff replaying every action word `u`, `\|u\| ≤ H`, from `h` and `h'` gives identical `Outcome` traces. SMT-relational: the same recursive definition, decided by a chain of solver Bool variables, `SAT` = distinct / `UNSAT` = same block | Audited `CLEAN`, passes local rerun (fresh, this session: 9/9 controls + 3/3 self-tests fired as expected). 2 named caveats remain open (table 3b) | `ratchet_contract/bridge_validation/bridge_action_predictive.py`, `bridge_smt_relational.py`, `bridge_interface.py`, `controls.py`, `bridge_self_tests.py` |
| SMT admission law | `SAT_B(C) ∧ UNSAT_B(C ∧ ¬φ)` — a satisfiable base plus an absent bounded countermodel; every solver model replayed in the executable semantics (`ROOT/RATCHET_KERNEL_AND_BOUNDARIES_pack178.md`; cited in `ROOT/HOW_THE_ENGINES_RUN_THE_RATCHET.md` point 9 and `ROOT/RUNNING_THE_RATCHET_ON_ENGINES_AND_LEV.md`'s division-of-labour table) | Exists as a declared law. Runs only as an embedded same/different instance inside the SMT-relational bridge (`s.add(Not(same_H)); s.check()` — the same UNSAT-of-negation shape, deciding one partition edge, not a general claim `C`). No standalone artifact carries this name to rerun on its own, and the embedded instance carries the SMT-not-independent caveat (table 3b) | No standalone file. Running instance: `bridge_smt_relational.py` (`_decide_same_z3`, `_decide_same_cvc5`) |

### The six gates, broken out

`adequacy` combines the other six; the worst verdict wins (`FAIL` beats `HOLD` beats
`UNRESOLVED`).

| Gate | Verdicts | What it checks | Status |
|---|---|---|---|
| `buildability_gate` | `PASS`/`FAIL` | candidate instantiates and runs its own probes on its own states without error | passes local rerun, audited `CLEAN` |
| `probe_validity_gate` | `PASS`/`HOLD`/`FAIL` | `D` separates the declared positive controls (else `HOLD`); `D` never falsely separates the declared negative controls (else `FAIL`) | passes local rerun, audited `CLEAN`; the negative-control path was added 2026-07-20 (finding F1) |
| `IDENTITY_GATE` | `PASS`/`FAIL`/`HOLD` | `reidentify()` exactly reproduces the probe-induced partition — the executable form of a=a iff a~b | passes local rerun, audited `CLEAN` |
| `persistence_gate` | `PASS`/`FAIL`/`UNRESOLVED` | `D`'s distinctions survive being pushed through `persist()` (delay/perturbation/relabel/partial-access) | passes local rerun, audited `CLEAN` |
| `evolvability_gate` | `PASS`/`FAIL` | `D`'s distinctions survive being pushed through `evolve(new_constraint)`, with no new primitive smuggled in | passes local rerun, audited `CLEAN`; the D-collapse and primitive-smuggle `FAIL` paths were added 2026-07-20 (finding F2) |
| `extension_gate` | `PASS`/`FAIL`/`HOLD` | a declared `nest_interface` recompute digest matches a fresh recompute of the induced partition | passes local rerun, audited `CLEAN` |

## Table 2: the boundary — who does what

| Actor | Allowed to | Never allowed to | Evidence in this repo |
|---|---|---|---|
| LLMs / councils (Claude, codex, grok) | supply and vet fuel: candidate packages, probes, demand-set (`D`) proposals, weakness-relation proposals; judge "genuine rival vs. strawman" | compute relative MSS, presumption, or any tooth | `system_v8/candidates/RANKING_VOID_llm_did_ratchets_job.md` — the binding incident. An LLM ranked 4 candidates by presumption, a second LLM "corrected" the ranking, the owner voided both: "an LLM is the entity MOST committed to primitive identity... the worst possible judge of that exact metric" |
| Code (`contract.py`/`gates.py`/`mss.py`/`ratchet_engine.py`) | compute partitions, `L_D`, coarseness, frontier, purgatory, branch merges — the sole operator on relative MSS | stand in an LLM verdict for any of the above | `ratchet_contract/README.md`'s boundary section; `selfcheck.json`'s `no_llm_or_network_calls_clean: true` (reconfirmed fresh this session) |
| Fuel gate + ClaimGate | decide pool eligibility and receipt admission, by exit code, before and after the ratchet runs | rank candidates against each other | `fuel_gate/README.md`: "It does not rank candidates... only on whether the pool... has the shape a pairwise comparison would need" |
| Lev OS | schedule each stage as a verifier-gated exec job (`lev exec "<step>" --verifier="python3 <gate>.py <args>"`), replay, keep provenance, write an immutable `exec.gate.run` receipt | judge MSS, or silently skip a verifier | `ROOT/RUNNING_THE_RATCHET_ON_ENGINES_AND_LEV.md`'s stage-by-stage list, as documented. Independently spot-checked this session: `~/.local/share/lev/events/runtime-events.jsonl` is live (370 events; 7 `exec.gate.run` entries dated 2026-07-16 to 2026-07-20; "claimgate" appears 13 times in the log). This session did not trace one specific event to one specific Codex-Ratchet ClaimGate run, so that narrower claim in the source doc stands as documented, not independently re-confirmed here |
| Engines (Julia canon / JAX workhorse / PyTorch learned) | emit the finite behaviour traces the trace-to-partition bridge turns into `π` | decide MSS themselves, or stand in for the partition kernel | `contract.py`'s `JuliaEngineAdapter`/`JaxEngineAdapter`/`PyTorchEngineAdapter` all raise `NotImplementedError` — interface-only. The one real numeric substrate running today is qutip, called directly inside `candidate_spinor_qit_exec.py`; it bypasses the `EngineAdapter` interface entirely, so the adapter layer itself is still untested by real use |

## The first real-carrier run (current HEAD, 2026-07-20 21:32, commit `d419077`)

Older docs in the read list describe the trace-to-partition bridge for real carriers as the
open target: `ROOT/HOW_THE_ENGINES_RUN_THE_RATCHET.md` calls it "the TARGET; currently a
gap," `ROOT/RUNNING_THE_RATCHET_ON_ENGINES_AND_LEV.md` marks it "[THIS IS THE MISSING
PIECE]," and `ratchet_contract/README.md`'s own "State" section (dated 16:51 the same day)
says "nothing here has been run on a real candidate." All three predate the current commit.
Since then, `ratchet_contract/fuel_sims/practice_run.py` has run that exact bridge once, on
two small real, non-toy carriers: the owner's proposed model as a real qutip 2-qubit
density-matrix candidate (GKSL/Lindblad amplitude damping via `mesolve`, Born-rule integer
shot counts, no floats) against a classical finite-relation rival, over the same 18-action
deck. The gap is now partially closed, at practice scale — one pair, one deck, horizon 1–2,
not yet audited, not yet generalised.

| Stage | What ran | Result |
|---|---|---|
| (a) `fuel_adequacy_gate`, on the real pool `system_v8/candidates/` | Principle Zero against the actual 4-candidate pool | `HOLD_INSUFFICIENT_FUEL` — the same missing slots as table 1's fuel-gate row, inherited by this pair because it is drawn from that pool |
| (b) `induce_action_predictive_partition`, horizon 1, thickened to 2 | 2 real carriers over an 11-point deck, 18-action shared vocabulary, 4 demanded pairs | spinor separates all 4 demanded pairs at horizon 1; classical separates 3 of 4 at horizon 1, and still 3 of 4 at horizon 2 (the order-sensitivity pair, at one specific root, stays merged) |
| (c) `IDENTITY_GATE` | both adapted candidates | both `PASS` — both partitions are probe-honest |
| (c) `persistence_gate(delay=5)` | both | spinor `PASS`; classical `FAIL` (2 demanded pairs collapse under delay plus perturbation) |
| (c) `evolvability_gate(require_purity)` | both | spinor `PASS`; classical `FAIL` (the order-sensitivity pair collapses) |
| (c) `frontier()` | both, demand-thickened | 1 survivor (spinor), 1 purgatory entry (classical, `persistence_demand` then `evolvability_demand`), antichain = [spinor] |
| (c) `pairwise_mss` (base, no thickening) | both | `HOLD` at `base_survivorship` — classical's own base partition already fails to separate the order pair |

Two things keep this at practice, named by the build itself rather than found later:

1. "Spinor survives, classical reaches purgatory" is a named practice artifact, not an MSS
   finding. The commit message traces the classical candidate's loss to its own
   `_delay_step` design and a root confound: from `root_plus0`, the `H0` rewrite lands on a
   symmetric fixed point where `CNOT01` is a no-op regardless of order — a fact about that
   one starting state, not a general order-insensitivity claim. Re-rooted at `root_00`, the
   same order pair separates cleanly and survives delay for both carriers (the
   "unconfounded" diagnostic in `practice_run.json`).
2. A genuine code finding, not yet fixed: `collapsed_demand_edges` cannot currently tell
   "never separated" apart from "separated, then lost under a continuation" — both read as
   one collapsed edge.

Verification note: the commit claims "passes local rerun (byte-identical x2)" by its own
builder. This session's own attempt to rerun `practice_run.py` fresh was blocked by the
file's own memory gate (22.9% available memory observed against a 25% floor required before
it will import qutip) — a genuine fail-closed refusal, not a code defect, and itself a small
piece of evidence that the gate checks a live condition rather than being decorative. This
session read the on-disk `results/practice_run.json` directly rather than treating the
builder's self-report as independently confirmed.

## Table 3a: audited-clean

| Component | Audit | What was checked | Findings |
|---|---|---|---|
| `ratchet_contract` core (`contract.py`/`gates.py`/`mss.py`) | fresh-context opus adversarial, 2026-07-20 | 6 targeted attacks: score-smuggling in `pairwise_mss`, genuineness of the `IDENTITY_GATE` `FAIL`, gate vacuity, demand-thickening behaviour, kernel-port fidelity against `ratchet_engine.py`, absence of LLM/network calls | 2 low-severity findings (F1: dead negative-control scaffolding; F2: under-shown `FAIL` branches), both fixed the same day and now demonstrated in `selfcheck.json` |
| `ratchet_contract/bridge_validation` (`bridge_action_predictive.py`/`bridge_smt_relational.py`/`controls.py`/`bridge_self_tests.py`) | fresh opus adversarial, 2026-07-20 | 12 checks (9 controls + 3 self-tests) independently re-derived and matched against `results/bridge_validation.json` | 2 non-fatal caveats, named but not fixed — carried into table 3b |

## Table 3b: open gaps

| # | Gap | What it means | Where |
|---|---|---|---|
| 1 | SMT bridge is not independent | `induce_smt_relational_partition` unions a pair only when `decision.reference_same` (the pure-Python recursion) is true; z3 and cvc5 gate agreement with that recursion, they do not decide the partition themselves | `bridge_smt_relational.py`, confirmed by reading the `union()` call directly |
| 2 | Trace-to-partition bridge for real carriers | named the missing piece in the older `ROOT/` docs; now partially demonstrated (2 real carriers, 1 deck, practice scale only, not yet audited or generalised) | `ratchet_contract/fuel_sims/` |
| 3 | D-too-thin | the demand set `D` must be thick enough to separate carriers; a 9-carrier `base_campaign` run returned `restricting_outer_changes_inner: false` | `ROOT/HOW_THE_ENGINES_RUN_THE_RATCHET.md` Part C.3, as documented (not independently rerun this session — out of this task's read list) |
| 4 | Pool-level fuel-adequacy `HOLD` | Principle Zero currently blocks every pairwise comparison drawn from `system_v8/candidates/`, including the first real-carrier pair | missing `countermodel` + `ablation_control` slots; 3 of 4 required model families; 11 provenance gaps |
| 5 | Engine adapters stubbed | `JuliaEngineAdapter`/`JaxEngineAdapter`/`PyTorchEngineAdapter` all raise `NotImplementedError`; the one live numeric engine (qutip) bypasses this interface entirely | `contract.py` |
| 6 | `collapsed_demand_edges` conflation | cannot yet distinguish "never separated" from "separated, then lost" | `gates.py`, named in the practice-run commit, not yet fixed |
| 7 | Practice-pair result is a named artifact, not an MSS finding | traced to the classical candidate's own design and a root-specific confound, not a general carrier-family property | `fuel_sims/practice_run.py`'s own diagnostic sections |

## What was rerun fresh this session

| Command | Result | Matches documented state |
|---|---|---|
| `ratchet_engine.py --self-test` | `PASS order_open_ratchet_v0_5` | yes |
| `ratchet_contract/run_contract_selfcheck.py` | `overall_ok: true` (all 4 confirmations true) | yes |
| `ratchet_contract/bridge_validation/run_bridge_validation.py` | `overall_ok: true` (all 5 confirmations true) | yes |
| `fuel_gate/fuel_adequacy_gate.py` | exit 1, `HOLD_INSUFFICIENT_FUEL`, same missing slots and provenance gaps | yes |
| `ratchet_contract/fuel_sims/practice_run.py` | blocked by the file's own memory gate (22.9% available, below the 25% floor) | not independently rerun this session; the on-disk receipt was read directly instead |

## Counts: audited-clean vs open

| Bucket | Count | Detail |
|---|---|---|
| Audited-clean bundles | 2 | `ratchet_contract` core (6/6 attacks clean); `bridge_validation` (12/12 checks re-derived) |
| Individual audited-clean checks | 18 | 6 contract-audit attacks + 12 bridge-validation checks, all reconfirmed by a fresh rerun this session |
| Running clean, not yet audited | 2 components | `ratchet_engine.py` kernel self-test (its own anti-fake-running invariants, but no separate fresh-context adversarial pass on file); `fuel_adequacy_gate.py` (self-verified against a synthetic pool, no separate fresh-context adversarial pass on file) |
| Open gaps, named | 7 | listed in table 3b |

Bottom-line count: 2 audited-clean bundles, 18 individual clean checks, against 7 named open
gaps.
