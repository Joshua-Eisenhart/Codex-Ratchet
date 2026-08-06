#!/usr/bin/env python3
"""Mechanical cross-lane comparison. This is the ONLY file that reads both lanes.

It compares the decisive observables the two lanes computed independently and
prints every disagreement. Nothing is asserted; every row is a measured pair.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R = lambda n: json.load(open(os.path.join(HERE, "results", n)))


def main():
    d1, d2, d4, d5 = (R("d1_root_support.json"), R("d2_root_geometry.json"),
                      R("d4_presentations.json"), R("d5_algebra.json"))
    jl = R("lane_julia.json")
    rows = []

    def cmp(label, py, ju):
        rows.append({"observable": label, "python_lane": py, "julia_lane": ju,
                     "lanes_agree": py == ju})

    # D1 ---------------------------------------------------------------
    for variant, v in d1["diagonal_data_variants"].items():
        for side, key in (("rival_A_diagonal_only", "rival_A_diagonal_only"),
                          ("rival_B_pair_field", "rival_B_pair_field")):
            p = v[key]
            j = jl["d1_root_support"][f"{variant}__{side}"]
            cmp(f"D1.{variant}.{side}.support_cardinality",
                p["support_cardinality"], j["support_cardinality"])
            cmp(f"D1.{variant}.{side}.exact_rank", p["exact_rank"], j["exact_rank"])
            cmp(f"D1.{variant}.{side}.exact_determinant",
                str(p["exact_determinant"]), str(int(float(j["exact_determinant"].split("//")[0]))
                                                 if "//" in j["exact_determinant"]
                                                 else int(j["exact_determinant"])))
            cmp(f"D1.{variant}.{side}.H0_pair_bits_key_present",
                "H0_pair_bits" in p, "H0_pair_bits" in j)

    # D2 ---------------------------------------------------------------
    for name, p in d2["one_skeleton_observables"].items():
        j = jl["d2_one_skeleton"][name]
        cmp(f"D2.{name}.edges", p["edges"], j["edges"])
        cmp(f"D2.{name}.degree_sequence", p["degree_sequence"], j["degree_sequence"])
        cmp(f"D2.{name}.is_bipartite", p["is_bipartite"], j["is_bipartite"])
        cmp(f"D2.{name}.triangle_count", p["triangle_count"], int(j["triangle_count"]))
        cmp(f"D2.{name}.four_cycle_count", p["four_cycle_count"], int(j["four_cycle_count"]))
    for name in ("cubical_4cube_2skeleton_24_squares", "torus_C4_box_C4_16_quads"):
        p, j = d2["two_cell_level"][name], jl["d2_two_cell_level"][name]
        for k in ("euler_characteristic_V_minus_E_plus_F", "rank_boundary_1",
                  "rank_boundary_2", "betti_0_over_Q", "betti_1_over_Q", "betti_2_over_Q"):
            cmp(f"D2.2cell.{name}.{k}", p[k], j[k])
        cmp(f"D2.2cell.{name}.d1_d2_is_zero", int(p["d1_d2_max_abs_entry"]) == 0,
            j["d1_d2_max_abs_entry"] in ("0", "0//1"))

    # D4 ---------------------------------------------------------------
    for name in ("finite_S2_octahedron", "finite_T2_C4_box_C4_quads"):
        p, j = d4["leg_2_sphere_vs_torus"][name], jl["d4_sphere_vs_torus"][name]
        for k in ("vertices", "edges", "faces", "euler_characteristic_V_minus_E_plus_F",
                  "betti_0_over_Q", "betti_1_over_Q", "betti_2_over_Q"):
            cmp(f"D4.{name}.{k}", p[k], j[k])

    # D5 ---------------------------------------------------------------
    pmap = {r["algebra"]: r for r in d5["algebras"]}
    pairs = [
        ("octonions over Z, Cayley-Dickson basis", "octonions_Octonions_jl"),
        ("quaternions over Z, Cayley-Dickson basis", "quaternions_Quaternions_jl"),
        ("M2(Z) matrix units under matrix product", "M2_Int_matrix_units"),
        ("symmetric 2x2 rationals under the Jordan product (AB+BA)/2", "jordan_symmetric_2x2"),
    ]
    for pn, jn in pairs:
        p, j = pmap[pn], jl["d5_algebra"][jn]
        cmp(f"D5.{jn}.nonzero_commutator_witness_count",
            p["nonzero_commutator_witness_count"], j["nonzero_commutator_witness_count"])
        cmp(f"D5.{jn}.nonzero_associator_witness_count",
            p["nonzero_associator_witness_count"], j["nonzero_associator_witness_count"])

    disagreements = [r for r in rows if not r["lanes_agree"]]
    out = {
        "compared": ["python_sim_stack", "julia"],
        "julia_version": jl["julia_version"],
        "comparison_count": len(rows),
        "disagreement_count": len(disagreements),
        "disagreements": disagreements,
        "rows": rows,
    }
    path = os.path.join(HERE, "results", "compare_lanes.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print(f"compared {len(rows)} observables across 2 lanes")
    print(f"disagreements: {len(disagreements)}")
    for r in disagreements:
        print("  DISAGREE", r["observable"], "python=", r["python_lane"], "julia=", r["julia_lane"])
    print(f"WROTE {path}", file=sys.stderr)
    return 1 if disagreements else 0


if __name__ == "__main__":
    sys.exit(main())
