# Premortem Transcript: Three-Wave Wizard

Superseded: this transcript used an over-hardening frame for MMMs. See `premortem-transcript-20260502-130941.md` for the corrected frame: MMMs and mini-MMMs are salience manifolds that lift system-native vocabulary and completion topology; receipt rules bind execution claims.

Timestamp: 2026-05-02 12:04:01 America/Los_Angeles

## Context

What: Redesign Wizard around three sequential councils: Decision Council, Failure Council, and Follow-up Council.

Who: Joshua, Codex Ratchet agents, Wizard workers, and future Codex/Claude/Gemini worker lanes.

Success: Simplify Wizard's visible architecture while preserving receipt truth, hard dissent, high useful parallelism, liveness rerouting, and actionable follow-ups.

## Premortem Frame

It is six months from now. The three-wave Wizard redesign failed. It became slower, more ceremonial, or less truthful than the current Wizard. We are looking back to understand what killed it.

## Raw Failure Reasons

1. The three councils became ceremonial wrappers that recreated the old voice/lane sprawl inside each council.
2. Failure Council softened into polite risk commentary instead of killing or quarantining unsupported decisions.
3. High parallelism caused worker stampedes, stale pending lanes, and receipt-count inflation.
4. Follow-up Council generated clever prompts instead of executable repo actions.
5. Decision Council overfit to Six Hats and lost project-specific Wizard strengths like Popper, Factory, Systems, and route-truth audit.

## Deep Dives

### 1. Council Wrapper Sprawl

Failure story: The labels looked cleaner at first, but each council rebuilt its own internal voice matrix, lane taxonomy, arbitration rules, exceptions, and receipt language. Agents learned the new names while keeping old behavior: ornate plurality, inflated route counts, and synthesis pretending to be execution.

Underlying assumption: Simplifying visible architecture would simplify operating behavior without enforceable receipt gates and role boundaries.

Early warnings: Council outputs name many internal roles even when only one or two changed the answer. Receipts prove that councils ran, but not which concrete worker changed which claim.

### 2. Failure Council Softening

Failure story: Decision Council emits proposals, Failure Council reviews risks, and unsupported decisions still flow to Follow-up Council with softer language. Caveats become candidate lanes, making weak ideas look productively preworked.

Underlying assumption: Failure Council would behave like a falsification gate without explicit kill/quarantine authority.

Early warnings: Failure outputs say "risky" or "worth checking" instead of `kill`, `quarantine`, `harden`, or `pass`. Missing evidence still gets follow-up lanes.

### 3. Parallelism Receipt Inflation

Failure story: The liveness rerouter becomes an inflation engine. A delayed worker produces a duplicate lane; the duplicate returns first; the original later returns conflicting fragments; both get counted as evidence. The system looks more rigorous while becoming less reliable.

Underlying assumption: High parallelism would increase useful independent evidence faster than coordination debt.

Early warnings: Wave summaries foreground spawned/returned counts over accepted canonical receipts. Follow-up options cite started, rerouted, late, or conflicting workers.

### 4. Follow-up Prompt Theater

Failure story: Follow-up Council produces elegant lane prompts that sound precise but still require Joshua to translate them into file edits, queue moves, tests, or commits. Wizard stops faking plurality but launders non-execution through clever next-step language.

Underlying assumption: Better follow-up candidates would naturally become executable repo actions without a hard actionability gate.

Early warnings: Follow-ups lack target artifact, command/check, owner, and done condition. Many labels recur, but few produce changed files, verified sims, queue movement, commits, or killed options.

### 5. Generic Hats Flatten Wizard

Failure story: Six Hats becomes the dominant model because it is easy to teach and summarize. Agents produce balanced perspectives instead of project-native objections. Popper softens into risk, Factory becomes generic execution planning, Systems becomes vague second-order commentary, and route-truth audit becomes bookkeeping.

Underlying assumption: Generic cognitive roles could preserve Wizard's project-specific epistemic machinery if embedded as internal behavior.

Early warnings: Decision outputs use polished hat language but stop naming killed claims, bottlenecks, queue state, feedback loops, and receipt boundaries. Follow-ups stop tracing to real route evidence or blocked/deferred waves.

## Opus Critique

Claude Opus recommended the three-wave layout with changes:

- Decision Council produces one selected bounded move plus one or two live alternatives. It should not do failure analysis.
- Failure Council reads Decision Council raw receipts, not the synthesis paragraph. It returns `kill`, `quarantine`, `harden`, or `pass`.
- If Failure Council kills the move, control returns to Decision Council with the kill receipt as exclusion evidence.
- Follow-up Council runs only after Failure status is written.
- Liveness/rerouter is inside each wave, not a fourth wave.
- Opus should be used for named arbitration conditions, not wide fanout.

## Synthesis

Most likely failure: The councils become prettier wrappers around old sprawl unless role contracts and receipt boundaries are enforceable.

Most dangerous failure: Failure Council softens and lets unsupported decisions survive, because then the simplified architecture actively weakens Wizard's safety function.

Hidden assumption: Cleaner structure will create cleaner behavior. It will not unless verdicts, canonical receipts, liveness state, and actionability are hard gates.

## Revised Plan

1. Make the three councils sequential write-barrier waves: Decision, Failure, Follow-up.
2. Allow high parallelism only inside a wave.
3. Add a liveness/rerouter role inside each wave.
4. Distinguish spawned, completed, accepted canonical, superseded, late, blocked, deferred, and simulated receipts.
5. Require Failure Council verdicts: `kill`, `quarantine`, `harden`, or `pass`.
6. Require Follow-up Council actionability: target, owner, check, done condition, and scout status.
7. Keep voices and hats as role libraries, not top-level architecture.

## Pre-Launch Checklist

1. Spike with a known-bad Decision claim and verify Failure Council returns `kill`.
2. Run one real repo decision through all three waves with wall-clock liveness limits.
3. Confirm every visible council slot maps to a terminal receipt or explicit blocked/deferred/simulated state.
4. Confirm Follow-up Council outputs executable next moves, not just prompts.
5. Repeat once on a different task shape before promoting the design.
