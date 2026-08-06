#!/usr/bin/env python3
"""Probe lane 2 -> the estate's own gate.

Builds carrier-table-shaped receipts for the ROOT-STRATA quantities out of the values
the engine lanes actually measured (every number is READ from a lane receipt, none is
retyped here), then LAUNCHES check_carrier_obligations.py on each one and records the
real exit code and disposition of that subprocess.

Includes deliberate negative controls, labelled as such:
  t05  the float32 lane's own H0_pair
  t07a/t07b  the same three declarations in two different orders
  t09  a kappa reported on an EMPTY fibre
  t10  the honest typed-release descriptor of an empty fibre

Exit 0 if every receipt was built and every checker subprocess ran; the dispositions
themselves are DATA, not this script's pass criterion.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
GATE = os.path.abspath(os.path.join(HERE, "..", "check_carrier_obligations.py"))
RECDIR = os.path.join(HERE, "gate_receipts")
OUT = os.path.join(RES, "gate_runs.json")
PY = sys.executable

EXIT_NAMES = {0: "PASS_THIS_TABLE", 1: "BLOCK", 2: "TABLE_REJECTED", 3: "PARK",
              4: "TABLE_ACCEPTED_NO_INPUT"}
EXPECTED_EXITS = {
    "t01_h0addr_only": 3,
    "t02_diag_no_support_restriction": 1,
    "t03_diag_with_support_restriction": 3,
    "t04_coherent_float64": 3,
    "t05_coherent_float32_NEGATIVE_CONTROL": 1,
    "t06_r3_full_field_equality_witness": 3,
    "t07a_two_pair_fields_diag_last": 1,
    "t07b_two_pair_fields_coherent_last": 1,
    "t11a_flip_probe_diag_last": 1,
    "t11b_flip_probe_coherent_last": 3,
    "t08_kappa_ext_u2": 3,
    "t09_kappa_ext_on_empty_fibre_NEGATIVE_CONTROL": 1,
    "t10_honest_empty_release_descriptor": 3,
}


def load(name):
    with open(os.path.join(RES, name + ".json")) as fh:
        return json.load(fh)


def main():
    os.makedirs(RECDIR, exist_ok=True)
    os.makedirs(RES, exist_ok=True)
    j64 = load("lane_jax_float64")
    j32 = load("lane_jax_float32")
    en = load("enum_reference")

    A = j64["R0"]["H0_addr_bits"]                        # 4.0
    CARD = j64["R0"]["cardinality"]                      # 16
    PD = j64["R1"]["DIAG"]["H0_pair_bits"]               # 4.0
    SD = j64["R1"]["DIAG"]["support_cardinality"]        # 16
    PC = j64["R1"]["COHERENT"]["H0_pair_bits"]           # log2 80
    SC = j64["R1"]["COHERENT"]["support_cardinality"]    # 80
    PC32 = j32["R1"]["COHERENT"]["H0_pair_bits"]         # float32 log2 80
    KFULL = j64["R3"]["FULL_FIELD"]["per_dim"]["4"]["kappa_bits"]        # 8.0
    RFULL = j64["R3"]["FULL_FIELD"]["per_dim"]["4"]["relation_cardinality"]   # 256
    KR2 = j64["R3"]["RESTRICTED"]["per_dim"]["2"]["kappa_bits"]          # log2 12
    RR2 = j64["R3"]["RESTRICTED"]["per_dim"]["2"]["relation_cardinality"]     # 12
    KE2 = j64["C1_C3"]["kappa_ext_bits"]["2"]            # log2 6
    FE2 = j64["C1_C3"]["fibre_cardinalities"]["2"]       # 6
    EMPTY = j64["C1_C3"]["empty_fibre_case"]["descriptor"]

    J4 = {"class": "finite_address_set", "cardinality": CARD, "n_bits": 4,
          "alphabet": "binary"}
    F_DIAG = {"class": "pair_indexed_field", "support_cardinality": SD,
              "index_set_ref": "J4"}
    F_COH = {"class": "pair_indexed_field", "support_cardinality": SC,
             "index_set_ref": "J4"}
    F_FULL = {"class": "pair_indexed_field", "support_cardinality": (CARD ** 2),
              "index_set_ref": "J4"}

    receipts = {}

    receipts["t01_h0addr_only"] = {
        "note": "R0 alone, values from lane_jax_float64",
        "data": {"h0_addr_bits": A},
        "typed_ontology": {"carriers": {"J4": dict(J4)},
                           "quantities": [{"id": "H0_addr", "at": "data.h0_addr_bits",
                                           "carrier_ref": "J4"}]}}

    receipts["t02_diag_no_support_restriction"] = {
        "note": "the owner diagram's DIAG pair field, declared honestly and with no "
                "support_restriction field. AM-03 live stake.",
        "data": {"h0_addr_bits": A, "h0_pair_diag_bits": PD},
        "typed_ontology": {"carriers": {"J4": dict(J4), "F_diag": dict(F_DIAG)},
                           "quantities": [
                               {"id": "H0_addr", "at": "data.h0_addr_bits",
                                "carrier_ref": "J4"},
                               {"id": "H0_pair", "at": "data.h0_pair_diag_bits",
                                "carrier_ref": "F_diag"}]}}

    fd2 = dict(F_DIAG)
    fd2["support_restriction"] = ("F[j][k] = 1 iff j == k, so supp F is the diagonal of "
                                 "J x J and |supp F| = |J| = 16")
    receipts["t03_diag_with_support_restriction"] = {
        "note": "same DIAG field, support_restriction declared",
        "data": {"h0_addr_bits": A, "h0_pair_diag_bits": PD},
        "typed_ontology": {"carriers": {"J4": dict(J4), "F_diag": fd2},
                           "quantities": [
                               {"id": "H0_addr", "at": "data.h0_addr_bits",
                                "carrier_ref": "J4"},
                               {"id": "H0_pair", "at": "data.h0_pair_diag_bits",
                                "carrier_ref": "F_diag"}]}}

    receipts["t04_coherent_float64"] = {
        "note": "COHERENT pair field, float64 lane",
        "data": {"h0_addr_bits": A, "h0_pair_coherent_bits": PC},
        "typed_ontology": {"carriers": {"J4": dict(J4), "F_coh": dict(F_COH)},
                           "quantities": [
                               {"id": "H0_addr", "at": "data.h0_addr_bits",
                                "carrier_ref": "J4"},
                               {"id": "H0_pair", "at": "data.h0_pair_coherent_bits",
                                "carrier_ref": "F_coh"}]}}

    receipts["t05_coherent_float32_NEGATIVE_CONTROL"] = {
        "note": "identical to t04 except the value is the one the float32 JAX lane "
                "measured. Same code path, one config flag.",
        "data": {"h0_addr_bits": A, "h0_pair_coherent_bits": PC32},
        "typed_ontology": {"carriers": {"J4": dict(J4), "F_coh": dict(F_COH)},
                           "quantities": [
                               {"id": "H0_addr", "at": "data.h0_addr_bits",
                                "carrier_ref": "J4"},
                               {"id": "H0_pair", "at": "data.h0_pair_coherent_bits",
                                "carrier_ref": "F_coh"}]}}

    receipts["t06_r3_full_field_equality_witness"] = {
        "note": "R3 FULL-FIELD cell: R_c = J x J, so kappa(c) = 2n = 8 and H0_pair over "
                "the full pair field is also 8. The table's own equality case.",
        "data": {"kappa_cell_bits": KFULL, "h0_pair_full_bits": KFULL},
        "typed_ontology": {"carriers": {
            "F_full": dict(F_FULL),
            "cell_top": {"class": "fibred_pair_relation", "cell_id": "(*,*,*,*)",
                         "relation_cardinality": RFULL,
                         "projection_ref": "pi : E -> K over {0,1,*}^4"}},
            "quantities": [
                {"id": "H0_pair", "at": "data.h0_pair_full_bits", "carrier_ref": "F_full"},
                {"id": "kappa_cell", "at": "data.kappa_cell_bits",
                 "carrier_ref": "cell_top"}]}}

    base_q = [{"id": "kappa_cell", "at": "data.kappa_cell_bits", "carrier_ref": "cell_top"}]
    qd = {"id": "H0_pair", "at": "data.h0_pair_diag_bits", "carrier_ref": "F_diag"}
    qc = {"id": "H0_pair", "at": "data.h0_pair_coherent_bits", "carrier_ref": "F_coh"}
    for tag, order in (("t07a_two_pair_fields_diag_last", [qc, qd]),
                       ("t07b_two_pair_fields_coherent_last", [qd, qc])):
        receipts[tag] = {
            "note": "ORDER PROBE. Two pair fields over the same J plus one R3 cell. "
                    "t07a and t07b differ ONLY in the order of the two H0_pair "
                    "declarations. cross_quantity_le on kappa_cell declares "
                    "scope 'same_index_set'.",
            "data": {"kappa_cell_bits": KFULL, "h0_pair_diag_bits": PD,
                     "h0_pair_coherent_bits": PC},
            "typed_ontology": {"carriers": {
                "F_diag": dict(F_DIAG), "F_coh": dict(F_COH),
                "cell_top": {"class": "fibred_pair_relation", "cell_id": "(*,*,*,*)",
                             "relation_cardinality": RFULL,
                             "projection_ref": "pi : E -> K over {0,1,*}^4"}},
                "quantities": base_q + order}}

    # kappa for a dim-3 restricted cell sits STRICTLY BETWEEN the two H0_pair values
    # (4.0 < 5.0 < 6.3219), so if the bound is order-determined the DISPOSITION flips,
    # not merely the reason string.
    KR3 = j64["R3"]["RESTRICTED"]["per_dim"]["3"]["kappa_bits"]            # 5.0
    RR3 = j64["R3"]["RESTRICTED"]["per_dim"]["3"]["relation_cardinality"]  # 32
    cell3 = {"class": "fibred_pair_relation", "cell_id": "(1,*,*,*)",
             "relation_cardinality": RR3,
             "projection_ref": "pi : E -> K over {0,1,*}^4"}
    q3 = [{"id": "kappa_cell", "at": "data.kappa_cell_bits", "carrier_ref": "cell_dim3"}]
    for tag, order in (("t11a_flip_probe_diag_last", [qc, qd]),
                       ("t11b_flip_probe_coherent_last", [qd, qc])):
        receipts[tag] = {
            "note": "FLIP PROBE. Identical carriers and identical values; the two H0_pair "
                    "declarations are in opposite order. kappa_cell = log2 32 = 5.0 lies "
                    "strictly between H0_pair(DIAG) = 4.0 and H0_pair(COHERENT) = "
                    "log2 80. Every number here is an honest measurement of this probe "
                    "lane's own R1 and R3 structures.",
            "data": {"kappa_cell_bits": KR3, "h0_pair_diag_bits": PD,
                     "h0_pair_coherent_bits": PC},
            "typed_ontology": {"carriers": {"F_diag": dict(F_DIAG), "F_coh": dict(F_COH),
                                            "cell_dim3": dict(cell3)},
                               "quantities": q3 + order}}

    receipts["t08_kappa_ext_u2"] = {
        "note": "C1-C3 extension capacity on the popcount quotient, class u = 2",
        "data": {"kappa_ext_bits": KE2},
        "typed_ontology": {"carriers": {"fib_u2": {
            "class": "declared_quotient_with_probes",
            "probe_family": ["p_popcount"], "quotient_class_id": 2,
            "fibre_cardinality": FE2,
            "constraint_set_ref": "C0 = identity constraint (E_C = E) for this probe lane"}},
            "quantities": [{"id": "kappa_ext", "at": "data.kappa_ext_bits",
                            "carrier_ref": "fib_u2"}]}}

    receipts["t09_kappa_ext_on_empty_fibre_NEGATIVE_CONTROL"] = {
        "note": "a kappa reported on the EMPTY fibre u = 5. No lane in this probe emits "
                "this; it is the malformed case the TYPED RELEASE rule names.",
        "data": {"kappa_ext_bits": 0.0},
        "typed_ontology": {"carriers": {"fib_u5": {
            "class": "declared_quotient_with_probes",
            "probe_family": ["p_popcount"], "quotient_class_id": 5,
            "fibre_cardinality": 0,
            "constraint_set_ref": "C0 = identity constraint (E_C = E)"}},
            "quantities": [{"id": "kappa_ext", "at": "data.kappa_ext_bits",
                            "carrier_ref": "fib_u5"}]}}

    receipts["t10_honest_empty_release_descriptor"] = {
        "note": "the descriptor every lane actually returned for u = 5: cardinality 0 and "
                "NO kappa key, so there is no quantity to declare.",
        "data": {"release_u5": EMPTY},
        "typed_ontology": {"carriers": {"fib_u5": {
            "class": "declared_quotient_with_probes",
            "probe_family": EMPTY["probe_family"],
            "quotient_class_id": EMPTY["quotient_class_id"],
            "fibre_cardinality": EMPTY["fibre_cardinality"],
            "constraint_set_ref": EMPTY["constraint_set_ref"]}},
            "quantities": []}}

    runs = {}
    for name, rec in receipts.items():
        p = os.path.join(RECDIR, name + ".json")
        with open(p, "w") as fh:
            json.dump(rec, fh, indent=1)
        cp = subprocess.run([PY, GATE, p], capture_output=True, text=True)
        try:
            got = json.loads(cp.stdout)
        except Exception:
            got = {"unparsed_stdout": cp.stdout[:800]}
        runs[name] = {"receipt_path": os.path.relpath(p, HERE),
                      "argv": [PY, GATE, p],
                      "measured_exit_code": cp.returncode,
                      "exit_name_in_estate_convention": EXIT_NAMES.get(cp.returncode,
                                                                       "unknown"),
                      "stderr_head": cp.stderr[:400],
                      "gate_stdout": got}

    unexpected = {
        name: {"expected_exit_code": EXPECTED_EXITS.get(name),
               "actual_exit_code": row["measured_exit_code"]}
        for name, row in runs.items()
        if EXPECTED_EXITS.get(name) != row["measured_exit_code"]
    }
    missing_expected = sorted(set(EXPECTED_EXITS) - set(runs))
    with open(OUT, "w") as fh:
        json.dump({"gate": os.path.relpath(GATE, HERE), "interpreter": PY,
                   "value_provenance": {
                       "h0_addr_bits": "results/lane_jax_float64.json R0.H0_addr_bits",
                       "h0_pair_diag_bits": "results/lane_jax_float64.json R1.DIAG.H0_pair_bits",
                       "h0_pair_coherent_bits": "results/lane_jax_float64.json R1.COHERENT.H0_pair_bits",
                       "h0_pair_coherent_bits_float32": "results/lane_jax_float32.json R1.COHERENT.H0_pair_bits",
                       "kappa_cell_bits": "results/lane_jax_float64.json R3.FULL_FIELD.per_dim.4.kappa_bits",
                       "kappa_ext_bits": "results/lane_jax_float64.json C1_C3.kappa_ext_bits.2",
                       "enum_cross_check": f"enum_reference H0_pair COHERENT = "
                                           f"{en['R1']['fields']['COHERENT']['H0_pair_bits']}"},
                   "expected_exit_codes": EXPECTED_EXITS,
                   "unexpected_exit_codes": unexpected,
                   "missing_expected_receipts": missing_expected,
                   "runs": runs}, fh, indent=1)
    print(json.dumps({"wrote": OUT, "receipts": len(receipts),
                      "measured_exit_codes": {k: v["measured_exit_code"]
                                              for k, v in runs.items()},
                      "unexpected_exit_codes": unexpected,
                      "missing_expected_receipts": missing_expected}, indent=1))
    return 0 if not unexpected and not missing_expected else 1


if __name__ == "__main__":
    sys.exit(main())
