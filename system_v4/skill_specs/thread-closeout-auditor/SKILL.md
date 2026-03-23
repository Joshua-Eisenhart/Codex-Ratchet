---
name: thread-closeout-auditor
description: Capture, normalize, append, and audit returned thread closeout replies for the Codex Ratchet system. Use when overlong worker threads have replied to the closeout prompt and those replies need to become repo-held packets, stop/continue/correct decisions, and next-batch routing input.
---

# Thread Closeout Auditor

Use this skill when thread closeout replies exist and need to be turned into repo-held controller artifacts.

## Core rules

- Do not audit thread replies from chat memory alone if they can be saved into the workspace.
- Treat closeout packets as controller-facing noncanon artifacts.
- Do not smooth contradictory thread diagnoses together.
- One returned thread = one packet line in the sink.
- Do not continue worker exploration from this skill; this skill is for capture and audit only.

## Repo surfaces

- Prompt source:
  - `work/zip_subagents/THREAD_CLOSEOUT_AUDIT_PROMPT__v1.md`
- Sink:
  - `system_v3/a2_derived_indices_noncanonical/thread_closeout_packets.000.jsonl`
- Template:
  - `system_v3/a2_derived_indices_noncanonical/thread_closeout_packet_template_v1.json`
- Operator notes:
  - `system_v3/a2_state/THREAD_CLOSEOUT_CAPTURE_QUICKSTART__v1.md`
  - `system_v3/a2_state/THREAD_CLOSEOUT_RESULT_SINK__v1.md`

## Tools

- Extract raw reply text into packet JSON:
  - `system_v3/tools/extract_thread_closeout_packet.py`
- Append validated packet into sink:
  - `system_v3/tools/append_thread_closeout_packet.py`
- Audit sink contents:
  - `system_v3/tools/audit_thread_closeout_packets.py`

## Workflow

1. Check whether packet JSON files already exist under:
   - `work/audit_tmp/thread_closeout_packets`
2. If only raw reply text exists, convert each reply:

```text
python3 system_v3/tools/extract_thread_closeout_packet.py \
  --reply-text work/audit_tmp/thread_closeout_packets/<thread_label>.txt \
  --source-thread-label "<thread_label>" \
  --out-json work/audit_tmp/thread_closeout_packets/<thread_label>.json
```

3. Append each packet:

```text
python3 system_v3/tools/append_thread_closeout_packet.py \
  --packet-json work/audit_tmp/thread_closeout_packets/<thread_label>.json
```

4. Audit the sink:

```text
python3 system_v3/tools/audit_thread_closeout_packets.py
```

5. Report:
   - packet count
   - stop lanes
   - continue-one-step lanes
   - correct-later lanes
   - strongest reusable outputs
   - next-batch implications

## Guardrails

- If the sink is empty, say so directly.
- If staging is empty, do not pretend ingestion happened.
- Do not infer artifact paths that are not present in the reply.
- If extraction fails because the reply format drifted, stop and report the exact field mismatch.
- Keep the final controller summary concise and decision-first.
