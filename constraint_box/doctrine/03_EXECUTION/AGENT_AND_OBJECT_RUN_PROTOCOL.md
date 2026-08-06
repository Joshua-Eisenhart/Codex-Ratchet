# Agent and Object Run Protocol

## Submission

The caller submits:

```text
task_kind
request_id
immutable payload bytes
```

It cannot select an executable, profile, checker, tolerance, exemption or
verdict.

## Proposal wave

An agent proposal may include:

- candidate mechanism;
- parent branch;
- known rivals;
- falsifiers;
- requested experiments;
- expected observations.

It may not include authority-bearing fields.  The implemented profile scans
nested content, so moving `verdict` under `digest` does not hide it.

## Controller settlement

```text
request
 -> profile lookup
 -> strict intake
 -> branch append
 -> capability authorization
 -> worker execution
 -> artifact binding
 -> independent evaluation
 -> branch event
 -> operational disposition
```

## Model replacement

Any model may be stopped and replaced between proposal waves.  The next model
receives a bounded projection generated from the object/branch store:

- live branches;
- parked branches;
- settled obstructions;
- active probes and demands;
- available capabilities;
- missing discriminators.

It does not receive authority because it inherited a conversation.
