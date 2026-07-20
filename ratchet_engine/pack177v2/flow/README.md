# Leviathan execution boundary

The concrete integration surface in this pack is `lev-plugin/`: a typed local
operation that invokes the frozen runner without a shell, emits lifecycle
events, and projects the receipts into a deterministic context graph.

No hand-authored FlowMind YAML is claimed executable here. The current Lev
estate has had parser/schema/executor drift; Desktop must compile any flow
through the parser at its pinned local Lev commit and receipt the resulting
native invocation. An illustrative YAML file is not a substitute for that
evidence.

Leviathan's allowed role is orchestration, eventing, graph state, provenance,
resumption, and fair scheduling. `mathematicalAuthority` is always false.

