# Data and Package Layout

```text
constraintbox/
  core/                 strict intake, policy, controller, ledger
  ensemble/             histories, projections, fibres, valuations
  branching/            preserve, park, prune, merge, re-offer
  constraints/          finite IR and bounded backends
  ratchet/              partitions and verified nested comparisons
  profiles/             controller-owned task profiles
  agents/               replaceable model adapters
  adapters/             CR, Sim Fleet and LevOS boundaries
  schemas/              closed contracts
  specs/                TLA+ and formal state model
  fixtures/             positive, negative, hostile, severance
```

## Persistent records

| Record | Required content |
|---|---|
| object snapshot | carrier, probes, constraints, relations and status |
| proposal | candidate, parents, falsifiers and requested capabilities |
| execution ticket | fixed profile, source, environment and bounds |
| artifact record | input/output hashes and process facts |
| evaluation | checker result and evidence refs |
| branch event | add, park, prune, merge or re-offer |
| Ratchet result | demand, survivors, frontier, uncompared rivals and `HOLD` reason |
| ledger head | local consistency cursor with trust ceiling |

Object snapshots and artifacts are immutable byte records.  New evidence
creates a new snapshot or event rather than rewriting prior history.
