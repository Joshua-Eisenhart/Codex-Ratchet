# Wizard Output Regression Checklist

Date: 2026-04-29

Use this checklist when changing `AGENTS.md`, `CODEX.md`, Wizard packet assets, or Wizard runtime adapters.

## Fails

Reject a Wizard output if any of these are true:

- It silently downgrades from the default Full Wizard to compact/partial Wizard without marking blocked/deferred/not-run waves.
- It calls a partial subset "Full Wizard" when required Full Wizard waves did not run or receive explicit blocked/deferred receipts.
- It claims voices ran but gives only one blended voice summary.
- Voice labels appear, but the sentences are interchangeable.
- A visible voice was controller-written instead of produced by a real subagent loaded with that exact voice mini-MMM.
- A pending, slow, or old-context worker is counted as an executed route before it returns a usable receipt.
- The controller waits idly on one route while independent routes could be run or rerouted through other Codex/Claude/tool lanes.
- A blocked or slow route is allowed to stall the critical path instead of being rerun on a different model/runtime and debugged separately.
- A Codex runtime/subagent-health failure is routed around with another model instead of being fixed first.
- A Codex subagent is counted as spawned without a spawn-agent tool receipt containing agent id, route-local mini-MMM path, assigned route, completion status, and usable output.
- Duplicate/rerouted workers return conflicting receipts without the controller marking which receipt was accepted, superseded, or left supplemental.
- Follow-up is mostly receipt inspection, route proof, contradiction listing, or orchestration debugging.
- A controller-local route is presented as spawned.
- A visible voice, lane, check, council, composition, or preworked follow-up option is claimed without a real subagent/tool/check receipt or an explicit blocked/deferred/future-only marker.
- LLM Council appears as executed without its own multi-subagent council wave and nested rounds/subsubagents when supported.
- A follow-up option is shown as valid/preworked without receipts for all three waves: Make/Assembly, Run/Scout, and Audit/Improve.
- A spawned subagent route lacks the exact lane-local mini-MMM scope for that route.
- The leader claims to run all voice or lane mini-MMMs in the main thread.
- The answer spends more space proving workers ran than giving useful content.
- Audit appears as a default section instead of fixing the answer.

## Passes

Accept only when:

- Full Wizard is attempted by default for substantive work, or an explicit reason is given for a blocked/deferred wave.
- Route truth is compactly stated in the header or Results boundary.
- Pending, blocked, deferred, and not-run routes are distinguished from completed spawned routes.
- Blocked or slow routes are rerouted to another model/runtime when doing so can continue the work safely.
- Codex spawn/reset/receipt health is verified before cross-model reroutes are used as substitutes.
- The leader uses the positive main MMM, while spawned routes use only their exact mini-MMM.
- Each visible voice has a distinct useful contribution from a real voice subagent when a voice wave ran.
- Council truth states whether a real multi-subagent council wave ran, was blocked, or was deferred.
- Follow-up truth states Make/Assembly, Run/Scout, and Audit/Improve status for every visible preworked option.
- Live Wizard validation uses `scripts/codex_harness_adapter.py validate --require-live-execution` when the output claims live spawned routes or preworked follow-up scouts.
- Council appears only if it materially changes the answer.
- Results state artifacts, blockers, checks, and accepted receipts without dumping logs.
- Follow-up is an audited useful prompt menu, mostly lanes and compositions.
- Quality/audit score is footer-only when used.

## Minimal Smoke Prompt

Ask:

> Run the proper Full Wizard on a failed output where the user says there were no voices, follow-up was broken, and the result read like a log.

The response must include readable voice content and useful follow-up prompts. Header truth alone is not enough.
