# Lev Freeze Audit

Status: external executor/auditor receipt only; no scientific authority.

Lev ran a read-only audit of original freeze commit `5f42e344d` and changed no
files. Execution receipt:

```text
receipt_id = rcpt-a59de648fd61de9e
receipt_content_sha256 = 5c8af5eb13df37f22283e6f0edb080c963b60401207337f019ff67af3fc71e75
exec_id = a6ad0f0b7ad2
cost_usd = 1.1572315
```

The Lev header advertised `claude-sonnet-4-5-20250929`, but the sealed backend
receipt identified `claude-opus-4-6`. This is a real model-routing mismatch and
prevents using the header as provider truth.

The audit correctly identified the substantive train weaknesses: S2 equals the
hash-order baseline, all winners have zero minimum robust coverage, and S4 has
poor diversity. It did not identify the original normalized-hash or independent
selection-derivation defects later caught by the fresh Codex audit, so it is
supporting evidence only.
