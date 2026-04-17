# Local Launch Checklist — Wiki Automation

Use this checklist immediately before starting a real wiki-builder automation run.

## Confirm lane separation
- [ ] this run is for wiki automation, not the sim runner
- [ ] no sim batch launcher or overnight probe runner is being reused as the wiki runtime
- [ ] the run contract is `system_v5/new docs/plans/wiki-automation-run-contract.md`

## Confirm files to read first
- [ ] `/Users/joshuaeisenhart/wiki/index.md`
- [ ] `/Users/joshuaeisenhart/wiki/concepts/topic-map.md`
- [ ] `/Users/joshuaeisenhart/wiki/concepts/current-research-overlays.md`
- [ ] `/Users/joshuaeisenhart/wiki/log.md`
- [ ] `system_v5/new docs/plans/wiki_ingest_and_lego_maintenance.md`
- [ ] `system_v5/new docs/plans/sim_backlog_matrix.md`
- [ ] `system_v5/new docs/plans/sim_truth_audit.md`
- [ ] `/Users/joshuaeisenhart/wiki/concepts/wiki-automation-contract.md`
- [ ] `/Users/joshuaeisenhart/wiki/concepts/wiki-automation-tick-template.md`
- [ ] `/Users/joshuaeisenhart/wiki/config/wiki_automation_surface_map.json`

## Confirm verification primitive
- [ ] `/Users/joshuaeisenhart/wiki/tools/wiki_probe.py` exists
- [ ] it can run before launch
- [ ] page count, missing-from-index, broken-link, and orphan checks are visible before tranche choice

## Confirm tranche
- [ ] exactly one tranche is chosen
- [ ] tranche order respected
- [ ] no neighboring-cluster widening is implicitly queued

## Confirm worker model
- [ ] Hermes = controller only
- [ ] Claude Code terminals only for genuinely independent concept clusters
- [ ] non-overlapping file sets only
- [ ] shared routing pages remain Hermes-reconciled surfaces

## Confirm shared surfaces rule
- [ ] `index.md` is Hermes-reconciled
- [ ] `log.md` is Hermes-reconciled
- [ ] `topic-map.md` is Hermes-reconciled
- [ ] `current-research-overlays.md` is Hermes-reconciled

## Confirm stop rules
- [ ] stop if file overlap appears
- [ ] stop if the run starts drifting into sim-runner work
- [ ] stop if workers widen outside the bounded concept cluster
- [ ] stop if verification is missing or ambiguous

## Final go / no-go
- [ ] if any box above is unchecked, do not launch
- [ ] if all boxes are checked, launch one bounded wiki tranche only
