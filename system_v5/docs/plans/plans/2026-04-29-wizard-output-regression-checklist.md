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
- Claude Bridge, Gemini, OMX, tmux, or plain tool output is counted as Codex-native subagent evidence.
- A Claude Bridge worker is counted without stream-mode Task/Agent evidence, completed task notification, receipt/artifact path, and usable output.
- A Gemini worker is counted without a durable command/OMX artifact containing route/prompt hash, model, exit status, output, conclusion, and open fields.
- An OMX team wave is claimed outside a live tmux leader pane/session, or tmux presence alone is treated as team execution.
- Header counts aggregate Codex, Claude, Gemini, OMX/tmux, and tools without showing the pool split.
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
- Worker pools are named separately in the header or Results boundary: Codex native, Claude Bridge, Gemini, OMX/tmux, and tools.
- Claude Bridge routes count only from stream-mode Task/Agent receipts; final prose alone is advisory.
- Gemini routes count only from direct CLI or `omx ask gemini` artifacts with route, model, exit/output, conclusion, and open fields.
- OMX team routes are either backed by live tmux leader/pane receipts or marked blocked; `omx ask` and `omx sparkshell` are counted as their own non-team surfaces.
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
