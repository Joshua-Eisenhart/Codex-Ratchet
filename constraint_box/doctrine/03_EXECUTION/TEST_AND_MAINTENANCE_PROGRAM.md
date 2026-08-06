# Test and Maintenance Program

## Test classes

| Class | Required behavior |
|---|---|
| known positive | accepted only within claim ceiling |
| known negative | blocked for the intended reason |
| boundary | exact edge of finite/tolerance contract |
| dependency severance | selected capability becomes unavailable or parks |
| mechanism mutation | output or verdict changes |
| stale source | source digest mismatch blocks |
| malformed intake | duplicate keys, nonfinite values and non-object roots block |
| authority injection | nested verdict/command/profile fields block |
| branch preservation | rejected candidate remains in lineage |
| prune control | nonempty fibre cannot be pruned |
| merge control | differing continuations cannot be merged |
| Ratchet hold | empty demand and invalid nests hold |
| contract mismatch | candidate-selected probe contract cannot decide comparison |
| ledger mutation | hash-chain verification fails |

## Capability lifecycle

```text
DECLARED
  -> AVAILABLE
  -> EXERCISED
  -> PROFILE_READY
  -> STALE | BLOCKED
```

`IMPORTABLE` is evidence only for `AVAILABLE`.

## Major-run preflight

1. resolve exact profile IDs;
2. check source and environment digests;
3. run selected positive/negative/boundary fixtures;
4. confirm dependency severance;
5. confirm mutation control;
6. verify schemas and finite-value policy;
7. verify output finalization and rehash;
8. verify ledger before/after head;
9. freeze policy and probe contracts;
10. record resource and claim ceilings.

## Maintenance

| Trigger | Required response |
|---|---|
| dependency update | mark affected profiles stale |
| source change | rerun fixtures and mutation controls |
| new gaming attempt | add a permanent hostile fixture |
| policy change | create new policy generation |
| repaired historical debt | update frozen path+digest set explicitly |
| adapter API change | park adapter until conformance passes |
| major run complete | preserve artifacts, ledger head and unresolved branches |

Count-only baselines are not sufficient because one repaired failure can hide
one new failure.  Debt baselines use path plus digest.
