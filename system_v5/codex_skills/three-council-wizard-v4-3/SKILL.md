---
name: three-council-wizard-v4-3
description: >-
  Run or develop Wizard v4.3 as the current Wizard route: object cards, proxy-drift checks, MMM maintenance, current Wizard councils/follow-up routing, and Claude/Hermes intake. Do not route current Wizard work through v4.2; v4.2 packet/skill surfaces are legacy/provenance unless the user explicitly asks for a historical v4.2 audit.
---

# Three-Council Wizard v4.3

Current rule: **Wizard is v4.3**. There is no v4.2-to-run for current work.

v4.3 is the active Wizard surface for object preservation, route truth, councils/follow-up routing, MMM maintenance, and proxy-drift checks. Older v4.2 packet files may be read as provenance or migration evidence only; do not load them as the current runtime or tell a worker to run v4.2.

## Boot Order

1. Current user request.
2. Repo/user authority surfaces (`AGENTS.md`, `CODEX.md`, current task docs).
3. v4.3 repo authority:
   - `system_v5/docs/WIZARD_V4_3_PRIMARY_OBJECT_PRESERVATION_SPEC_20260526.md`
   - `scripts/wizard_v4_3_object_preservation.py`
4. Current-task v4.3 packet path, usually:
   - `/Users/joshuaeisenhart/wiki/wizard/hermes-version-current/packets/hermes_v4_3_retrocausal_object_card.json`
5. Current Hermes/Wizard v4.3 surfaces:
   - `/Users/joshuaeisenhart/wiki/wizard/hermes-version-current/README.md`
   - `/Users/joshuaeisenhart/wiki/wizard/hermes-version-current/00_READ_FIRST.md`
   - `/Users/joshuaeisenhart/wiki/wizard/hermes-version-current/15_HERMES_WIZARD_V4_3_OBJECT_PRESERVATION.md`
   - `/Users/joshuaeisenhart/wiki/wizard/hermes-version-current/16_HERMES_WIZARD_MAINTENANCE_GOVERNOR.md`
6. v4.3 MMM maintenance/candidate surfaces when the task touches MMMs.

## What v4.3 Does

Run v4.3 when any of these are true:

- the task has a novel or fragile primary object;
- a proxy, analogy, carrier, metric, or route label could become the object;
- the user asks for Wizard, v4.3, object preservation, MMM improvement, or current Wizard maintenance;
- Claude/Hermes/Codex mechanics are being mined into the current stack;
- a durable claim or compiled move needs route truth and object preservation.

The v4.3 guard checks:

- primary object card and object statement hash;
- source anchors, first-class fields, invariants, and forbidden substitutions;
- lateral mapping type: `adapter`, `probe`, `analogy`, or `proxy`;
- preservation, loss, preconditions, and kill controls;
- evidence spine, claim ceiling, blocked consumers, and proxy drift.

Validator pass means only that the object-preservation card passed this guard. It does not prove a sim, proof, physics claim, Axis0 claim, formal admission, or FULL council execution.

## Run Path

In `/Users/joshuaeisenhart/Codex-Ratchet`, use the repo validator:

```bash
python3 scripts/wizard_v4_3_object_preservation.py validate --input <packet.json>
```

For the existing Hermes packet:

```bash
python3 scripts/wizard_v4_3_object_preservation.py validate --input /Users/joshuaeisenhart/wiki/wizard/hermes-version-current/packets/hermes_v4_3_retrocausal_object_card.json
```

For negative controls:

```bash
python3 scripts/wizard_v4_3_object_preservation.py selftest --out /tmp/v43_selftest.json
```

Do not follow a clean v4.3 guard with a v4.2 run. If a historical v4.2 artifact is inspected, label it `legacy/provenance` and keep it out of current-run claims.

## Skill And Agent Composition

Treat v4.3 as the active skill-of-skills route, with strict receipt truth:

- use task-specific skills only after the v4.3 object/route boundary is named;
- count a worker route only when the runtime returns a real receipt with assigned route, loaded salience slices, terminal status, and usable output;
- treat Claude/Hermes outputs as pressure until local file reads and validator/probe results confirm them;
- never promote a reference-only MMM candidate without explicit admission scope and verification.

## Output Rules

Say the version boundary plainly:

- `Wizard is v4.3; v4.2 is legacy/provenance, not the current run target.`
- `v4.3 object-preservation guard passed; no sim/proof/admission claim.`
- `v4.3 reference-only MMM candidate used as overlay, not promoted.`

Never say:

- the old “v43 plus v42” binding phrase
- instructions that hand current work to the old version after v4.3
- claims that the old version remains the runtime
- `v4.3 replaced v4.2` as if both are live peers; instead say current Wizard is v4.3 and old v4.2 surfaces are provenance
- `object proven by validator`
- `MMM-backed` without a preload receipt
- `Codex-native subagent` without a spawn receipt

## Repair Loop

If a v4.3 check fails:

1. Name the first failing field or drift phrase.
2. Repair only that packet or route source.
3. Rerun the validator.
4. Scan compiled output for semantic proxy drift.
5. Keep historical v4.2 packet references out of current-run language unless the user explicitly asks for historical comparison.
