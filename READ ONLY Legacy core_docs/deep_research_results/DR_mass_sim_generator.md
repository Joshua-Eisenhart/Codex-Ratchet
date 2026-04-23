# Systematic Procedural Generation for Computational Math Proof Sims in Python

## Executive summary

This report designs a “Mass Sim Generator” for *systematic* and *reproducible* procedural generation of computational-proof simulations, specifically aimed at producing **50 distinct** `*_sim.py` scripts from a list of conceptual goals. The generation mechanism is centered on **randomized tensor-contraction hypotheses** (Einstein summation / tensor-network style), with implementation options using either **Jinja2 templates** or **Python AST construction / transformation**.

Two integration constraints are dominant if you want these sims to “feel native” inside the Ratchet-style CPTP/density-matrix ecosystem already present in your repository. First, existing probe sims treat a run as a sequence of falsifiable tests producing **EvidenceToken** objects and writing results to an `a2_state/sim_results` directory colocated under the probe directory. citeturn13view0turn13view1turn13view3 Second, the CPTP/density-matrix sims in `system_v4/probes` commonly import shared density-matrix utilities and the `EvidenceToken` type from a local runner module and then save a JSON “evidence ledger” at the end of execution. citeturn13view2turn13view3

From a generator-engine perspective, the best-practice architecture is a **spec-driven pipeline**: *conceptual goal → hypothesis spec (IR) → code render → syntax/compile validation → deterministic output path + manifest*. This pipeline supports both Jinja2 and AST backends while keeping safety, determinism, and testing tractable. Jinja2’s own docs emphasize that sandboxing can help with untrusted templates, but also warns you must still enforce **resource limits** and treat sandboxing as imperfect. citeturn2search0turn2search1 Python’s AST tooling provides a safer shape-guarantee for code generation, but the standard docs warn that `ast.parse()` does not guarantee the code will compile, and extremely complex inputs can even crash the interpreter due to compiler stack depth limits. citeturn10search8turn10search2

A critical repository-layout note: in the public tree view of `system_v4`, there is an existing `system_v4/tools` directory, but no visible `system_v4/research` directory. citeturn14view0turn12view0 If you require the exact path `system_v4/research/tools/mass_sim_generator.py`, you will likely need to **create** that directory (or map to `system_v4/tools` if you decide to align with the current structure). citeturn14view0

Finally, the current environment’s GitHub connector tools exposed to this assistant are **read-only** (repository search and file fetch). Therefore, I cannot directly commit/push files on your behalf from this session; the report includes a commit checklist and exact file paths so you can apply the changes locally.

## Ratchet-aligned execution model and conventions

The existing Ratchet-style probe runner defines an `EvidenceToken` dataclass intended to represent a falsifiable test outcome (PASS/KILL), including optional measurement and kill reason fields. citeturn13view0 The runner also persists results by creating an `a2_state/sim_results` directory relative to the probe module directory and emitting a JSON bundle that includes the evidence ledger and summary counts. citeturn13view1

The Navier–Stokes “formal proof sim” demonstrates the integration pattern you want to imitate for mass-generated sims: it imports `EvidenceToken` plus density-matrix utilities from `proto_ratchet_sim_runner`, runs multiple SIM blocks, then saves a JSON file to `a2_state/sim_results`. citeturn13view2turn13view3

**Implication for mass generation:** to integrate cleanly, each generated `*_sim.py` should:

- Import `EvidenceToken` and any shared density-matrix helpers from your canonical probe runner module (or a new shared helper module you create for tensor-hypothesis sims). citeturn13view2  
- Provide a deterministic entrypoint (`run_all()` or `main()`), generating an evidence ledger (list of tokens) and saving JSON to `a2_state/sim_results/<sim_name>_results.json`. citeturn13view1turn13view3  
- Encode each hypothesis run as “KILL_IF …” style checks (you already use this style explicitly in prose and in control flow). citeturn13view3  

This makes the generated sims legible to existing Ratchet audit and evidence-graph practices (even if they are not immediately wired into an explicit dependency graph file).

## Procedural code generation architecture and engine tradeoffs

A generator that produces 50 distinct simulation scripts is easiest to keep correct if you separate **(A) hypothesis-spec generation** from **(B) code rendering**. The core design pattern is:

1. **Conceptual goals layer (human)**: a list of goal strings / IDs (e.g., “Trace-preservation under randomized Kraus contraction”).
2. **Intermediate representation (IR)**: a structured “HypothesisSpec” that fully describes the simulation in machine terms: contraction equation(s), shapes, random seeds, backend preferences, thresholds, expected invariants.
3. **Renderer**: render IR to a Python module file using either (i) template rendering, or (ii) AST synthesis.
4. **Gatekeeper**: validate syntax and compilation, then persist with deterministic filename conventions + a manifest.

### Jinja2 vs AST comparison table

| Dimension | Jinja2 template rendering | Python AST generation / transformation |
|---|---|---|
| Safety (injection / code integrity) | Higher risk if *any* user-controlled input is inserted as raw code; mitigations include strict escaping, restricting template features, and treating templates as trusted-only. Jinja’s sandbox is for untrusted templates, but is not a “perfect security” solution and requires resource limiting. citeturn2search0turn10search1 | Better structural safety: you construct valid nodes, so “code injection” becomes “data in constants” rather than raw code. Still must avoid generating overly deep/large ASTs; parsing/unparsing complex code can blow recursion/stack limits. citeturn10search2turn10search8 |
| Syntactic correctness | No guarantee; you must validate the rendered output (parse + compile). A practical pattern is “render → `ast.parse()` → write” (your broader ecosystem already does this style of validation). fileciteturn22file0L1-L1 | High guarantee: if you build nodes correctly and `ast.fix_missing_locations`, code will parse; but compilation can still fail if you generate invalid contexts (e.g., `return` at top-level). citeturn10search8turn10search2 |
| Flexibility and readability | Excellent for whole-file scaffolds, long docstrings, and consistent formatting; templates are easy to review in diffs. Jinja compiles templates to optimized Python code and supports caching. citeturn2search1 | Great for programmatic refactors and constrained generation; worse for human readability unless you layer a stable pretty-printer and keep the AST patterns simple. `ast.unparse` output is not guaranteed to match original formatting and can raise `RecursionError` for complex ASTs. citeturn10search2 |
| Ease of testing | Straightforward golden-file tests: “given spec → generated text hash stable.” You still need parse/compile checks. citeturn10search8 | Strong structural tests: assert node shapes, walk AST, validate invariants; but golden-file diffs are noisier due to unparse formatting changes. citeturn10search2turn2search4 |
| Integration with tooling | Works well with formatters/linters post-render (ruff/black), plus parse/compile gates. | Works well for transformations (NodeTransformer), but you may still run formatters after unparse. NodeTransformer is the standard mechanism for AST rewriting. citeturn2search4 |

### Design recommendation

For a generator whose prime constraints are **correctness, reproducibility, and safety**, a practical “best of both” approach is:

- Use **Jinja2** for the *outer module scaffolding* (imports, metadata header, consistent `main()` boilerplate).
- Use **AST** for the *dangerous interior bits*: generating contraction expressions, embedding structured metadata safely, and optionally generating test snippets or invariants code.

If you must choose one: an AST-first approach reduces injection-style risk (data becomes `ast.Constant`), but it increases tooling complexity and dependence on `ast.unparse` (Python ≥3.9). citeturn10search2 A Jinja2-first approach is simpler to ship, but requires disciplined escaping rules and robust validation gates. citeturn2search0turn10search1

## Randomized tensor-contraction hypothesis generation

This section focuses on making each generated sim meaningfully distinct and mathematically coherent.

### Contraction primitive choices: numpy.einsum, opt_einsum, torch.einsum

**NumPy `einsum`** is the baseline: it encodes tensor contractions in Einstein notation and can optionally optimize intermediate contractions. citeturn0search1 The `optimize` parameter can be `False`, `True`, `'greedy'`, `'optimal'`, or an explicit path list produced by `np.einsum_path`. citeturn0search1turn0search0 `np.einsum_path` returns a contraction order and a printable cost report, which can be logged into metadata for reproducibility and performance auditing. citeturn0search0

**opt_einsum** generalizes contraction-path search and supports reusable “compiled” contraction expressions for specific shapes: `contract_expression(subscripts, *shapes)` returns a callable you can reuse and cache, including reuse of constant tensors and backend-specific optimizations. citeturn0search6 This is a strong fit for sims that repeatedly apply the same contraction in a CPTP loop.

**PyTorch `einsum`** gives you a second backend for cross-checking the same Einstein equation (CPU and optionally CUDA). citeturn1search5 In a proof-sim context, torch is most useful as a *redundant oracle* to detect incorrect hypotheses/spec-generation bugs (“the same equation produces divergent results across backends”).

### How to randomize hypotheses while staying valid

The core problem with “random Einstein equations” is validity: you must ensure that index symbols and tensor shapes match the intended contraction semantics.

A robust hypothesis generator should build a contraction in a hypergraph-like way:

1. Choose **rank** (tensor order) for each operand, e.g. 2–4.
2. Choose a global pool of **index symbols** (letters) and assign them to operand axes.
3. Decide which indices are **latent** (summed) vs **output** (free).
4. Construct an equation like `"ab,bc,cd->ad"` with consistent repeated indices and output ordering.

Recommended constraints for stability:

- Limit to small dimensions (e.g., 2–8 per index) to keep generated sims fast and reduce numerical conditioning issues.
- Cap rank and number of operands to avoid exponential intermediate blowups (also reduces AST/unparse complexity risk). citeturn10search2
- Prefer **pairwise repeated** latent indices (each summed index appears exactly twice across all operands), which yields clearer contraction semantics and easier shape-checking.

### Hypothesis “families” that map well to computational proof sims

To connect tensor hypotheses to “proof-like” work, define a small set of hypothesis families and randomize within them. Examples:

- **Backend equivalence hypothesis:** compute the same contraction with NumPy (`einsum`) and opt_einsum (`contract_expression`), assert numerical agreement within tolerance. citeturn0search1turn0search6  
- **Path invariance hypothesis:** compute `np.einsum(..., optimize=False)` vs `optimize='greedy'` or explicit `einsum_path`; results must match within tolerance even if intermediate ordering differs. citeturn0search1turn0search0  
- **Tensor identity hypothesis:** generate a contraction that corresponds to a known identity (e.g., trace cyclicity or associativity of chained matmuls) and then test across random instances.
- **CPTP-loop hypothesis:** use contractions to build (or apply) a quantum channel, then test required invariants: trace preservation, positivity, and optionally entropy monotonicity under specific channels. The existing probe ecosystem already uses density-matrix validity projection utilities and “KILL_IF” checks, so these sims fit naturally. citeturn13view2turn13view3

### Reproducibility: seeds, spawned streams, and determinism

The generator should treat randomness as a first-class artifact.

A recommended approach is:

- Use `numpy.random.SeedSequence` with a single base entropy, then `spawn(n)` to create `n=50` independent (non-overlapping) child seed sequences. citeturn1search1  
- Construct each sim’s `numpy.random.Generator` via `default_rng(child_seed)` (or via explicit BitGenerator), recognizing that `Generator` uses a BitGenerator (default PCG64) and accepts a SeedSequence as its seed. citeturn1search7turn1search1  

If using torch as an oracle backend, seed it explicitly with `torch.manual_seed`. citeturn1search3 If you require deterministic execution (especially on GPU), PyTorch provides `torch.use_deterministic_algorithms(True)` but notes this setting alone may not be sufficient for full reproducibility across environments. citeturn1search0

## Validation, testing, and sandboxing strategy

Because you are generating code that you will later execute, your safety and correctness posture should mirror what secure systems do for “untrusted or semi-trusted code artifacts.”

### Generation-time gates: parse, compile, and static checks

1. **Parse gate:** always run `ast.parse(generated_source)` before writing or importing. This catches syntax errors early, but it does not guarantee the code will compile or run (missing scoping/context checks). citeturn10search8turn10search2  
2. **Compile gate:** run `compile(generated_source, filename, "exec")` (or equivalently `py_compile`) to catch “valid AST but invalid module” cases (e.g., a bare `return`). Python’s docs explicitly warn that parsing does not guarantee valid executable code. citeturn10search8  
3. **Static analysis gate:** run a security linter such as **Bandit**, which explicitly works by building an AST and scanning nodes for risky patterns. citeturn9search6  
4. **Type-check gate:** if you add type hints to the generator and shared helper modules, a static checker like mypy can catch integration bugs without executing the sims. citeturn15search4  

### Runtime sandboxing: resource limits + subprocess control

Even if generated code is “yours,” it is programmatically assembled and should be run with guardrails.

- Use `subprocess.run(..., timeout=...)` for each sim execution in a smoke-test harness; Python’s subprocess docs cover timeout behavior and caveats. citeturn9search2turn9search3  
- On Unix, use the `resource` module (`setrlimit`) in the child process to cap CPU time, memory, and file size. The module exists specifically to measure/control resources, but is Unix-only. citeturn9search0turn9search1  
- If you allow any user-supplied text to influence templates or generation, treat this as an injection surface. OWASP’s testing guide describes template injection risks when user input is embedded unsafely into template evaluation contexts (even though your context is “code generation,” the same principle applies). citeturn10search1  
- If you choose Jinja2: its sandbox documentation explicitly recommends resource limiting because small templates can render huge outputs, and it cautions that the sandbox is not a complete security solution. citeturn2search0  

### Unit testing pattern recommendations

Given you want 50 generated scripts:

- Generator unit tests should validate determinism and uniqueness (“same seed → same manifest and file content hashes; different seed → different”).  
- A lightweight smoke suite can run 3–5 generated scripts under subprocess timeouts and confirm they emit results JSON and at least one EvidenceToken.

If you already use pytest in your repository, parameterization is a good fit for “run N generated cases” tests; pytest’s docs show standard parametrization patterns. citeturn15search0

## Recommended implementation plan with diagrams and example snippets

### Implementation flow diagram

```mermaid
flowchart TD
  A[Conceptual Goals List] --> B[MassSimGenerator CLI]
  B --> C[SeedSequence base entropy]
  C --> D[Spawn 50 child seeds]
  D --> E[Generate HypothesisSpec IR<br/>einsum eqn, shapes, backend, tolerances]
  E --> F{Render Engine}
  F -->|Jinja2| G[Render template to source]
  F -->|AST| H[Build AST Module + unparse]
  G --> I[Validate: ast.parse + compile]
  H --> I[Validate: ast.parse + compile]
  I --> J[Write *_sim.py + metadata header]
  J --> K[Update manifest.json (spec hashes, seeds, paths)]
  K --> L[Optional: smoke-run subset via subprocess + timeouts]
```

### File placement and naming conventions

**Generator location (requested):**
- `system_v4/research/tools/mass_sim_generator.py`

**Repository reality check:** `system_v4/` currently shows a `tools/` folder but not `research/` in the public tree view. citeturn14view0turn12view0 If you need the requested path, create the directories:
- `system_v4/research/`
- `system_v4/research/tools/`

**Generated sim output directory (recommended):**
- `system_v4/probes/mass_generated/` (new folder) so they sit alongside other probe sims and can share `proto_ratchet_sim_runner` imports and `a2_state/sim_results` output conventions. citeturn13view2turn13view1  

**Naming rule:**
- `mass_<goal_slug>__<spechash8>_sim.py`  
where `spechash8` is the first 8 hex chars of a SHA-256 of the canonical JSON representation of the HypothesisSpec IR.

This naming yields stable deduplication and makes it easy to reconstruct provenance.

### Metadata header format for each generated file

Use the top-of-file module docstring to store:

- generator name + version
- generation timestamp
- base seed entropy + per-file seed
- goal ID + goal text
- contraction spec: equation(s), index sizes, operand shapes
- backend selection and tolerances
- expected outputs: results JSON file path
- dependency hints (numpy required; opt_einsum/torch optional)

This mirrors the heavy docstring usage you already employ in probe sims. citeturn13view2

### Example Jinja2 template fragment (illustrative)

```python
# sim_template.j2 (illustrative fragment)

"""
{{ title }}
Generated by mass_sim_generator.py
generated_utc: {{ generated_utc }}
goal_id: {{ goal_id }}
goal_text: {{ goal_text_repr }}
spec_hash: {{ spec_hash }}
base_seed_entropy: {{ base_seed_entropy }}
child_seed: {{ child_seed }}
einsum_equation: {{ einsum_equation }}
index_sizes: {{ index_sizes_json }}
"""

from __future__ import annotations

import json
import os
from datetime import datetime
import numpy as np

from proto_ratchet_sim_runner import EvidenceToken
```

Key safety rule: `goal_text_repr` should be a *Python string literal representation* (e.g., via a custom filter `py_repr`) rather than raw insertion. This keeps “goal text” from becoming executable code.

### Example AST-based generation fragment (illustrative)

```python
import ast

def build_module_docstring(meta: dict[str, object]) -> ast.Expr:
    doc = (
        "Mass-generated Sim\n\n"
        + "\n".join(f"{k}: {v!r}" for k, v in meta.items())
    )
    return ast.Expr(value=ast.Constant(value=doc))

def build_minimal_module(meta: dict[str, object]) -> ast.Module:
    body: list[ast.stmt] = [
        build_module_docstring(meta),
        ast.Import(names=[ast.alias(name="json"), ast.alias(name="os")]),
        ast.Import(names=[ast.alias(name="numpy", asname="np")]),
    ]
    mod = ast.Module(body=body, type_ignores=[])
    return ast.fix_missing_locations(mod)

# Later:
# source = ast.unparse(build_minimal_module(meta))
```

Note the standard-library warning that `ast.unparse` exists (new in Python 3.9) and that unparse can fail with recursion errors on extremely complex ASTs. citeturn10search2

### Sample `mass_sim_generator.py` outline (not a full file)

The outline below is designed to satisfy: accept goals, generate 50 unique sims, randomize tensor hypotheses, support seeds, write metadata, and include basic unit tests. It is intentionally incomplete in areas that depend on your final Ratchet API hook choices.

```python
"""
mass_sim_generator.py (outline)

Target path (requested):
  system_v4/research/tools/mass_sim_generator.py

Generates:
  <out_dir>/mass_<goal_slug>__<hash8>_sim.py  (default count=50)
  <out_dir>/manifest.json
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import numpy as np

Engine = Literal["jinja2", "ast"]
Backend = Literal["numpy", "opt_einsum", "torch", "auto"]

@dataclass(frozen=True)
class Goal:
    goal_id: str
    text: str
    weight: float = 1.0

@dataclass(frozen=True)
class ContractionSpec:
    equation: str                 # e.g. "ab,bc->ac"
    index_sizes: dict[str, int]   # e.g. {"a": 4, "b": 3, "c": 5}
    dtypestr: str                 # "float64" or "complex128"
    operands: list[list[str]]     # list of index labels per operand

@dataclass(frozen=True)
class HypothesisSpec:
    spec_id: str
    goal: Goal
    seed: int                     # per-script seed (child)
    contraction: ContractionSpec
    backend: Backend
    atol: float = 1e-8
    rtol: float = 1e-6
    n_trials: int = 32
    mode: str = "backend_equivalence"  # hypothesis family selector

def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def stable_hash8(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:8]

def slugify(s: str) -> str:
    # Keep ASCII-ish, lowercase, underscores, and cap length for filesystem sanity.
    out = []
    for ch in s.lower():
        out.append(ch if ch.isalnum() else "_")
    return "_".join("".join(out).split("_"))[:48] or "goal"

def spawn_seeds(base_seed: int, n: int) -> list[int]:
    # Use SeedSequence so child streams are well-separated and reproducible.
    ss = np.random.SeedSequence(base_seed)
    children = ss.spawn(n)
    # Convert each child to a single int seed (portable logging)
    return [int(c.generate_state(1, dtype=np.uint64)[0]) for c in children]

def random_contraction_spec(rng: np.random.Generator) -> ContractionSpec:
    # Strategy: generate 2–4 operands, rank 2–4, ensure consistent index usage.
    # Keep it simple: each latent index appears exactly twice across operands.
    # Return equation + index_sizes + operand index lists.
    raise NotImplementedError

def build_hypothesis_specs(goals: list[Goal], base_seed: int, count: int) -> list[HypothesisSpec]:
    child_seeds = spawn_seeds(base_seed, count)
    specs: list[HypothesisSpec] = []
    for i in range(count):
        rng = np.random.default_rng(child_seeds[i])
        goal = rng.choice(goals, p=np.array([g.weight for g in goals]) / sum(g.weight for g in goals))
        con = random_contraction_spec(rng)
        spec_dict = {
            "goal_id": goal.goal_id,
            "seed": child_seeds[i],
            "equation": con.equation,
            "index_sizes": con.index_sizes,
            "dtypestr": con.dtypestr,
            "mode": "backend_equivalence",
        }
        spec_hash = stable_hash8(spec_dict)
        specs.append(HypothesisSpec(
            spec_id=f"S_MASS_{goal.goal_id}_{spec_hash}",
            goal=goal,
            seed=child_seeds[i],
            contraction=con,
            backend="auto",
        ))
    return specs

def render_sim_source(spec: HypothesisSpec, engine: Engine) -> str:
    if engine == "jinja2":
        return render_with_jinja2(spec)   # optional dependency
    return render_with_ast(spec)

def validate_source(source: str, filename: str) -> None:
    # Parse gate
    tree = ast.parse(source, filename=filename, mode="exec")
    # Compile gate: parsing doesn't guarantee compilable code
    compile(tree, filename, "exec")

def write_outputs(specs: list[HypothesisSpec], out_dir: Path, engine: Engine, overwrite: bool) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"generated_utc": utc_iso(), "items": []}

    seen = set()
    for spec in specs:
        goal_slug = slugify(spec.goal.goal_id)
        spec_hash = stable_hash8({
            "spec_id": spec.spec_id,
            "equation": spec.contraction.equation,
            "index_sizes": spec.contraction.index_sizes,
            "seed": spec.seed,
        })
        if spec_hash in seen:
            continue
        seen.add(spec_hash)

        filename = f"mass_{goal_slug}__{spec_hash}_sim.py"
        path = out_dir / filename
        if path.exists() and not overwrite:
            continue

        source = render_sim_source(spec, engine=engine)
        validate_source(source, filename=str(path))
        path.write_text(source, encoding="utf-8")

        manifest["items"].append({
            "file": filename,
            "spec_id": spec.spec_id,
            "goal_id": spec.goal.goal_id,
            "seed": spec.seed,
            "equation": spec.contraction.equation,
            "index_sizes": spec.contraction.index_sizes,
        })

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--goals-json", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--count", type=int, default=50)
    ap.add_argument("--base-seed", type=int, default=0)
    ap.add_argument("--engine", choices=["jinja2", "ast"], default="ast")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    goals_raw = json.loads(args.goals_json.read_text(encoding="utf-8"))
    goals = [Goal(**g) for g in goals_raw["goals"]]

    specs = build_hypothesis_specs(goals, base_seed=args.base_seed, count=args.count)
    write_outputs(specs, out_dir=args.out_dir, engine=args.engine, overwrite=args.overwrite)

if __name__ == "__main__":
    main()
```

Why the parse+compile gate is important: Python’s docs explicitly warn that parsing does not guarantee executable validity and compilation can still raise `SyntaxError` exceptions for code that yields a valid AST. citeturn10search8

### Basic unit test sketch for the generator

If you adopt pytest, its parametrization support fits naturally for “N seeds / N cases.” citeturn15search0

```python
# test_mass_sim_generator.py (illustrative)
import json
from pathlib import Path

def test_deterministic_manifest(tmp_path: Path):
    # Run generator twice with same base seed and same goals.
    # Compare manifest.json hashes + a sample file byte-for-byte.
    pass

def test_generated_files_parse_and_compile(tmp_path: Path):
    # For each generated file, read source, ast.parse, compile.
    pass
```

A security-focused extension: run Bandit over the generated directory in CI (Bandit builds an AST per file and applies security plugins). citeturn9search6

## Commit workflow and checklist

### Placement options

- **Requested path:** `system_v4/research/tools/mass_sim_generator.py` (requires creating `system_v4/research/tools/` because it is not visible in the current `system_v4` folder listing). citeturn14view0  
- **Repo-aligned alternative:** `system_v4/tools/mass_sim_generator.py` (fits the existing `system_v4/tools` folder). citeturn12view0  

### Checklist

Confirm repository structure and targets:

- Verify whether `system_v4/research/` already exists locally (if not, create it).
- Decide where generated sims should live (`system_v4/probes/mass_generated/` is a strong default for shared utilities and results conventions). citeturn13view2turn13view3  
- Decide which engines you ship by default:
  - AST-only (stdlib, Python ≥3.9 for `ast.unparse`) citeturn10search2  
  - Jinja2 optional with fallback; if used, decide whether templates are trusted-only or need sandboxing. citeturn2search0turn2search1  

Validation gates before commit:

- `python -m py_compile system_v4/research/tools/mass_sim_generator.py`
- Run generator with `--count 3` and inspect:
  - `manifest.json`
  - generated sim files parse/compile
  - generated sims create `a2_state/sim_results` outputs when executed (smoke test)
- Optional: run Bandit on generator + generated code. citeturn9search6  

Sandboxing for smoke runs:

- Run each sim via subprocess with a timeout. citeturn9search2  
- On Unix, optionally apply `resource.setrlimit` in the child. citeturn9search0  

### Git commands and commit message convention

```bash
# From repo root
git checkout -b feat/mass-sim-generator

mkdir -p system_v4/research/tools
# (and optionally) mkdir -p system_v4/probes/mass_generated

# Add files
git add system_v4/research/tools/mass_sim_generator.py
# plus any templates/tests you create

git commit -m "Autopoietic Hub: Add mass sim generator for tensor proof sims"
git push -u origin feat/mass-sim-generator
```

If you also generate sims to commit them (as opposed to treating them as build artifacts), do it in a separate commit:

```bash
python system_v4/research/tools/mass_sim_generator.py \
  --goals-json system_v4/research/tools/goals.json \
  --out-dir system_v4/probes/mass_generated \
  --count 50 --base-seed 12345 --engine ast

git add system_v4/probes/mass_generated manifest.json
git commit -m "Autopoietic Hub: Add 50 mass-generated tensor contraction sims"
git push
```

### Notes on unspecified details and how the design accommodates them

- **Target Python version:** unspecified. If you rely on `ast.unparse`, you need Python ≥3.9. citeturn10search2 If you must support earlier versions, consider an optional dependency such as `astunparse` (or constrain the generator to template-based rendering). citeturn0search3  
- **Execution environment / sandboxing:** unspecified. The recommended approach uses subprocess timeouts universally and Unix `resource` limits when available. citeturn9search2turn9search0  
- **Exact Ratchet engine API hooks:** partially inferred from existing evidence-token and results-writing patterns. The generator is designed so sims can align to the existing EvidenceToken ledger and `a2_state/sim_results` conventions without requiring deeper engine coupling. citeturn13view0turn13view1turn13view3