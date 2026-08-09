# WAVE TAXONOMY, ROLES, AND THE HARVEST (2026-08-06)

## 1. Dead loops — the rule, stated so it is checkable

> loops that dont have reciepts and dont advance something are dead.

A loop iteration is **live** only if both hold:
1. it emitted at least one receipt, and
2. its declared monotone measure moved in the declared direction.

An iteration that emits no receipt is not a round, it is a no-op. An
iteration whose measure does not move is **spinning**, and spinning
must halt and report rather than consume its remaining budget. This is
already enforced structurally by the wave-graph gate (every cycle
carries a budget AND a declared measure; `progress: "vibes"` is
refused), and it needs one addition: the **round receipt** must carry
`measure_before` and `measure_after`, so deadness is computed, not
asserted.

## 2. Wave kinds

Waves differ by what they *do to the work*, not by which members they
contain. The same voice, skill, or tool appears in many waves in
different roles.

| Wave | Job | Deterministic share | Loops on |
|---|---|---|---|
| **W-INDEX** | build shared structures once: scan, tokenize, path sets, hashes, receipt index | ~100% | staleness |
| **W-INDUCTION** | from instances to candidate structure: sweep configs, harvest examples, propose rivals, retain the antichain | mixed | new_rival_readings (increase then saturate) |
| **W-DEDUCTION** | from declared structure to consequences: SMT discharge, exact recompute, order/cycle verdicts, range membership | high | unresolved_count |
| **W-PROMPT** | prompt management: generate, diversify, packetize, diversity-gate before dispatch | LLM-heavy generation, deterministic gating | prompt_diversity (must reach DIVERSE) |
| **W-OUTPUT** | output management: normalise returns into typed packets, strip logs, compile human surface, bind receipts | mixed | unparsed_returns |
| **W-CONTEXT** | context management: what enters the next wave — index queries not directory dumps, distilled receipts, killed assumptions carried, entropy burned in short children | deterministic selection, LLM distillation | context_bytes (decrease) |
| **W-PROJECT** | project management: registry coverage, member staleness, blocker classes, work queue order | ~100% | never_run_count |
| **W-REPAIR** | build the missing artifact: task cards, adapters, fixtures, exemplars | hybrid | missing_exemplar_count |
| **W-VERIFY** | gates, controls, canaries, release refusal | ~100% | defect_count |

**W-INDUCTION and W-DEDUCTION are the pair the whole project is
about.** Induction gathers and proposes; deduction discharges and
refuses. They loop on each other: deduction's UNRESOLVED becomes
induction's queue; induction's survivors become deduction's obligations.

## 3. The parallel management process (not a wave)

> a parallel mangement process to ensure we dont get stuck loops doing
> nothjing useful. and ways to repair.

**W-WATCH** runs *beside* the spine, not in it. It never touches
content. It watches machinery:

- **stuck**: a wave started and returned no receipt inside its timeout
- **spinning**: measure unchanged across N iterations while budget burns
- **starved**: a member declared for this wave never dispatched
- **stampede**: concurrent child starts above the limiter
- **drift**: index staleness above threshold while later waves consume it

Its interventions are the Wizard's manager verbs, and only these:
`kill · demote · reroute · shrink · override · block_full ·
accept_with_reason · no_intervention_needed`.

It has **no vote and no content opinion**. It cannot decide a claim is
wrong; it can decide a loop is dead. That distinction is the whole
reason it can run in parallel safely.

Repair paths it can trigger: shrink the wave shape (fewer children,
tighter timeout), reroute to a different runtime, re-enter W-INDEX if
staleness caused the stall, or block_full and report.

## 4. Members are reused; the unit is member × role × wave

A voice, skill, agent or tool is **not a seat**. The same member takes
different roles in different waves and different nesting levels:

| Member | W-INDUCTION | W-DEDUCTION | W-PROMPT | W-VERIFY |
|---|---|---|---|---|
| `voice.zhuangzi` | rival-reading generator | — | **prompt generator** for other members | — |
| `voice.popper` | falsifier of candidates | killed/open/survived verdict | falsifier framing for a child prompt | control designer |
| `voice.hume` | scope of the harvest | evidence boundary | uncertainty framing | — |
| `z3` | — | discharge | — | control satisfiability |
| `rustworkx` | structure of the candidate space | order/cycle verdict | — | wave-graph gate |
| `portion` | admissible range of a swept parameter | membership refusal | — | bound check |
| `strict_consumer` | — | — | — | recompute gate |

**Registry consequence:** the member registry needs a second table —
`member × role × wave` — because coverage of a *member* is weaker than
coverage of its *roles*. `voice.zhuangzi` used only as a council seat
and never as a prompt generator is half-integrated, and today's
auditor would report it COVERED.

## 5. The harvest — all four repos cloned and inventoried

| Repo | Size | Contents | Use |
|---|---|---|---|
| **lev-os/agents** | 248 MB, 4,813 files | **61 skills** incl. `codex-autoresearch`, `skill-discovery`, `flowmind-author`, `arch`, `research`, `ux`, `exec`, `close`, `lev`, `now`/`here-now`, plus `skills-db`, `skills-state.json`, `lev-skills.sh`, `research-results.tsv` | primary harvest source; `skill-discovery` is itself a harvesting tool |
| **lev-os/agent-lease** | 596 KB, 32 files | "agentguard" — **git hooks that force validation**, 31 tests, `hooks/ lib/ skills/ test/` | the owner is right: LLM decision-making with no real gate, but the *hook enforcement* pattern is directly retoolable as a CB pre-commit custody surface |
| **HKUDS/nanobot** | 22 MB, 1,154 files | swarm/agent runtime | candidate encasement for CB |
| **HKUDS/ClawTeam** | 21 MB, 198 files | team/swarm management | candidate encasement |

**Harvest rule (from the failures this week):** a harvested skill is a
**described member** until a receipt shows it ran under CB with a task
card and proof depth. Import the *file* and you have documentation;
import the file plus an exemplar and you have a member. The registry
must mark harvested entries `source_repo` + `harvest_date` so a future
audit can tell inherited from earned.

## 6. On encasement — ConstraintBoxClaw

The layering the owner describes is:

```
   swarm manager (nanobot / ClawTeam / zeroclaw)   <- runs many agents
        └── CB                                      <- gates them
              └── members (voices, skills, agents, tools, sim lanes)
```

The one invariant that must survive encasement: **the encasing runtime
must not be able to promote.** If the swarm manager can mark work done,
CB is decoration. Concretely, before adopting any encasement, check:
does it have a verdict field that its own agents can write? If yes, that
field must be neutered or ignored, exactly as CB already refuses
producer `all_pass`.

Not now — but the check is cheap and should be run before any adoption
decision.
