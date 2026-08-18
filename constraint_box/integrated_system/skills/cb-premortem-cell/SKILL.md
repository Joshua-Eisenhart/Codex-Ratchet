---
name: cb-premortem-cell
description: Run one digest-bound premortem lens inside a ConstraintBox ZIP cell.
---

# CB Premortem Cell

This is an embedded worker procedure, not a decision-maker. It receives one
exact target byte string, one assigned lens, one bounded compact mini-MMM
combination, and this skill file. The target bytes are immutable input.

The worker must return exactly one JSON object through the declared
`output_delivery=provider_response` route. The object must contain exactly:

```text
schema
lens
target_sha256
failure_mechanisms
evidence
limits
falsifier
warning
finite_repair
rerun_operation
claim_ceiling
```

`failure_mechanisms`, `evidence`, and `limits` are non-empty arrays of plain
strings. The other fields are non-empty strings. `lens` and `target_sha256`
must match the packet manifest. The response must not claim promotion,
authority, semantic consensus, or release.

The `evidence` array must contain exactly one delivery echo for the supplied
skill, every assigned MMM, and the tool evidence. Copy the exact strings from
the member prompt, with no unlabeled digest substitute, duplicate label, extra
label, or echo in another field. The formats are:

```text
skill_bytes_delivered_echo:path=SKILLS/cb-premortem-cell/SKILL.md;sha256=<supplied skill sha256>
mmm_bytes_delivered_echo:voice=<voice>;path=MMMS/<voice>.md;sha256=<supplied MMM sha256>
tool_bytes_delivered_echo:path=output/tool_evidence.json;canonical_sha256=<supplied canonical_sha256>
```

These are delivery echoes only. They do not prove that a worker read,
executed, consumed, or comprehended the bytes. The receipt must keep
`mmm_read_proved:false`, `skill_read_proved:false`, and `skill_executed:false`.

The three admitted lenses are:

- `likely_failure`: the most likely concrete repeated-use failure;
- `dangerous_failure`: the most damaging authority, custody, or evidence
  failure, even if uncommon;
- `hidden_assumption`: an assumption that lets a passing receipt overstate
  what actually happened.

Use the supplied target and packet files only. Name direct evidence, a finite
falsifier, an early warning, a bounded repair, and the exact operation that
would rerun the check. Keep competing findings separate. Do not vote, select
a winner, edit live source, launch a child, or write an authoritative receipt.

The parent ZIP wave validates the JSON shape, target digest, provider/model
request binding, MMM and skill byte binding, ancestry, retry history, and
negative controls. A fluent answer without the exact JSON object is a refusal.

Claim ceiling: one bounded premortem observation for one packet target; not a
truth disposition, gate, promotion, release, or proof that a model understood
the MMM or skill.
