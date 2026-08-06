# TLA+ Verification Status

`ConstraintBox.tla` is a proposed bounded transition model for the controller
state machine. It was checked with TLC 2.19 from stable `tla2tools.jar` 1.7.4.

The intended next verification is:

```bash
java -XX:+UseParallelGC -jar tla2tools.jar \
  -config ConstraintBox.cfg ConstraintBox.tla
```

Executed invariants:

- state and generation fields retain their declared types;
- a proposal cannot self-admit;
- eligibility requires nonempty worker evidence;
- the policy generation captured at authorization stays frozen through
  running, observation and evaluation.

The bounded model produced 73 states and 45 distinct states. The acceptance
control changes the eligibility invariant to demand empty evidence; TLC then
reports the expected violation.

This does not model branch pruning, merging, MSS comparison, tool availability,
or full worker process semantics. Those remain separate executable contracts.
The specification is therefore still `PROPOSED`; “model-checked” applies only
to this bounded transition model.
