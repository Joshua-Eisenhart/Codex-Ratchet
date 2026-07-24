# ClaimGate at the harness level — proposed patch

**For:** the LevOS dev
**From:** Codex-Ratchet
**Status:** PROPOSED patch, runnable today. Nothing here is installed into `~/lev-main`, which is treated as read-only throughout. `promotion_allowed: false`.

---

## What this answers

Your objection, verbatim:

> the receipt / gate attempt can easily devolve into theatre and goal seeking, really u need an agent that is watching the worker
> we need agents checking the eval of the eval ... the token spend becomes astronomical

You're right that agents-watching-agents doesn't terminate. **This terminates the regress in computation instead.** A gate that is theatre fails three mechanical tests, and the whole battery costs **zero LLM tokens**.

---

## 1. Correction to my own first plan: the hook layer

I was about to write this against Claude Code's `PreToolUse`/`PostToolUse` JSON. That's the wrong altitude — it's a one-vendor solution. You already have the right layer:

```
context/schemas/abstract-hooks.yaml            ← the contract
plugins/platforms/src/shared/hooks-registrar.ts
plugins/platforms/src/shared/hooks-manifest.ts
plugins/platforms/src/{claude-code,cursor,openclaw,...}   ← per-harness adapters
```

The schema's own words: *define once here → implement per adapter.* So the policy is written against **`abstract-hooks@1.0.0` lifecycle events**, and every adapter inherits it.

Your schema already has a gate slot — I didn't have to invent one:

| lifecycle family | events used | ClaimGate role |
|---|---|---|
| `task` | `task_start`, `task_complete` | mint / close the run ticket — your "per task hooks are the real winner" |
| `tool` | `pre_tool_use`, `post_tool_use` | route seal / admission seal |
| `validation` | `validation_pass`, `validation_fail`, `escalation` | verdicts; `escalation` = owner-decision path |

---

## 2. Honest finding about pi

I checked the repo before building against it. **pi has no documented hooks or plugin system.** Its packages are `pi-ai` (multi-provider LLM API), `pi-agent-core` (tool calling + state), `pi-coding-agent` (CLI), `pi-tui`. The extension story in the docs is *containerization patterns*, not hooks.

So "ClaimGate at pi level" has to be one of three, and it's your call which:

1. **Tool-dispatch shim in `pi-agent-core`** — the interception point is where tool calls are dispatched. Thinnest patch, needs a fork.
2. **Container boundary** — pi's own documented pattern; the gate owns the filesystem/network edge outside the process. This is the only one that reaches real confinement.
3. **Tool proxy / MCP layer** — gate sits between pi and its tools, no pi patch at all.

This patch is written so the gate is a **plain CLI**, which means it drops into any of the three without change.

---

## 3. What's in the patch

```
system_v8/harness_patch/
  gate_policy.yaml     policy AS DATA, against abstract-hooks events
  harness_gate.py      the gate: mint | pre | post → verdict + events.jsonl + exit code
  flip_harness.py      the anti-theatre battery (z3 × JAX), 0 LLM tokens
  run_demo.sh          end-to-end, all legs
  results/             receipts from the run below
```

### The verdict vocabulary is deliberate

Pre-run never emits `PASS`. Models launder "INTAKE_APPROVED" into "admitted", so:

```
pre-run   ROUTE_SEALED | PENDING_EVIDENCE | PARKED_POLICY | BLOCKED_INVALID
post-run  ADMITTED_WITHIN_CEILING | PENDING_EXTERNAL_CHECK | PARKED_INCOMPARABLE | BLOCKED | QUARANTINED
```

`ROUTE_SEALED` means *eligible to run*, not *admitted*.

---

## 4. Verified runs (actual output, this machine)

### Route seal — protects your read-only constraint

```
mint    → TICKET_MINTED tkt_1286be5f6e5e                                   exit 0
Write /Codex-Ratchet/system_v8/x.json    → ROUTE_SEALED                    exit 0
Write ~/lev-main/plugins/x.ts            → BLOCKED_INVALID (protected root) exit 1
Write /Codex-Ratchet/../lev-main/core/y.ts → BLOCKED_INVALID                exit 1
WebFetch                                  → BLOCKED_INVALID (out of scope)  exit 1
```

Note case 4: the `../lev-main` traversal is caught because paths are **canonicalised (realpath) before the prefix check**, not string-matched. Symlink and `..` escapes into `lev-main` are blocked.

### Admission seal — hostile intake

| fixture | verdict | exit |
|---|---|---|
| `{"all_pass":false,"all_pass":true}` | BLOCKED — duplicate key rejected **at raw parse** | 1 |
| `{"metric":NaN}` | BLOCKED — non-finite rejected at raw parse | 1 |
| `{"promotion_allowed":true}` | BLOCKED — producer self-verdict; gate computes its own state | 1 |
| clean receipt | ADMITTED_WITHIN_CEILING, `raw_digest=bbdad32a9f42` | 0 |
| absent file | BLOCKED — *missing is not N/A-ok* | 1 |

The duplicate-key case matters: ordinary `json.loads` silently last-wins, so `all_pass` flips to `true` before any checker sees it. This parses raw bytes once with `object_pairs_hook`, and hashes the bytes **before** canonicalisation.

### The Lev bridge — verified CLI contracts only

```
lev triggers dispatch results/events.jsonl --receipt results/fixtures/clean.json --exec-dry-run --json
```

returned:

```json
{"schema": "lev.event_dispatch.one_shot_dispatch_receipt.v1",
 "policy": {"decision": "allow"},
 "side_effect": {"class": "read"},
 "result": {"status": "ok"}}
```

`lev-main` was not written to. The other seam, `lev gate validate <gate-id>`, is available for gate-run evidence.

---

## 5. The anti-theatre battery — the piece worth your time

Three mechanical tests, from the template that caught **this repo's own decorative SMT** (commits `4fcd539d6`, `b12c0e8c7`, where nearly every z3 leg was the tautology `recover(k)==A ∧ recover(k)==B → UNSAT`, true for any `A≠B`):

1. **ERASE** — drop the pinned mechanism → verdict must become SAT
2. **PERTURB** — perturb pinned entries (JAX-batched) → `flip_rate` must exceed threshold
3. **CORE** — the unsat core must be a proper subset of the real constraints

Measured, on a real claim ("stage order is load-bearing in the Type-1 engine loop"):

| candidate | erase flips | flip_rate | unsat core | verdict |
|---|---|---|---|---|
| real engine loop | unsat → sat ✓ | **1.0** | 2 of 6 pinned | **LOAD_BEARING** |
| commuting-z control | sat → sat ✗ | **0.0** | 0 | **DECORATIVE_OR_TAUTOLOGY** |

`battery_discriminates: true`, `llm_tokens_spent: 0`.

**On your SMT scepticism** — you said taking text into a scalar and proving on that is "recreating embeddings". Agreed, and that isn't this. The solver never touches text-derived scalars. It pins already-exact discrete objects (measured transition tables, partition digests, exact enumerations) and answers one question: **did this mechanism bear weight?** A dependency test, not a semantic proof. That's why it works at the harness level and not just "deep in an ML model".

---

## 6. Where we already agree

- **"each domain has its own domain based acceptance criteria"** — that's the `applicability` block in `gate_policy.yaml`: per claim type, each lane gets `REQUIRED_GENERATOR / REQUIRED_REFERENCE / OPTIONAL_SUPPORT / FORBIDDEN / NOT_APPLICABLE`, and only policy assigns it. A producer may request a lane; it can never downgrade a requirement.
- **"axiom/constraint digger workflows will be more important than claim gate"** — agreed, and there's a measurement behind it. The digger is the demand set `D`. In our bridge run, sweeping probe resolution showed the comparator only discriminates in a **narrow band**: too coarse and every candidate destroys `D`; too fine and nothing merges. Our own base campaign hit `restricting_outer_changes_inner: false` on all nine carriers — `D` too thin to separate anything. The digger isn't downstream of the gate; it's what lets the gate see at all.
- **flowmind as the home for policy** — `gate_policy.yaml` is data, not code, precisely so it's tweakable and so a z3/TLA+ parser could consume it later.

---

## 7. The ceiling — stated on every receipt

```
enforcement_level: E2_SUPERVISED_EXECUTION
forbidden_wording: ["bypass prevented", "cannot be bypassed", "sandboxed", "non-bypass"]
```

A hook inside the agent's own process is **supervised execution**, not confinement. The model still holds a shell. This may say *admission control*; it may never say *bypass prevented*. Reaching real confinement needs the OS to deny the capability — measured by running forbidden-write and forbidden-network canaries **from the exact run identity**. That's the direction "llms run inside levos" points, and it's host work, not repo work.

---

## 8. To run it

```bash
cd system_v8/harness_patch && ./run_demo.sh
```

Requires: python with `jax` + `z3-solver`, node ≥22, `lev` on PATH. Nothing writes outside `system_v8/harness_patch/results/`.
