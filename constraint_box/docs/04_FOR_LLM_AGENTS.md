# Rules for LLM agents

1. Scope: repository changes. Modify only paths authorized by the current card. Adjacent refactors, cleanup, formatting, and generated-file refreshes are forbidden. Detection: compare the changed-path list to the card allowlist; any extra path is a violation.

2. Scope: tests. Never edit, delete, skip, weaken, reorder, or replace a test to make a result pass. Detection: inspect the diff for test paths and compare assertions, fixtures, discovery names, and skip markers to the pre-work tree. An authorized new regression is allowed only when the card asks for it.

3. Scope: tool outcomes. Never write a tool result, `ran`, `passed`, `verdict`, `load_bearing`, or equivalent outcome as a literal when the file does not invoke or observe something able to produce it. Detection: run the repo-root `claimgate_plugin/slop_gate.py`; S1 and the bridge check `check_no_uncomputed_verdict.py` flag named-tool literal outcomes without a tool or launcher.

4. Scope: fixes. A fix without a test is not a guarded fix. Required proof: retain the test in a throwaway copy, revert only the fix, and show the test fails for the original defect. Detection: the work receipt must name the reverted expression or hunk, the exact command, the nonzero result, and the restored passing result.

5. Scope: pins. Treat every digest pin as data. It does not follow the file it names. After the final edit to a pinned file, recompute the digest, update the pin only when authorized, and compare it to the file again. Detection: hash the named source and compare it to the manifest. This controller pin went stale twice in two days and was stale again in the S1 run documented on 2026-07-27.

6. Scope: status language. Use only this ladder: `exists` < `runs` < `passes local rerun` < `canonical by process`. Never infer a higher label from a lower label. Detection: for every status phrase, require the evidence needed for that exact rung. A file proves `exists`; a command exit proves at most `runs`; a fresh bounded suite can prove `passes local rerun`; repository process alone can establish `canonical by process`.

7. Scope: promotion. Preserve explicit claim ceilings. Never change or imply a change from `promotion_allowed: false` unless the owner and the governing process authorize promotion. Detection: search outputs and prose for promotion language and compare it with the source receipt.

8. Scope: measurement coverage. Record what was not measured. Use `controls_not_measured` where the estate schema supports it. Detection: enumerate required controls from the active profile and compare them to recorded control keys; absent controls must be named, not hidden behind an aggregate pass.

9. Scope: check polarity. Define what every nonzero and zero exit means before wiring it. A regression must fail on deviation in either direction from each recorded per-case expectation. Detection: force one expected-pass case to fail and one expected-fail case to pass; both movements must make the regression nonzero with distinct reason codes.

10. Scope: producer trust. Do not accept producer-authored receipt fields as evidence that the producer performed the claimed operation. Detection: identify the independent observation that binds the world to the claim. If every observation can be authored or recognized by the producer, lower the claim and record the control as incomplete.

11. Scope: visible probes. Before adding a poison, mutation, challenge, sentinel, or hidden case, state whether the worker can distinguish the probed run from ordinary execution. Detection: inspect environment, imports, callable metadata, source, process arguments, files, and timing visible to the worker. An identifiable probe cannot prove ordinary execution.

12. Scope: false positives. Every new slop or policy signature requires an honest nearby negative fixture. Detection: the regression must contain both a positive and negative case, and an unexpected finding on the negative must fail with a false-positive reason.

13. Scope: duplicate trees. Always state whether a measurement used repo-root `claimgate_plugin/` or `constraint_box/claimgate_plugin/`. Never merge their results. Detection: record the absolute working directory and source path in the receipt. The trees differ and canonical ownership is open.

14. Scope: applicability. Do not say the applicability registry gates controller or estate decisions. It is CLI-reachable but unwired. Detection: trace imports and callers from `controller.py` and `estate.py`; neither uses `ApplicabilityRegistry`.

15. Scope: ledgers. Do not describe the default sibling head as an external trust root. Detection: identify where the retained head lives and who can rewrite it. If it is beside the ledger under the same authority, the chain supplies consistency only.

16. Scope: external gate results. Treat a nonzero gate exit as a policy disposition, not a scientific verdict. Detection: report the exact command, exit code, resolved chain root, and claim ceiling.

17. Scope: errors. Never convert missing input, timeout, unavailable dependency, parse failure, or evaluation failure into claim refusal or success. Detection: assert separate reason codes and exits for precondition, evaluation, and policy outcomes.

18. Scope: unresolved work. When an authorized change cannot close a defect, add or update an open `PROVENANCE.md` row if the card permits that file. Do not soften, omit, or reword the defect as completed. Detection: compare the final claim with the observed counterexample and defect register. If the card forbids editing `PROVENANCE.md`, report the needed row in the handoff instead.

19. Scope: commands. Never write “should pass” for an acceptance command. Run it and paste the real summary and exit, or label it unmeasured. Detection: require a fresh command receipt.

20. Scope: inherited documents. Treat old handoff prose as routing context until current code, tests, and receipts confirm it. Detection: cite the present source or mark the statement unchecked.

## Completion self-check

Before claiming done, answer YES to every applicable question:

- Did I change only authorized paths?
- Did I leave existing tests intact?
- Does every tool outcome come from an invocation or independent observation?
- Does every fix have a regression with demonstrated teeth?
- Do all pins match the final files they name?
- Did I use no status above the evidence rung earned?
- Did I preserve `promotion_allowed: false`?
- Did I list every required control that was not measured?
- Did I test movement in both directions where policy expectations are recorded?
- Did I test an honest negative for every new detector?
- Did I name the exact ClaimGate tree and working directory?
- Did I paste real command results and exits?
- Did I leave every open defect visible?
