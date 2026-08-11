# AUTORESEARCH, DETERMINISTIC AUTORESEARCH, AND NANOCHAT — feasibility

Status: **plan only, nothing built.** Owner: "not something to just
all do now. can plan if feasible."

## 1. You already have autoresearch. Two skills, installed.

`~/.agents/skills/codex-autoresearch/` — "Autonomous goal-directed
iteration. Modify → Verify → Keep/Discard → Repeat." Modes `loop`,
`plan`, `debug`, `fix`, `security`, `ship`, `exec`; helper scripts for
run init, resume check, launch gate, supervisor status, runtime
control; references for hard invariants, environment awareness,
health-check, pivot, parallel, hypothesis-perspectives. `cdo` can use
it as a long-running scheduler while owning the epistemology.

`~/.codex/skills/karpathy-bounded-improve/` — the small-target
version, explicitly *"not permissionless self-mutation."* It already
demands the fields that stop runaway: `target_path`, `artifact_type`,
`allowed_write`, **`round_cap`**, `score_function`, `acceptance_test`,
`stop_condition` — with validation that the cap, score function and
acceptance test are non-empty **before any edit**.

So the runaway-files problem is already addressed in your own design.
What is missing is not a bound; it is **CB enforcing the bound from
outside the loop.**

## 2. The core loop is your ratchet

```
codex-autoresearch : read → define mechanical metric → baseline →
                     one focused change → verify by command →
                     keep or discard → log → repeat
ratchet            : propose → probe → survive or be excluded →
                     retain the antichain
```

These are the same loop. Autoresearch is a ratchet whose candidates
are configuration changes and whose probe is a command. That means CB
already knows how to gate it: candidates are proposals, the verify
command is the oracle, `keep` is an admission, and nothing promotes.

## 3. Deterministic autoresearch — yes, and it is the cheap half

An autoresearch loop is deterministic whenever the **proposal step**
is systematic rather than generated. Replace "ask a model for a
change" with "enumerate the configuration space", and the whole loop
becomes reproducible:

| Loop step | LLM autoresearch | Deterministic autoresearch |
|---|---|---|
| propose | model writes a diff | sweep / grid / bisect / mutation operator over a declared space |
| verify | run the command | same command |
| score | model reads output | declared `score_function` |
| keep | model judges | strict inequality against baseline |
| log | prose summary | receipt |

Concrete deterministic sweeps already available in your stack, all
free to run and all yielding real results:

- **wave shape**: parents x children x concurrency x timeout, scored
  by completed-per-second from `fanout_receipt.json` — the measured
  ladder in `SUBSUBAGENT_SCALING_RUNBOOK_v1.md` **is** the output of a
  hand-run deterministic autoresearch pass. Automating it is a sweep.
- **diversity bounds**: collapse/couple thresholds in
  `input_diversity_gate`, scored against labelled collapsed and
  diverse fixtures.
- **council composition**: which 3-9 members per layer-3 council,
  scored by how often the council's verdict survives the next gate.
- **index shape**: sqlite schema and index set, scored by query time
  on the real receipt corpus.
- **tolerance selection**: the recompute-contract tolerance, scored
  against known-good and known-drifted receipts.

**The rule that keeps it honest:** a deterministic sweep must include
its negative controls in the space. If a swept configuration cannot be
made to fail, the score function is not measuring anything.

## 4. The runaway problem is a CB problem, and CB already has the parts

| Runaway failure | Existing CB organ |
|---|---|
| candidate files accumulate forever | receipt index dedupes by sha; artifacts are content-addressed |
| no one can tell which run produced what | lease binds a git tree; receipts carry run_id |
| the loop declares its own success | producer verdicts refused; `promotion_allowed=false` |
| improvements are unreproducible | recompute-from-bytes; canonical JSON |
| the loop never stops | `round_cap` + `stop_condition` are already required fields |
| cleanup deletes evidence | release gate refuses zero-evidence; deletion is its own gate |

Missing piece, small: a **budget member** — declared caps on rounds,
wall time, tokens, and *files created* — with the loop blocked when a
cap is hit rather than trusted to stop itself.

## 5. Where this sits in the layer order

CB core (lean) → deterministic autoresearch over CB's own knobs →
sim engines under CB → autoresearch over integrations → holodeck.

Deterministic autoresearch is cheap enough to run at the CB layer
**now**, because its subjects are CB's own configuration. LLM
autoresearch waits for a mature CB, exactly per the owner's ordering.

## 6. NanoChat — feasibility on this machine

Measured: **Apple M1 Pro, 10 CPU cores, 16 GPU cores, 16 GB unified
memory.**

Honest reading:

- **Training a nanochat-scale model from scratch on this machine is
  not feasible in useful time.** The published nanochat runs assume
  8xH100-class hardware for hours. On 16 GB unified memory the ceiling
  is a very small model on a very small corpus, and the wall time is
  days per iteration, which destroys the autoresearch loop that
  motivates it.
- **Running a small local model for inference is feasible.** 7-8B
  quantised (4-bit) fits in 16 GB and runs at usable speed via MLX or
  llama.cpp on M-series. 3-4B runs comfortably.
- **Fine-tuning a small model with LoRA on M1 Pro is feasible** for
  narrow tasks — hours, not days — and is the realistic version of
  "a nanochat per layer."
- **Renting for training runs is the standard answer** if a real
  from-scratch model is wanted; `brev-cli` is already installed in
  both skill sets, which is a rental path you already have.

### What a local model is actually good for here

Not judgment. The gate must stay deterministic. But three jobs suit a
small local model well, and all three are high-volume and cheap:

1. **Normalisation** — turning prose into typed claim packets so the
   SDG can check structure. High volume, low stakes, no verdict.
2. **Diversity generation** — zhuangzi-style prompt variation for the
   exploration lane. Quality bar is "different", not "correct".
3. **Triage classification** — labelling blockers (`no_task_card`,
   `missing_runtime`) in Wave 1, where a wrong label costs one rerun.

A local model doing these three removes most of the token cost from
the swarm while the expensive models stay for build and arbitration.

### Sequencing, if it is wanted

1. lean CB first (unchanged);
2. deterministic autoresearch over CB's own knobs — free, immediate;
3. local inference model for normalisation and triage (MLX/llama.cpp,
   no training);
4. LoRA fine-tune on your own receipt corpus for the three jobs above;
5. from-scratch nanochat **only** on rented hardware, and only if
   steps 3-4 show a specific ceiling that fine-tuning cannot lift.

## 7. Open questions, named

- Per-layer models (CB / sim / CR / holodeck) versus one model with
  per-layer LoRA adapters — the adapter route is far cheaper and
  probably sufficient.
- Whether the deterministic sweep space should be declared in the
  registry alongside members, so autoresearch subjects are themselves
  auditable.
- How to score "process effectiveness" without a model judging it.
  Current candidates: gate-survival rate, rounds-to-clean, member
  coverage delta per cycle — all deterministic.
