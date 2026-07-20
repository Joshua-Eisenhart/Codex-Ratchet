# Ratchet bridge plugin

This proposal follows the current Leviathan SDK-first plugin form:

- config.yaml registers one typed Poly SDK operation;
- the handler executes the frozen local census and residual-to-obligation
  compiler;
- lifecycle-significant transitions emit canonical events;
- the operation returns census, fuel, fair-queue, and graph receipt paths;
- Leviathan never selects a candidate, MSS frontier, truth value, or admission.

Desktop must install this only in an isolated Lev worktree, run the local
plugin validator/typecheck, confirm registry discovery, invoke the registered
operation through the commit-native Poly/Exec surface, and export the emitted
events. Static presence is not a native-binding receipt.

The projected queue is deliberately source-fair and unscored. It contains all
current anonymous obligations. Proposal and owner-hypothesis entries are
visible in the graph with `selector_access=false`; Lev may route a typed
candidate to an obligation but may not rank or admit it.

The plugin contains no external target, credential access, persistence,
network action, or remote execution. It is an authorized local mathematical
validation operation over user-owned files.
