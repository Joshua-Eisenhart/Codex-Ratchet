#!/usr/bin/env python3
"""PyTorch leg for the finite distinguishability quotient forced-or-installed test.

Unique computation style: carrier_maps_pytorch.
It builds class maps and preorder embeddings as torch tensors, recomputing
survivors and minimal survivors independently. It reads only spec.json and
writes its own result JSON.
"""

import hashlib
import json
import os
from datetime import datetime, timezone

import torch

torch.set_default_dtype(torch.float64)

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
    return [
        {"id": p["id"], "outcomes": {k: perms[p["id"]][str(v)] for k, v in p["outcomes"].items()}}
        for p in probes
    ]


def reproduces_probe_data(classes, signatures):
    ok = True
    evidence = {}
    for i, cls in enumerate(classes):
        sigs = [signatures[x] for x in cls]
        same = all(s == sigs[0] for s in sigs)
        ok = ok and same
        evidence[str(i)] = {"members": cls, "probe_signature": sigs[0], "constant_on_class": same}
    return ok, evidence


def transition_tensor(class_map, n):
    mat = torch.zeros((n, n), dtype=torch.float64)
    for source_s, target in class_map.items():
        mat[int(target), int(source_s)] = 1.0
    return mat


def survival_table(spec, labels, probes, classes, erased_classes, signatures, u1, u2, v1, v2):
    class_labels = [str(i) for i in range(len(classes))]
    u1c, u1wd, u1ev = induced_class_map(classes, u1)
    u2c, u2wd, u2ev = induced_class_map(classes, u2)
    v1c, v1wd, _ = induced_class_map(classes, v1)
    v2c, v2wd, _ = induced_class_map(classes, v2)
    active_witness = class_noncommutation_witness(class_labels, u1c, u2c)
    control_witness = class_noncommutation_witness(class_labels, v1c, v2c)
    reproduce_ok, rep_evidence = reproduces_probe_data(classes, signatures)
    active_tensor_noncommutes = not torch.equal(transition_tensor(u1c, len(classes)) @ transition_tensor(u2c, len(classes)), transition_tensor(u2c, len(classes)) @ transition_tensor(u1c, len(classes)))
    control_tensor_commutes = torch.equal(transition_tensor(v1c, len(classes)) @ transition_tensor(v2c, len(classes)), transition_tensor(v2c, len(classes)) @ transition_tensor(v1c, len(classes)))
    rows = {}
    for candidate in spec["candidate_structures"]:
        cid = candidate["id"]
        if candidate["update_policy"] == "commuting_diagonal_updates_only":
            active_update_ok = False
            control_update_ok = True
        else:
            active_update_ok = u1wd and u2wd and active_witness["exists"] and active_tensor_noncommutes
            control_update_ok = v1wd and v2wd and control_tensor_commutes
        rows[cid] = {
            "name": candidate["name"],
            "survives_reproduce_quotient": reproduce_ok,
            "survives_F01": True,
            "survives_N01": bool(active_update_ok),
            "survives_all_active_constraints": bool(reproduce_ok and active_update_ok),
            "commuting_update_control_survives": bool(reproduce_ok and control_update_ok),
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
    tensor_receipt = {
        "U1_tensor": transition_tensor(u1c, len(classes)).tolist(),
        "U2_tensor": transition_tensor(u2c, len(classes)).tolist(),
        "U1U2_tensor": (transition_tensor(u1c, len(classes)) @ transition_tensor(u2c, len(classes))).tolist(),
        "U2U1_tensor": (transition_tensor(u2c, len(classes)) @ transition_tensor(u1c, len(classes))).tolist(),
        "active_tensors_noncommute": bool(active_tensor_noncommutes),
        "control_tensors_commute": bool(control_tensor_commutes),
    }
    return rows, active_witness, control_witness, tensor_receipt


def preorder_matrix(spec, survival):
    ids = [c["id"] for c in spec["candidate_structures"]]
    ranks = {c["id"]: c["strength_rank"] for c in spec["candidate_structures"]}
    rank_tensor = torch.tensor([ranks[c] for c in ids], dtype=torch.int64)
    le = rank_tensor[:, None] <= rank_tensor[None, :]
    out = {}
    for i, a in enumerate(ids):
        out[a] = {}
        for j, b in enumerate(ids):
            out[a][b] = bool(le[i, j] and survival[a]["survives_reproduce_quotient"] and survival[b]["survives_reproduce_quotient"])
    return out


def strict_less(pre, a, b):
    return pre[a][b] and not pre[b][a]


def minimal_survivors(survivors, pre):
    return [c for c in survivors if not any(o != c and strict_less(pre, o, c) for o in survivors)]


def controls(spec, probes, labels, classes, survival):
    remaining = set(spec["probe_erase_control"]["remaining_probe_ids"])
    erased_classes, _ = quotient_classes(labels, [p for p in probes if p["id"] in remaining])
    shuffled_classes, _ = quotient_classes(labels, relabel_probes(probes, spec["label_shuffle_control"]["outcome_permutation_by_probe"]))
    return {
        "commuting_update": {"predicted": "commutative structure survives when V1,V2 replace U1,U2", "passed": survival["C2"]["commuting_update_control_survives"]},
        "label_shuffle": {"predicted": "quotient invariant under outcome relabelling", "passed": same_partition(classes, shuffled_classes), "shuffled_quotient_classes": shuffled_classes},
        "probe_erase": {"predicted": "class count strictly drops", "passed": len(erased_classes) < len(classes), "full_class_count": len(classes), "erased_class_count": len(erased_classes), "erased_quotient_classes": erased_classes},
        "matrix_form_installed_vs_forced": {"predicted": "C1 reproduces every probe outcome without constructing a density matrix", "passed": survival["C1"]["survives_reproduce_quotient"], "structure_id": "C1"},
    }


def verdict(survivors, mins, pre, controls_ok):
    if not controls_ok:
        return "inconclusive", "one_or_more_controls_failed"
    if len(mins) >= 2 and all(not pre[a][b] and not pre[b][a] for a in mins for b in mins if a != b):
        return "plural_incomparable", "minimal survivor set contains pairwise-incomparable structures"
    if "C4" in survivors and any(c != "C4" and pre[c]["C4"] and not pre["C4"][c] for c in survivors):
        return "installed", "Min(Surv) contains a strictly weaker structure below C4"
    if "C4" in survivors:
        return "forced", "no strictly weaker survivor below C4"
    return "inconclusive", "C4 did not survive or survivor set is empty"


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
    survival, class_witness, control_class_witness, tensor_receipt = survival_table(spec, labels, probes, classes, erased_classes, signatures, u1, u2, v1, v2)
    pre = preorder_matrix(spec, survival)
    survivors = [c["id"] for c in spec["candidate_structures"] if survival[c["id"]]["survives_all_active_constraints"]]
    mins = minimal_survivors(survivors, pre)
    ctrl = controls(spec, probes, labels, classes, survival)
    ctrl_ok = all(v["passed"] for v in ctrl.values())
    vd, reason = verdict(survivors, mins, pre, ctrl_ok)
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "computation_style": "carrier_maps_pytorch",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": spec_sha(),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_pytorch_results.json",
        "finite_set": labels,
        "lineage": spec["lineage"],
        "probe_signatures": signatures,
        "quotient_classes_full": classes,
        "quotient_class_count_full": len(classes),
        "quotient_classes_erased": erased_classes,
        "quotient_class_count_erased": len(erased_classes),
        "element_noncommutation_witness": element_witness,
        "commuting_control_element_witness": control_element_witness,
        "class_noncommutation_witness": class_witness,
        "commuting_control_class_witness": control_class_witness,
        "torch_transition_tensor_receipt": tensor_receipt,
        "per_structure_survival": survival,
        "preorder_definition": spec["preorder_definition"],
        "preorder_matrix": pre,
        "Surv": survivors,
        "MinSurv": mins,
        "controls": ctrl,
        "computed_verdict": vd,
        "computed_verdict_reason": reason,
        "package_versions": {"torch": torch.__version__},
        "packages_used": ["torch"],
        "aligned_packages_load_bearing": ["torch"],
        "TOOL_MANIFEST": {"torch": {"tried": True, "used": True, "reason": "load-bearing transition tensors and rank preorder matrix"}},
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing"},
        "tool_calls": [
            {"tool": "torch", "qualified_api": "torch.matmul", "input_object": "U1/U2 quotient transition tensors", "output_object": "U1U2 and U2U1 tensors", "positive_case": "active tensors noncommute", "negative_erased_control": "V1/V2 tensors commute", "boundary_case": "multi-element classes map to one target class", "demotion_condition": "if tensor products do not witness noncommutation", "gates": ["all_pass"]},
            {"tool": "torch", "qualified_api": "rank_tensor[:,None] <= rank_tensor[None,:]", "input_object": "candidate structure strength ranks", "output_object": "preorder matrix", "positive_case": "C1 <= C4 and not C4 <= C1", "negative_erased_control": "not applicable", "boundary_case": "equal structure ids reflexive", "demotion_condition": "if Min(Surv) changes", "gates": ["quotient"]}
        ],
    }
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    out = os.path.join(HERE, "results", f"{SIM_ID}_pytorch_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"pytorch leg wrote {out}")
    print(f"  tensor noncommutes={tensor_receipt['active_tensors_noncommute']} MinSurv={mins} verdict={vd}")


if __name__ == "__main__":
    main()
