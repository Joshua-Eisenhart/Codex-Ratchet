# TENSION MAP

Batch id: `BATCH_work_surface_broken_thread_extract_and_zipvm_golden_harness__v1`

## Tension 1: curated transcript package vs authority uncertainty

Evidence
- The broken-thread package is formalized and includes `/canon/` ZIPs.
- `READ_THIS_FIRST__v2__AUTHORITY_CONFLICT_SAFE.md` says not to trust authority labels until the source header is quoted directly.

Meaning
- The package is useful for navigation, but it cannot be treated as self-authenticating canon.

## Tension 2: repo-status claims vs thread-derived evidence

Evidence
- `BRANCHTHREAD_ISSUE_LEDGER__v1.md` and `UPGRADE_STATUS_SUMMARY__v1.md` assign statuses such as `PRESENT_IN_REPO` and `IMPLEMENTED_IN_REPO`.
- `docs/07_PLAN_ASSESSMENT_AND_RECOMMENDED_SEQUENCE.md` explicitly warns that assistant claims in the transcript should be treated as claims unless verified in-repo.

Meaning
- The distillation is operationally useful, but any “already fixed” claim still needs direct repo verification before promotion.

## Tension 3: strict fail-closed validator vs broad compatibility ladder

Evidence
- `validate_zip_vm_output.py` is deliberately simple and fail-closed.
- `expected_checks/` holds `14` profiles, including a long legacy-compat ladder.
- The cascade audit report records success by matching whichever profile passes first.

Meaning
- The harness is strict inside each profile, but broad across generations. That preserves compatibility while weakening a single normalized return shape.

## Tension 4: temporary scratch naming vs durable runtime residue

Evidence
- the selector-audit state snapshot under `work/audit_tmp/a1_pack_selector_audit_0047` contains `332` canonical-ledger steps and a `14`-term registry.

Meaning
- The `audit_tmp` label understates the persistence and value of the artifact. This is hidden state residue, not disposable scratch.

## Tension 5: no-Pro-first discipline vs Pro-era extraction packaging

Evidence
- `NEXT_EXECUTION_ROADMAP__NO_PRO_FIRST__v1.md` says to use Pro only when local extraction reliability is exceeded.
- The surrounding batch is itself built from curated transcript extraction, issue mining, and packaging surfaces that grew out of high-entropy assistant interactions.

Meaning
- The lane is trying to reduce dependence on remote/high-context reasoning, but it is doing so using artifacts produced by earlier high-context spillover.

## Tension 6: passed golden audits vs unresolved upgrade backlog

Evidence
- `work/golden_tests/reports/CASCADE_AUDIT__WIGGLE_RETURNS__2026_03_02__00_39_32.md` reports `10` passes and `0` failures.
- `TOP_OPEN_UPGRADES__v1.md` and `UPGRADE_STATUS_SUMMARY__v1.md` still preserve substantial `OPEN` and `PARTIAL` work around canonical ascent, discovery gating, negative-sim enforcement, and append confirmation.

Meaning
- Packaging quality checks and execution-governance readiness are not the same thing. The prototype lane proves transport conformance more readily than ratchet movement.

## Tension 7: reusable extraction discipline vs bundled "canon" residue

Evidence
- The broken-thread package includes two ZIPs under `canon/`.
- The same batch also carries explicit warnings against trusting packaged labels without direct source confirmation.

Meaning
- The extraction discipline is reusable, but the naming inside the package risks accidentally upgrading bundled reference material into current law.
