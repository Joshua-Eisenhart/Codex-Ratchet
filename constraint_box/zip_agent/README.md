# ConstraintBox ZIP Agent package

This directory is the contained implementation of the recovered ZIP_JOB idea. A ZIP is
the process language: it binds ordered typed tasks, all source bytes, required
outputs, allowed local operations, child-job identities, and exact hashes. The
only successful result is a return ZIP.

It is deliberately separated from the dirty legacy/root package while the
protocol is being falsified. It uses the contained Python runtime's Pydantic
and JSON Schema libraries, plus the standard library. Provider choices are
run data; no model roster is kernel policy.

## What runs now

```text
ZIP_JOB
  -> safe ZIP/member validation
  -> JSON Schema plus strict Pydantic validation
  -> exact member hash registry
  -> ordered task/dependency validation
  -> finite local operation registry
  -> optional child ZIP dispatch through this runtime
  -> declared model workers through receipt-bound adapters
  -> failure, repair, and strategy council packets
  -> exact required-output realization
  -> per-task receipts
  -> executing package-source fingerprint
  -> deterministic RETURN ZIP
  -> content-addressed temp cache plus append-only SQLite index
```

The project context lives under `project_state/`: a digest-linked JSONL event
chain, checked `HEAD`, content-addressed retained objects, generated `CURRENT.md`,
plans, progress notes, and run packets/returns. Codex and Hermes sources are
imported as full snapshots followed by verified append deltas when possible;
rewritten history falls back to a new full snapshot.

The runtime does not execute free task prose. Local Python operations use the
finite registry. Model workers receive declared files and may write only their
declared outputs; retries and acceptance are deterministic CB actions.

## Quick run

From this directory:

```bash
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent build-demo --out /tmp/cb-zip-demo.zip
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent run /tmp/cb-zip-demo.zip --return-zip /tmp/cb-zip-demo.return.zip --cache-dir /tmp/cb-zip-cache
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent verify-return /tmp/cb-zip-demo.return.zip --input /tmp/cb-zip-demo.zip
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent failure-wave --target /tmp/cb-zip-demo.zip --wave-packet /tmp/cb-zip-failure-wave.zip --return-zip /tmp/cb-zip-failure-wave.return.zip --cache-dir /tmp/cb-zip-cache
PYTHONPATH=src ../.venv/bin/python -m pytest -q -p no:cacheprovider
```

Live provider packets must be run through the CB-owned process-box authority
envelope so a fresh nonce and process receipt are issued. A direct live-provider
run intentionally HOLDs. The current operator sequence is documented in each
run directory; a single public composition command remains planned.

Project context commands:

```bash
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent project-sync --project-state project_state --codex-rollout /path/to/rollout.jsonl
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent project-verify --project-state project_state
PYTHONPATH=src ../.venv/bin/python -m constraintbox_zip_agent project-render --project-state project_state --out project_state/CURRENT.md
```

## Authority cut

- `00_RUN_ME_FIRST.md` is human/model guidance, never executable authority.
- A task can request only an operation in both its packet declaration and the
  runtime's finite registry.
- A child task supplies a child ZIP; the parent runtime validates its ID and
  depth, then invokes it. The child cannot privately launch itself.
- MMM and skill bytes are hash-bound and delivered, but their semantic effect
  is not proved. Receipts keep `mmm_read_proved: false` and `skill_executed: false`.
- Cache/index rows are retrieval aids, not admission or lifecycle transitions.
- Failure produces no return ZIP at the CLI path.

## Claim ceiling

This is a local deterministic ZIP transport/executor with observed model-backed
worker routes and a retained project ledger. It does not prove OS-wide
containment, universal host-hook enforcement, MMM cognition, semantic quality,
portable installation, CB Light adoption, promotion, or release.
