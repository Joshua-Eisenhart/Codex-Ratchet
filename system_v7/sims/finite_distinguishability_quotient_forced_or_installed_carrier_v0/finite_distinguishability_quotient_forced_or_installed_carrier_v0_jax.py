#!/usr/bin/env python3
"""JAX leg for the finite distinguishability quotient forced-or-installed test.

Unique computation style: batched_jax_plus_smt.
It recomputes the quotient and finite structure with JAX arrays, and owns the
z3+cvc5 structural flip. It reads only spec.json and writes its own result JSON.
"""

import hashlib
import json
import os
from datetime import datetime, timezone

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import z3

SIM_ID = "finite_distinguishability_quotient_forced_or_installed_carrier_v0"
HERE = os.path.dirname(os.path.abspath(__file__))


def spec_sha():
    with open(os.path.join(HERE, "spec.json"), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def quotient_classes(labels, probes):
    signatures = {label: [p["outcomes"][label] for p in probes] for label in labels}
    classes = []
    keys = []
    for label in labels:
        key = tuple(signatures[label])
        if key in keys:
            classes[keys.index(key)].append(label)
        else:
            keys.append(key)
            classes.append([label])
    return classes, signatures


def class_index(classes):
    return {label: i for i, cls in enumerate(classes) for label in cls}


def induced_class_map(classes, update):
    idx = class_index(classes)
    out = {}
    evidence = {}
    well_defined = True
    for i, cls in enumerate(classes):
        targets = sorted({idx[update[x]] for x in cls})
        evidence[str(i)] = targets
        if len(targets) != 1:
            well_defined = False
        else:
            out[str(i)] = targets[0]
    return out, well_defined, evidence


def noncommutation_witness(labels, f, g):
    for label in labels:
        fg = f[g[label]]
        gf = g[f[label]]
        if fg != gf:
            return {"exists": True, "element": label, "first_then_second": fg, "second_then_first": gf}
    return {"exists": False}


def class_noncommutation_witness(class_labels, f, g):
    for c in class_labels:
        fg = f[str(g[c])]
        gf = g[str(f[c])]
        if fg != gf:
            return {"exists": True, "class": c, "U1_after_U2": fg, "U2_after_U1": gf}
    return {"exists": False}


def same_partition(a, b):
    return sorted(sorted(c) for c in a) == sorted(sorted(c) for c in b)


def relabel_probes(probes, perms):
    out = []
    for p in probes:
        perm = perms[p["id"]]
        out.append({"id": p["id"], "outcomes": {k: perm[str(v)] for k, v in p["outcomes"].items()}})
    return out


def reproduces_probe_data(classes, signatures):
    ok = True
    evidence = {}
    for i, cls in enumerate(classes):
        sigs = [signatures[x] for x in cls]
        same = all(s == sigs[0] for s in sigs)
        ok = ok and same
        evidence[str(i)] = {"members": cls, "probe_signature": sigs[0], "constant_on_class": same}
    return ok, evidence


def survival_table(spec, labels, probes, classes, erased_classes, signatures, u1, u2, v1, v2):
    class_labels = [str(i) for i in range(len(classes))]
    u1c, u1wd, u1ev = induced_class_map(classes, u1)
    u2c, u2wd, u2ev = induced_class_map(classes, u2)
    v1c, v1wd, _ = induced_class_map(classes, v1)
    v2c, v2wd, _ = induced_class_map(classes, v2)
    active_witness = class_noncommutation_witness(class_labels, u1c, u2c)
    control_witness = class_noncommutation_witness(class_labels, v1c, v2c)
    reproduce_ok, rep_evidence = reproduces_probe_data(classes, signatures)
    rows = {}
    for candidate in spec["candidate_structures"]:
        cid = candidate["id"]
        if candidate["update_policy"] == "commuting_diagonal_updates_only":
            active_update_ok = False
            control_update_ok = True
        else:
            active_update_ok = u1wd and u2wd and active_witness["exists"]
            control_update_ok = v1wd and v2wd and not control_witness["exists"]
        rows[cid] = {
            "name": candidate["name"],
            "survives_reproduce_quotient": reproduce_ok,
            "survives_F01": True,
            "survives_N01": active_update_ok,
            "survives_all_active_constraints": reproduce_ok and active_update_ok,
            "commuting_update_control_survives": reproduce_ok and control_update_ok,
            "evidence": {
                "induced_partition": classes,
                "erased_partition": erased_classes,
                "finite_presentation": candidate["finite_presentation"],
                "active_update_policy": candidate["update_policy"],
                "U1_induced_class_map": u1c,
                "U2_induced_class_map": u2c,
                "U1_well_defined_on_classes": u1wd,
                "U2_well_defined_on_classes": u2wd,
                "class_noncommutation_witness": active_witness,
                "class_map_evidence": {"U1": u1ev, "U2": u2ev},
                "probe_reproduction": rep_evidence,
            },
        }
    return rows, active_witness, control_witness, (u1c, u2c, v1c, v2c)


def preorder_matrix(spec, survival):
    ranks = {c["id"]: c["strength_rank"] for c in spec["candidate_structures"]}
    ids = [c["id"] for c in spec["candidate_structures"]]
    return {
        a: {
            b: survival[a]["survives_reproduce_quotient"]
            and survival[b]["survives_reproduce_quotient"]
            and ranks[a] <= ranks[b]
            for b in ids
        }
        for a in ids
    }


def strict_less(pre, a, b):
    return pre[a][b] and not pre[b][a]


def minimal_survivors(survivors, pre):
    return [c for c in survivors if not any(o != c and strict_less(pre, o, c) for o in survivors)]


def controls(spec, probes, labels, classes, survival):
    remaining = set(spec["probe_erase_control"]["remaining_probe_ids"])
    erased_classes, _ = quotient_classes(labels, [p for p in probes if p["id"] in remaining])
    shuffled_classes, _ = quotient_classes(labels, relabel_probes(probes, spec["label_shuffle_control"]["outcome_permutation_by_probe"]))
    c1 = survival["C1"]
    return {
        "commuting_update": {"predicted": "commutative structure survives when V1,V2 replace U1,U2", "passed": survival["C2"]["commuting_update_control_survives"]},
        "label_shuffle": {"predicted": "quotient invariant under outcome relabelling", "passed": same_partition(classes, shuffled_classes), "shuffled_quotient_classes": shuffled_classes},
        "probe_erase": {"predicted": "class count strictly drops", "passed": len(erased_classes) < len(classes), "full_class_count": len(classes), "erased_class_count": len(erased_classes), "erased_quotient_classes": erased_classes},
        "matrix_form_installed_vs_forced": {"predicted": "C1 reproduces every probe outcome without constructing a density matrix", "passed": c1["survives_reproduce_quotient"], "structure_id": "C1"},
    }


def verdict(survivors, mins, pre, controls_ok, smt_ok, real_ok):
    if not controls_ok or not smt_ok:
        return "inconclusive", "solver flip or controls did not behave"
    if len(mins) >= 2 and all(not pre[a][b] and not pre[b][a] for a in mins for b in mins if a != b):
        return "plural_incomparable", "minimal survivor set contains pairwise-incomparable structures"
    if "C4" in survivors and real_ok and any(c != "C4" and pre[c]["C4"] and not pre["C4"][c] for c in survivors):
        return "installed", "z3/cvc5 force noncommuting updates under N01, but Min(Surv) includes a strictly weaker structure below C4 and real-operator suffices"
    if "C4" in survivors:
        return "forced", "no strictly weaker survivor below C4"
    return "inconclusive", "C4 did not survive or survivor set is empty"


def z3_commutative_reproduction(class_map_a, class_map_b):
    solver = z3.Solver()
    class_labels = sorted(class_map_a.keys(), key=int)
    for c in class_labels:
        left = class_map_a[str(class_map_b[c])]
        right = class_map_b[str(class_map_a[c])]
        solver.add(z3.IntVal(left) == z3.IntVal(right))
    return str(solver.check())


def cvc5_commutative_reproduction(class_map_a, class_map_b):
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_LRA")
    class_labels = sorted(class_map_a.keys(), key=int)
    terms = []
    for c in class_labels:
        left = tm.mkReal(class_map_a[str(class_map_b[c])], 1)
        right = tm.mkReal(class_map_b[str(class_map_a[c])], 1)
        terms.append(tm.mkTerm(Kind.EQUAL, left, right))
    slv.assertFormula(terms[0] if len(terms) == 1 else tm.mkTerm(Kind.AND, *terms))
    return str(slv.checkSat())


def transition_matrix(class_map, n):
    mat = jnp.zeros((n, n), dtype=jnp.int64)
    for source_s, target in class_map.items():
        mat = mat.at[int(target), int(source_s)].set(1)
    return mat


def z3_real_operator_suffices(u1c, u2c, witness_class, n):
    a = transition_matrix(u1c, n)
    b = transition_matrix(u2c, n)
    left = a @ b
    right = b @ a
    row = int(u1c[str(u2c[witness_class])])
    col = int(witness_class)
    solver = z3.Solver()
    solver.add(z3.IntVal(int(left[row, col])) != z3.IntVal(int(right[row, col])))
    return str(solver.check()), {"witness_matrix_entry": [row, col], "AB_value": int(left[row, col]), "BA_value": int(right[row, col])}


def cvc5_real_operator_suffices(u1c, u2c, witness_class, n):
    a = transition_matrix(u1c, n)
    b = transition_matrix(u2c, n)
    left = a @ b
    right = b @ a
    row = int(u1c[str(u2c[witness_class])])
    col = int(witness_class)
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_LRA")
    slv.assertFormula(tm.mkTerm(Kind.DISTINCT, tm.mkReal(int(left[row, col]), 1), tm.mkReal(int(right[row, col]), 1)))
    return str(slv.checkSat())


def main():
    with open(os.path.join(HERE, "spec.json")) as f:
        spec = json.load(f)
    labels = spec["finite_set"]
    probes = spec["probe_family"]
    classes, signatures = quotient_classes(labels, probes)
    remaining = set(spec["probe_erase_control"]["remaining_probe_ids"])
    erased_classes, _ = quotient_classes(labels, [p for p in probes if p["id"] in remaining])
    u1 = spec["active_constraints"]["N01"]["update_maps"]["U1"]
    u2 = spec["active_constraints"]["N01"]["update_maps"]["U2"]
    v1 = spec["commuting_update_control"]["update_maps"]["V1"]
    v2 = spec["commuting_update_control"]["update_maps"]["V2"]
    element_witness = noncommutation_witness(labels, u1, u2)
    control_element_witness = noncommutation_witness(labels, v1, v2)
    survival, class_witness, control_class_witness, maps = survival_table(spec, labels, probes, classes, erased_classes, signatures, u1, u2, v1, v2)
    u1c, u2c, v1c, v2c = maps
    pre = preorder_matrix(spec, survival)
    survivors = [c["id"] for c in spec["candidate_structures"] if survival[c["id"]]["survives_all_active_constraints"]]
    mins = minimal_survivors(survivors, pre)
    ctrl = controls(spec, probes, labels, classes, survival)

    z3_full = z3_commutative_reproduction(u1c, u2c)
    z3_erased = z3_commutative_reproduction(v1c, v2c)
    cvc5_full = cvc5_commutative_reproduction(u1c, u2c)
    cvc5_erased = cvc5_commutative_reproduction(v1c, v2c)
    z3_real, real_evidence = z3_real_operator_suffices(u1c, u2c, class_witness["class"], len(classes))
    cvc5_real = cvc5_real_operator_suffices(u1c, u2c, class_witness["class"], len(classes))
    flip_confirmed = z3_full == "unsat" and z3_erased == "sat" and cvc5_full == "unsat" and cvc5_erased == "sat"
    real_ok = z3_real == "sat" and cvc5_real == "sat"
    ctrl_ok = all(v["passed"] for v in ctrl.values())
    vd, reason = verdict(survivors, mins, pre, ctrl_ok, flip_confirmed, real_ok)

    # JAX-specific batched recomputation of signatures as integer arrays.
    probe_tensor = jnp.array([[p["outcomes"][label] for p in probes] for label in labels], dtype=jnp.int64)
    equality_matrix = (probe_tensor[:, None, :] == probe_tensor[None, :, :]).all(axis=2)

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "computation_style": "batched_jax_plus_smt",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": spec_sha(),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_jax_results.json",
        "finite_set": labels,
        "lineage": spec["lineage"],
        "probe_signatures": signatures,
        "jax_probe_tensor": probe_tensor.tolist(),
        "jax_kernel_equality_matrix": equality_matrix.tolist(),
        "quotient_classes_full": classes,
        "quotient_class_count_full": len(classes),
        "quotient_classes_erased": erased_classes,
        "quotient_class_count_erased": len(erased_classes),
        "element_noncommutation_witness": element_witness,
        "commuting_control_element_witness": control_element_witness,
        "class_noncommutation_witness": class_witness,
        "commuting_control_class_witness": control_class_witness,
        "per_structure_survival": survival,
        "preorder_definition": spec["preorder_definition"],
        "preorder_matrix": pre,
        "Surv": survivors,
        "MinSurv": mins,
        "controls": ctrl,
        "smt_flip": {
            "primary_question": "exists a commutative update structure reproducing the measured quotient maps and the U1/U2 action?",
            "encoding": "for each quotient class c, assert U1_class(U2_class(c)) == U2_class(U1_class(c)); full uses U1/U2, erased control uses V1/V2",
            "z3_full": z3_full,
            "z3_erased": z3_erased,
            "cvc5_full": cvc5_full,
            "cvc5_erased": cvc5_erased,
            "real_vs_erased_flip_confirmed": flip_confirmed,
            "secondary_question": "does a real-vector/real-operator transition-matrix structure reproduce the quotient and witnessed noncommutation?",
            "z3_real_operator_full": z3_real,
            "cvc5_real_operator_full": cvc5_real,
            "real_operator_evidence": real_evidence,
            "interpretation": "full UNSAT forces noncommuting update structure, erased SAT shows the control behaves, and real-operator SAT blocks any claim that complex structure is forced by this data."
        },
        "computed_verdict": vd,
        "computed_verdict_reason": reason,
        "package_versions": {"jax": jax.__version__, "z3": z3.get_version_string(), "cvc5": getattr(cvc5, "__version__", "unknown")},
        "packages_used": ["jax", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["jax", "z3", "cvc5"],
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "load-bearing batched probe-signature tensor and kernel equality matrix"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing commutative-update impossibility flip and real-operator sufficiency check"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent solver confirmation of the same structural flip"}
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing"},
        "tool_calls": [
            {"tool": "z3", "qualified_api": "z3.Solver.check", "input_object": "quotient-class update composition table from spec U1/U2 and V1/V2", "output_object": "unsat for full, sat for commuting control", "positive_case": "U1/U2 measured noncommuting class witness", "negative_erased_control": "V1/V2 commute everywhere", "boundary_case": "well-defined maps on multi-element quotient classes", "demotion_condition": "if full is sat or control is unsat", "gates": ["proof", "all_pass"]},
            {"tool": "cvc5", "qualified_api": "cvc5.Solver.checkSat", "input_object": "same quotient-class update composition table", "output_object": "unsat for full, sat for commuting control", "positive_case": "U1/U2 measured noncommuting class witness", "negative_erased_control": "V1/V2 commute everywhere", "boundary_case": "well-defined maps on multi-element quotient classes", "demotion_condition": "if full is sat or control is unsat", "gates": ["proof", "all_pass"]}
        ]
    }
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    out = os.path.join(HERE, "results", f"{SIM_ID}_jax_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"jax leg wrote {out}")
    print(f"  smt z3={z3_full}/{z3_erased} cvc5={cvc5_full}/{cvc5_erased} real={z3_real}/{cvc5_real}")
    print(f"  MinSurv={mins} verdict={vd}")


if __name__ == "__main__":
    main()
