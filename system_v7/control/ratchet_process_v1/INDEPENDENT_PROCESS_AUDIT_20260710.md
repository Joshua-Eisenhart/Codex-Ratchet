# Independent Process Audit - 2026-07-10

Status: advisory process audit. This is not a scientific receipt and does not
admit the Ratchet, an engine, a mathematical rung, or a physical claim.

## Audit Sequence

1. Four independent Claude Sonnet 4.6 high-effort lanes audited the root math,
   MSS semantics, validator, and bundle integrity. All four completed. They
   found underspecified root identity, an untyped N01 witness, asymmetric
   co-view licensing, MSS frontier and supersession gaps, validator bypasses,
   and dirty-bundle ambiguity.
2. The implementation was repaired. A four-lane confirmation returned three
   passes and one timeout; the timed-out validator lane was rerouted directly.
3. The rerouted validator audit found one remaining bypass: a card could be
   `ACCEPT_PROVISIONAL` while all later structures remained unearned.
4. Admission was bound to an explicit claim dependency list and a path-bound
   receipt registry. Predecessor, raw-record, rule, target, control, view,
   agreement, audit, decision, parent, and current-status references now have
   file/hash checks appropriate to their role.
5. A final direct high-effort audit returned `PASS` for the repaired bypass and
   all requested receipt-binding checks.

## Advisory Receipt Hashes

The bridge output lived under `/tmp` during this run; these hashes record the
audited artifacts but do not turn ephemeral advisory output into Ratchet
evidence.

- initial four-lane fanout receipt:
  `8206c65de7b7df616489b6398d3532b64051f7fa81ff7d9f9a36ef291ad7fa1f`
- first confirmation fanout receipt:
  `7f2e47c919c868708a3426dde25a346cc166e618bc9f79920c2526d083b85daa`
- validator reroute receipt:
  `bbdc0664255cd2219f015e7457aa042c85cf93587090bcef09a94b7171d7e5d8`
- final validator audit receipt:
  `892727f3409bddd917255e2d9827531c2bbc3afdd2c36655bc94c9ec2d94c9de`
- final validator audit output:
  `119f649f3f887f09d8cf005a2892fe5ffcf6e221564978b7b8c6e13b0312c536`

## Ceiling

The audit supports only this statement: the process specification and current
validator resist the tested structural fabrication paths. The proposal card is
still `UNRUN`; no recursive dual-Ratchet survivor has been earned.
