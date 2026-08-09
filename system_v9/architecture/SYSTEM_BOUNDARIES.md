# V9 system boundaries

## ConstraintBox

ConstraintBox is a lean deterministic constraint runtime. Its core third-party
set is exactly Z3, CVC5, SymPy, Rustworkx, and Maude. Python standard-library
modules do not count as external tools. JAX, PyTorch, Julia, PySINDy, Java,
TLC, and Apalache are not CB core. Old modules that call those systems are
legacy bridge implementations until extracted behind v9 bridge envelopes.

## ClaimGate

ClaimGate decides whether a bounded artifact meets an evidence policy. It does
not perform the scientific computation it gates. The repository-root
`claimgate_plugin/` is the live source authority. `claimgate/` is legacy and
the ignored copy under `constraint_box/` is provenance only.

## Sim Engines

Sim Engines owns the complete computation estate: NumPy/SciPy, JAX, PyTorch,
Julia, QIT, topology, graph, optimization, system-identification, SMT sidecars,
and optional world-model libraries. Installation, import, API smoke,
function-level receipt, and claim-bearing use are separate status levels.

## Codex Ratchet

CR owns ordered research stages, candidate generation, comparison, and routing.
It consumes CB, ClaimGate, and Sim Engines through bridges. Their availability
does not make them CR internals.

## Holodeck

Holodeck owns trainable prediction, associative memory, perception, and world
model experiments. It may use Sim Engines and QIT engines, especially PyTorch,
but remains independently installable and testable. V9 creates its product
boundary and tool profile; it does not assert that a complete world model
already exists.

## Non-conflation rule

Every cross-product call must identify a bridge record. Direct source imports
that predate v9 are legacy debt, not proof that a bridge is complete. A product
must pass its independent test with unrelated heavy runtimes absent unless its
own selected install profile explicitly requires them.
