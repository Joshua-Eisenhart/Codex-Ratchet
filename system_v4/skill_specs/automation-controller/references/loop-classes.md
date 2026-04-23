# Loop Classes

## RETURN_AUDIT_LOOP

Use when new quarantined `Pro` returns need:
- completeness checks
- fast audit
- optional second-pass audit
- classification

## SAFE_MAINTENANCE_LOOP

Use when the task is:
- archive-first maintenance
- stale generated-artifact reduction
- bounded path cleanup with no deletion

## PRO_PACKET_PREP_LOOP

Use when the task is:
- prepare bounded `Pro` request packets
- build ZIP jobs in temp/quarantine space
- attach stop rules and output contracts

## QUEUE_CHECK_LOOP

Use when the task is:
- recurring readiness checks
- bounded status reporting
- no production-side mutation

## RUN_MONITOR_LOOP

Use when the task is:
- watch long-running lanes
- classify stop/continue/correct
- summarize health and drift risk

## DISPATCH_RECOMMENDER_LOOP

Use when the task is:
- suggest the next bounded Codex or `Pro` step
- summarize blockers
- recommend routing without executing it

