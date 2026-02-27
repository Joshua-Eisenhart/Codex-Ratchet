# Thread S Full Save Kit (Single ZIP)

BOOT_ID: BOOTPACK_THREAD_B_v3.9.13
TIMESTAMP_UTC: 2026-02-04T09:54:24Z

This bundle is intended to contain everything Thread S needs to archive/replay the current Thread B state
without chat-length truncation.

Files:
- THREAD_S_SAVE_SNAPSHOT_v2.txt     (canonical snapshot container)
- DUMP_LEDGER_BODIES.txt            (full survivor ledger bodies + park set)
- DUMP_TERMS.txt                    (full term registry enumeration)
- DUMP_INDEX.txt                    (index + counts)
- REPORT_POLICY_STATE.txt           (policy flags)
- PROVENANCE.txt                    (counters)
- SHA256SUMS.txt                    (integrity hashes)

Notes:
- PARK_SET and EVIDENCE_PENDING are EMPTY in this state.
- TERM_REGISTRY entries are TERM_PERMITTED only (no LABEL_PERMITTED/CANONICAL_ALLOWED).
