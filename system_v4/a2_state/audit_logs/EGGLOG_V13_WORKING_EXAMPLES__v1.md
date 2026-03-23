# Egglog V13 Working Examples — Audit Log

> **Date**: 2026-03-22  
> **egglog version**: 13.0.1  
> **venv**: `.venv_spec_graph`  
> **Status**: ✅ ALL EXAMPLES PASS

---

## API Summary (v13 — from installed source)

The egglog Python API wraps the Rust `egglog` (egg-smol) engine. Key types:

| Concept | Python API |
|---|---|
| Custom sorts | `class Foo(Expr)` with `__init__` stub → constructor |
| Built-in sorts | `i64`, `String`, `Bool`, `f64`, `BigInt`, `BigRat` |
| Functions | `@function` decorator on a typed stub |
| Relations | `relation("name", Type1, Type2, ...)` → returns `Unit` |
| Rewrites | `rewrite(lhs).to(rhs)` |
| Rules | `rule(*facts).then(*actions)` |
| Equality | `eq(a).to(b)` for checking; `union(a).with_(b)` as action |
| Variables | `var("name", Type)` |
| E-graph | `EGraph()` — `.register()`, `.run(N)`, `.extract()`, `.check()` |
| Rulesets | `ruleset(*rules)` — grouping for schedule control |
| Saturation | `.run(N)` returns `RunReport`; stops early if no rules fire |

---

## Example 1: Basic Datatypes & Extraction

**Goal**: Define a numeric sort, register an expression, rewrite it, extract the simplified form.

```python
from egglog import *

class Num(Expr):
    def __init__(self, value: i64Like) -> None: ...
    def add(self, other: 'Num') -> 'Num': ...

egraph = EGraph()
x = egraph.let('x', Num(1).add(Num(2)))

# Rewrite: Num(a).add(Num(b)) => Num(a + b)
egraph.register(
    rewrite(Num(var('a', i64)).add(Num(var('b', i64)))).to(
        Num(var('a', i64) + var('b', i64))
    )
)
egraph.run(10)
result = egraph.extract(x)
assert str(result) == "Num(3)"
```

**Result**: `Num(3)` ✅  
**Key insight**: `i64Like` accepts Python `int` literals. `var('name', type)` creates pattern variables.

---

## Example 2: Rewrite Rules — Transitive Path Closure

**Goal**: Use `relation` and `rule` to derive transitive reachability from edges.

```python
from egglog import *

class Node(Expr):
    def __init__(self, name: StringLike) -> None: ...

edge = relation('edge', Node, Node)
path = relation('path', Node, Node)

# edge(a,b) => path(a,b)
r1 = rule(
    edge(var('a', Node), var('b', Node)),
).then(
    path(var('a', Node), var('b', Node)),
)

# path(a,b) ∧ edge(b,c) => path(a,c)
r2 = rule(
    path(var('a', Node), var('b', Node)),
    edge(var('b', Node), var('c', Node)),
).then(
    path(var('a', Node), var('c', Node)),
)

egraph = EGraph()
a, b, c = Node('A'), Node('B'), Node('C')
egraph.register(edge(a, b), edge(b, c), r1, r2)
egraph.run(10)
egraph.check(path(a, c))  # ✅ A can reach C
```

**Result**: `path(A, C)` proven ✅  
**Key insight**: `rule(*facts).then(*actions)` is the general mechanism. Relations are zero-cost facts (return `Unit`).

---

## Example 3: Saturation & Run Reports

**Goal**: Observe saturation behavior — the engine stops when no new rewrites fire.

```python
from egglog import *

class Math(Expr):
    def __init__(self, value: i64Like) -> None: ...
    def double(self) -> 'Math': ...

egraph = EGraph()
egraph.register(
    rewrite(Math(var('x', i64)).double()).to(
        Math(var('x', i64) + var('x', i64))
    )
)
x = egraph.let('x', Math(3).double())
report = egraph.run(10)

result = egraph.extract(x)
assert str(result) == "Math(6)"

# RunReport shows: iteration 1 had 1 match, iteration 2 had 0 → saturated
# Engine ran 2 of 10 allowed iterations before stopping
```

**Result**: `Math(6)`, saturated in 2 iterations ✅  
**Key insight**: `egraph.run(N)` returns a `RunReport` with per-iteration match counts. Saturation = 0 matches in final iteration.

---

## Example 4: Graph Node Promotion as Rewrite

**Goal**: Model the Codex Ratchet tier-promotion pipeline — `CANDIDATE → PROPOSED → KERNEL` — as equality-saturation rewrite rules gated on structural conditions.

```python
from egglog import *

class Tier(Expr):
    @classmethod
    def CANDIDATE(cls) -> 'Tier': ...
    @classmethod
    def PROPOSED(cls) -> 'Tier': ...
    @classmethod
    def KERNEL(cls) -> 'Tier': ...

class GNode(Expr):
    def __init__(self, name: StringLike, tier: Tier) -> None: ...

class Support(Expr):
    def __init__(self, node: GNode, count: i64Like) -> None: ...

promoted = relation('promoted', GNode)

# CANDIDATE with >=2 supports → PROPOSED
promote_to_proposed = rule(
    GNode(var('name', String), Tier.CANDIDATE()),
    Support(GNode(var('name', String), Tier.CANDIDATE()), var('n', i64)),
    var('n', i64) >= i64(2),
).then(
    union(GNode(var('name', String), Tier.CANDIDATE())).with_(
        GNode(var('name', String), Tier.PROPOSED())
    ),
    promoted(GNode(var('name', String), Tier.PROPOSED())),
)

# PROPOSED with >=4 supports → KERNEL
promote_to_kernel = rule(
    GNode(var('name', String), Tier.PROPOSED()),
    Support(GNode(var('name', String), Tier.PROPOSED()), var('n', i64)),
    var('n', i64) >= i64(4),
).then(
    union(GNode(var('name', String), Tier.PROPOSED())).with_(
        GNode(var('name', String), Tier.KERNEL())
    ),
    promoted(GNode(var('name', String), Tier.KERNEL())),
)

egraph = EGraph()
alpha = egraph.let('alpha', GNode('alpha', Tier.CANDIDATE()))
beta  = egraph.let('beta',  GNode('beta',  Tier.CANDIDATE()))

egraph.register(
    Support(GNode('alpha', Tier.CANDIDATE()), i64(3)),  # qualifies
    Support(GNode('beta',  Tier.CANDIDATE()), i64(1)),  # does not
    promote_to_proposed,
    promote_to_kernel,
)
egraph.run(10)

egraph.check(promoted(GNode('alpha', Tier.PROPOSED())))  # ✅
# beta NOT promoted (check would raise)

# Second phase: add PROPOSED-level support for alpha
egraph.register(Support(GNode('alpha', Tier.PROPOSED()), i64(5)))
egraph.run(10)
egraph.check(promoted(GNode('alpha', Tier.KERNEL())))    # ✅
```

**Result**: alpha: `CANDIDATE → PROPOSED → KERNEL`. beta stays `CANDIDATE`. ✅  
**Key insight**: `union(a).with_(b)` merges e-classes so the node IS its promoted form. `rule` with an inequality guard (`>=`) gates promotion on structural evidence.

---

## Architectural Notes for Codex Ratchet Integration

1. **E-graphs as promotion auditors**: Load the A2 graph nodes + edges as egglog facts. Promotion rules encode the invariants. If `egraph.check()` passes, the promotion is structurally sound.
2. **Saturation = completeness**: Running to saturation guarantees all derivable promotions have been found — no manual iteration needed.
3. **Reversibility**: `egraph.push()` / `egraph.pop()` allow speculative promotion testing without mutation.
4. **Probe pattern**: The companion `egglog_graph_rewrite_probe.py` wraps this into a reusable function that takes `(nodes, edges, support_map)` and returns `{node: final_tier}`.
