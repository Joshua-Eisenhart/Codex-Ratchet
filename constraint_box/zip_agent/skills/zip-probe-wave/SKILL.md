---
name: zip-probe-wave
description: Use when building and running one deterministic ConstraintBox ZIP work cycle over the current Light tool manifest and an existing operation field.
---

# ZIP Probe Wave

This skill turns source material, the current tool manifest, and a prior local
field into one validated ZIP_JOB. The prompt is never canon. The return ZIP is
the result; prose is not.

## 1. Bind inputs into one packet

```bash
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent build-work-cycle \
  --prompt /path/to/prompt.md \
  --tool-manifest ../config/cb_light_tools_v1.json \
  --prior-field /path/to/summary.json \
  --seed 81402 --jobs 16 --pair-samples 128 \
  --out /tmp/cb-zip-probe-work-cycle.zip
```

Record the packet digest. The packet must contain the prompt bytes, manifest,
prior field summary, request, and task definition in its file registry.

## 2. Validate before execution

```bash
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent validate \
  /tmp/cb-zip-probe-work-cycle.zip
```

Any unknown operation, missing member, digest drift, alias, or schema error is a
refusal. Do not repair the packet in memory.

## 3. Run the local field

```bash
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent run \
  /tmp/cb-zip-probe-work-cycle.zip \
  --return-zip /tmp/cb-zip-probe-work-cycle.return.zip \
  --cache-dir /tmp/cb-zip-probe-cache
```

The operation runs two fresh-process imports and one severance negative for
every manifest tool, plus seeded AB/BA pair observations. It compiles a finite
observational quotient and one coupled mass/topology artifact. Z3, CVC5,
SymPy, and Rustworkx cross-check finite identities; they do not vote on policy.

## 4. Verify and inspect

```bash
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent verify-return \
  /tmp/cb-zip-probe-work-cycle.return.zip \
  --input /tmp/cb-zip-probe-work-cycle.zip
```

Required outputs:

- `output/interpretations.json`
- `output/probe_events.jsonl`
- `output/measured_quotient.json`
- `output/entropy_topology.json`
- `output/work_cycle.json`

Only operation-mapped tools may receive an operation rank. Generic import-only
tools remain tied and explicitly unmapped.

## 5. Run the nested failure wave

Use the `zip-failure-wave` skill with the work-cycle input packet as its target.
All three child returns and the compiled parent return are required. A mutation
refusal is evidence for that boundary only.

## 6. Optional second field

Change only `seed` or `pair-samples`, rebuild the packet, and compare quotient
classes, components, and AB/BA divergences. Do not merge fields by prose.

## MMM and model boundary

This version is entirely deterministic and therefore does not load an MMM. A
future model-filled child must use `mmm-preload` before its task, return its own
child ZIP, and remain proposal-only until a deterministic consumer accepts or
holds the observation. No provider or model name belongs in this skill.

Claim ceiling: local observational tool field and ZIP custody only; not global
tool usefulness, prompt truth, model execution, hook enforcement, admission,
portability, promotion, or release.
