# CS And Engineering Model

Date: 2026-05-23

Status: engineering translation. Not canon by itself.

## 1. Engineering Slogan

Every idea must become:

```text
finite type -> finite operation -> finite control -> finite receipt
```

If it cannot be expressed that way, it remains thesis or research pressure.

## 2. Core Types

### Constraint

```text
Constraint {
  id: string,
  role: root_constraint | derived_constraint | candidate_fence | process_law,
  statement: string,
  forbidden_primitive: string?,
  root_pressure: [F01, N01],
  enforcement_gate: string?
}
```

### Candidate

```text
Candidate {
  id: string,
  family: string,
  carrier: finite object,
  operation_registry: finite list,
  controls: finite list,
  readouts: finite list,
  claim_ceiling: string
}
```

### Sim Receipt

```text
Receipt {
  script_path: string,
  result_path: string,
  all_pass: bool,
  classification: formal_scout | tool_lego_fit_probe | canonical | baseline,
  tool_manifest: object,
  positive: object,
  graveyard_companions: object,
  boundary: object,
  blockers: list,
  open_next_work: list
}
```

## 3. Bounded Work As A State Machine

```text
idea
  -> translated
  -> bounded
  -> scaffolded
  -> run
  -> linted
  -> fresh-rerun
  -> audited
  -> classified
  -> admitted | killed | kept_as_candidate | split
```

Failure at any stage is information.

## 4. CS Translation Of The Root Constraints

### F01: Finitude

Engineering meaning:

```text
No unbounded data structure is allowed as a primitive.
```

Concrete requirements:

```text
finite arrays
finite tensors
finite graph
finite registry
finite path count
finite sample count
finite run timeout
finite result artifact
finite claim ceiling
```

Typical controls:

```text
capacity overflow
path-count overflow
dimension overflow
unbounded-loop rejection
context-window fence
```

### N01: Noncommutation

Engineering meaning:

```text
Composition order is part of the object.
```

Concrete requirements:

```text
ordered token list
left/right action audit
forward vs reversed path test
commuting control
operator family recorded separately from semantic label
```

Typical controls:

```text
commuting replacement
order reversal
path shuffle
token-precedence swap
classical probability baseline
```

## 5. Sim Families

### Micro Tool/Function Sim

Tests one tool function or one math primitive.

Example:

```text
Can this cvc5 call prove this exact bounded relation?
Can this torch operation preserve density-matrix validity?
```

### Tool-Lego Fit Probe

Tests whether a tool can support a small admissible target.

Example:

```text
Can tensor contraction machinery represent this finite noncommuting carrier?
```

### Formal Scout

Tests a bounded candidate family.

Example:

```text
Does a Holodeck-QIT-FEP world-memory update beat passive, commuting, classical,
and product-cut controls?
```

### Integration Scout

Tests whether multiple already-receipted pieces compose.

Example:

```text
Can derived flux steer a source-backed QIT engine token path before the
Holodeck-QIT-FEP update?
```

### Proof Target Scout

Tests whether a conjectural proof route can be reduced to finite checks,
counterexample search, symbolic certificates, or a theorem statement.

Example:

```text
Can a Navier-Stokes regularity toy fixture be translated into a finite
energy/entropy/dissipation gate without pretending to solve the PDE?
```

## 6. Engineering Rules For QIT Alignment

Preferred runtime objects:

```text
density matrices
CPTP maps
Kraus instruments
finite POVM/effect families
finite process tensors
finite path sums
finite graph/lattice/cell registries
```

Avoid as primitives:

```text
real-valued probability distribution without a probe
continuous time
continuous path integral
classical Markov blanket
global objective function
global scalar order
coordinate distance
identity/equality without probe family
```

## 7. What "Done" Means For A Scout

A scout is done only when:

```text
script exists
result JSON exists
all_pass status is known
contract lint passes or failure is documented
fresh-rerun passes or failure is documented
positive, graveyard, and boundary sections are present
claim ceiling is explicit
next work is named
```

Passing a scout means:

```text
the bounded fixture survived its controls
```

It does not mean:

```text
the whole theory is true
```

