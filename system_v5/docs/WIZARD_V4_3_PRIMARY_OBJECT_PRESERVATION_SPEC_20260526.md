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
- a stop condition.

The validator rejects packets that collapse root constraints into extended
constraints, promote analogies/proxies, omit the primary object's first-class
fields, or skip wildcard/fixation-breaker lanes.

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

This rule lets Claude improve the Wizard's mechanics without letting Claude
doctrine, worker summaries, or route prose become project truth.

## Command Surface

```bash
python3 scripts/wizard_v4_3_object_preservation.py example
python3 scripts/wizard_v4_3_object_preservation.py validate --input packet.json
python3 scripts/wizard_v4_3_object_preservation.py selftest --out /tmp/v43_selftest.json
python3 scripts/wizard_v4_3_object_preservation.py loop --max-loops 3 --out /tmp/v43_loop.json
```

The self-test suite intentionally includes failures for Axis0 proxy promotion,
FEP analogy promotion, missing shell fields, root/extended constraint collapse,
underdefined `jk fuzz`, and no wildcard lane. The example packet also carries a
hashed object statement so later corrections can invalidate stale object cards
instead of letting the loop keep optimizing an older paraphrase.

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

If v4.2 returns a polished plan that drops the primary object or promotes a
proxy, v4.3 marks that answer invalid even if the route topology was otherwise
healthy.
