## PURPOSE
- "# Simulation protocol v1"
- "**ID: S1_01**"

## HARD_FENCES
- "**STATEMENT: It is forbidden for protocol execution status to modify, weaken, override, or constrain kernel admissibility or kernel-derived artifacts.**"
- "**STATEMENT: It is forbidden to mix kernel artifacts, optional overlay artifacts, and protocol artifacts into an indistinguishable output stream; artifact classes must remain explicitly separable.**"
- "**STATEMENT: It is forbidden to execute a run without an explicit run manifest that declares the exact frozen kernel set and the optional overlay set (if any) as inputs.**"
- "**STATEMENT: It is forbidden for a run to depend on undeclared external sources for inputs; all inputs must be explicit finite encodings included in the run manifest.**"
- "**STATEMENT: It is forbidden to require any overlay for running or replaying kernel artifacts; overlays are optional and must be removable without affecting kernel replay.**"
- "**STATEMENT: It is forbidden to mutate input payloads in place; any transformation of inputs must produce explicitly new derived payloads with explicit lineage declarations.**"
- "**STATEMENT: It is forbidden to execute an unbounded or implicit step schedule; every run must declare an explicit finite step list.**"
- "**STATEMENT: It is forbidden for execution outcomes to depend on undeclared nondeterministic degrees of freedom; any nondeterminism must be explicitly declared as an optional protocol feature.**"
- "**STATEMENT: It is forbidden for execution to depend on undeclared environment state; all environment dependencies must be explicitly declared in the run manifest.**"
- "**STATEMENT: It is forbidden to omit a complete execution tape; each executed step must produce a tape entry binding step index, input identifiers, output identifiers, and status.**"
- "**STATEMENT: It is forbidden to require temporal metadata for replay; replay must depend only on the ordered tape index and declared payloads.**"
- "**STATEMENT: It is forbidden for replay to require hidden intermediate state; all intermediate artifacts required for replay must be explicitly present or explicitly declared as absent.**"
- "**STATEMENT: It is forbidden to perform silent auto-repair on failures; any repair attempt must be explicitly logged as a separate step with explicit inputs and outputs.**"
- "**STATEMENT: It is forbidden to present partial runs as complete; truncation or failure must be explicitly recorded and propagated to all derived protocol summaries.**"
- "**STATEMENT: It is forbidden to assume a default halt-or-continue policy; the run policy must be explicitly declared and recorded in the run manifest.**"
- "**STATEMENT: It is forbidden for diagnostics to gate acceptance, rejection, or admissibility of kernel artifacts; diagnostics are non-binding and removable.**"
- "**STATEMENT: It is forbidden for diagnostics to assert correctness status; diagnostics may report only declared structural properties of artifacts and tape completeness properties.**"
- "**STATEMENT: It is forbidden to attach diagnostic outputs as if they were kernel-derived structure; diagnostic artifacts must remain explicitly typed as protocol artifacts.**"
- "**STATEMENT: It is forbidden to use hidden caches; any reuse of prior artifacts must be explicit via identifiers recorded in the run manifest and tape.**"
- "**STATEMENT: It is forbidden to carry protocol state across runs without explicit import declarations; cross-run reuse must be declared as explicit inputs.**"

## CONTAINERS
- NONE_FOUND

## ALLOWED_SPEC_KINDS
- NONE_SPECIFIED

## FORBIDDEN_PRIMITIVES
- "**STATEMENT: It is forbidden for protocol execution status to modify, weaken, override, or constrain kernel admissibility or kernel-derived artifacts.**"
- "**STATEMENT: It is forbidden to mix kernel artifacts, optional overlay artifacts, and protocol artifacts into an indistinguishable output stream; artifact classes must remain explicitly separable.**"
- "**STATEMENT: It is forbidden to execute a run without an explicit run manifest that declares the exact frozen kernel set and the optional overlay set (if any) as inputs.**"
- "**STATEMENT: It is forbidden for a run to depend on undeclared external sources for inputs; all inputs must be explicit finite encodings included in the run manifest.**"
- "**STATEMENT: It is forbidden to require any overlay for running or replaying kernel artifacts; overlays are optional and must be removable without affecting kernel replay.**"
- "**STATEMENT: It is forbidden to mutate input payloads in place; any transformation of inputs must produce explicitly new derived payloads with explicit lineage declarations.**"
- "**STATEMENT: It is forbidden to execute an unbounded or implicit step schedule; every run must declare an explicit finite step list.**"
- "**STATEMENT: It is forbidden for execution outcomes to depend on undeclared nondeterministic degrees of freedom; any nondeterminism must be explicitly declared as an optional protocol feature.**"
- "**STATEMENT: It is forbidden for execution to depend on undeclared environment state; all environment dependencies must be explicitly declared in the run manifest.**"
- "**STATEMENT: It is forbidden to omit a complete execution tape; each executed step must produce a tape entry binding step index, input identifiers, output identifiers, and status.**"
- "**STATEMENT: It is forbidden to require temporal metadata for replay; replay must depend only on the ordered tape index and declared payloads.**"
- "**STATEMENT: It is forbidden for replay to require hidden intermediate state; all intermediate artifacts required for replay must be explicitly present or explicitly declared as absent.**"
- "**STATEMENT: It is forbidden to perform silent auto-repair on failures; any repair attempt must be explicitly logged as a separate step with explicit inputs and outputs.**"
- "**STATEMENT: It is forbidden to present partial runs as complete; truncation or failure must be explicitly recorded and propagated to all derived protocol summaries.**"
- "**STATEMENT: It is forbidden to assume a default halt-or-continue policy; the run policy must be explicitly declared and recorded in the run manifest.**"
- "**STATEMENT: It is forbidden for diagnostics to gate acceptance, rejection, or admissibility of kernel artifacts; diagnostics are non-binding and removable.**"
- "**STATEMENT: It is forbidden for diagnostics to assert correctness status; diagnostics may report only declared structural properties of artifacts and tape completeness properties.**"
- "**STATEMENT: It is forbidden to attach diagnostic outputs as if they were kernel-derived structure; diagnostic artifacts must remain explicitly typed as protocol artifacts.**"
- "**STATEMENT: It is forbidden to use hidden caches; any reuse of prior artifacts must be explicit via identifiers recorded in the run manifest and tape.**"
- "**STATEMENT: It is forbidden to carry protocol state across runs without explicit import declarations; cross-run reuse must be declared as explicit inputs.**"

## ROLE_IN_SYSTEM
- UNMAPPED

## OPEN_QUESTIONS
- NONE_MARKED_OPEN
