# Fable Freeze V2 Audit

Status: external advisory only; no scientific authority.

- model requested and observed: `claude-fable-5`;
- effort: `medium`;
- return code: `0`;
- timed out: `false`;
- cost: `$1.696158`;
- local receipt:
  `/tmp/cr-fable-eca-freeze-audit/20260710T133322Z-eca-freeze-v2-retry-f0eb7f478a05.receipt.json`;
- raw stream:
  `/tmp/cr-fable-eca-freeze-audit/20260710T133322Z-eca-freeze-v2-retry-f0eb7f478a05.stream.jsonl`.

The auditor read corrected commit `8615977aa` and did not read confirmation or
test data. It found that the v2 correction genuinely fixes the normalized-hash
overstatement and circular winner acceptance. It independently checked that
the controller rederives the full top-32 shortlists and winners from all 2,500
screen records and 96 exact records.

Residual risks named by the audit:

1. two-engine agreement can preserve a shared authoring bug;
2. read confinement remains self-declared rather than OS-traced;
3. normalization fallbacks are weaker than comparing independently emitted raw
   fields;
4. freeze integrity relies on git history and file hashes;
5. canned mutations do not prove general tamper evidence;
6. the final frozen payload is emitted from Julia after cross-runtime gates.

The audit classified the work as finite target-aware experimental design, not
learning or perception. Its train-only analysis predicted validation trouble
from the zero robust fixture floors without opening reserved data.
