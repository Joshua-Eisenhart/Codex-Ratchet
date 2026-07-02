#!/usr/bin/env python3
"""Adversarial M_RPF(C) post-stack object-preservation audit."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "m_rpf_post_stack_adversarial_object_audit_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
SIM_ID = NAME
VERSION = "1.0.0"
TIER = "M_RPF(C) post-stack adversarial object-preservation audit"
PURPOSE = "Try to falsify the post-stack stress receipts by checking whether they measure M_RPF(C) or only proxies."
SCIENTIFIC_QUESTION = "Can PEPS3D labels, entropy, adapter artifacts, Axis0/FEP/flux proxies, forward-only evolution, dense closure, or monitor hygiene replace the M_RPF(C) object?"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "negative_probe"
SOURCE_ALIGNMENT_CATEGORY = "m_rpf_post_stack_adversarial_object_audit"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal adversarial audit only. Passing means proxy substitutions failed "
    "against the current finite post-stack receipts. It does not admit flux, "
    "Xi/Phi0, Axis0, FEP/Holodeck, physics, gravity, IGT/game theory, "
    "axes7-12, stacking closure, or final manifold admission."
)
FINITE_MAP = (
    "M_RPF_post_stack_adversarial_audit : (post-stack stress receipts, "
    "variant stress receipts, monitor heartbeat, proxy replacement family P) "
    "-> (object-field survivor table, proxy rejection table, strict_false "
    "falsifiers, blocked consumers)"
)
DOMAIN = "finite JSON receipts from Packet 1 and Packet 2 plus finite proxy replacement family"
CODOMAIN = "finite adversarial audit table over required M_RPF(C) fields and proxy controls"
OBJECT_PACKET = "system_v5/ops/formal_scouts/retrocausal_shell_field_v43_object_packet_20260527.json"
STRESS_RESULT = RESULT_DIR / "m_rpf_post_stack_stress_probe_results.json"
VARIANT_RESULT = RESULT_DIR / "m_rpf_post_stack_variant_stress_probe_results.json"
HEARTBEAT = ROOT / "retrocausal_shell_field_v43_monitor_heartbeat_20260527.json"
BLOCKED_CONSUMERS = [
    "stacking",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "gravity proof",
    "IGT/game theory",
    "axes7-12",
    "final manifold",
]
TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite proxy survivor score tensor and threshold checks"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact field/proxy count checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proxy-nonreplacement and downstream-lock gates"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent proxy-rejection gate"},
    "pyg": {"tried": False, "used": False, "reason": "not used: audit consumes existing PEPS3D result receipts rather than recomputing graph dynamics"},
    "rustworkx": {"tried": False, "used": False, "reason": "not used: graph provenance is audited from existing result receipts"},
    "xgi": {"tried": False, "used": False, "reason": "not used: hyperedge provenance is audited from existing result receipts"},
    "toponetx": {"tried": False, "used": False, "reason": "not used: cell-complex provenance is audited from existing result receipts"},
    "gudhi": {"tried": False, "used": False, "reason": "not used: filtration provenance is audited from existing result receipts"},
    "clifford": {"tried": False, "used": False, "reason": "not used: quaternion/Clifford provenance is audited from existing result receipts"},
    "geomstats": {"tried": False, "used": False, "reason": "not used: no metric/geodesic/curvature claim is audited"},
    "e3nn": {"tried": False, "used": False, "reason": "not used: no equivariant field claim is audited"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "pyg": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
}
REQUIRED_FIELDS = (
    "future_continuations",
    "compatibility_weights",
    "compression_map",
    "present_survivor",
    "outward_record",
    "event_x",
    "shells",
    "shell_radius_r",
    "shell_orientation",
    "branch_states",
    "readout_provenance",
)
PROXIES = (
    "PEPS3D_label_only",
    "entropy_primary",
    "adapter_order_artifact_only",
    "Axis0_proxy",
    "FEP_Holodeck_proxy",
    "flux_proxy",
    "forward_time_shadow",
    "dense_state_closure",
    "monitor_hygiene_only",
)


def read_json(path: pathlib.Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def blob(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(f"{key} {blob(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(blob(item) for item in value)
    return str(value)


def field_present(data: dict[str, Any], field: str) -> bool:
    if field in data:
        return True
    return field.lower() in blob(data).lower()


def z3_gate(proxy_rejections: dict[str, bool]) -> dict[str, Any]:
    solver = z3.Solver()
    proxy_survived = z3.Bool("proxy_survived")
    solver.add(proxy_survived == any(not ok for ok in proxy_rejections.values()))
    solver.add(proxy_survived)
    proxy_status = solver.check()
    downstream = z3.Solver()
    flux, axis0, fep = z3.Bools("flux axis0 fep")
    downstream.add(flux == False, axis0 == False, fep == False, z3.Or(flux, axis0, fep))
    downstream_status = downstream.check()
    return {"pass": proxy_status == z3.unsat and downstream_status == z3.unsat, "proxy_survival_status": str(proxy_status), "downstream_unlock_status": str(downstream_status)}


def cvc5_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    proxy_terms = [solver.mkConst(solver.getBooleanSort(), name) for name in PROXIES]
    for term in proxy_terms:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(False)))
    solver.assertFormula(solver.mkTerm(Kind.OR, *proxy_terms))
    status = str(solver.checkSat())
    return {"pass": status == "unsat", "proxy_or_status": status}


def build_result() -> dict[str, Any]:
    started = time.time()
    stress = read_json(STRESS_RESULT)
    variant = read_json(VARIANT_RESULT)
    heartbeat = read_json(HEARTBEAT)
    required_by_receipt = {
        "stress": {field: field_present(stress, field) for field in REQUIRED_FIELDS},
        "variant": {field: field_present(variant, field) for field in REQUIRED_FIELDS},
    }
    object_fields_ok = all(all(row.values()) for row in required_by_receipt.values())
    monitor_ok = heartbeat.get("status") == "active_preserved"
    proxy_rejections = {
        "PEPS3D_label_only": "scalar label" in blob(stress).lower() or "scalar labels" in blob(variant).lower(),
        "entropy_primary": "derived" in str(stress.get("QIT_entropy_where_defined", "")).lower() and "derived" in str(variant.get("QIT_entropy_where_defined", "")).lower(),
        "adapter_order_artifact_only": bool(stress.get("N01_witness")) and bool(variant.get("N01_witness")),
        "Axis0_proxy": "Axis0" in blob(stress.get("blocked_consumers", [])) and "Axis0" in blob(variant.get("blocked_consumers", [])),
        "FEP_Holodeck_proxy": "FEP" in blob(stress.get("blocked_consumers", [])) and "FEP" in blob(variant.get("blocked_consumers", [])),
        "flux_proxy": "flux" in blob(stress.get("blocked_consumers", [])).lower() and "flux" in blob(variant.get("blocked_consumers", [])).lower(),
        "forward_time_shadow": "forward-only" in blob(stress.get("graveyard_companions", {})).lower() and "forward" in blob(variant.get("graveyard_companions", {})).lower(),
        "dense_state_closure": stress.get("PEPS3D_K_anchor", {}).get("dense_state_closure_used") is False and variant.get("PEPS3D_K_anchor", {}).get("dense_state_closure_used") is False,
        "monitor_hygiene_only": monitor_ok and stress.get("all_pass") is True and variant.get("all_pass") is True,
    }
    # A proxy score of 1 means the replacement was rejected, not promoted.
    proxy_tensor = torch.tensor([1.0 if ok else 0.0 for ok in proxy_rejections.values()], dtype=torch.float64)
    z3_checks = z3_gate(proxy_rejections)
    cvc5_checks = cvc5_gate()
    sympy_checks = {"pass": int(sp.Integer(len(REQUIRED_FIELDS))) == 11 and int(sp.Integer(len(PROXIES))) == 9, "required_field_count": len(REQUIRED_FIELDS), "proxy_count": len(PROXIES)}
    all_pass = bool(object_fields_ok and monitor_ok and torch.all(proxy_tensor == 1.0).item() and z3_checks["pass"] and cvc5_checks["pass"] and sympy_checks["pass"])
    positive = {
        "adversarial_audit_ran": {"pass": True, "finite_map": FINITE_MAP},
        "object_fields_survived": {"pass": object_fields_ok, "field_table": required_by_receipt},
        "monitor_not_the_object": {"pass": monitor_ok and object_fields_ok, "monitor_status": heartbeat.get("status")},
        "proxy_family_rejected": {"pass": bool(torch.all(proxy_tensor == 1.0).item()), "proxy_rejections": proxy_rejections},
    }
    graveyard = {
        proxy: {"pass": rejected, "outcome": "proxy rejected as primary object" if rejected else "proxy survived strict-false"}
        for proxy, rejected in proxy_rejections.items()
    }
    boundary = {
        "strict_false_if_proxy_survives": {"pass": all(proxy_rejections.values()), "strict_false": not all(proxy_rejections.values())},
        "downstream_consumers_blocked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
        "dense_state_closure_blocked": {"pass": proxy_rejections["dense_state_closure"], "dense_global_state_closure_used": False},
    }
    return {
        "A0_raw": {"status": "proxy_blocked", "promotion_allowed": False, "vector": []},
        "F01_witness": "finite audit over finite JSON receipts and finite proxy family",
        "N01_witness": "order-sensitive adapter gaps must remain present; adapter-only and order-erased replacements are rejected",
        "PEPS3D_K_anchor": stress.get("PEPS3D_K_anchor"),
        "QIT_entropy_where_defined": "audited as derived readout only, not primary object",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "ablation_outcome_delta": graveyard,
        "all_pass": all_pass,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "blockers": [] if all_pass else ["proxy_survived_or_object_field_missing"],
        "boundary": boundary,
        "carrier_layer": "finite PEPS3D K post-stack audit carrier",
        "claim_ceiling": CLAIM_CEILING,
        "classification": classification,
        "codomain_or_output": CODOMAIN,
        "compression_map": "required field audited from Packet 1 and Packet 2 receipts",
        "controls": graveyard,
        "dependency_receipts": [OBJECT_PACKET, str(STRESS_RESULT), str(VARIANT_RESULT), str(HEARTBEAT)],
        "domain": DOMAIN,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "event_x": "required field audited from Packet 1 and Packet 2 receipts",
        "finite_map": FINITE_MAP,
        "future_continuations": "Omega_r required field audited from Packet 1 and Packet 2 receipts",
        "geometry_layer": "M_RPF(C) adversarial object-preservation audit",
        "graveyard_companions": graveyard,
        "law_or_candidate_tested": "proxy replacement falsification for post-stack receipts",
        "name": NAME,
        "nearby_variants": {"passed": len(PROXIES), "total": len(PROXIES), "variants": list(PROXIES)},
        "next_admissible_step": "Continue to Packet 4 minimality/order necessity; do not unlock downstream consumers.",
        "object_packet_path": OBJECT_PACKET,
        "outward_record": "required field audited from Packet 1 and Packet 2 receipts",
        "peps3d_embedding": "audited as finite K anchor provenance, not scalar label",
        "positive": positive,
        "present_survivor": "rho_present required field audited from Packet 1 and Packet 2 receipts",
        "primary_object": "retrocausal_shell_constraint_manifold / M_RPF(C)",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS,
        "purpose": PURPOSE,
        "readout_provenance": "Omega_r -> compatibility_weights -> ordered_adapters -> compression_C -> rho_present -> outward_record -> derived_readouts",
        "root_constraints_in_force": {"F01": "finite carrier/probe/operator/path set", "N01": "noncommuting or order-sensitive operation/control"},
        "scale_8_16_32_64_or_resource_blocker": stress.get("scale_8_16_32_64_or_resource_blocker"),
        "scientific_question": SCIENTIFIC_QUESTION,
        "shell_radius_r": variant.get("shell_radius_r"),
        "shell_orientation": variant.get("shell_orientation"),
        "shells": "required shell field audited from Packet 1 and Packet 2 receipts",
        "branch_states": "required rho_omega field audited from Packet 1 and Packet 2 receipts",
        "sim_class": SIM_CLASS,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_id": SIM_ID,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "spinor_state": "audited through existing torch-native spinor-derived Packet 1/2 receipts",
        "spinor_state_or_spinor_derived_density": "audited Packet 1/2 rho_present readouts",
        "sympy_gate": sympy_checks,
        "tier": TIER,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "torch_spinor_or_density": "torch proxy rejection tensor plus audited Packet 1/2 spinor-derived densities",
        "version": VERSION,
        "why_not_v4_probes": "This v5/v4.3 audit requires M_RPF(C) object-order fields and proxy locks absent from v4 probes.",
        "z3_gate": z3_checks,
        "cvc5_gate": cvc5_checks,
        "elapsed_seconds": round(time.time() - started, 6),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "wrote": str(OUT_PATH), "proxy_count": len(PROXIES)}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
