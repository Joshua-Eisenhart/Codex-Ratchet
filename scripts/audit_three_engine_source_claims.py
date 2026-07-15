#!/usr/bin/env python3
"""Audit three-engine envelopes against actual engine source usage.

The existing shape validator checks declared result fields. This audit is stricter:
it reads each envelope's declared Julia/JAX/PyTorch source paths, scans imports and
package-specific source tokens, and classifies likely rich-tool claims as source-
backed, weak/source-thin, or blocked. It is a conservative gate: it can flag false
positives for human review, but it should not let decorative package declarations
pass silently.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_RESULTS = Path("system_v5/ops/formal_scouts/results")
DEFAULT_JSON_OUT = Path("system_v5/evidence/three_engine_source_claim_audit_20260608.json")
DEFAULT_MD_OUT = Path("system_v5/docs/maintenance/three_engine_source_claim_audit_20260608.md")

JULIA_SUPPORT_ONLY = {"LinearAlgebra", "JSON", "JSON3", "Dates", "SHA", "Random", "Statistics"}
PY_SUPPORT_ONLY = {"json", "hashlib", "datetime", "math", "pathlib", "typing", "fractions"}
PY_CONTROL_ONLY = {"numpy", "scipy", "mpmath"}

# Tokens that normally show the package carried a real object/check, not just a manifest string.
PACKAGE_TOKENS: dict[str, list[str]] = {
    # Julia rich packages
    "QuantumOptics": [r"\bKet\s*\(", r"\bdm\s*\(", r"\bOperator\s*\(", r"\bptrace\s*\(", r"\bentropy_vn\s*\(", r"\bSpinBasis\s*\(", r"\bNLevelBasis\s*\(", r"\btensor\s*\("],
    "CliffordAlgebras": [r"\bCliffordAlgebra\s*\(", r"CliffordAlgebras\.\w+", r"\bMultiVector\b", r"\.e[0-9]+\b", r"basis\""],
    "Grassmann": [r"@basis\b", r"\bVGA\b", r"\bSubmanifold\b", r"Grassmann\."],
    "QuantumClifford": [r"\bS\"", r"\bStabilizer", r"\bPauliOperator", r"QuantumClifford\."],
    "Manifolds": [r"Manifolds\.", r"\bSphere\s*\(", r"\bdistance\s*\(", r"\bshortest_geodesic\s*\(", r"\bmanifold_volume\s*\("],
    "Z3": [r"\bZ3\.", r"\bSolver\s*\(", r"\bContext\s*\(", r"\bassert\w*\s*\("],
    "ITensors": [r"\bIndex\s*\(", r"\bITensor\s*\(", r"\bMPS\s*\(", r"\bsiteinds\s*\("],
    "ITensorMPS": [r"\bMPS\s*\(", r"\bsiteinds\s*\("],
    "ITensorNetworks": [r"ITensorNetworks\.", r"\bITensorNetwork"],
    "DifferentialEquations": [r"\bODEProblem\s*\(", r"\bsolve\s*\(", r"\bSDEProblem\s*\("],
    "Graphs": [r"\bSimpleGraph\s*\(", r"\badd_edge!\s*\(", r"Graphs\."],
    "Attractors": [r"Attractors\.", r"\bbasins_of_attraction\s*\(", r"\battractors\s*\(", r"\battractors_continuation\s*\("],
    "DynamicalSystems": [r"DynamicalSystems\.", r"\bCoupledODEs\s*\(", r"\bDiscreteDynamicalSystem\s*\(", r"\btrajectory\s*\("],
    "TensorOperations": [r"@tensor", r"TensorOperations\."],
    "Symbolics": [r"@variables", r"Symbolics\."],

    # Python/JAX rich packages
    "jax": [r"jax\.config", r"jax\.device_get", r"jax\.vmap", r"jax\.jit", r"jax\.jac", r"jax\.grad", r"jax\.random", r"jax\.lax"],
    "jax.numpy": [r"\bjnp\.", r"import\s+jax\.numpy"],
    "jaxlib": [r"\bxla_client\.make_cpu_client\s*\(", r"\bclient\.devices\s*\(", r"\bclient\.platform\b"],
    "jax.scipy.linalg": [r"\bjsp_linalg\.expm\s*\(", r"\bjax\.scipy\.linalg\.\w+\s*\("],
    "diffrax": [r"diffrax\.", r"\bODETerm\s*\(", r"\bdiffeqsolve\s*\(", r"\bTsit5\s*\("],
    "jaxopt": [r"jaxopt\.", r"\bGradientDescent\s*\(", r"\bLBFGS\s*\("],
    "lineax": [r"lineax\.", r"\blinear_solve\s*\("],
    "jraph": [r"jraph\.", r"\bGraphsTuple\s*\("],
    "ott": [r"ott\.", r"PointCloud\s*\(", r"Sinkhorn\s*\("],
    "galois": [r"\bgalois\.GF\s*\(", r"\bGF\s*=\s*galois\.GF\s*\(", r"\bGF\s*\([^)]*\)\.row_space\s*\(", r"\bGF\s*\([^)]*\)\s*\*\s*\bGF\s*\(", r"\bGF\s*\([^)]*\)\s*\*\*\s*2\b"],
    "e3nn_jax": [r"e3nn_jax\.", r"\bIrreps\s*\("],
    "netket": [r"netket\.", r"\bnk\."],
    "qutip": [r"qutip\.", r"\bQobj\s*\(", r"\btensor\s*\("],
    "quimb": [r"quimb\.", r"\bMPS_", r"\bMatrixProductState", r"\bqtn\."],
    "quimb.tensor": [r"quimb\.tensor", r"\bMPS_", r"\bMatrixProductState", r"\bqtn\."],
    "cotengra": [r"cotengra\.", r"\bHyperOptimizer\s*\("],
    "toponetx": [r"toponetx\.", r"\bSimplicialComplex\s*\(", r"\bCellComplex\s*\("],
    "gudhi": [r"gudhi\.", r"\bSimplexTree\s*\("],
    "rustworkx": [r"rustworkx\.", r"\brx\."],
    "networkx": [r"networkx\.", r"\bnx\.", r"\bGraph\s*\("],
    "xgi": [r"xgi\.", r"\bHypergraph\s*\("],
    "z3": [r"\bz3\.Solver\s*\(", r"\bz3\.Real\s*\(", r"\bz3\.Int\s*\(", r"\bz3\.Bool\s*\(", r"\bsolver\.add\s*\(", r"\bcheck\s*\("],
    "cvc5": [r"\bcvc5\.Solver\s*\(", r"\bmkConst\s*\(", r"\bmkTerm\s*\(", r"\bassertFormula\s*\(", r"\bcheckSat\s*\("],
    "sympy": [r"sympy\.", r"\bsp\.symbols\s*\(", r"\bsp\.Rational\s*\(", r"\bsp\.log\s*\(", r"\bMatrix\s*\(", r"\bsimplify\s*\("],
    "julia_gf4_stdlib": [r"\bgf4_add\s*\(", r"\bgf4_mul\s*\(", r"\bgf4_inv\s*\(", r"\brank_gf4\s*\(", r"\bspan_projective_points\s*\(", r"\bprojective_class\s*\(", r"\bfrobenius_boundary\s*\("],

    # PyTorch rich packages
    "torch": [r"\btorch\.", r"import\s+torch"],
    "torch.func": [r"torch\.func", r"\bjacrev\s*\(", r"\bvmap\s*\(", r"\bhessian\s*\("],
    "functorch": [r"functorch", r"\bjacrev\s*\(", r"\bvmap\s*\("],
    "torch_ga": [r"torch_ga", r"\bGeometricAlgebra\s*\("],
    "kingdon": [r"\bkingdon\b", r"\bAlgebra\s*\(", r"\.blades\["],
    "torch_geometric": [r"torch_geometric", r"\bData\s*\(", r"\bHeteroData\s*\("],
    "clifford": [r"import\s+clifford", r"\bCl\s*\(", r"\blayout\."],
    "geomstats": [r"geomstats\.", r"Hypersphere\s*\(", r"SpecialOrthogonal\s*\("],
    "e3nn": [r"e3nn\.", r"\bIrreps\s*\("],
}

# For a stricter "claim-rich" bar, at least one package in these sets must be source-backed.
ENGINE_RICH_PACKAGES = {
    "julia": {"QuantumOptics", "CliffordAlgebras", "Grassmann", "QuantumClifford", "Manifolds", "Z3", "ITensors", "ITensorMPS", "ITensorNetworks", "DifferentialEquations", "Graphs", "Attractors", "DynamicalSystems", "TensorOperations", "Symbolics", "julia_gf4_stdlib"},
    "jax": {"jaxlib", "diffrax", "jaxopt", "lineax", "jraph", "ott", "galois", "e3nn_jax", "netket", "qutip", "quimb", "quimb.tensor", "cotengra", "toponetx", "gudhi", "rustworkx", "networkx", "xgi", "z3", "cvc5", "sympy"},
    "pytorch": {"torch_ga", "kingdon", "torch_geometric", "clifford", "geomstats", "e3nn", "torch.func", "functorch", "z3", "cvc5", "sympy"},
}

# Baseline packages can be legitimate local compute but not enough for rich-tool claims.
ENGINE_BASELINE = {
    "julia": JULIA_SUPPORT_ONLY | {"LinearAlgebra"},
    "jax": {"jax", "jax.numpy"} | PY_SUPPORT_ONLY,
    "pytorch": {"torch"} | PY_SUPPORT_ONLY,
}

# Local source-defined routes intentionally have no external import. They must
# still prove themselves through concrete function/API tokens above.
LOCAL_SOURCE_PACKAGES = {
    "julia": {"julia_gf4_stdlib"},
}


def rel_or_str(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def normalize_path(path_value: str | None, root: Path) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    return path if path.is_absolute() else root / path


def strip_manifest_blocks(text: str) -> str:
    """Remove obvious manifest/depth string blocks so token evidence is not self-referential."""
    lines = []
    skip_depth = 0
    for line in text.splitlines():
        if re.search(r"TOOL_MANIFEST|TOOL_INTEGRATION_DEPTH|packages_used|aligned_packages_load_bearing|load_bearing", line):
            skip_depth = max(skip_depth, 1)
            continue
        if skip_depth:
            # Drop adjacent dictionary literal/comment strings near manifest declarations.
            if line.strip().startswith(("\"", "'", ":", "=>")) or "reason" in line or "used" in line or "tried" in line:
                continue
            skip_depth -= 1
        lines.append(line)
    return "\n".join(lines)


def python_imports(text: str) -> set[str]:
    imports: set[str] = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                imports.add(name)
                imports.add(name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
                imports.add(node.module.split(".")[0])
    if "from torch.func" in text or "import torch.func" in text:
        imports.add("torch.func")
    if "import jax.numpy" in text:
        imports.add("jax.numpy")
    return imports


def julia_imports(text: str) -> set[str]:
    imports: set[str] = set()
    for line in text.splitlines():
        match = re.match(r"\s*(?:using|import)\s+(.+)", line)
        if not match:
            continue
        names = match.group(1).split(":")[0]
        for part in names.split(","):
            token = part.strip().split(".")[0]
            if token:
                imports.add(token)
    return imports


def source_imports(engine: str, text: str) -> set[str]:
    return julia_imports(text) if engine == "julia" else python_imports(text)


def token_hits(package: str, text: str) -> list[str]:
    source_only = strip_manifest_blocks(text)
    hits = []
    for pattern in PACKAGE_TOKENS.get(package, []):
        if re.search(pattern, source_only):
            hits.append(pattern)
    return hits


def source_hash(path: Path) -> str | None:
    import hashlib
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def get_declared_load_bearing(rec: dict[str, Any]) -> list[str]:
    for key in ("aligned_packages_load_bearing", "load_bearing_packages"):
        value = rec.get(key)
        if isinstance(value, list):
            return [str(x) for x in value]
    packages = rec.get("packages")
    if isinstance(packages, dict):
        value = packages.get("load_bearing")
        if isinstance(value, list):
            return [str(x) for x in value]
    return []


def audit_engine(engine: str, rec: dict[str, Any], root: Path) -> dict[str, Any]:
    source = normalize_path(rec.get("source_path"), root)
    result = normalize_path(rec.get("result_path"), root)
    declared_used = [str(x) for x in rec.get("packages_used", [])] if isinstance(rec.get("packages_used"), list) else []
    declared_load = get_declared_load_bearing(rec)
    out: dict[str, Any] = {
        "engine": engine,
        "source_path": rel_or_str(source, root) if source else None,
        "result_path": rel_or_str(result, root) if result else None,
        "source_exists": bool(source and source.exists()),
        "result_exists": bool(result and result.exists()),
        "declared_packages_used": declared_used,
        "declared_load_bearing": declared_load,
        "reads_peer_result_declared": rec.get("reads_peer_result"),
    }
    if not source or not source.exists():
        out.update({"classification": "blocked_missing_source", "problems": ["source_path missing or absent"]})
        return out

    text = source.read_text(encoding="utf-8", errors="replace")
    imports = source_imports(engine, text)
    # Normalize aliases and package strings to match result declarations.
    if engine == "jax" and "jax" in imports and "jax.numpy" in declared_used:
        imports.add("jax.numpy")
    if engine == "pytorch" and ("torch.func" in text or "from torch.func" in text):
        imports.add("torch.func")

    backed: dict[str, list[str]] = {}
    thin: list[str] = []
    not_imported: list[str] = []
    for package in declared_load:
        hits = token_hits(package, text)
        imported = (
            package in imports
            or package.split(".")[0] in imports
            or (package in LOCAL_SOURCE_PACKAGES.get(engine, set()) and bool(hits))
        )
        if imported and hits:
            backed[package] = hits
        elif imported:
            thin.append(package)
        else:
            not_imported.append(package)

    rich_backed = sorted(set(backed) & ENGINE_RICH_PACKAGES.get(engine, set()))
    baseline_claims = sorted(set(declared_load) & ENGINE_BASELINE.get(engine, set()))
    problems: list[str] = []
    if not declared_load:
        problems.append("no declared load-bearing packages")
    if not rich_backed:
        problems.append("no source-backed rich package evidence for this engine")
    if thin:
        problems.append("declared load-bearing packages imported but source-token-thin: " + ", ".join(thin))
    if not_imported:
        problems.append("declared load-bearing packages not imported in source: " + ", ".join(not_imported))
    if baseline_claims and not rich_backed:
        problems.append("load-bearing set is baseline/support-only")
    if rec.get("reads_peer_result") is not False:
        problems.append("reads_peer_result not explicitly false")

    if rich_backed and not thin and not not_imported:
        classification = "source_backed_rich_tool_claim"
    elif rich_backed:
        classification = "mixed_source_backed_with_thin_claims"
    elif declared_load:
        classification = "declared_rich_but_source_thin_or_baseline"
    else:
        classification = "no_load_bearing_claim"

    out.update(
        {
            "classification": classification,
            "imports": sorted(imports),
            "source_sha256": source_hash(source),
            "source_backed_load_bearing": backed,
            "source_thin_load_bearing": thin,
            "not_imported_load_bearing": not_imported,
            "rich_backed_packages": rich_backed,
            "baseline_claims": baseline_claims,
            "problems": problems,
        }
    )
    return out


def envelope_paths(results_dir: Path) -> list[Path]:
    paths = []
    for path in sorted(results_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if payload.get("schema_version") == "three_engine_sim_result_v1" and isinstance(payload.get("engines"), dict):
            # Controller/envelope files are the ones whose own name has envelope or whose engines contain all three.
            if "envelope" in path.name or set(payload["engines"].keys()) >= {"julia", "jax", "pytorch"}:
                paths.append(path)
    return paths


def audit_envelope(path: Path, root: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    engines = payload.get("engines") if isinstance(payload.get("engines"), dict) else {}
    engine_audits = {engine: audit_engine(engine, rec, root) for engine, rec in engines.items() if isinstance(rec, dict)}
    engine_classes = {engine: audit["classification"] for engine, audit in engine_audits.items()}
    problems = [f"{engine}: {problem}" for engine, audit in engine_audits.items() for problem in audit.get("problems", [])]
    all_three_present = set(engine_audits.keys()) >= {"julia", "jax", "pytorch"}
    all_source_backed = all(
        audit.get("classification") in {"source_backed_rich_tool_claim", "mixed_source_backed_with_thin_claims"}
        for audit in engine_audits.values()
    )
    if not all_three_present:
        verdict = "blocked_missing_engine_lane"
    elif all_source_backed and not problems:
        verdict = "source_backed_all_lanes"
    elif all_source_backed:
        verdict = "source_backed_but_review_needed"
    else:
        verdict = "validator_false_positive_or_source_thin"
    return {
        "path": rel_or_str(path, root),
        "object_id": payload.get("object_id"),
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "formal_admission_allowed": payload.get("formal_admission_allowed"),
        "all_pass": payload.get("all_pass"),
        "claim_path_tools": payload.get("claim_path_tools"),
        "verdict": verdict,
        "engine_classes": engine_classes,
        "problems": problems,
        "engines": engine_audits,
    }


def render_markdown(report: dict[str, Any], json_rel: str) -> str:
    lines: list[str] = []
    s = report["summary"]
    lines.append("# Three-Engine Source-Claim Audit — 2026-06-08")
    lines.append("")
    lines.append("Status: source-level audit. This is stricter than the envelope shape validator and does not promote claims.")
    lines.append("")
    lines.append("## Bottom line")
    lines.append("")
    lines.append("The old validator can pass envelopes whose declared package fields look correct. This audit checks whether the declared Julia/JAX/PyTorch load-bearing packages are actually imported and used in source-token evidence. Source-token evidence is still not mathematical proof, but it catches decorative package claims.")
    lines.append("")
    lines.append(f"Full JSON: `{json_rel}`")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- envelopes audited: `{s['envelope_count']}`")
    lines.append(f"- source-backed all lanes: `{s['verdict_counts'].get('source_backed_all_lanes', 0)}`")
    lines.append(f"- source-backed but review needed: `{s['verdict_counts'].get('source_backed_but_review_needed', 0)}`")
    lines.append(f"- validator false-positive/source-thin: `{s['verdict_counts'].get('validator_false_positive_or_source_thin', 0)}`")
    lines.append("")
    lines.append("### Verdict counts")
    lines.append("")
    for key, value in s["verdict_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append("### Engine class counts")
    lines.append("")
    for engine, counts in s["engine_class_counts"].items():
        lines.append(f"#### `{engine}`")
        for key, value in counts.items():
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")
    lines.append("## Review-needed / source-thin examples")
    lines.append("")
    for item in report["envelopes"]:
        if item["verdict"] in {"validator_false_positive_or_source_thin", "source_backed_but_review_needed"}:
            lines.append(f"### `{item['object_id']}`")
            lines.append(f"- path: `{item['path']}`")
            lines.append(f"- verdict: `{item['verdict']}`")
            for problem in item.get("problems", [])[:12]:
                lines.append(f"  - {problem}")
            lines.append("")
    lines.append("## Safe interpretation")
    lines.append("")
    lines.append("- `source_backed_*` means there is source evidence that package-native calls exist. It does not mean admission/canon.")
    lines.append("- `validator_false_positive_or_source_thin` means the envelope shape validator was too permissive for rich-tool truth.")
    lines.append("- Any current/future consolidation should use this audit or a stricter AST/runtime audit before calling a sim rich-tool-backed.")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_OUT)
    args = parser.parse_args()

    root = args.repo.resolve()
    results_dir = args.results_dir if args.results_dir.is_absolute() else root / args.results_dir
    json_out = args.json_out if args.json_out.is_absolute() else root / args.json_out
    md_out = args.md_out if args.md_out.is_absolute() else root / args.md_out

    envelopes = [audit_envelope(path, root) for path in envelope_paths(results_dir)]
    verdict_counts = Counter(item["verdict"] for item in envelopes)
    engine_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for item in envelopes:
        for engine, cls in item.get("engine_classes", {}).items():
            engine_counts[engine][cls] += 1

    report = {
        "schema": "three_engine_source_claim_audit.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": str(root),
        "source_results_dir": rel_or_str(results_dir, root),
        "claim_ceiling": "Source-token audit only; no mathematical admission or canonical promotion.",
        "summary": {
            "envelope_count": len(envelopes),
            "verdict_counts": dict(verdict_counts.most_common()),
            "engine_class_counts": {engine: dict(counter.most_common()) for engine, counter in engine_counts.items()},
        },
        "envelopes": envelopes,
    }
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md_out.write_text(render_markdown(report, rel_or_str(json_out, root)), encoding="utf-8")
    print(json.dumps({"status": "ok", "json_out": rel_or_str(json_out, root), "md_out": rel_or_str(md_out, root), "summary": report["summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
