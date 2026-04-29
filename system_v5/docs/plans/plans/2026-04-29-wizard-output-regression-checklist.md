# Wizard Output Regression Checklist

Date: 2026-04-29

Use this checklist when changing `AGENTS.md`, `CODEX.md`, Wizard packet assets, or Wizard runtime adapters.

## Fails

Reject a Wizard output if any of these are true:

- It claims voices ran but gives only one blended voice summary.
- Voice labels appear, but the sentences are interchangeable.
- Follow-up is mostly receipt inspection, route proof, contradiction listing, or orchestration debugging.
- A controller-local route is presented as spawned.
- The answer spends more space proving workers ran than giving useful content.
- Audit appears as a default section instead of fixing the answer.

## Passes

Accept only when:

- Route truth is compactly stated in the header or Results boundary.
- Each visible voice has a distinct useful contribution when a voice wave ran.
- Council appears only if it materially changes the answer.
- Results state artifacts, blockers, checks, and accepted receipts without dumping logs.
- Follow-up is an audited useful prompt menu, mostly lanes and compositions.
- Quality/audit score is footer-only when used.

## Minimal Smoke Prompt

Ask:

> Run the proper Full Wizard on a failed output where the user says there were no voices, follow-up was broken, and the result read like a log.

The response must include readable voice content and useful follow-up prompts. Header truth alone is not enough.

