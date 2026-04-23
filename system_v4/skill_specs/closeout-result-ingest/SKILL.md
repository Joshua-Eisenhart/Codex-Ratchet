---
name: closeout-result-ingest
description: Convert returned thread closeout replies into repo-held packet artifacts for the Codex Ratchet system. Use when raw thread closeout text or packet JSON exists and needs to be normalized, appended into the closeout sink, and summarized for controller use.
---

# Closeout Result Ingest

Use this skill when returned thread closeout audits need to become repo-held artifacts instead of staying in chat memory.

## Core rules

- One returned thread = one packet line in the sink.
- Do not leave returned closeout results only in chat.
- Preserve exact artifact paths and diagnosis values when present.
- Do not smooth contradictory thread diagnoses together.
- If staging or sink is empty, say so directly.

## Owner surfaces

- `system_v3/a2_state/THREAD_CLOSEOUT_RESULT_SINK__v1.md`
- `system_v3/a2_state/THREAD_CLOSEOUT_CAPTURE_QUICKSTART__v1.md`
- `system_v3/a2_derived_indices_noncanonical/thread_closeout_packet_template_v1.json`
- `system_v3/a2_derived_indices_noncanonical/thread_closeout_packets.000.jsonl`

## Tools

- Extract raw reply text:
  - `system_v3/tools/extract_thread_closeout_packet.py`
- Append validated packet:
  - `system_v3/tools/append_thread_closeout_packet.py`
- Audit sink:
  - `system_v3/tools/audit_thread_closeout_packets.py`

## Workflow

1. Check staging under:
   - `work/audit_tmp/thread_closeout_packets`
2. If only raw reply text exists, convert each file:

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
   - strongest outputs
   - immediate controller implications

## Guardrails

- Do not invent packet fields that the reply did not support.
- If extraction fails, report the exact mismatch and stop.
- Do not treat the sink as doctrine; it is controller-facing noncanon.
- Do not skip validation and append malformed packets.
