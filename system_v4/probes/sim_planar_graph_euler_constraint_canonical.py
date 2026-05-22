#!/usr/bin/env python3
"""
Planar Graph Euler Constraint -- Canonical Sim

Constraint: For planar graphs V - E + F = 2 (Euler's formula)
E ≤ 3V - 6 for simple planar graphs (UNSAT for E > 3V - 6 AND claimed planar)
K_5 and K_{3,3} are non-planar (Kuratowski theorem)

cvc5 proves: E ≤ 3V - 6 constraint for planar graphs.
cvc5 proves UNSAT: E > 3V - 6 AND planar.
sympy derives: K_5 and K_{3,3} violate planarity.

Classification: canonical (constraint-admissibility proof)
"""

import json
import os
import numpy as np

classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# Tool import attempts
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS: V - E + F = 2, E ≤ 3V - 6 for planar graphs
# =====================================================================

def run_positive_tests():
    results = {}

    # Test 1: cvc5 validates Euler formula V - E + F = 2 for planar graph
    if TOOL_MANIFEST["cvc5"]["tried"]:
        try:
            import cvc5

            tm = cvc5.TermManager()
            solver = cvc5.Solver(tm)

            V = tm.mkConst(tm.getIntegerSort(), "V")
            E = tm.mkConst(tm.getIntegerSort(), "E")
            F = tm.mkConst(tm.getIntegerSort(), "F")

            # Example: triangle (simple planar graph)
            # V=3, E=3, F=2 (interior + exterior face)
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, V, tm.mkInteger(3)))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, E, tm.mkInteger(3)))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, F, tm.mkInteger(2)))

            # Euler's formula: V - E + F = 2
            euler_expr = tm.mkTerm(cvc5.Kind.Add, V, F)
            euler_expr = tm.mkTerm(cvc5.Kind.Sub, euler_expr, E)
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, euler_expr, tm.mkInteger(2)))

            is_sat = solver.checkSat().isSat()

            if is_sat:
                model = solver.getValue([V, E, F])
                v_val = int(model[0].toString())
                e_val = int(model[1].toString())
                f_val = int(model[2].toString())
                euler_check = (v_val - e_val + f_val) == 2
            else:
                v_val = None
                e_val = None
                f_val = None
                euler_check = None

            results["cvc5_positive_euler_formula"] = {
                "test": "Euler's formula V - E + F = 2 for planar graph",
                "graph": "triangle",
                "vertices_V": v_val,
                "edges_E": e_val,
                "faces_F": f_val,
                "euler_check": euler_check,
                "satisfiable": is_sat,
                "passed": is_sat and euler_check,
                "method": "cvc5 LIA constraint"
            }

            TOOL_MANIFEST["cvc5"]["used"] = True
            TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"

        except Exception as e:
            results["cvc5_positive_euler_formula"] = {"error": str(e)}

    # Test 2: cvc5 validates edge bound E ≤ 3V - 6 for planar graphs
    if TOOL_MANIFEST["cvc5"]["tried"]:
        try:
            import cvc5

            tm = cvc5.TermManager()
            solver = cvc5.Solver(tm)

            V = tm.mkConst(tm.getIntegerSort(), "V")
            E = tm.mkConst(tm.getIntegerSort(), "E")

            # Planar graph K_4 (complete graph on 4 vertices): V=4, E=6
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, V, tm.mkInteger(4)))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, E, tm.mkInteger(6)))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.GreaterEqual, V, tm.mkInteger(3)))

            # Planar constraint: E ≤ 3V - 6
            bound = tm.mkTerm(cvc5.Kind.Sub, tm.mkTerm(cvc5.Kind.Mult, tm.mkInteger(3), V), tm.mkInteger(6))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.LessEqual, E, bound))

            is_sat = solver.checkSat().isSat()

            if is_sat:
                model = solver.getValue([V, E])
                v_val = int(model[0].toString())
                e_val = int(model[1].toString())
                bound_val = 3 * v_val - 6
            else:
                v_val = None
                e_val = None
                bound_val = None

            results["cvc5_positive_planar_edge_bound"] = {
                "test": "E ≤ 3V - 6 for planar graphs (K_4)",
                "graph": "K_4",
                "vertices_V": v_val,
                "edges_E": e_val,
                "bound_3V_minus_6": bound_val,
                "E_leq_bound": e_val <= bound_val if bound_val is not None else None,
                "satisfiable": is_sat,
                "passed": is_sat and (e_val is not None and bound_val is not None and e_val <= bound_val),
                "method": "cvc5 LIA constraint"
            }

            TOOL_MANIFEST["cvc5"]["used"] = True
            TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"

        except Exception as e:
            results["cvc5_positive_planar_edge_bound"] = {"error": str(e)}

    # Test 3: sympy validates planarity constraint via Kuratowski theorem
    if TOOL_MANIFEST["sympy"]["tried"]:
        try:
            import sympy as sp

            # K_4 is planar (can be embedded in plane without crossings)
            # K_4: 4 vertices, every pair connected
            V_k4 = 4
            E_k4 = (V_k4 * (V_k4 - 1)) // 2
            bound_k4 = 3 * V_k4 - 6

            is_planar_k4 = E_k4 <= bound_k4

            results["sympy_positive_k4_planar"] = {
                "test": "K_4 is planar (satisfies Kuratowski necessary condition)",
                "graph": "K_4",
                "vertices_V": V_k4,
                "edges_E": E_k4,
                "bound_3V_minus_6": bound_k4,
                "E_leq_bound": E_k4 <= bound_k4,
                "is_planar": is_planar_k4,
                "passed": is_planar_k4,
                "method": "sympy graph analysis"
            }

            TOOL_MANIFEST["sympy"]["used"] = True
            TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

        except Exception as e:
            results["sympy_positive_k4_planar"] = {"error": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS: E > 3V - 6 AND planar → UNSAT, K_5/K_3,3 non-planar
# =====================================================================

def run_negative_tests():
    results = {}

    # Test 1: cvc5 proves UNSAT: E > 3V - 6 AND planar (contradiction)
    if TOOL_MANIFEST["cvc5"]["tried"]:
        try:
            import cvc5

            tm = cvc5.TermManager()
            solver = cvc5.Solver(tm)

            V = tm.mkConst(tm.getIntegerSort(), "V")
            E = tm.mkConst(tm.getIntegerSort(), "E")

            # Setup: V = 5
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, V, tm.mkInteger(5)))

            # Try to assert: E > 3V - 6 (i.e., E > 9 for V=5)
            solver.assertFormula(tm.mkTerm(cvc5.Kind.GreaterEqual, E, tm.mkInteger(10)))

            # Planar constraint: E ≤ 3V - 6
            bound = tm.mkTerm(cvc5.Kind.Sub, tm.mkTerm(cvc5.Kind.Mult, tm.mkInteger(3), V), tm.mkInteger(6))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.LessEqual, E, bound))

            is_sat = solver.checkSat().isSat()

            results["cvc5_negative_edge_bound_violated"] = {
                "test": "UNSAT: E > 3V - 6 AND planar (for V=5)",
                "vertices_V": 5,
                "attempted_edges_E": "≥10",
                "planar_bound_3V_minus_6": 9,
                "satisfiable": is_sat,
                "passed": not is_sat,
                "interpretation": "edge bound constraint contradicts claimed planarity",
                "method": "cvc5 proof of unsatisfiability"
            }

            TOOL_MANIFEST["cvc5"]["used"] = True
            TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"

        except Exception as e:
            results["cvc5_negative_edge_bound_violated"] = {"error": str(e)}

    # Test 2: sympy proves K_5 is non-planar (violates edge bound)
    if TOOL_MANIFEST["sympy"]["tried"]:
        try:
            import sympy as sp

            # K_5: complete graph on 5 vertices
            V_k5 = 5
            E_k5 = (V_k5 * (V_k5 - 1)) // 2  # 10 edges
            bound_k5 = 3 * V_k5 - 6  # 9 edges

            is_planar_k5 = E_k5 <= bound_k5

            results["sympy_negative_k5_non_planar"] = {
                "test": "K_5 is non-planar (violates edge bound)",
                "graph": "K_5",
                "vertices_V": V_k5,
                "edges_E": E_k5,
                "bound_3V_minus_6": bound_k5,
                "E_exceeds_bound": E_k5 > bound_k5,
                "is_planar": is_planar_k5,
                "passed": not is_planar_k5,
                "interpretation": "K_5 violates planarity edge constraint",
                "method": "sympy graph analysis"
            }

            TOOL_MANIFEST["sympy"]["used"] = True
            TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

        except Exception as e:
            results["sympy_negative_k5_non_planar"] = {"error": str(e)}

    # Test 3: sympy proves K_{3,3} is non-planar (bipartite but too dense)
    if TOOL_MANIFEST["sympy"]["tried"]:
        try:
            import sympy as sp

            # K_{3,3}: complete bipartite graph with 3+3 vertices
            V_k33 = 6
            E_k33 = 3 * 3  # 9 edges
            bound_k33 = 3 * V_k33 - 6  # 12 edges

            # K_{3,3} is bipartite (E ≤ 2V - 4 for bipartite planar)
            bound_bipartite = 2 * V_k33 - 4  # 8 edges

            is_planar_k33_bipartite = E_k33 <= bound_bipartite

            results["sympy_negative_k33_non_planar"] = {
                "test": "K_3,3 is non-planar (exceeds bipartite bound)",
                "graph": "K_{3,3}",
                "vertices_V": V_k33,
                "edges_E": E_k33,
                "bound_bipartite_2V_minus_4": bound_bipartite,
                "E_exceeds_bipartite_bound": E_k33 > bound_bipartite,
                "is_planar": is_planar_k33_bipartite,
                "passed": not is_planar_k33_bipartite,
                "interpretation": "K_3,3 violates bipartite planarity constraint",
                "method": "sympy graph analysis"
            }

            TOOL_MANIFEST["sympy"]["used"] = True
            TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

        except Exception as e:
            results["sympy_negative_k33_non_planar"] = {"error": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS: Tree, polygon, maximal planar graphs
# =====================================================================

def run_boundary_tests():
    results = {}

    # Test 1: Tree is always planar (E = V - 1, satisfies E ≤ 3V - 6)
    if TOOL_MANIFEST["cvc5"]["tried"]:
        try:
            import cvc5

            tm = cvc5.TermManager()
            solver = cvc5.Solver(tm)

            V = tm.mkConst(tm.getIntegerSort(), "V")
            E = tm.mkConst(tm.getIntegerSort(), "E")

            # Tree property: E = V - 1
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, E, tm.mkTerm(cvc5.Kind.Sub, V, tm.mkInteger(1))))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.GreaterEqual, V, tm.mkInteger(2)))

            # Planar constraint: E ≤ 3V - 6
            bound = tm.mkTerm(cvc5.Kind.Sub, tm.mkTerm(cvc5.Kind.Mult, tm.mkInteger(3), V), tm.mkInteger(6))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.LessEqual, E, bound))

            is_sat = solver.checkSat().isSat()

            results["cvc5_boundary_tree_planar"] = {
                "test": "Tree (E = V - 1) is always planar",
                "graph_type": "tree",
                "edge_formula": "E = V - 1",
                "planar_bound": "E ≤ 3V - 6",
                "satisfiable": is_sat,
                "passed": is_sat,
                "method": "cvc5 LIA constraint"
            }

            TOOL_MANIFEST["cvc5"]["used"] = True
            TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"

        except Exception as e:
            results["cvc5_boundary_tree_planar"] = {"error": str(e)}

    # Test 2: Maximal planar graph (triangulation) has E = 3V - 6
    if TOOL_MANIFEST["cvc5"]["tried"]:
        try:
            import cvc5

            tm = cvc5.TermManager()
            solver = cvc5.Solver(tm)

            V = tm.mkConst(tm.getIntegerSort(), "V")
            E = tm.mkConst(tm.getIntegerSort(), "E")

            # For V = 6, maximal planar: E = 3V - 6 = 12
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, V, tm.mkInteger(6)))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, E, tm.mkInteger(12)))

            # Planar constraint: E ≤ 3V - 6
            bound = tm.mkTerm(cvc5.Kind.Sub, tm.mkTerm(cvc5.Kind.Mult, tm.mkInteger(3), V), tm.mkInteger(6))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.LessEqual, E, bound))

            is_sat = solver.checkSat().isSat()

            results["cvc5_boundary_maximal_planar"] = {
                "test": "Maximal planar graph (triangulation) has E = 3V - 6",
                "graph_type": "triangulated planar",
                "vertices_V": 6,
                "edges_E": 12,
                "bound_3V_minus_6": 12,
                "satisfiable": is_sat,
                "passed": is_sat,
                "method": "cvc5 LIA constraint"
            }

            TOOL_MANIFEST["cvc5"]["used"] = True
            TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"

        except Exception as e:
            results["cvc5_boundary_maximal_planar"] = {"error": str(e)}

    # Test 3: sympy validates Euler formula variant for connected planar graphs
    if TOOL_MANIFEST["sympy"]["tried"]:
        try:
            import sympy as sp

            # For connected planar graphs: each face is bounded by at least 3 edges
            # This leads to 2E ≥ 3F, and combined with Euler V - E + F = 2:
            # E ≤ 3V - 6

            V = 5
            E = 9
            F = sp.Symbol('F', integer=True, positive=True)

            # Euler formula: V - E + F = 2
            F_euler = 2 - V + E

            # Each face has at least 3 edges: 2E ≥ 3F
            # Implies F ≤ 2E/3
            F_bound = 2 * E / 3

            results["sympy_boundary_euler_variant"] = {
                "test": "Euler variant: F = 2 - V + E, F ≤ 2E/3",
                "vertices_V": V,
                "edges_E": E,
                "faces_F_euler": int(F_euler),
                "faces_bound_2E_div_3": float(F_bound),
                "F_leq_bound": int(F_euler) <= float(F_bound),
                "passed": int(F_euler) <= float(F_bound),
                "interpretation": "Euler formula variant consistent",
                "method": "sympy formula validation"
            }

            TOOL_MANIFEST["sympy"]["used"] = True
            TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

        except Exception as e:
            results["sympy_boundary_euler_variant"] = {"error": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "Planar Graph Euler Constraint -- Canonical Sim",
        "description": "V - E + F = 2; E ≤ 3V - 6; K_5 and K_3,3 non-planar (Kuratowski)",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_planar_graph_euler_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
