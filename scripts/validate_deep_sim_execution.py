#!/usr/bin/env python3
"""Validate deep sim execution receipts without promoting them.

This is an execution-depth audit, not a formal admission gate.  It checks
whether a result JSON contains the evidence needed to call a run a serious
independent sim under the current nonclassical layer/geometry standard.

Profiles:
  layer_full        independent manifold-layer execution receipt
  geometry_full     standalone geometry or G-structure execution receipt
  jax_geometry      JAX-native geometry/tool receipt
  dual_backend      PyTorch/JAX comparison receipt

The script intentionally reports missing evidence instead of softening it into
"complete".  A receipt can pass this audit and still remain blocked from
stacking, Axis0, flux, physics, or final manifold admission.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import glob
import json
import math
from pathlib import Path
from typing import Any


QIT_TERMS = (
    "von_neumann",
    "renyi",
    "mutual_information",
    "conditional_entropy",
    "coherent_information",
    "log_negativity",
    "negativity",
    "relative_entropy",
    "entanglement_entropy",
    "entanglement_spectrum",
    "path_entropy",
    "shell_possibility_entropy",
)

NETWORK_TERMS = ("mps", "peps2d", "peps3d")

PROOF_TERMS = ("z3", "cvc5", "sympy")
GEOMETRY_TOOLS = (
    "clifford",
    "geomstats",
    "e3nn",
    "rustworkx",
    "xgi",
    "toponetx",
    "gudhi",
    "quimb",
    "cotengra",
    "opt_einsum",
    "pyg",
    "torch_geometric",
)
PRIMARY_BACKEND_TOOLS = (
    "jax",
    "julia",
    "pepskit",
    "tensorkit",
    "itensors",
    "quantumclifford",
)
JAX_TERMS = (
    "jax",
    "jnp",
    "jax.numpy",
    "jax_enable_x64",
    "x64_enabled",
    "jax.vmap",
    "jax.grad",
    "jax.jacfwd",
    "diffrax",
    "equinox",
    "flax",
    "optax",
    "jaxopt",
    "lineax",
    "jraph",
    "ott",
    "netket",
    "e3nn_jax",
)

DYNAMIC_TERMS = (
    "dynamic",
    "evolution",
    "transport",
    "holonomy",
    "path",
    "order",
    "order_gap",
    "noncommut",
    "channel",
    "generator",
    "gksl",
    "lindblad",
    "compression",
    "outward_record",
    "update",
    "time",
)

DOWNSTREAM_LOCK_TERMS = (
    "stacking",
    "flux",
    "xi",
    "phi0",
    "axis0",
    "fep",
    "holodeck",
    "gravity",
    "physics",
    "final_manifold",
    "manifold_admission",
)


def walk(obj: Any, path: str = ""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            next_path = f"{path}.{key}" if path else str(key)
            yield next_path, key, value
            yield from walk(value, next_path)
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            next_path = f"{path}[{idx}]"
            yield next_path, str(idx), value
            yield from walk(value, next_path)


def as_text(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, default=str).lower()


def values_for_keys(obj: Any, *needles: str) -> list[Any]:
    needles_l = tuple(n.lower() for n in needles)
    out: list[Any] = []
    for _, key, value in walk(obj):
        key_l = str(key).lower()
        if any(n in key_l for n in needles_l):
            out.append(value)
    return out


def has_key_or_text(obj: Any, *needles: str) -> bool:
    text = as_text(obj)
    keys = " ".join(str(key).lower() for _, key, _ in walk(obj))
    return any(n.lower() in text or n.lower() in keys for n in needles)


def nonempty(value: Any) -> bool:
    return value not in (None, "", [], {}, 0, False)


def has_any_nonempty_key(obj: Any, *needles: str) -> bool:
    return any(nonempty(value) for value in values_for_keys(obj, *needles))


def numeric_values(obj: Any, path_needles: tuple[str, ...] = ()) -> list[float]:
    found: list[float] = []
    for path, _, value in walk(obj):
        path_l = path.lower()
        if path_needles and not any(n in path_l for n in path_needles):
            continue
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            found.append(float(value))
    return found


def has_nonzero_delta(obj: Any, min_count: int = 1) -> tuple[bool, int]:
    vals = numeric_values(obj, ("ablation", "delta", "gap", "drop"))
    count = sum(1 for value in vals if abs(value) > 1e-12)
    if count < min_count:
        signals = numeric_values(obj, ("signal",))
        controls = numeric_values(obj, ("control",))
        signal_count = sum(1 for value in signals if abs(value) > 1e-12)
        control_floor = max((abs(value) for value in controls), default=0.0)
        separated_signal_count = sum(1 for value in signals if abs(value) > control_floor + 1e-12)
        count = max(count, signal_count, separated_signal_count)
    return count >= min_count, count


def site_ladder(obj: Any) -> tuple[bool, str]:
    if has_any_nonempty_key(obj, "native_scale") and has_key_or_text(
        obj,
        "native_scale_rows_pass",
        "native_scale_not_universal_qubit_ladder",
        "native_scale_name",
    ):
        return True, "explicit native scale rows present"
    vals = numeric_values(obj, ("site_counts", "scales", "scale", "max_sites", "qubit"))
    ints = {int(round(v)) for v in vals if abs(v - round(v)) < 1e-9}
    if {8, 16, 32, 64}.issubset(ints):
        return True, "legacy bounded site-budget ladder present"
    if any(v >= 64 for v in vals) and has_key_or_text(obj, "resource_blocker", "scale_blocker"):
        return True, "max >=64 plus explicit resource blocker"
    blocker = values_for_keys(obj, "resource_blocker", "scale_blocker")
    if any(isinstance(v, str) and v.strip() for v in blocker):
        return True, "explicit resource blocker"
    return False, f"found scale values {sorted(ints)[:12]}"


def count_terms(obj: Any, terms: tuple[str, ...]) -> int:
    text = as_text(obj)
    return sum(1 for term in terms if term.lower() in text)


def load_bearing_tools(obj: Any) -> set[str]:
    tools: set[str] = set()
    for path, key, value in walk(obj):
        path_l = path.lower()
        key_l = str(key).lower()
        value_l = str(value).lower()
        if "tool_integration_depth" in path_l or "tool_manifest" in path_l:
            if "load_bearing" in value_l:
                tools.add(key_l)
        if key_l in {"actual_tools_used", "required_tools", "proof_surfaces_used"}:
            if isinstance(value, list):
                tools.update(str(v).lower() for v in value)
    aliases = {
        "torch_geometric": "pyg",
        "pytorch": "torch",
        "jax.numpy": "jax",
        "jnp": "jax",
        "gudhi": "gudhi",
        "toponetx": "toponetx",
    }
    return {aliases.get(t, t) for t in tools}


def downstream_locked(obj: Any) -> tuple[bool, list[str]]:
    text = as_text(values_for_keys(obj, "blocked_consumers", "downstream_blocks", "claim_ceiling"))
    found = [term for term in DOWNSTREAM_LOCK_TERMS if term in text]
    return len(found) >= 4, found


def backend_parity(obj: Any) -> dict[str, Any]:
    if isinstance(obj, dict) and isinstance(obj.get("backend_parity"), dict):
        return obj["backend_parity"]
    return {}


def parity_row_ok(row: dict[str, Any]) -> bool:
    if not row:
        return False
    if row.get("present") is not True or row.get("pass") is not True:
        return False
    dynamic_delta = row.get("dynamic_transport_max_delta")
    entropy_delta = row.get("entropy_readout_max_delta")
    if isinstance(dynamic_delta, (int, float)) and isinstance(entropy_delta, (int, float)):
        dynamic_tol = float(row.get("dynamic_transport_tolerance", 1.0e-8))
        entropy_tol = float(row.get("entropy_readout_tolerance", 5.0e-8))
        peps_delta = row.get("peps_virtual_carrier_max_delta")
        peps_ok = True
        if isinstance(peps_delta, (int, float)):
            peps_tol = float(row.get("peps_virtual_carrier_tolerance", 1.0e-8))
            peps_ok = float(peps_delta) <= peps_tol
        side_delta = row.get("geometry_side_witness_max_delta")
        side_ok = True
        if isinstance(side_delta, (int, float)):
            side_tol = float(row.get("geometry_side_witness_tolerance", 1.0e-8))
            side_ok = float(side_delta) <= side_tol
        topology_delta = row.get("topology_signature_max_delta")
        topology_ok = True
        if isinstance(topology_delta, (int, float)):
            topology_tol = float(row.get("topology_signature_tolerance", 1.0e-8))
            topology_ok = float(topology_delta) <= topology_tol
        return float(dynamic_delta) <= dynamic_tol and float(entropy_delta) <= entropy_tol and peps_ok and side_ok and topology_ok
    return isinstance(row.get("max_delta"), (int, float)) and float(row["max_delta"]) <= 1.0e-8


def detect_profile(path: Path, data: Any, requested: str) -> str:
    if requested != "auto":
        return requested
    name = path.name.lower()
    text = as_text(data)
    has_dual_contract = "comparison_contract" in text and "torch_pass" in text and "jax_pass" in text
    if "dual_backend" in name or has_dual_contract:
        return "dual_backend"
    if ("_jax_" in name or name.endswith("_jax_probe_results.json")) and "gstruct" not in name and "g_structure" not in name:
        return "jax_geometry"
    if "gstruct" in name or "g_structure" in name or "geometry" in name or "geom_" in name:
        return "geometry_full"
    if "jax" in name or '"backend": "jax"' in text:
        return "jax_geometry"
    return "layer_full"


class ReceiptCheck:
    def __init__(self, path: Path, profile: str, data: Any):
        self.path = path
        self.profile = profile
        self.data = data
        self.passed: list[str] = []
        self.failed: list[str] = []
        self.warnings: list[str] = []

    def require(self, name: str, ok: bool, detail: str = ""):
        row = name if not detail else f"{name}: {detail}"
        if ok:
            self.passed.append(name)
        else:
            self.failed.append(row)

    def warn(self, name: str, ok: bool, detail: str = ""):
        if not ok:
            self.warnings.append(name if not detail else f"{name}: {detail}")

    def common(self):
        all_pass_vals = values_for_keys(self.data, "all_pass")
        self.require("run_passed", any(v is True for v in all_pass_vals), "no true all_pass field")
        self.require("identity", has_any_nonempty_key(self.data, "sim_id", "object_id", "name"), "needs explicit sim_id/name/object_id")
        fm = has_any_nonempty_key(self.data, "finite_map")
        dom = has_any_nonempty_key(self.data, "domain")
        cod = has_any_nonempty_key(self.data, "codomain", "codomain_or_output", "output_space")
        self.require("finite_map_domain_codomain", fm and dom and cod, f"finite_map={fm} domain={dom} codomain={cod}")
        controls = has_any_nonempty_key(self.data, "controls", "control", "negatives", "negatives_run", "kill_conditions")
        self.require("controls_or_negatives", controls, "needs removal/scramble/negative controls")
        locked, found = downstream_locked(self.data)
        self.require("downstream_locked", locked, f"locks={found}")
        tools = load_bearing_tools(self.data)
        self.require("tool_manifest_load_bearing", len(tools) >= 3, f"tools={sorted(tools)}")

    def root_constraints(self):
        text = as_text(self.data)
        f01 = "f01" in text or "finite distinguish" in text or "finite_carrier" in text or "finite carrier" in text
        n01 = "n01" in text or "noncommut" in text or "order_sensitive" in text or "order gap" in text or "order_gap" in text
        self.require("root_constraints_F01_N01", f01 and n01, f"F01={f01} N01={n01}")

    def layer_full(self):
        self.common()
        self.root_constraints()
        self.require(
            "primary_backend_spinor_or_density",
            has_key_or_text(
                self.data,
                "jax",
                "julia",
                "pepskit",
                "tensorkit",
                "spinor_state",
                "spinor-derived density",
                "carrier tensor",
            ),
            "needs JAX- or Julia-family primary spinor/density/carrier evidence",
        )
        network_count = count_terms(self.data, NETWORK_TERMS)
        self.require("non_dense_network_views_MPS_PEPS2D_PEPS3D", network_count == len(NETWORK_TERMS), f"{network_count}/3 views present")
        self.require("peps3d_carrier_anchor", has_key_or_text(self.data, "peps3d", "quimb.tensor.peps3d", "finite spinor-network carrier anchor"), "needs actual PEPS3D-like carrier anchor")
        scale_ok, scale_detail = site_ladder(self.data)
        self.require("native_scale_or_bounded_resource_blocker", scale_ok, scale_detail)
        self.require("dynamic_geometry_surface", count_terms(self.data, DYNAMIC_TERMS) >= 3, "needs transport/path/order/channel/update evidence")
        qit_count = count_terms(self.data, QIT_TERMS)
        self.require("qit_entropy_family", qit_count >= 4, f"{qit_count} entropy/correlation terms")
        ab_ok, ab_count = has_nonzero_delta(self.data, min_count=3)
        self.require("numeric_nonvacuous_ablations", ab_ok, f"{ab_count} nonzero ablation/drop/gap values")
        tools = load_bearing_tools(self.data)
        proof_ok = bool(tools.intersection(PROOF_TERMS)) and bool(tools.intersection(PRIMARY_BACKEND_TOOLS))
        geom_ok = len(tools.intersection(GEOMETRY_TOOLS)) >= 4
        self.require("proof_and_geometry_tool_depth", proof_ok and geom_ok, f"tools={sorted(tools)}")
        parity = backend_parity(self.data)
        shared = parity.get("shared_carrier", {}) if isinstance(parity.get("shared_carrier"), dict) else {}
        target = parity.get("target_specific", {}) if isinstance(parity.get("target_specific"), dict) else {}
        shared_ok = (
            parity_row_ok(shared)
            and "shared" in str(shared.get("scope", "")).lower()
        )
        target_declared = "present" in target and "parity_level" in parity
        target_ok = parity_row_ok(target)
        self.require("shared_carrier_jax_parity_present", shared_ok, f"shared={shared}")
        self.require("target_specific_jax_parity_declared", target_declared, f"parity_level={parity.get('parity_level')}")
        self.require("target_specific_numeric_jax_parity", target_ok, f"target={target}")
        self.warn(
            "target_specific_jax_parity_partial",
            bool(target.get("complete_target_internal_jax_mirror")),
            f"unmirrored={target.get('unmirrored_target_internals', [])}",
        )

    def geometry_full(self):
        self.common()
        self.require("known_value_or_invariant_checks", has_any_nonempty_key(self.data, "known_value_checks", "invariant", "tool_certificates", "smt_certificates"), "needs known math checks/certificates")
        neg_ok = has_any_nonempty_key(self.data, "negatives", "negatives_run", "kill_conditions")
        ab_ok, ab_count = has_nonzero_delta(self.data, min_count=1)
        self.require("negative_or_ablation_kills_signature", neg_ok or ab_ok, f"negatives={neg_ok} nonzero_deltas={ab_count}")
        tools = load_bearing_tools(self.data)
        self.require("proof_or_exact_surface", bool(tools.intersection(PROOF_TERMS)) or has_key_or_text(self.data, "unsat", "exact"), f"tools={sorted(tools)}")
        self.require("full_representation_or_resource_note", has_key_or_text(self.data, "full faithful", "full dimension", "resource_note", "scale", "seeds", "site_counts"), "needs scale/full-representation statement")
        root_text = as_text(self.data)
        aligned = "f01" in root_text and ("n01" in root_text or "noncommut" in root_text or "order" in root_text)
        self.warn("not_yet_bound_to_two_root_constraints", aligned, "ok for standalone math, blocker before manifold use")
        embedded = has_key_or_text(self.data, "spinor_network", "peps3d", "mps", "peps2d", "spinor_state")
        self.warn("not_yet_embedded_as_spinor_network_carrier", embedded, "standalone geometry still needs carrier embedding before layer stacking")

    def jax_geometry(self):
        self.common()
        self.require("jax_backend_x64", has_key_or_text(self.data, "jax", "x64_enabled", "jax_enable_x64", "complex128"), "needs JAX x64 evidence")
        self.require("jax_transform_used", has_key_or_text(self.data, "jax.vmap", "jax.grad", "jax.jacfwd", "vmap", "grad", "jacfwd", "jit"), "needs JAX transform/autodiff/vectorization evidence where meaningful")
        self.require("known_value_or_invariant_checks", has_any_nonempty_key(self.data, "known_value_checks", "invariant", "smt_certificates"), "needs known math checks")
        self.require("controls_or_kill_conditions", has_any_nonempty_key(self.data, "kill_conditions", "negatives", "controls"), "needs JAX-side controls")
        host_numpy_claim = "numpy is host-side" in as_text(self.data) or "numpy\": \"supportive" in as_text(self.data)
        self.warn("host_numpy_only_supportive", host_numpy_claim or "numpy" not in as_text(self.data), "host NumPy must not be claim-bearing")

    def dual_backend(self):
        self.common()
        self.require("torch_and_jax_paths", has_key_or_text(self.data, "torch_pass", "torch") and has_key_or_text(self.data, "jax_pass", "jax"), "needs both backends")
        deltas = numeric_values(self.data, ("delta", "max_rho_delta", "max_entropy_delta", "gradient_delta"))
        small_delta = bool(deltas) and max(abs(v) for v in deltas if math.isfinite(v)) < 1e-5
        self.require("backend_agreement_delta", small_delta, f"max_delta={max(deltas) if deltas else 'missing'}")
        self.require("dynamic_or_state_evolution", count_terms(self.data, DYNAMIC_TERMS) >= 2, "needs state/dynamics comparison")
        self.require("same_controls", has_key_or_text(self.data, "same_controls", "kill_conditions", "controls"), "needs same controls across backends")

    def run(self) -> dict[str, Any]:
        getattr(self, self.profile)()
        total = len(self.passed) + len(self.failed)
        score = round(100.0 * len(self.passed) / total, 1) if total else 0.0
        return {
            "path": str(self.path),
            "profile": self.profile,
            "execution_pass": not self.failed,
            "score": score,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "next_repair": self.next_repair(),
        }

    def next_repair(self) -> str:
        if not self.failed:
            if self.warnings:
                return f"passes execution-depth profile; address warning: {self.warnings[0]}"
            return "passes execution-depth profile; no promotion implied"
        first = self.failed[0].split(":", 1)[0]
        return f"repair first failed criterion: {first}"


def expand_inputs(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            paths.extend(Path(m) for m in matches)
        else:
            paths.append(Path(pattern))
    deduped = sorted({p for p in paths})
    return [p for p in deduped if p.exists()]


def validate_files(paths: list[Path], profile: str) -> dict[str, Any]:
    results = []
    missing_by_criterion: dict[str, int] = {}
    warnings_by_type: dict[str, int] = {}
    for path in paths:
        data = json.loads(path.read_text())
        resolved_profile = detect_profile(path, data, profile)
        check = ReceiptCheck(path, resolved_profile, data).run()
        for failed in check["failed"]:
            criterion = failed.split(":", 1)[0]
            missing_by_criterion[criterion] = missing_by_criterion.get(criterion, 0) + 1
        for warning in check["warnings"]:
            criterion = warning.split(":", 1)[0]
            warnings_by_type[criterion] = warnings_by_type.get(criterion, 0) + 1
        results.append(check)

    profile_counts: dict[str, dict[str, int]] = {}
    for result in results:
        row = profile_counts.setdefault(result["profile"], {"total": 0, "pass": 0, "fail": 0})
        row["total"] += 1
        if result["execution_pass"]:
            row["pass"] += 1
        else:
            row["fail"] += 1

    return {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "kind": "deep_sim_execution_audit",
        "not_formal_admission": True,
        "claim_boundary": "Pass means this receipt satisfied the selected execution-depth profile only. It does not admit a manifold layer, select a G-structure, open stacking/order claims, or unlock Axis0/FEP/flux/physics.",
        "input_count": len(results),
        "execution_pass_count": sum(1 for r in results if r["execution_pass"]),
        "execution_fail_count": sum(1 for r in results if not r["execution_pass"]),
        "warning_total": sum(len(r["warnings"]) for r in results),
        "profile_counts": profile_counts,
        "missing_by_criterion": dict(sorted(missing_by_criterion.items())),
        "warnings_by_type": dict(sorted(warnings_by_type.items())),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="result JSON files or shell globs")
    parser.add_argument("--profile", default="auto", choices=["auto", "layer_full", "geometry_full", "jax_geometry", "dual_backend"])
    parser.add_argument("--write-json", help="optional audit artifact path")
    parser.add_argument("--fail-on-warnings", action="store_true", help="exit nonzero when any receipt has warnings")
    parser.add_argument("--report-only", action="store_true", help="always exit 0 after reporting")
    args = parser.parse_args()

    paths = expand_inputs(args.files)
    if not paths:
        print(json.dumps({"error": "no existing input files matched"}, indent=2))
        return 2

    report = validate_files(paths, args.profile)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.write_json:
        out = Path(args.write_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n")
    print(text)
    if args.report_only:
        return 0
    if args.fail_on_warnings and report["warning_total"] > 0:
        return 1
    return 0 if report["execution_fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
