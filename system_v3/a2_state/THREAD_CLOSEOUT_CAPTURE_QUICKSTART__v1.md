# THREAD_CLOSEOUT_CAPTURE_QUICKSTART__v1

Status: DRAFT / NONCANON / A2 OP NOTE
Date: 2026-03-09
Role: shortest path for turning thread closeout replies into repo-held packets

## 1) Fill one packet JSON

Preferred path:
- the worker thread should self-save its own raw closeout body into:
  - `work/audit_tmp/thread_closeout_packets/<dispatch_id>.txt`
- then the controller can convert and append it later
- do not make the operator carry returned text by hand if the worker can write into the shared workspace

Then either fill one packet JSON directly, or extract it from the saved raw text.

Start from:
- `system_v3/a2_derived_indices_noncanonical/thread_closeout_packet_template_v1.json`

Fill one file per returned thread.

Suggested temporary location:
- `work/audit_tmp/thread_closeout_packets/<thread_label>.json`

If you only have a raw pasted closeout reply, first convert it with:

```text
python3 system_v3/tools/extract_thread_closeout_packet.py \
  --reply-text work/audit_tmp/thread_closeout_packets/<thread_label>.txt \
  --source-thread-label "<thread_label>" \
  --out-json work/audit_tmp/thread_closeout_packets/<thread_label>.json
```

## 2) Append it into the sink

Run:

```text
python3 system_v3/tools/append_thread_closeout_packet.py \
  --packet-json work/audit_tmp/thread_closeout_packets/<thread_label>.json
```

Default sink:
- `system_v3/a2_derived_indices_noncanonical/thread_closeout_packets.000.jsonl`

Staging folder:
- `work/audit_tmp/thread_closeout_packets/`

## 3) After multiple packets are appended

Then run the controller audit over the sink:
- compare `final_decision`
- compare `thread_diagnosis`
- compare strongest outputs
- identify:
  - stop lanes
  - one-more-step lanes
  - correction-later lanes

Audit command:

```text
python3 system_v3/tools/audit_thread_closeout_packets.py
```

## 4) Current rule

Until a real `thread closeout auditor` skill exists, this is the correct manual capture path.
