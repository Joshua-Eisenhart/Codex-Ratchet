# RUNNING THE SWARM THROUGH CB — the exemplar program

Refinement from the owner: the diverging/converging swarm runs
**through CB — its tools and gates** — and the program must not only
integrate every tool, skill, agent, voice, MMM and gate, but
**exemplify** each one.

That word changes the objective. Coverage asks *did it run.*
Exemplification asks *did the run show what it is for.*

## 1. CB is the transport, not a bystander

Every council dispatch — every voice, every child, every skill, every
sim lane — goes **through** the CB chain:

```
lease issue          binds the git tree; TREE_MISMATCH if the tree moves
  └── request        policy assessment BEFORE any work is proposed
        └── capability-box   fresh run dir, output outside the receipt dir
              └── member runs (LLM, skill, tool, or lane)
                    └── receipt   five route-truth fields + evidence boundary
                          └── strict consumer   recompute from bytes
                                └── receipt index   exact lookup, sqlite
                                      └── coverage auditor   machinery only
```

Nothing in the swarm writes a result that did not pass through this
chain. That is what makes the swarm auditable without anyone judging
its content.

## 2. The exemplar law

> A member is **integrated** when it runs.
> A member is **exemplified** when its run demonstrates the thing it
> exists to do — and, where it can refuse, when it actually refuses.

Three exemplar classes:

| Class | Requirement | Applies to |
|---|---|---|
| **positive** | the member does its job on a real input and returns a usable result | every member |
| **refusal** | the member declines something it must decline, naming the reason | every gate, every guard, every auditor |
| **severance** | with the member removed, exactly one named claim demotes and the system still runs | every deterministic member and sim lane |

**A gate that has only ever passed has not been exemplified.** This is
the sharpest consequence: exemplifying a gate means *making it fire.*

## 3. What exemplification requires, per member kind

**`voice` (9).** Positive: a run where the voice's distinctive output
appears — Popper returns killed/open/survived, Feynman returns a
pass/fail an outsider could run, Zhuangzi returns an exclusion
condition and a genuinely different prompt for another member.
Refusal: not applicable — voices propose, they never gate.
Extra for zhuangzi: its exemplar is **a prompt it generated that
`input_diversity_gate` scored DIVERSE against its siblings.**

**`formal_agent` (36).** Positive: a receipt naming agent spec + task
card + MMM slice + proof depth. Refusal: for managers and auditors —
`manager.child_health` must show a real intervention verb fired (kill,
demote, reroute, shrink, override, block_full); `council-collapse-
auditor` must show a detected collapse, not a clean sheet.

**`skill` (59).** Positive: invoked, returned, receipted. Refusal:
where the skill embeds a check (sim-contract-gatekeeper,
terrain-operator-math-lock, source-math-lock), it must reject a
deliberately malformed input once.

**`deterministic` (17).** All three classes are mandatory and cheap:
- z3/cvc5/enumeration: real claim BOUNDED_SAT, erased control
  BOUNDED_UNSAT, malformed claim UNRESOLVED — **already exemplified**.
- rustworkx: acyclic PASS, injected back-edge BLOCKED — **exemplified**.
- portion: value inside the box, value outside refused — **exemplified**.
- msgspec: valid decode, plus unknown-field/wrong-type/missing-field
  refusals — **exemplified**.
- pygit2: identical tree id to `git write-tree`, then TREE_MISMATCH on
  a changed tree — **exemplified**.
- sympy, maude, rfc8785, sqlite3: positive done; **refusal exemplars
  outstanding**.
- the gates themselves: see §4.

**`sim_lane` (10).** Positive: a lane result under capability dispatch
with the lock recorded. Severance: with the lane absent, the envelope
must demote to a lower ceiling rather than fail — the ceiling-scaled
lane policy already does this (two lanes ELIGIBLE at a carrier-level
claim; authoritative claims BLOCKED without julia and pytorch).

**`mmm` (9 slices).** Exemplified when a member primed with slice A
and a member primed with slice B produce outputs whose root inputs
score DIVERSE — i.e. the slice measurably changed what was salient.
An MMM that makes no measurable difference is decoration.

## 4. The gates' own exemplars — each must be seen refusing

| Gate | Refusal exemplar | Status |
|---|---|---|
| `strict_receipt_consumer` | mutated artifact byte → mismatch | **done** (1558f20f → 2e8f3354) |
| `cb_release_gate` | zero declared digests → ZERO_DECLARATIONS | **done** (self-test) |
| `cb_layer_purity` | torch import inside the package → violation | **done** (self-test) |
| `cb_independence_gate` | empty closure → refuses to certify; dev tool in closure → BLOCKED | **done** |
| `semantic_drift_gate` | unbridged escalation → PARKED; encoding-as-identity → BLOCKED | **done** (7/7) |
| commitment ledger | acknowledgement then reversion → REVERSION_AFTER_ACKNOWLEDGEMENT | **done** (9/9) |
| `input_diversity_gate` | four nodes, one MMM, shared preamble → COLLAPSED | **done** |
| `repo_state_gate` | claimed path absent from this checkout → NOT VISIBLE | **done** |
| `member_coverage_auditor` | declared member never in a receipt → NEVER_RUN; spawned-never-returned → STUCK | **done** |
| `three_engine_seal` | numpy declared load_bearing → hard reject | **outstanding** |
| `verify_attractor_basin_envelope` | wrong-radii twin / missing lane / severed SMT | **outstanding** |
| capability-box policy gate | output inside receipt dir; dirty run dir | **done** (refused me twice) |
| lease | tree moved after issue → TREE_MISMATCH | **done** |

Nine of thirteen gates already have a refusal exemplar on record. The
program's first cheap win is the remaining four.

## 5. How this maps onto the waves

- **W0 census** now reports three states per member, not one:
  `NEVER_RUN` / `RUN_NOT_EXEMPLIFIED` / `EXEMPLIFIED`.
- **W1 triage** classifies the missing exemplar class (positive,
  refusal, severance) rather than only the blocker.
- **W2 build** produces the exemplar fixture — and for refusal
  exemplars this is a canary, which is the thing the canary corpus was
  already built to hold.
- **W3 execute** runs both sides: the positive and the refusal.
- **W4 verify** admits a member as EXEMPLIFIED only when the required
  classes for its kind are all present, each with a receipt that
  recomputes.

Exit condition, tightened: not `clean coverage` but **every member
EXEMPLIFIED or PARKED with a named blocker.**

## 6. Why this is worth the cost

The exemplar corpus is simultaneously four things:

1. **the integration proof** — every member demonstrably works;
2. **the regression suite** — every refusal exemplar is a permanent
   canary, and escaped defects join it;
3. **the documentation** — a member's exemplar is the clearest
   possible statement of what it is for;
4. **MMM source material** — the phrasing of real refusals is exactly
   the in-voice vocabulary the constraint-box MMM should carry.

One system, run once, produces all four. That is the payoff for
running the swarm through CB rather than beside it.

## 7. Honest status

Nothing in this program has been executed as a wave. What exists: the
chain in §1 is verified working end to end in a container; nine of the
thirteen gate refusal exemplars are on record; five deterministic
members are fully exemplified. The rest is designed, registered, and
unrun.
