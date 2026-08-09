# INTEGRATION WAVE PROGRAM — nested councils, looped to a measured exit

Status: **proposed design, not yet run.** Owner flagged that good wave
structure has not been worked out; this is a first concrete structure
whose exit condition is deterministic rather than declared.

## The objective, stated so a machine can check it

The registry declares **137 members** (voices, formal agents, skills,
deterministic tools, sim lanes). Almost all are DESCRIBED. The program
succeeds when each is RUN or explicitly PARKED with a named blocker.

> A member is RUN only when a receipt names its spec, task card,
> MMM/slice preload, runtime target, output, and proof depth.

**Exit condition:** `member_coverage_auditor.py` returns `clean: true`,
or every remaining member is PARKED with a named blocker.
**The loop does not terminate on a model saying it is done.** It
terminates on machinery evidence.

## The five waves

### WAVE 0 — CENSUS (deterministic, zero LLMs)

Members: `repo_state_gate`, `member_coverage_auditor`,
`cb_independence_gate`, `cb_layer_purity_and_canaries`,
`strict_receipt_consumer`, `cb_receipt_index`.

Output: the work queue — NEVER_RUN / STALE / STUCK per member, plus
branch/HEAD/dirty state so nothing lands where nobody is standing.

Cost: seconds. No models. This wave is the loop's clock.

### WAVE 1 — TRIAGE (wide, cheap, maximally diverse)

Question per member: *why has this never run?* Classification only,
one member per child, no building.

Blocker classes: `no_task_card` · `no_adapter` · `missing_runtime` ·
`no_fixture` · `superseded` · `genuinely_unused` · `unknown`.

Shape: **fast scout — 8 parents x 8 Haiku children,
`stop-after-completed 4`, timeout 120s, concurrency 4/parent,
`global-max-active 8`.** Cheap models are correct here; this is
classification, not judgment.

Councils (3, each a council of councils):
- `triage.artifact` — members: repo-doc-archaeologist ·
  fabrication-auditor · voice-hume. Floor: `pygit2`, `sqlite3` index.
- `triage.runtime` — members: codex-ratchet-tool-status-auditor ·
  voice-factory. Floor: `cb_independence_gate`, `deps` resolution.
- `triage.contract` — members: sim-contract-gatekeeper ·
  voice-popper. Floor: `msgspec` strict decode against the task-card
  schema.

Divergence: `voice-zhuangzi` generates the per-child prompt so each
child receives a genuinely different framing.
Gate: `input_diversity_gate` must return DIVERSE before results are
accepted. COLLAPSED means the wave was one opinion and is rerun.

### WAVE 2 — MAKE RUNNABLE (build the missing artifact)

Only for members triaged `no_task_card`, `no_adapter`, `no_fixture`.

Shape: **safe default — 8 parents x 12 Sonnet-high, timeout 260s,
concurrency 4/parent.** Building needs the stronger models.

Councils:
- `build.task_card` — members: prompt-packetizer · scope-keeper ·
  voice-orwell. Floor: `msgspec` validates the emitted card against
  `CHILD_TASK_CARD_SCHEMA_v4_3`; rejection is mechanical.
- `build.adapter` — members: claude-pattern-intake ·
  smt-proof-engineer · voice-feynman. Floor: `z3` + `cvc5` when the
  adapter carries a decidable claim.
- `build.fixture` — members: premortem-agent · falsifier-agent ·
  voice-popper. Floor: `hypothesis` as a FINDER, then the discovered
  example is **frozen as a static fixture** so the test runs without it.

### WAVE 3 — EXECUTE AND RECEIPT

Run each newly-runnable member once, for real, and emit the
five-field route-truth receipt (`action_class`,
`execution_claim_state`, `proof_depth`, `receipt`, `evidence_boundary`).

Shape: mixed by member kind —
`deterministic` members run locally, no council;
`skill` and `formal_agent` members run under their runtime;
`sim_lane` members run under capability dispatch with the lock
recorded.

Council: `execute.route_truth` — members: route-truth-agent ·
route-sequencer · manager.child_health. Floor: `rustworkx` for
dependency order and cycle refusal; `cb_release_gate` refuses any
release whose evidence count is zero.

### WAVE 4 — VERIFY (deterministic again, closes the loop)

Re-run Wave 0's tools plus `semantic_drift_gate` on any claim packets
produced. Emit the delta: how many members moved NEVER_RUN → COVERED,
which went STUCK, which are newly STALE.

Label the cycle honestly: `SMOKE_FORMAT` · `SMOKE_TOPOLOGY` ·
`REAL_ATTEMPT_PARTIAL` · `REAL_ATTEMPT_FULL`.

## The loops

```
   W0 census ──► W1 triage ──► W2 build ──► W3 execute ──► W4 verify
    ▲                │            ▲   │                        │
    │                │            └───┘  build⇄execute inner loop
    │                │                   (fix, rerun, until the
    │                │                    member emits a receipt)
    │                └── triage⇄build loop for reclassified blockers
    └──────────────────────────────────────────────────────────┘
        W4 delta becomes W0's input; repeat until exit condition
```

Loop rules:
1. **A wave may loop within itself** — build⇄execute is the tight
   inner loop for one member.
2. **Waves loop with each other** — W4 feeds W0; a member that fails
   execution returns to triage with a new blocker class.
3. **Barriers hold.** W2 cannot start until W1 accepts or blocks.
4. **Cheap first.** Every cycle starts with the deterministic census;
   models only run on what the census says is missing.
5. **Progress is monotone or the cycle is a defect.** If a cycle
   produces zero NEVER_RUN → COVERED transitions and no new PARKED
   blockers, the loop is spinning and must stop and report, not
   continue.

## What each wave costs, from the measured ladder

| Wave | Shape | Model | Measured |
|---|---|---|---|
| 0, 4 | none | — | seconds, no models |
| 1 | 8 x 8, stop-after-4 | Haiku | 32 completed, 18 abandoned, 14 not launched — stable rolling shape |
| 2 | 8 x 12, t260, conc 4 | Sonnet-high | 96 completed, parents 57–143 s |
| 3 | mixed | per member | deterministic members are free |
| arbitration | 1 x 1, t180 | Opus | 23.5 s, rare, doctrine conflicts only |

Limiter rule carried: add parents before raising per-parent
concurrency; keep Claude per-parent at 4 and `global-max-active` at 8.

## What CB does and does not do here

CB runs Waves 0 and 4 in full, supplies the deterministic floor
members inside Waves 1–3, and gates every receipt. CB does **not**
choose wave shapes, does not score any member's output, and does not
decide when the work is good — only whether the machinery ran and the
receipts hold.

## First cycle, concretely

1. Run W0 against `config/council_member_registry_v1.json` and
   `config/council_member_registry_skills_v1.json` with the existing
   receipt trees. This produces the first real NEVER_RUN list — the
   number nobody has yet.
2. Do **not** launch W1 across all 137. Take the first 8 members from
   the deterministic kind (they need no council and no model) and
   drive them to COVERED. That proves the loop end-to-end at zero
   model cost.
3. Only then open W1 on the LLM-backed kinds.

## Open, and named as open

- Which wave handles cross-member integration (two members that only
  work together) is unassigned.
- No wave yet handles **removal**: a member triaged `genuinely_unused`
  should be deleted, and nothing here deletes.
- The `all_of_the_above` lane and the compositions (All-A Build, All-B
  Divergence, All-C Closeout, Max Assembly) are unmapped onto these
  waves.
