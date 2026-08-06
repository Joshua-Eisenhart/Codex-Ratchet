# E4 — the lease binds the index but runs the export

`reproduce.py` creates a fresh Git repository at runtime with an attribute that
marks `bound-but-not-run.txt` as `export-ignore`. Git is invoked only with that
temporary repository as its working directory.

- Should happen: the lease should refuse because the bound tree's byte set is
  not the byte set executed.
- Current behavior: the runner executes an archive with the ignored file
  absent, then `verify_lease()` returns `VALID` for the index tree that still
  contains it.
- Exact reach: `lease.staged_tree_id()` uses `git write-tree`;
  `lease.materialize_tree()` uses `git archive`; `lease.issue_lease()` binds the
  first identity but runs the second materialization; `lease.verify_lease()`
  compares only the tree id.

This fixture captures the identity mismatch. It does not harden lease behavior.
