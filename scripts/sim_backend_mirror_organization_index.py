#!/usr/bin/env python3
"""Build an organization index for sim objects and backend mirror state.

This index is intentionally not an admission gate. It answers operational
questions:

- What mathematical object family does this sim appear to target?
- Which backend does it actually touch: PyTorch, JAX, both, neither?
- Does it have a visible result receipt?
- Is it part of the active v5 scout/lego estate, legacy v4 estate, or retired
  exploration estate?
- Which families have JAX/PyTorch mirror gaps?

It avoids treating folder role as the main category. The main categories are
the target object family and backend mirror state.
"""

from __future__ import annotations

import ast
import json
import warnings
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


warnings.filterwarnings("ignore", category=SyntaxWarning)


ROOT = Path(__file__).resolve().parents[1]
FORMAL_ROOT = ROOT / "system_v5" / "ops" / "formal_scouts"
LEGOS_ROOT = ROOT / "system_v5" / "legos"
V4_PROBES = ROOT / "system_v4" / "probes"
RETIRED_EXPLORATION_ROOT = ROOT / "system_v5" / "grok_sim"

READINESS_INDEX = ROOT / "system_v5" / "evidence" / "formal_scout_readiness_index.json"
OUT_JSON = ROOT / "system_v5" / "evidence" / "sim_backend_mirror_organization_index.json"
OUT_MD = ROOT / "system_v5" / "docs" / "SIM_BACKEND_MIRROR_ORGANIZATION_INDEX.md"


FAMILY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("shell_possibility_field", ("rpf", "retrocausal", "possibility", "shell", "omega")),
    ("finite_probe_response", ("finite_effect", "sic", "povm", "response_quotient", "quotient", "probe")),
    ("spinor_density_carrier", ("spinor_density", "density_carrier", "torch_complex_spinor", "unit_spinor")),
    ("mps_peps_peps3d_carrier", ("peps3d", "peps2d", "peps", "mps", "tensor_network")),
    ("hopf_fibration", ("hopf_fibration", "s3_to_s2", "projective_hopf", "s2_hopf", "u1_hopf")),
    ("nested_hopf_tori", ("nested_hopf", "hopf_tori", "hopf_torus", "torus_leaf")),
    ("hopf_connection_holonomy", ("connection_holonomy", "holonomy", "hopf_connection")),
    ("left_right_weyl_chirality", ("left_right_weyl", "weyl_spinor", "chirality", "chiral")),
    ("terrain_weyl_law", ("terrain", "gksl", "lindblad", "dissipator", "funnel", "vortex", "pit", "hill")),
    ("operator_channel_action", ("operator", "channel", "cptp", "kraus", "substage", "commutation")),
    ("entropy_qit_readout", ("entropy", "coherent_information", "conditional", "renyi", "negativity", "relative_entropy")),
    ("clifford_quaternion_rotor", ("clifford", "quaternion", "rotor", "gamma")),
    ("g_structure_candidate", ("g_structure", "gstruct", "spin7", "g2", "spinc", "spin_c", "su3", "calabi", "symplectic", "contact_sasakian")),
    ("alt_geometry_candidate", ("twistor", "dirac_monopole", "spectral_triple", "seiberg", "projective_fubini")),
    ("axis0_xi_phi_bridge", ("axis0", "xi", "phi0", "bridge")),
    ("attractor_basin_world_model", ("attractor", "basin", "lewm", "world_model", "lirpa", "active_policy")),
    ("tool_microprobe", ("jaxtool", "tool", "capability", "optax", "diffrax", "netket", "lineax", "jaxopt", "qutip")),
    ("formal_validator_meta", ("readiness", "validator", "index", "audit", "classifier", "receipt")),
    ("classical_baseline", ("classical", "baseline", "carnot", "szilard", "landauer")),
]


TOOL_TOKENS: dict[str, tuple[str, ...]] = {
    "pytorch": ("import torch", "from torch", "torch."),
    "jax": ("import jax", "from jax", "jax.", "jax.numpy", "import jax.numpy"),
    "jax_numpy": ("jax.numpy", "jnp."),
    "numpy": ("import numpy", "from numpy", "np."),
    "pyg": ("torch_geometric", "from torch_geometric"),
    "quimb": ("import quimb", "from quimb", "quimb.", "qtn."),
    "cotengra": ("import cotengra", "from cotengra", "cotengra."),
    "autoray": ("import autoray", "from autoray", "autoray."),
    "opt_einsum": ("opt_einsum",),
    "z3": ("import z3", "from z3", "z3."),
    "cvc5": ("import cvc5", "from cvc5", "cvc5."),
    "sympy": ("import sympy", "from sympy", "sympy.", "sp."),
    "clifford": ("import clifford", "from clifford", "clifford."),
    "geomstats": ("geomstats",),
    "e3nn": ("import e3nn", "from e3nn", "e3nn"),
    "gudhi": ("import gudhi", "from gudhi", "gudhi"),
    "toponetx": ("toponetx", "import tnx", "from toponetx"),
    "rustworkx": ("rustworkx",),
    "xgi": ("import xgi", "from xgi", "xgi."),
    "auto_lirpa": ("auto_LiRPA", "auto_lirpa", "BoundedModule", "BoundedTensor"),
    "flax": ("import flax", "from flax", "flax."),
    "equinox": ("import equinox", "from equinox", "eqx."),
    "optax": ("import optax", "from optax", "optax."),
    "diffrax": ("import diffrax", "from diffrax", "diffrax."),
    "netket": ("import netket", "from netket", "netket."),
    "jraph": ("import jraph", "from jraph", "jraph."),
    "blackjax": ("import blackjax", "from blackjax", "blackjax."),
    "orbax": ("import orbax", "from orbax", "orbax."),
}


@dataclass(frozen=True)
class SourceRow:
    path: Path
    estate: str
    stem: str
    text: str


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_text(path: Path) -> str:
    try:
        return path.read_text(errors="ignore")
    except OSError:
        return ""


def source_files() -> list[SourceRow]:
    roots = [
        (FORMAL_ROOT, "active_formal_scout"),
        (LEGOS_ROOT, "lego"),
        (V4_PROBES, "legacy_v4_probe"),
        (RETIRED_EXPLORATION_ROOT, "retired_exploration"),
    ]
    rows: list[SourceRow] = []
    for root, estate in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts or path.name.startswith("."):
                continue
            if path.is_relative_to(FORMAL_ROOT / "results"):
                continue
            rows.append(SourceRow(path=path, estate=estate, stem=path.stem, text=read_text(path)))
    return rows


def result_index() -> dict[str, list[Path]]:
    out: dict[str, list[Path]] = defaultdict(list)
    for path in sorted(ROOT.rglob("*.json")):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        stem = path.stem
        if stem.endswith("_results"):
            stem = stem[: -len("_results")]
        out[stem].append(path)
    return out


def formal_readiness() -> dict[str, dict[str, Any]]:
    if not READINESS_INDEX.exists():
        return {}
    payload = json.loads(READINESS_INDEX.read_text())
    rows = payload.get("rows", [])
    by_source: dict[str, dict[str, Any]] = {}
    for row in rows:
        source = row.get("source_path")
        expected = row.get("validator_expected_source_path")
        if source:
            by_source[source] = row
        if expected:
            by_source.setdefault(expected, row)
    return by_source


def imported_modules(text: str) -> set[str]:
    modules: set[str] = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return modules
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def detect_tools(text: str) -> list[str]:
    tools: set[str] = set()
    imports = imported_modules(text)
    import_alias = {
        "torch": "pytorch",
        "jax": "jax",
        "numpy": "numpy",
        "quimb": "quimb",
        "cotengra": "cotengra",
        "autoray": "autoray",
        "z3": "z3",
        "cvc5": "cvc5",
        "sympy": "sympy",
        "clifford": "clifford",
        "geomstats": "geomstats",
        "e3nn": "e3nn",
        "gudhi": "gudhi",
        "toponetx": "toponetx",
        "rustworkx": "rustworkx",
        "xgi": "xgi",
        "flax": "flax",
        "equinox": "equinox",
        "optax": "optax",
        "diffrax": "diffrax",
        "netket": "netket",
        "jraph": "jraph",
        "blackjax": "blackjax",
        "orbax": "orbax",
    }
    for module, tool in import_alias.items():
        if module in imports:
            tools.add(tool)
    lowered = text.lower()
    for tool, needles in TOOL_TOKENS.items():
        if any(needle.lower() in lowered for needle in needles):
            tools.add(tool)
    return sorted(tools)


def detect_family(stem: str, text: str) -> str:
    # Use the source/object key as the primary classifier. Most formal scouts
    # include broad negative claim ceilings in their body, such as "no Axis0
    # claim" or "no final manifold admission"; using full source text would turn
    # disclaimers into false object-family evidence.
    hay = stem.lower()
    matches: list[tuple[int, str]] = []
    for family, needles in FAMILY_RULES:
        score = sum(1 for needle in needles if needle.lower() in hay)
        if score:
            matches.append((score, family))
    if not matches:
        return "uncategorized"
    matches.sort(key=lambda item: (-item[0], item[1]))
    return matches[0][1]


def backend_state(tools: list[str]) -> str:
    has_torch = "pytorch" in tools
    has_jax = "jax" in tools
    if has_torch and has_jax:
        return "dual_pytorch_jax"
    if has_torch:
        return "pytorch_only"
    if has_jax:
        return "jax_only"
    if "numpy" in tools:
        return "numpy_or_classical_only"
    return "no_numeric_backend_detected"


def normalized_object_key(stem: str) -> str:
    key = stem.lower()
    for prefix in ("sim_", "run_"):
        if key.startswith(prefix):
            key = key[len(prefix) :]
    replacements = [
        "jax_native_",
        "_jax_native",
        "_pytorch",
        "_torch",
        "_jax",
        "_dual_backend",
        "_dual_engine",
        "_full_deep_network",
        "_deep_probe",
        "_probe",
        "_results",
    ]
    for old in replacements:
        key = key.replace(old, "_")
    while "__" in key:
        key = key.replace("__", "_")
    return key.strip("_")


def paired_result_paths(row: SourceRow, results: dict[str, list[Path]]) -> list[str]:
    stems = {row.stem}
    if row.stem.startswith("sim_"):
        stems.add(row.stem[len("sim_") :])
    else:
        stems.add(f"sim_{row.stem}")
    found: list[Path] = []
    for stem in stems:
        found.extend(results.get(stem, []))
    return sorted({rel(path) for path in found})


def build_index() -> dict[str, Any]:
    results = result_index()
    readiness = formal_readiness()
    rows: list[dict[str, Any]] = []
    for source in source_files():
        tools = detect_tools(source.text)
        result_paths = paired_result_paths(source, results)
        readiness_row = readiness.get(rel(source.path), {})
        family = detect_family(source.stem, source.text)
        backend = backend_state(tools)
        rows.append(
            {
                "source_path": rel(source.path),
                "stem": source.stem,
                "estate": source.estate,
                "family": family,
                "normalized_object_key": normalized_object_key(source.stem),
                "backend_state": backend,
                "tools_detected": tools,
                "result_paths": result_paths,
                "result_count": len(result_paths),
                "has_result": bool(result_paths),
                "formal_readiness_status": readiness_row.get("readiness_status"),
                "formal_validation_pass": readiness_row.get("validation_pass"),
                "formal_all_pass": readiness_row.get("all_pass"),
                "promotion_allowed": readiness_row.get("promotion_allowed"),
                "public_status_label": readiness_row.get("public_status_label", "exists"),
            }
        )

    family_counts = Counter(row["family"] for row in rows)
    backend_counts = Counter(row["backend_state"] for row in rows)
    estate_counts = Counter(row["estate"] for row in rows)
    family_backend_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    family_estate_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        family_backend_counts[row["family"]][row["backend_state"]] += 1
        family_estate_counts[row["family"]][row["estate"]] += 1

    active_rows = [row for row in rows if row["estate"] in {"active_formal_scout", "lego"}]
    by_family_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in active_rows:
        by_family_key[(row["family"], row["normalized_object_key"])].append(row)

    mirror_clusters: list[dict[str, Any]] = []
    for (family, key), cluster in sorted(by_family_key.items()):
        backends = sorted({row["backend_state"] for row in cluster})
        has_torch = any(row["backend_state"] in {"pytorch_only", "dual_pytorch_jax"} for row in cluster)
        has_jax = any(row["backend_state"] in {"jax_only", "dual_pytorch_jax"} for row in cluster)
        if has_torch and has_jax:
            status = "has_pytorch_and_jax_surface"
        elif has_torch:
            status = "missing_jax_mirror"
        elif has_jax:
            status = "missing_pytorch_mirror"
        else:
            status = "missing_both_primary_backends"
        mirror_clusters.append(
            {
                "family": family,
                "normalized_object_key": key,
                "mirror_status": status,
                "backend_states": backends,
                "source_count": len(cluster),
                "source_paths": [row["source_path"] for row in cluster[:12]],
                "extra_source_count": max(0, len(cluster) - 12),
            }
        )

    mirror_status_counts = Counter(cluster["mirror_status"] for cluster in mirror_clusters)
    high_value_families = [
        "mps_peps_peps3d_carrier",
        "nested_hopf_tori",
        "hopf_fibration",
        "hopf_connection_holonomy",
        "left_right_weyl_chirality",
        "terrain_weyl_law",
        "operator_channel_action",
        "entropy_qit_readout",
        "clifford_quaternion_rotor",
        "g_structure_candidate",
        "alt_geometry_candidate",
        "shell_possibility_field",
        "finite_probe_response",
        "spinor_density_carrier",
    ]
    mirror_gap_samples = [
        cluster
        for cluster in mirror_clusters
        if cluster["family"] in high_value_families
        and cluster["mirror_status"] in {"missing_jax_mirror", "missing_pytorch_mirror"}
    ][:80]

    def short_rows(items: list[dict[str, Any]], limit: int = 60) -> list[dict[str, Any]]:
        keep = []
        for row in items[:limit]:
            keep.append(
                {
                    "source_path": row["source_path"],
                    "family": row["family"],
                    "backend_state": row["backend_state"],
                    "has_result": row["has_result"],
                    "formal_readiness_status": row.get("formal_readiness_status"),
                    "formal_validation_pass": row.get("formal_validation_pass"),
                }
            )
        return keep

    active_high_value = [row for row in active_rows if row["family"] in high_value_families]
    active_missing_result = [row for row in active_high_value if not row["has_result"]]
    active_validator_red = [
        row
        for row in active_rows
        if row["estate"] == "active_formal_scout"
        and row.get("formal_validation_pass") is False
    ]
    retired_high_value = [
        row
        for row in rows
        if row["estate"] == "retired_exploration" and row["family"] in high_value_families
    ]
    dual_surface_without_single_compare = []
    for cluster in mirror_clusters:
        if cluster["mirror_status"] != "has_pytorch_and_jax_surface":
            continue
        cluster_rows = by_family_key[(cluster["family"], cluster["normalized_object_key"])]
        if not any(row["backend_state"] == "dual_pytorch_jax" for row in cluster_rows):
            dual_surface_without_single_compare.append(cluster)

    queue_full = {
        "repair_jax_mirrors_for_pytorch_active_high_value": [
            cluster
            for cluster in mirror_clusters
            if cluster["family"] in high_value_families
            and cluster["mirror_status"] == "missing_jax_mirror"
        ],
        "repair_pytorch_mirrors_for_jax_active_high_value": [
            cluster
            for cluster in mirror_clusters
            if cluster["family"] in high_value_families
            and cluster["mirror_status"] == "missing_pytorch_mirror"
        ],
        "write_explicit_dual_backend_comparison_receipts": dual_surface_without_single_compare,
        "add_or_repair_result_receipts": short_rows(active_missing_result, limit=len(active_missing_result)),
        "fix_or_preserve_formal_validator_red": short_rows(active_validator_red, limit=len(active_validator_red)),
        "port_retired_exploration_only_if_still_wanted": short_rows(retired_high_value, limit=len(retired_high_value)),
    }
    next_action_queue = {
        key: values[:60]
        for key, values in queue_full.items()
    }
    next_action_queue_total_counts = {
        key: len(values)
        for key, values in queue_full.items()
    }

    return {
        "schema": "sim_backend_mirror_organization_index.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "boundary": (
            "organization_only_not_rerun_not_admission_not_promotion; "
            "families are heuristic routing buckets; mirror status is source-surface detection"
        ),
        "source_count": len(rows),
        "active_source_count": len(active_rows),
        "family_counts": dict(family_counts),
        "backend_counts": dict(backend_counts),
        "estate_counts": dict(estate_counts),
        "family_backend_counts": {k: dict(v) for k, v in sorted(family_backend_counts.items())},
        "family_estate_counts": {k: dict(v) for k, v in sorted(family_estate_counts.items())},
        "mirror_status_counts": dict(mirror_status_counts),
        "mirror_gap_samples": mirror_gap_samples,
        "next_action_queue": next_action_queue,
        "next_action_queue_total_counts": next_action_queue_total_counts,
        "rows": rows,
    }


def md_table(rows: list[list[str]]) -> list[str]:
    if not rows:
        return []
    header = rows[0]
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
    for row in rows[1:]:
        out.append("| " + " | ".join(row) + " |")
    return out


def render_markdown(index: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Sim Backend Mirror Organization Index",
        "",
        f"Generated: `{index['generated_at']}`",
        "",
        "Boundary: organization only. This does not rerun, admit, promote, or complete any sim.",
        "",
        "This index organizes by target object family plus backend mirror state. Folder/estate is secondary.",
        "",
        "## Summary",
        "",
        f"- Source files indexed: `{index['source_count']}`",
        f"- Active source files indexed: `{index['active_source_count']}`",
        f"- Backend states: `{index['backend_counts']}`",
        f"- Mirror statuses over active source clusters: `{index['mirror_status_counts']}`",
        f"- Estate counts: `{index['estate_counts']}`",
        "",
        "## How To Use This Index",
        "",
        "1. Pick the mathematical object family, not the folder.",
        "2. Pick one source row or cluster.",
        "3. Check whether PyTorch, JAX, or both are present.",
        "4. If only one backend exists, write or repair the mirror before treating the row as a dual-engine result.",
        "5. Check the result receipt and formal readiness status before citing the sim.",
        "6. For retired exploration rows, port the idea into active v5 scout/lego form before using it as evidence.",
        "",
        "## Family Counts",
        "",
    ]
    family_rows = [["family", "count", "pytorch", "jax", "dual", "numpy/control", "no numeric", "active", "legacy", "retired"]]
    for family, count in sorted(index["family_counts"].items(), key=lambda item: (-item[1], item[0])):
        backends = index["family_backend_counts"].get(family, {})
        estates = index["family_estate_counts"].get(family, {})
        family_rows.append(
            [
                f"`{family}`",
                str(count),
                str(backends.get("pytorch_only", 0)),
                str(backends.get("jax_only", 0)),
                str(backends.get("dual_pytorch_jax", 0)),
                str(backends.get("numpy_or_classical_only", 0)),
                str(backends.get("no_numeric_backend_detected", 0)),
                str(estates.get("active_formal_scout", 0) + estates.get("lego", 0)),
                str(estates.get("legacy_v4_probe", 0)),
                str(estates.get("retired_exploration", 0)),
            ]
        )
    lines.extend(md_table(family_rows))
    lines.extend(
        [
            "",
            "## Mirror Gap Samples",
            "",
            "These are not all gaps. They are the first high-value active clusters where one primary backend is missing.",
            "",
        ]
    )
    gap_rows = [["family", "object key", "status", "sources"]]
    for cluster in index["mirror_gap_samples"][:40]:
        sample = "<br>".join(f"`{path}`" for path in cluster["source_paths"][:4])
        extra = cluster.get("extra_source_count", 0)
        if extra:
            sample += f"<br>... +{extra}"
        gap_rows.append(
            [
                f"`{cluster['family']}`",
                f"`{cluster['normalized_object_key']}`",
                f"`{cluster['mirror_status']}`",
                sample,
            ]
        )
    lines.extend(md_table(gap_rows))
    lines.extend(
        [
            "",
            "## Next Action Queue",
            "",
            "These are routing queues, not execution claims.",
            "",
        ]
    )
    queue = index["next_action_queue"]
    queue_counts = index.get("next_action_queue_total_counts", {})
    queue_rows = [["queue", "count", "first examples"]]
    for name, items in queue.items():
        examples = []
        for item in items[:3]:
            if "source_paths" in item:
                examples.append(f"`{item['family']}::{item['normalized_object_key']}`")
            else:
                examples.append(f"`{item['source_path']}`")
        queue_rows.append([f"`{name}`", str(queue_counts.get(name, len(items))), "<br>".join(examples)])
    lines.extend(md_table(queue_rows))
    lines.extend(
        [
            "",
            "## Active Rule",
            "",
            "A PyTorch/JAX pair is useful only when both sides compute the same named finite map or readout and a receipt compares them. A JAX-only or PyTorch-only row is still usable, but its next action is mirror repair, not composition or layer completion.",
            "",
            "Machine index: `system_v5/evidence/sim_backend_mirror_organization_index.json`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    index = build_index()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(render_markdown(index))
    print(f"wrote {rel(OUT_JSON)}")
    print(f"wrote {rel(OUT_MD)}")
    print(f"source_count={index['source_count']}")
    print(f"active_source_count={index['active_source_count']}")
    print(f"backend_counts={index['backend_counts']}")
    print(f"mirror_status_counts={index['mirror_status_counts']}")


if __name__ == "__main__":
    main()
