# Never-Run Triage

`system_v5/ops/never_run_cohorts.json` is an intake surface for sims that have no canonical result. It must not directly enqueue broad work.

Default rule:

- Any unlisted low-volume family inherits `review_required_before_queueing`: inspect the sim contract, stage gate, runner class, and result target before admission.

Named cohort rules:

- `calibration`: keep as calibration/baseline work only; require a concrete Carnot/Szilard/tool-function fixture, explicit baseline role, and no bridge/nonclassical promotion language before queueing.
- `coupling`: require prior receipts for each exact tool/function being coupled.
- `cvc5`: run only one micro solver surface per packet until a fresh function receipt exists.
- `geometry`: require the named geometry backend and a classical baseline divergence note.
- `gtower`: keep at tool-lego fit stage until supporting function receipts exist.
- `pure`: admit only if the sim has explicit falsifier/output evidence, not prose-only framing.
- `gap`: route to repair or graveyard decision before execution.
- `hopf`: require a minimal fixture plus divergence log.
- `weyl`: require baseline and admissibility boundary.
- `lego`: run only after tool/function evidence exists for the lego target.
- `fep`: require a concrete observable and killed/open/survived status.
- `igt`: require a finite game/payoff observable plus an explicit bridge/no-promotion boundary.
- `gerbestack`: require topology/coexistence evidence before bridge claims.
- `torch`: require a PyTorch role audit before queueing; legacy or helper-only torch rows stay blocked from nonclassical promotion unless removal changes the relevant observable.
- `gerbe`: require topology evidence and no axis promotion language.
- `integration`: require exact source receipts for each integrated component.
- `leviathan`: require local runner contract and result target.
- `other`: manual owner review before queueing.
- `bridge`: bridge evidence is not scientific promotion; require admission gate clearance.

Owner surface:

- The runner may work a cohort only after its rule is named here or the default rule is explicitly accepted in a receipt.
- Large cohorts should be split into one tool/function/lego-target triple per packet.
- New high-volume families should be added here before queue admission.
