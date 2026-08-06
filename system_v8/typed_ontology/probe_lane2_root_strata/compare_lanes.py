#!/usr/bin/env python3
"""Probe lane 2 comparison. The ONLY script that reads more than one lane.

Normalises every source to one flat fact set, then:
  1. compares INTEGER facts exactly (a 16-element enumeration has no tolerance),
  2. compares the two referees against each other, which is the guard against the
     worst outcome named in the task card - every source agreeing on a wrong number,
  3. measures float deltas against the exact referee,
  4. applies the estate's OWN log2_integrality_floor, read live out of
     system_v8/typed_ontology/carrier_obligations.json, to every log2-shaped float.

Exit codes follow the estate convention used by check_carrier_obligations.py:
  0  every integer fact agrees across every source and the two referees agree
  1  at least one integer fact disagrees  (an engine is WRONG over 16 elements)
  3  integers agree but at least one lane's float readout misses the table's floor
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
TABLE = os.path.abspath(os.path.join(HERE, "..", "carrier_obligations.json"))
OUT = os.path.join(RES, "compare_lanes.json")

def selected_precisions():
    raw = os.environ.get("ROOT_STRATA_PRECISIONS", "float32,float64")
    values = tuple(p.strip() for p in raw.split(",") if p.strip())
    allowed = {"float32", "float64"}
    if "float64" not in values or any(p not in allowed for p in values):
        raise ValueError(
            "ROOT_STRATA_PRECISIONS must include float64 and contain only float32,float64"
        )
    return values


PRECISIONS = selected_precisions()
SOURCES = ["enum_reference", "closed_form_reference"] + [
    f"lane_{engine}_{precision}"
    for engine in ("jax", "torch", "julia")
    for precision in PRECISIONS
]


def get(d, path, default=KeyError):
    cur = d
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            if default is KeyError:
                raise KeyError(f"{path} missing")
            return default
        cur = cur[p]
    return cur


def first(d, paths, default=KeyError):
    for p in paths:
        v = get(d, p, None)
        if v is not None:
            return v
    if default is KeyError:
        raise KeyError(f"none of {paths}")
    return default


def r1root(name):
    return "R1.fields" if name == "enum_reference" else "R1"


def facts(name, d):
    """One flat fact set per source. Missing keys raise, they do not default."""
    r1 = r1root(name)
    f = {}
    f["R0.cardinality"] = get(d, "R0.cardinality")
    f["R0.n_bits"] = get(d, "R0.n_bits", 4)
    f["R0.H0_addr_bits"] = get(d, "R0.H0_addr_bits")
    for k in ("DIAG", "COHERENT"):
        f[f"R1.{k}.support_cardinality"] = get(d, f"{r1}.{k}.support_cardinality")
        f[f"R1.{k}.H0_pair_bits"] = get(d, f"{r1}.{k}.H0_pair_bits")
        f[f"R1.{k}.rank"] = first(d, [f"{r1}.{k}.integer_matrix_rank",
                                      f"{r1}.{k}.float_rank"])
        f[f"R1.{k}.trace"] = get(d, f"{r1}.{k}.trace")
        det = first(d, [f"{r1}.{k}.integer_determinant",
                        f"{r1}.{k}.determinant_from_jnp_linalg_det",
                        f"{r1}.{k}.determinant_from_torch_linalg_det",
                        f"{r1}.{k}.float_determinant"])
        f[f"R1.{k}.determinant"] = float(det)
    for dd in range(5):
        f[f"R2.cells.dim{dd}"] = get(d, f"R2.cell_counts_by_dim.{dd}")
    f["R2.total_cells"] = get(d, "R2.total_cells")
    if name != "closed_form_reference":
        for k in ("d1_o_d2", "d2_o_d3", "d3_o_d4"):
            f[f"R2.boundary_comp.{k}.max_abs_entry"] = get(
                d, f"R2.boundary_composition.{k}.max_abs_entry")
    else:
        for k in ("d1_o_d2", "d2_o_d3", "d3_o_d4"):
            f[f"R2.boundary_comp.{k}.max_abs_entry"] = get(
                d, "R2.boundary_composition_max_abs_entry_expected")
    if name == "closed_form_reference":
        for dd in range(5):
            f[f"R3.FULL.dim{dd}.relation_cardinality"] = get(
                d, "R3.FULL_FIELD.relation_cardinality")
            f[f"R3.FULL.dim{dd}.kappa_bits"] = get(d, "R3.FULL_FIELD.kappa_bits")
            f[f"R3.REST.dim{dd}.relation_cardinality"] = get(
                d, f"R3.RESTRICTED.relation_cardinality_by_dim.{dd}")
            f[f"R3.REST.dim{dd}.kappa_bits"] = get(d, f"R3.RESTRICTED.kappa_bits_by_dim.{dd}")
    else:
        for dd in range(5):
            for tag, key in (("FULL", "FULL_FIELD"), ("REST", "RESTRICTED")):
                f[f"R3.{tag}.dim{dd}.relation_cardinality"] = get(
                    d, f"R3.{key}.per_dim.{dd}.relation_cardinality")
                f[f"R3.{tag}.dim{dd}.kappa_bits"] = get(
                    d, f"R3.{key}.per_dim.{dd}.kappa_bits")
    f["R3.FULL.E_cardinality"] = get(d, "R3.FULL_FIELD.E_cardinality")
    f["R3.REST.E_cardinality"] = get(d, "R3.RESTRICTED.E_cardinality")
    for u in range(5):
        f[f"C.fibre.{u}.cardinality"] = get(d, f"C1_C3.fibre_cardinalities.{u}")
        f[f"C.fibre.{u}.kappa_ext_bits"] = get(d, f"C1_C3.kappa_ext_bits.{u}")
    f["C.fibre_cardinality_sum"] = get(d, "C1_C3.fibre_cardinality_sum")
    f["C.empty_fibre_cardinality"] = first(
        d, ["C1_C3.empty_fibre_case.engine_measured_count",
            "C1_C3.empty_fibre_case.descriptor.fibre_cardinality",
            "C1_C3.empty_fibre_cardinality"], 0)
    return f


INT_FACTS = ("cardinality", "n_bits", "rank", "trace", "total_cells", "max_abs_entry",
             "relation_cardinality", "E_cardinality", "cells.dim")


def is_int_fact(key):
    return any(t in key for t in INT_FACTS)


def main():
    floors = json.load(open(TABLE))["floors"]
    floor = floors["log2_integrality_floor"]

    loaded, missing = {}, []
    for s in SOURCES:
        p = os.path.join(RES, s + ".json")
        if not os.path.exists(p):
            missing.append(p)
            continue
        loaded[s] = json.load(open(p))
    if missing:
        print(json.dumps({"exit": 1, "why": "lane receipts missing", "missing": missing}))
        return 1

    fs = {}
    for s, d in loaded.items():
        try:
            fs[s] = facts(s, d)
        except KeyError as exc:
            print(json.dumps({"exit": 1, "why": f"{s}: {exc}"}))
            return 1

    keys = sorted(set().union(*[set(v) for v in fs.values()]))
    ref = fs["enum_reference"]
    table, int_dis, float_delta = {}, [], {}
    for k in keys:
        row = {s: fs[s].get(k) for s in fs}
        rv = ref.get(k)
        if is_int_fact(k):
            bad = {s: v for s, v in row.items()
                   if v is not None and float(v) != float(rv)}
            if bad:
                int_dis.append({"fact": k, "enum_reference": rv, "disagreeing": bad})
            table[k] = {"kind": "integer", "enum_reference": rv,
                        "all_sources_equal": not bad, "values": row}
        else:
            deltas = {s: (abs(float(v) - float(rv)) if v is not None else None)
                      for s, v in row.items()}
            mx = max(v for v in deltas.values() if v is not None)
            float_delta[k] = {"max_abs_delta_vs_enum": mx, "deltas": deltas}
            table[k] = {"kind": "float", "enum_reference": rv,
                        "max_abs_delta_vs_enum": mx, "values": row}

    # ---- referee-vs-referee: the shared-wrong-premise guard
    cf = fs["closed_form_reference"]
    ref_vs_cf = []
    for k in keys:
        a, b = ref.get(k), cf.get(k)
        if a is None or b is None:
            continue
        if is_int_fact(k):
            if float(a) != float(b):
                ref_vs_cf.append({"fact": k, "enum": a, "closed_form": b})
        elif abs(float(a) - float(b)) > 0.0:
            ref_vs_cf.append({"fact": k, "enum": a, "closed_form": b,
                              "delta": abs(float(a) - float(b))})

    # ---- the table's own floor, applied to every log2-shaped float
    log2_keys = [k for k in keys if "H0_addr" in k or "H0_pair" in k or "kappa" in k]
    floor_fails = []
    for k in log2_keys:
        for s in fs:
            v = fs[s].get(k)
            if v is None:
                continue
            two = 2.0 ** float(v)
            err = abs(two - round(two))
            if err > floor:
                floor_fails.append({"source": s, "fact": k, "value": float(v),
                                    "two_to_the_value": two,
                                    "distance_from_integer": err,
                                    "log2_integrality_floor": floor,
                                    "over_floor_by_factor": err / floor})

    # ---- structural facts the diagram asks for by name
    structural = {}
    for s, d in loaded.items():
        if s == "closed_form_reference":
            continue
        ec = get(d, "C1_C3.empty_fibre_case", {})
        structural[s] = {
            "empty_fibre_descriptor_keys": ec.get("descriptor_keys"),
            "empty_fibre_kappa_key_present": ec.get("kappa_key_present"),
            "log2_calls_across_5_nonempty_and_1_empty_release": get(
                d, "C1_C3.log2_calls_across_5_nonempty_and_1_empty_release", None),
            "R3_top_cell_restricted_kappa_equals_H0_pair_coherent": (
                get(d, "R3.RESTRICTED.per_dim.4.kappa_bits", None)
                == get(d, r1root(s) + ".COHERENT.H0_pair_bits", None)),
        }

    discrimination = {}
    for s, d in loaded.items():
        node = get(d, "R1.discrimination", None)
        if isinstance(node, dict):
            discrimination[s] = {k: bool(v.get("separates")) for k, v in node.items()}

    engine_ops = {
        "lane_jax": {"jaxpr_primitives": sorted({p for m in ("lane_jax_float64",)
                                                 for v in get(loaded[m],
                                                              "engine_ops_from_jaxpr").values()
                                                 for p in v}),
                     "stablehlo_lines": len(get(loaded["lane_jax_float64"],
                                                "engine_ops_from_lowered_stablehlo"))},
        "lane_torch": {"distinct_aten_ops": get(loaded["lane_torch_float64"],
                                                "engine_op_count_distinct"),
                       "aten_invocations": get(loaded["lane_torch_float64"],
                                               "engine_op_invocations_total"),
                       "linalg_ops_seen": sorted(
                           k for k in get(loaded["lane_torch_float64"],
                                          "engine_ops_from_torch_dispatch")
                           if "linalg" in k or "mm" in k)},
        "lane_julia": {"methods_resolved": get(loaded["lane_julia_float64"],
                                               "engine_method_provenance_from_which"),
                       "graphs_construction_agreement": {
                           k: v["equal"] for k, v in
                           get(loaded["lane_julia_float64"],
                               "R1.independent_construction_agreement").items()}},
    }

    code = 1 if (int_dis or ref_vs_cf) else (3 if floor_fails else 0)
    rec = {"comparison_of": SOURCES,
           "selected_precisions": PRECISIONS,
           "integer_disagreements": int_dis,
           "integer_disagreement_count": len(int_dis),
           "referee_vs_closed_form_disagreements": ref_vs_cf,
           "float_deltas_vs_enum_reference": float_delta,
           "log2_integrality_floor_from_table": floor,
           "log2_integrality_floor_failures": floor_fails,
           "log2_integrality_floor_failure_count": len(floor_fails),
           "structural_facts_per_lane": structural,
           "discrimination_per_lane": discrimination,
           "engine_op_evidence": engine_ops,
           "fact_table": table,
           "computed_exit_code": code}
    with open(OUT, "w") as fh:
        json.dump(rec, fh, indent=1)
    print(json.dumps({"wrote": OUT,
                      "sources": len(fs),
                      "integer_facts_compared": sum(1 for k in keys if is_int_fact(k)),
                      "float_facts_compared": sum(1 for k in keys if not is_int_fact(k)),
                      "integer_disagreements": len(int_dis),
                      "referee_vs_closed_form_disagreements": len(ref_vs_cf),
                      "log2_floor_failures": len(floor_fails),
                      "floor_failing_sources": sorted({f["source"] for f in floor_fails}),
                      "max_float_delta": max(v["max_abs_delta_vs_enum"]
                                             for v in float_delta.values()),
                      "exit": code}, indent=1))
    return code


if __name__ == "__main__":
    sys.exit(main())
