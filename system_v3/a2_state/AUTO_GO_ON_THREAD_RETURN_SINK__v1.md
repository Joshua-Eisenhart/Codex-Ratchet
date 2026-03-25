# AUTO_GO_ON_THREAD_RETURN_SINK__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-11
Role: define the exact repo-held sink for raw returned thread text used by the auto-`go on` control chain

## 1) Raw return staging path

Raw returned thread text should be staged in:
- `work/audit_tmp/auto_go_on_thread_returns/`

Suggested file naming:
- `<thread_label>.txt`

This sink is:
- append-safe
- noncanon
- controller-facing
- meant for raw returned thread text before normalization

## 2) Packet staging path

The corresponding cycle packet should be written to:
- `work/audit_tmp/auto_go_on_thread_returns/<thread_label>.cycle.json`

The resulting normalized outputs should be written to:
- `work/audit_tmp/auto_go_on_thread_returns/<thread_label>.out/`

Expected outputs in that directory:
- `auto_go_on_thread_result.json`
- `auto_go_on_runner_output.json`

## 3) One-line rule

If a thread returns a bounded result in chat and the return is eligible for continuation evaluation:
- save the raw returned text under:
  - `work/audit_tmp/auto_go_on_thread_returns/<thread_label>.txt`
- create one cycle packet
- run the packet-driven cycle helper

Do not leave returned thread text only in chat memory if it needs continuation routing.

## 4) Current manual toolchain

Current packet-creation helper:
- `system_v3/tools/create_auto_go_on_cycle_packet.py`

Current packet-driven cycle helper:
- `system_v3/tools/run_auto_go_on_cycle_from_packet.py`

Underlying helpers:
- `system_v3/tools/extract_auto_go_on_thread_result.py`
- `system_v3/tools/auto_go_on_runner.py`

## 5) Current shortest path

1. Save raw return text:
- `work/audit_tmp/auto_go_on_thread_returns/<thread_label>.txt`

2. Create cycle packet:

```text
python3 system_v3/tools/create_auto_go_on_cycle_packet.py \
  --reply-text /home/ratchet/Desktop/Codex\ Ratchet/work/audit_tmp/auto_go_on_thread_returns/<thread_label>.txt \
  --target-thread-id <thread_id> \
  --thread-class <A2_WORKER|A1_WORKER|A2_CONTROLLER> \
  --boot-surface /abs/path/to/boot.md \
  --source-decision-record /abs/path/to/decision_record.md \
  --expected-return-shape "bounded worker return with STOP or one more bounded pass" \
  --fallback-role <fallback_role> \
  --fallback-scope "<fallback_scope>" \
  --out-dir /home/ratchet/Desktop/Codex\ Ratchet/work/audit_tmp/auto_go_on_thread_returns/<thread_label>.out \
  --out-json /home/ratchet/Desktop/Codex\ Ratchet/work/audit_tmp/auto_go_on_thread_returns/<thread_label>.cycle.json
```

3. Run cycle:

```text
python3 system_v3/tools/run_auto_go_on_cycle_from_packet.py \
  --packet-json /home/ratchet/Desktop/Codex\ Ratchet/work/audit_tmp/auto_go_on_thread_returns/<thread_label>.cycle.json
```

## 6) Current decision use

Read:
- `work/audit_tmp/auto_go_on_thread_returns/<thread_label>.out/auto_go_on_runner_output.json`

Possible final runner outputs:
- `RUNNER_OUTPUT__STOP`
- `RUNNER_OUTPUT__CLOSEOUT`
- `RUNNER_OUTPUT__MANUAL_REVIEW`
- `RUNNER_OUTPUT__SENDER_PACKET`

If the output is:
- `RUNNER_OUTPUT__SENDER_PACKET`
then the current live send path remains:
  - manual operator sends exactly:
    - `go on`

## 7) Immediate implication

After this note:
- the auto-`go on` chain has a real repo-held staging path for raw returned thread text
- the remaining gap is no longer sink absence
- the remaining gap is later reducing the two-command operator path into one smaller wrapper or browser-assisted path
