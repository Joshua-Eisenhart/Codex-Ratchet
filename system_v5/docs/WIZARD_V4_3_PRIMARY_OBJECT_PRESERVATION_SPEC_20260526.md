# Wizard v4.3 Primary Object Preservation Spec

Status: additive guard over Wizard v4.2, not a replacement runtime.

Purpose: keep an unfamiliar primary object alive while still letting the Wizard
think laterally. The target failure is the recurring pattern where a proxy,
analogy, metric, or first useful suggestion becomes functional canon.

## Core Rule

Wizard v4.3 requires a primary object card before councils, sims, or follow-up
loops can claim progress on a novel object.

The card must define:

- the object in plain language;
- a stable object statement and hash;
- source anchors;
- native terms;
- weirdness features that are easy for LLMs to erase;
- first-class fields;
- domain and output;
- allowed operations;
- invariants that must survive translation;
- forbidden substitutions;
- negative controls;
- adapter and promotion policy.

For Joshua Eisenhart's shell model, the object is not Axis0, FEP, scalar
entropy, PEPS3D, or a Wolfram analogy. Those can be adapters, probes,
analogies, or proxies. The object is the finite retrocausal possibility field:
shell-indexed possible futures compress inward through compatibility into a
present survivor and leave an outward record.

## Lateral Thinking Contract

v4.3 does not ban lateral thinking. It types it.

- `adapter`: a real bridge into a tool or representation. It may become
  claim-bearing only if it says what it preserves, what it loses, its
  preconditions, and its kill control.
- `probe`: a test surface. It may become claim-bearing only with the same
  preservation/loss/kill-control discipline.
- `analogy`: a useful way to think. It cannot promote into object truth.
- `proxy`: a reduced readout. It cannot promote into object truth.

This is the key distinction: wild exploration is allowed, but promotion is
controlled.

## Loop Shape

A v4.3 packet must name:

- root constraints;
- extended constraints;
- wildcard lateral lanes;
- fixation breakers;
- loop phases including build, premortem, repair, and selftest;
- method contracts that preserve the original Wizard's useful checks without
  importing Claude as authority;
- a stop condition.

The validator rejects packets that collapse root constraints into extended
constraints, promote analogies/proxies, omit the primary object's first-class
fields, skip wildcard/fixation-breaker lanes, or omit/soften the required
method contracts.

## Method Contracts Mined From Original Wizard

The original Claude Wizard/global instructions contain useful mechanics. v4.3
ports only the mechanics that block known failure modes, not Claude behavior law.

Accepted pattern cards:

| Pattern | Port | Why accepted | Minimal test |
|---|---|---|---|
| question is not authorization | `method_contracts.question_is_not_authorization` | prevents a "why/what/whether" prompt from becoming an implementation order | `python3 scripts/wizard_v4_3_object_preservation.py selftest` |
| order checked separately | `method_contracts.order_check_separate` | prevents content-correct but order-wrong synthesis | `python3 scripts/wizard_v4_3_object_preservation.py selftest` |
| baseline preservation while debugging | `method_contracts.baseline_preservation` | preserves tuned answer/output shape while debugging runtime path | `python3 scripts/wizard_v4_3_object_preservation.py selftest` |
| falsifier-first and Feynman testability | `method_contracts.falsifier_first` and `method_contracts.feynman_testability` | keeps voice methods from becoming decorative labels | `python3 scripts/wizard_v4_3_object_preservation.py selftest` |
| synthesis names the refused merge | `method_contracts.synthesis_refusal` | prevents "held apart" receipts from being merged in the next sentence | `python3 scripts/wizard_v4_3_object_preservation.py selftest` |
| human offload discipline | `method_contracts.human_offload` | resolves tool-recoverable work before asking the owner | `python3 scripts/wizard_v4_3_object_preservation.py selftest` |

Rejected or not ported:

| Pattern | Reason |
|---|---|
| every response ends with a full follow-up block | too Claude-output-specific; Codex already has a concise output contract and should not print worker menus for every answer |
| always fire all voice and lane slots | would create fake plurality unless every slot has a distinct executable packet and receipt |
| Claude model routing rules | Claude pool rules are reference-only; Codex worker-pool truth belongs to `AGENTS.md` |
| Claude global markdown-edit rule | Codex editing policy is governed by Codex developer instructions and repo authority |

The method contract fields are:

```json
{
  "question_is_not_authorization": "A question asks for an answer; it is not authorization to implement unless the user explicitly says to do it.",
  "order_check_separate": "Any sequence or ordering claim must be checked separately from content correctness, with the order witness named.",
  "baseline_preservation": "When debugging runtime behavior, preserve the tuned visible/output baseline and debug the execution path underneath.",
  "falsifier_first": "A Popper pass names the target claim, strongest live falsifier, decisive check, and killed/open/survived classification before agreement.",
  "feynman_testability": "A Feynman pass names the operation, the observable measured, and the pass/fail condition.",
  "synthesis_refusal": "Synthesis must name distinct receipts and explicitly refuse the merge, sequence, or reframe it is not performing.",
  "human_offload": "Resolve with tools before asking; ask the human only for private, preference-bound, or unrecoverable information."
}
```

## Evidence Spine

v4.3 also requires an `evidence_spine`. This is the bridge from "the Wizard had
a good route" to "the route preserved the actual object." It keeps the object
card connected to the source locks and receipts that can defend it.

The spine must name:

- `wizard_runtime`: the runtime relationship, usually "v4.3 guard over v4.2
  packet-current." There is no durable `packet-v4-3-current` unless one is
  explicitly created and validated; v4.3 is an additive guard over v4.2.
- `source_math_locks`: source-lock artifacts or docs that pin the object's
  native math before workers translate it.
- `sim_audit_receipts`: sim/proof/result audit receipts when the packet is used
  to support a sim, proof, or result move. Empty is allowed only when the packet
  is not making a sim/proof/result claim.
- `claude_pattern_cards`: useful Claude workflow, skill, or agent mechanics
  mined as pattern cards. Claude material is reference only, never Codex
  authority and never the primary object.
- `claim_ceiling`: the strongest claim the packet permits.
- `blocked_consumers`: downstream consumers blocked until the packet plus its
  receipts satisfy their own gates.

For Claude-derived updates, the pattern card shape is:

```json
{
  "source_path": ".claude/skills/wizard-v43/SKILL.md",
  "pattern_name": "object-preservation preflight before councils",
  "port_as": "skill",
  "target_path": "/Users/joshuaeisenhart/.codex/skills/three-council-wizard-v4-3/SKILL.md",
  "authority_reason": "Claude material is reference only, not authority; Codex gates through AGENTS.md, CODEX.md, and this validator.",
  "minimal_test": "python3 scripts/wizard_v4_3_object_preservation.py selftest"
}
```

Original Wizard/global mechanics may use absolute source paths such as
`/Users/joshuaeisenhart/.claude/CLAUDE.md` when the owner supplies that material
as source input. The pattern card still must say Claude is reference only, not
authority.

This rule lets Claude improve the Wizard's mechanics without letting Claude
doctrine, worker summaries, or route prose become project truth.

## Command Surface

```bash
python3 scripts/wizard_v4_3_object_preservation.py example
python3 scripts/wizard_v4_3_object_preservation.py validate --input packet.json
python3 scripts/wizard_v4_3_object_preservation.py selftest --out /tmp/v43_selftest.json
python3 scripts/wizard_v4_3_object_preservation.py loop --max-loops 3 --out /tmp/v43_loop.json
python3 scripts/wizard_v4_3_object_preservation.py gate-v42 --input packet.json --task "..." --out /tmp/v43_gate_v42.json
```

The self-test suite intentionally includes failures for Axis0 proxy promotion,
FEP analogy promotion, missing shell fields, root/extended constraint collapse,
underdefined `jk fuzz`, no wildcard lane, missing evidence spine, missing method
contracts, weak order-contract wording, and unclear Claude authority. The
example packet also carries a hashed object statement so later corrections can
invalidate stale object cards instead of letting the loop keep optimizing an
older paraphrase.

`gate-v42` is the executable join between v4.3 and the live v4.2 runtime. It:

- validates the v4.3 primary object card;
- checks the v4.2 boot files and their `authority_status` fields;
- runs the v4.2 packet conformance validator;
- writes a machine-readable receipt that states the claim ceiling;
- optionally launches `scripts/wizard_v4_2.py` with `--launch-v42`.

A `gate-v42` receipt without `--launch-v42` is only a preflight. It cannot be
described as a council run. A `gate-v42 --launch-v42 --dry-run-v42` receipt is
only a topology rehearsal. It cannot be described as `FULL`. A non-dry v4.2
launch still gets its completion status from the v4.2 compiled header and
worker receipts, not from v4.3. v4.3 guards object preservation; it does not
prove the object, admit a sim, or replace the council topology.

## Integration With v4.2

Run v4.3 before v4.2 when the task contains a novel object or when prior runs
show salience drift. v4.3 produces the object-preservation contract. v4.2 then
runs councils around that contract.

If the object is source-math, sim, proof, or result-bearing work, v4.3 must
preserve the newer v4.2 overlays before the v4.2 council run:

- source math lock: exact source formulas and forbidden shorthand are loaded
  before workers translate the object;
- sim audit spine: scout/parity/proof/admission ceilings stay visible;
- collapse auditor: shared-premise and fake-plurality checks run before a
  positive route is accepted;
- Claude pattern intake: Claude updates are mined into Codex pattern cards,
  not imported as behavior law.

v4.3 is a preflight and compile gate:

```text
v4.3 object card validates
-> v4.2 councils run
-> v4.3 validates the compiled next packet
-> loop repairs object-preservation failures before new exploration
```

The local executable receipt form is:

```text
gate-v42 validates object card
-> gate-v42 checks v4.2 boot/conformance
-> optional gate-v42 launches v4.2
-> v4.2 compiled header and receipts decide council completion
-> v4.3 object card remains the preservation boundary for the next packet
```

If v4.2 returns a polished plan that drops the primary object or promotes a
proxy, v4.3 marks that answer invalid even if the route topology was otherwise
healthy.
