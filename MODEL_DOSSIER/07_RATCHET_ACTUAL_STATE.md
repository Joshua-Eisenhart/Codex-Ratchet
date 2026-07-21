# Ratchet actual state: what it can ratchet today, and why

Bottom line. The ratchet's judgment machinery (the six gates plus partition-coarseness
MSS in `ratchet_contract/`) is real code, audited clean, and reruns clean. It has flowed
end to end exactly once, on two small executable 2-qubit toy carriers, and that one run
returned honest holds at both ends: the candidate pool itself is on a fuel-adequacy hold,
and the pairwise result inside that hold is a named practice artifact, not a carrier-family
verdict. No layer of any of the four proposed manifolds beyond a thin executable slice
exists as code. No presumption ranking between the four candidates exists — the one that
was computed was computed by an LLM, and that is void by the project's own rule, for a
reason worth taking seriously: an LLM is structurally the entity most committed to
primitive identity, which leaves it the worst available judge of how little primitive
identity a candidate installs.

## Scope and sources

This document covers the pipeline named in the build task: `fuel_adequacy_gate.py` (repo
root `fuel_gate/`) feeding `bridge_action_predictive.py` feeding `gates.py`/`mss.py`
(`ratchet_contract/`), run against the four-candidate pool in `system_v8/candidates/`.
Sources read: `ratchet_contract/fuel_sims/results/practice_run.json` and its source
commit `d41907742`; the four candidate files, `STRAWMAN_AUDIT.md`,
`RANKING_VOID_llm_did_ratchets_job.md`, `PRESUMPTION_RANKING_CORRECTION.md`, and the two
`judge_rival_*.md` files in `system_v8/candidates/`; `ratchet_contract/README.md`,
`ratchet_contract/results/AUDIT_VERDICT.md`, `ratchet_contract/results/selfcheck.json`,
and `ratchet_contract/bridge_validation/results/AUDIT_VERDICT.md`;
`fuel_gate/fuel_adequacy_gate.py` and its manifest and verdict;
`system_v7/constraint_core/RATCHET_SPEC.md`; `system_v8/README.md`; and the `ROOT/`
verbatim-authority docs. `MODEL_DOSSIER/` held no other lane's file when this one was
written.

Two adjacent programs live in this repo and are deliberately out of scope here: the
`system_v7/constraint_core` manifold-layer audit ladder (a separate, older lane with its
own L1–L8 status report), and the `system_v8/loop3_senses` perception/world-engine lane
(the "senses before scale" thread visible in the recent commit log). Neither is the
fuel/pool/gate ratchet this document reports on; folding them in would blur two distinct
narratives that should stay distinct.

Two of the source files were reran fresh in this session rather than taken on the
commit's word: `ratchet_engine.py --self-test` and `run_contract_selfcheck.py`. Both
exited 0 with output byte-identical to the committed receipts (confirmed with `git diff
--stat`, no changes). Where a status below rests on that rerun, it is labelled `passes
local rerun` and dated to this session. Where it rests only on a commit's own claim
(the qutip-dependent practice run, which needs the sim-stack interpreter this task did not
call for re-executing), it is labelled `runs` and attributed to the commit, not to this
session's verification.

## 1. What the ratchet can actually ratchet today

### Can ratchet today

| Capability | Status | Evidence |
|---|---|---|
| Fixture-grammar self-test in the order-open kernel: all 75 ordered set-partitions of 4 demand families executed, over 10,000 parameter proposals run, alias census non-empty, chunking- and relisting-invariance confirmed, three deliberately-corrupted inputs (canonical-order claim, decorative dig pool, re-admitted killed receipt) correctly rejected | `passes local rerun` (reran this session, exit 0, `PASS order_open_ratchet_v0_5`) | `system_v7/constraint_core/ratchet/ratchet_engine.py --self-test`, fixture `ratchet/examples/root_order_open_packet_v0_5.json`. Different lane from the v8 pool; `ratchet_contract` cites it only as the byte-for-byte source of its own coarseness kernel. |
| Toy-candidate discrimination and pairwise MSS in the execution contract: 4 built toys (`toy_raw_label`, `toy_quotient_respecting`, `toy_frozen`, `toy_amnesiac`) exercise every one of the 6 gates plus `adequacy` to at least 2 distinct verdicts each (none vacuous), and `pairwise_mss`/`frontier` return real `A_WEAKER`, `B_WEAKER`, `INCOMPARABLE`, and `HOLD` outcomes on constructed pairs | `passes local rerun` (reran this session, exit 0, `overall_ok:true`, byte-identical to the committed receipt) and independently audited `CLEAN` by a fresh-context adversarial pass, with 2 low-severity findings (F1, F2) fixed and now demonstrated firing inside the receipt itself, not just on the auditor's own inputs | `ratchet_contract/run_contract_selfcheck.py` → `results/selfcheck.json`; audit `results/AUDIT_VERDICT.md`; build commit `1a009b5a5`, audit commit `11af960df`, fix commit `b48d87871` |
| The 2-qubit spinor-vs-classical practice pair flowing end to end: `fuel_adequacy_gate` read against the real pool, `bridge_action_predictive` inducing partitions for both candidates over an 11-point shared deck and 4 demanded pairs, `gates.py`/`mss.py` computing `IDENTITY_GATE`, `persistence_gate`, `evolvability_gate`, a frontier, and a pairwise verdict, on two REAL executable carriers (qutip 2-qubit density matrix vs. a plain integer weight-and-edge relation) — with every hold reported as a hold, not smoothed | `runs`, internally cross-checked this session (`stage_b_vs_stage_c_cross_check` reads `true`/`true` for both candidates, i.e. the adapter's `IDENTITY_GATE` partition matches the bridge's own partition exactly, as the adapter is built to guarantee). The commit self-reports `passes local rerun (byte-identical x2)`; this session did not re-invoke the qutip-dependent run to confirm that claim independently | `ratchet_contract/fuel_sims/results/practice_run.json`, commit `d41907742` |
| The gate/MSS machinery itself: `buildability_gate`, `probe_validity_gate`, `IDENTITY_GATE`, `persistence_gate`, `evolvability_gate`, `extension_gate`, `adequacy`, and `mss.py`'s pure partition-coarseness frontier and pairwise operator — no score, no weighted sum, no LLM or network call anywhere (mechanically grep-confirmed, reconfirmed this session) | audited `CLEAN` | `ratchet_contract/results/AUDIT_VERDICT.md`, commit `11af960df` |

### Cannot ratchet yet

| Gap | Status | Evidence |
|---|---|---|
| A real multi-layer manifold carrier. All four candidates propose towers (9, 3, 8, and 13 layers); none has more than one thin executable slice. The exec files say so themselves: `candidate_spinor_qit_exec.py` is explicitly "NOT the 9-layer `candidate_spinor_qit.md` schedule executed in full", and `candidate_classical_exec.py` implements only a flat weight-and-edge relation, not the doc's own Layer 1/2 index-and-closure structure | `exists` (prose) for every layer beyond the executed slice; `runs` only for the flat 2-qubit pair | `system_v8/candidates/*.md`; `ratchet_contract/fuel_sims/candidate_*_exec.py` docstrings |
| A real MSS verdict between any two candidates. `pairwise_mss_base_no_thickening` returned `HOLD` at `base_survivorship`; the frontier's apparent "spinor survives, classical to purgatory" reading is named a practice artifact by the commit itself, not a carrier-family result (detail in section 4) | `HOLD`, named as non-canonical by its own commit | `practice_run.json`'s `stage_c_gates_mss_kernel.frontier` and `pairwise_mss_base_no_thickening`; commit `d41907742` |
| Pool-level fuel adequacy. `fuel_adequacy_gate.py` ("Principle Zero") returns `HOLD_INSUFFICIENT_FUEL`: 2 of 6 required pool roles are empty (`countermodel`, `ablation_control`); only 3 of a floor of 4 distinct model families are present; 11 provenance fields are thin or type-mismatched. This hold is inherited by every pairwise comparison drawn from the pool, including the practice pair | `HOLD_INSUFFICIENT_FUEL` (deterministic code gate, not an opinion) | `fuel_gate/results/first_pool_verdict.json`, commit `ecede647a`; embedded again in `practice_run.json`'s `stage_a_fuel_adequacy` |
| A presumption or relative-MSS ranking across the four candidates. Void — see section 3 | `HOLD` (void, not merely absent) | `system_v8/candidates/RANKING_VOID_llm_did_ratchets_job.md`, commit `bf99866f3` |
| Two bridges that can actually disagree. The SMT-relational bridge (`bridge_smt_relational.py`) currently induces its partition from the same recursion the action-predictive bridge uses; z3/cvc5 gate agreement but do not decide the partition. The owner's "two live rivals" bar is not yet met | audited `CLEAN` on what it does, with the gap named as a caveat, not hidden | `ratchet_contract/bridge_validation/results/AUDIT_VERDICT.md`, commit `ad323cc70` |
| Engine-real traces feeding the partition kernel. `JuliaEngineAdapter`, `JaxEngineAdapter`, and `PyTorchEngineAdapter` in `contract.py` are interface-only stubs; nothing in `system_v8/candidates/` has been compiled onto Julia, JAX, or PyTorch yet | `exists` (interface only) | `ratchet_contract/README.md` "State"; `ROOT/HOW_THE_ENGINES_RUN_THE_RATCHET.md` Part C |

## 2. Layer status ledger

Two different things are called "layers" in this material and they must not be merged:
the contract's own gate machinery (real code, judged genuine or not by adversarial audit),
and each candidate's proposed manifold layers (mostly prose, judged genuine-rival-or-
strawman by `STRAWMAN_AUDIT.md`). A third thing — the judge itself (the demand family,
probe family, and weakness relation that turns candidate output into a verdict) — is
neither genuine nor tainted; it is simply thin, and `STRAWMAN_AUDIT.md` calls this the
most dangerous finding in the set.

### 2a. Contract gate machinery — genuine, with one open reporting gap

| Gate | What it checks | Toy-verified | Status |
|---|---|---|---|
| `buildability_gate` | the candidate runs its own probes on its own states without error | yes (FAIL demonstrated on a non-roster broken fixture) | genuine |
| `probe_validity_gate` | the demand set separates declared positive controls and does not leak declared negative controls | yes (own-D PASS, thin-D HOLD, leaky-D FAIL all fire) | genuine |
| `IDENTITY_GATE` | `pi_probes` (raw probe-fingerprint equality) equals `pi_reidentify` (the candidate's own induced partition) — the executable form of `a=a iff a~b` | yes (`toy_raw_label` FAILs on unearned identity; three others PASS) | genuine |
| `persistence_gate` | demanded distinctions survive a declared continuation (delay/perturbation/relabel/partial access), by re-running the same partition kernel, not by trusting the candidate's own claim | yes (`toy_amnesiac` FAILs) | genuine, but see the open finding below |
| `evolvability_gate` | demanded distinctions survive `evolve()`, and `evolve()` does not smuggle a new declared primitive | yes (`toy_frozen` FAILs on no admissible extension; two non-roster fixtures isolate D-collapse and primitive-smuggle separately) | genuine |
| `extension_gate` | a declared whole-nest recompute digest matches a fresh recompute | yes (`toy_frozen` FAILs on a stale digest) | genuine |
| `adequacy` / `mss.py` frontier and pairwise operator | AND of the above; MSS as pure partition coarseness, no score | yes; independently audited `CLEAN`, no LLM/network call anywhere | genuine |

Open finding, surfaced by the practice run rather than the earlier audit: `persistence_gate`'s
`collapsed_persistence_demand_edges` reads one way in the JSON whether a pair was
separated and then lost under continuation, or was never separated at the base horizon at
all. The practice run hit both cases in the same call and the reason dict does not
distinguish them (detail in section 4). This is a labelling-precision gap in the receipt,
not a wrong verdict — the FAIL itself is correct in both cases — but it means "collapsed"
cannot currently be read as "was previously true," and any future reader of a
`persistence_gate` reason dict should check the base-horizon partition separately before
inferring loss.

### 2b. Candidate manifold layers — per `STRAWMAN_AUDIT.md`, none yet executed past a slice

| Candidate | Proposed layers | Audit verdict | Executed today | Named tension |
|---|---|---|---|---|
| spinor/QIT (`candidate_spinor_qit.md`) | 9, bottom-up, negative conditional entropy `S(A\|B)<0` as proposed gradient | genuine, strong — the closest member to ROOT_CARD line 3 (density matrices) and line 4 (spinor chain); self-flags its own richness | a flat 2-qubit density matrix and 3 named unitary gates; no minimal-ideal Clifford presentation, no cut-conditioned entropy is actually computed anywhere in code | none named as fatal; the file's own honest weakness is that "the carrier is already rich" (positivity, trace, complex scalars, Clifford relations do not follow from root distinguishability alone) |
| classical relational (`candidate_classical_bottomup.md`) | 3, bottom-up, no drive by design | genuine, deliberately weak, best-grounded — the only member wired to prior executed receipts (`base_campaign_receipt.json`) at Layer 0, and the only one whose Layers 1–2 are honestly labelled `PROPOSED_NOT_YET_SIMULATED` in its own text | a flat integer weight-and-edge relation; Layers 1–2 (indexed rewrite family, persistent-distinction closure) are not implemented | in direct, acknowledged tension with ROOT_CARD line 3 ("everything has to run on density matrices if it is the MSS"); the file names this itself rather than resolving it |
| nonassociative octonion (`candidate_foreign_nonassoc.md`) | 8, bottom-up through density/Hopf/S²/S³/coface/basin | genuine but weakest-built and frame-tensioned | none; zero code exists for this candidate anywhere in the repo | installs nonassociativity at the floor ("L1 Associator Floor... load-bearing"), against `RATCHET_SPEC.md` §3's binding rule that the composition floor is association-unspecified until a nonzero associator is witnessed. The file itself flags this as "Owner decision required" |
| top-down 12→0 (`candidate_topdown_12to0.md`) | 13, top-down, distinction-opening-vs-locking as proposed drive | genuine as an order-rival, thinnest carrier, least independent content | none; zero code exists for this candidate anywhere in the repo | presumes stable multi-agent/engine-differentiated objects at the entry point before any distinguishability constraint has earned them — the file's own weakness #1 admits it "may still smuggle object-like thinking upward"; the audit calls that "the frame's most-forbidden move" and notes the top-down order leaves the presumption irreducible |

None of the four is a strawman or a filler mask of another; the audit checked this
explicitly (distinct carriers, distinct orders, distinct or absent drives, no shared
author skeleton) and it stands.

### 2c. The judge itself — open, not genuine or tainted, because nothing is installed

Only one weakness relation is installed in code: partition refinement
(`RATCHET_SPEC.md` §6, `gates.py`/`mss.py`'s `partition_coarser`). `RATCHET_SPEC.md` §6
names this a proposed relation and explicitly flags "rival categorical, computational,
resource, predictive, or dynamical preorders" as live digs — none of them installed.

Two proposals sit ready but are pure fuel, unexecuted, and not yet committed to git:

- `judge_rival_weakness_relations.md` — 4 rival preorders (resource/description-length,
  categorical/factorisation, predictive/continuation-reachability, dynamical/basin-size),
  each with an exact definition and a prediction for how it would reorder the four
  candidates relative to partition refinement.
- `judge_rival_demand_families.md` — 4 rival demand families (`D1`–`D4`) built to thicken
  the one demand set that has actually been run, because that one demand set is
  demonstrably too thin: `base_campaign`'s single executed run, over two anonymous
  packets, returned `restricting_outer_changes_inner: false` and
  `order_T2T1_equals_T1T2: true` for all nine tested base carriers — a result about the
  demand set's discrimination power, not about the carriers.

`STRAWMAN_AUDIT.md` names this convergence as its most dangerous finding: the four
candidates genuinely diverge, but the demand family, probe family, and weakness relation
that would judge them are shared and unexamined across all four. A pairwise tooth run
against a demand set that thin, the audit warns, would be a fixture artifact "regardless
of how good the carriers are."

### 2d. Bridge infrastructure — one genuine judge, one not yet independent

- `bridge_action_predictive.py` (the action-conditioned predictive-quotient bridge):
  audited `CLEAN`. It genuinely computes partitions from finite outcome traces, installs
  neither primitive probability (`Outcome` rejects non-integer, non-positive
  multiplicities) nor primitive time (`step_C` is a pure fold over an ordered finite
  word), and its C2 control catches illicit relabelling by outcome content where a
  partition-digest-only check provably would not.
- `bridge_smt_relational.py` (the z3/cvc5 relational bridge): audited `CLEAN` on what it
  does, but with a named, non-fatal caveat — it induces its partition from the same
  `_reference_same` recursion the action-predictive bridge uses, so z3 and cvc5 currently
  gate agreement rather than decide the partition independently. As built, the two
  bridges structurally cannot disagree. The named fix is to compile candidate behaviour to
  an actual finite theory (ground model plus carrier axioms) and let the solvers decide
  distinguishability by entailment.

## 3. The nominalist axiom check

The owner's root axiom (`ROOT/ROOT_CARD.md`, outranks every spec, pack, wiki page, memory
file, and machine draft in this repository): "there is only one kind of
substance — constraint on distinguishability. Identity is not primitive; it emerges from
indistinguishability under probes (`a=a iff a~b`)." The same card's nesting law states
"everything has to run on density matrices if it is the MSS... and everything runs with
probes if it is MSS." Read together: a candidate that installs raw, self-identical,
sharply distinguishable atoms — `A=A` at the floor — presumes more than the root axiom
licenses. A candidate whose states are an operational quotient at probe resolution, where
non-orthogonal presentations are genuinely indistinguishable until a probe separates them,
presumes less. QIT/density-matrix carriers presuming less than a raw classical relation
is not a preference; it is what the axiom says, read plainly.

This repo's own machinery has already been tested against that standard once, and the
test and its correction are both on record as three sequential receipts:

1. `STRAWMAN_AUDIT.md` (commit `69b3c15ce`) ranked presumption by counting named
   mathematical machinery: classical < spinor/QIT < nonassoc < top-down, classical read as
   presuming least because it names the fewest structures. The audit flagged its own
   risk in the same breath: "it is computed by the same partition/structure-count logic
   all four candidates share... if that logic is the wrong weakness relation, this ranking
   is wrong with them."
2. `PRESUMPTION_RANKING_CORRECTION.md` (commit `254d480a8`) inverted it, naming the
   error precisely: counting machinery is the rationalist metric — Occam over named
   objects — and it is exactly the object-biased reading the audit existed to catch. Under
   the nominalist metric (how much primitive identity/`A=A` a candidate installs, not how
   much named structure it uses), classical (raw self-identical atoms) and top-down
   (registries of definite agent-objects) presume the most; spinor/QIT (`rho` as a
   probe-resolution quotient, identity emergent) presumes the least. Corrected order,
   most to least: classical ~ top-down > nonassociative > spinor/QIT.
3. `RANKING_VOID_llm_did_ratchets_job.md` (commit `bf99866f3`) voided both rankings,
   including the correction just written. Computing relative presumption or relative MSS
   is the ratchet's job, and the ratchet is code; an LLM stating that verdict is an LLM
   pretending to be the ratchet, regardless of which direction its answer points. The reason is stated as doubly void, not just procedurally void: the metric in
   question is "how little primitive identity is installed," and an LLM is the entity most
   committed to primitive identity — `A=A`, objects, universals — by its own training. It
   is, structurally, the worst available judge of exactly this question.

What survives is only the metric principle — presumption is measured by installed
primitive identity, `a=a iff a~b` native is least, `A=A` installed is most — held as a
specification for a future deterministic code operator, not as a verdict. Current state:
`HOLD`. No presumption ranking exists, not the auditor's, not the corrected one, not any,
until (a) the candidates are executable finite structures rather than prose, and (b) a
deterministic code operator measures installed primitive identity and is run on them. This
is, by name, the same hold `fuel_adequacy_gate.py` independently returns — two
structurally unrelated code paths (a provenance/pool-shape gate, and a rule voiding
LLM-computed rankings) landed on the same `HOLD` state, which the fuel-gate commit message
calls out explicitly ("Independently confirms the RANKING_VOID hold state").

One forward-looking reconciliation is on record and worth carrying forward rather than
re-deriving later: `ROOT/HOW_THE_ENGINES_RUN_THE_RATCHET.md` (commit `d4b2a179f`) notes
that the already-installed partition-refinement relation may turn out to be the correct
nominalist metric once it runs on real compiled candidates against a sufficiently thick
demand set — a candidate that installs `A=A` imposes the discrete (finest) base partition,
which is maximal presumption under partition refinement; a candidate that distinguishes
only what probes require is coarser, which is less presumption under the same relation. If
that holds, the earlier audit's error was counting named machinery instead of computing
the partition, and the code, run properly, already ranks correctly without a new relation
being invented. This is named explicitly as a hypothesis the code decides by being run,
not yet run, and not an LLM verdict either way.

The standing invariant, stated the way the build task asked for it: this is the owner's
axiom, not an experimental output, and it is not up for the code to overturn. A future
deterministic presumption operator, run on real candidates, is judged against it —
spinor/QIT carriers must come out presuming less than or equal to a raw classical relation
that installs definite, self-identical atoms at the floor. If a properly executed run
(real compiled candidates, a demand set thick enough to discriminate, the code's own
partition-refinement relation or an equivalent identity-burden meter) ever outputs
"classical presumes less," that is evidence the operator's encoding, the candidate's
compilation, or the demand set is broken. It is not evidence against `a=a iff a~b`.

## 4. Why the practice pair's result is not a verdict

The frontier in `practice_run.json` keeps `spinor_qit_exec_pkg` as the sole survivor and
sends `classical_relational_exec_pkg` to purgatory. Read on its own this looks like a
carrier-family result. The commit behind it (`d41907742`) names, in its own message,
exactly why it is not one, and the receipt supports the claim on inspection:

- A confound, not a loss: one of the four demanded pairs — the two orderings of `H0`
  then `CNOT01` versus `CNOT01` then `H0`, rooted at `root_plus0` — is already
  unseparated for the classical carrier at the base horizon, before any continuation is
  applied (`stage_b`'s `D_status` shows `separated: false` at horizon 1, and it stays
  `false` after the thickened rerun at horizon 2). The reason is a specific, hand-verified
  fixed point: from `root_plus0 = (2,2,0,0)`, the `H0` rewrite lands on the symmetric
  vector `(1,1,1,1)`, on which `CNOT01` is a no-op regardless of which order it ran in —
  a fact about this starting state, not about classical carriers generally. The same pair,
  rooted instead at `root_00` (where both carriers do separate the two orderings at base),
  survives a full `delay_long` for both candidates — the classical carrier's
  order-sensitivity mechanism is not, in general, fragile to delay. `persistence_gate` and
  `evolvability_gate` both then report this pair as "collapsed," which is imprecise for a
  distinction that was never present to lose — the section 2a finding.
- A real, but implementation-specific, loss: a second demanded pair —
  `couple_inner_outer` versus `couple_neighbor_neighbor` — genuinely is separated at base
  for the classical carrier and genuinely is lost, but only under delay, not under
  perturbation (`couple_pair_persistence_isolation` isolates this cleanly:
  `delay_short_x5_only` and `delay_short_x5_plus_perturb` both fail it;
  `perturb_only` alone does not). This traces to
  `candidate_classical_exec.py`'s `_delay_step`: it clears the carrier's entire edge
  relation whenever any weight moves at all, by construction. That is a design choice in
  this one exec file, not a property every "classical relation" carrier must share — a
  differently written classical carrier could retain edges through delay.

Both findings are named plainly in the commit message rather than smoothed into "spinor
wins." The first is a labelling-precision gap in the gate machinery, not a lost
distinction. The second is a real weakness, but a weakness of one implementation choice
inside one exec candidate, not of the classical-relational carrier family the pool's
minimal rival is meant to represent. Neither licenses reading the current frontier as
evidence that QIT carriers out-persist classical ones in general.

## 5. Bottom line, repeated

What the ratchet can actually ratchet today: its own judgment machinery (gates, MSS
frontier, both bridges) is real, audited, and reruns clean; it has been exercised exactly
once end to end, on two flat 2-qubit toy carriers, inside a pool the machinery's own
Principle-Zero gate already calls fuel-inadequate. Everything upstream of that — the four
candidates' actual manifold layers, a real presumption ranking, an independent
second bridge, engine-real traces — is prose, void, or stub.

The biggest open gap is the judge, not the candidates: one weakness relation
(partition refinement) is installed, the only demand set ever run was too thin to
separate nine unrelated base carriers, and the pool is missing two of its six required
roles (`countermodel`, `ablation_control`). Four rival demand families and four rival
weakness relations are drafted as fuel and sitting uncommitted. Until the pool clears
`fuel_adequacy_gate` and a demand set thick enough to discriminate is run through real,
compiled (not prose) candidates, any pairwise result this pipeline returns — including
the one it has already returned — is infrastructure exercise, not an MSS verdict.
