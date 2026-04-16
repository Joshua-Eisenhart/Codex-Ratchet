#!/usr/bin/env python3
"""
CVC5 Batch 81: Hyland-Ong Game Semantics Canonical Sim

Game semantics (Hyland-Ong): plays are sequences of alternating O (Opponent) and P (Proponent) moves.
The fundamental constraint is move alternation: if move k is by O, move k+1 must be by P.

This sim uses cvc5 (QF_LIA) to enforce alternation constraints via SMT proof and sympy to compute
strategy count formulas |Strat(A→B)| = |Strat(A)|^|Strat(B)|.

Classification: canonical (cvc5 load_bearing, sympy supportive)
"""

import json
import os

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pytorch not needed; pure symbolic/algebraic computation via cvc5 and sympy"},
    "pyg": {"tried": False, "used": False, "reason": "PyG message passing not needed; game semantics handled via SMT solver"},
    "z3": {"tried": False, "used": False, "reason": "z3 not needed; cvc5 handles all SMT constraint proofs in this sim"},
    "cvc5": {"tried": False, "used": False, "reason": "cvc5 SMT solver: load_bearing proof of game semantics constraints"},
    "sympy": {"tried": False, "used": False, "reason": "sympy: supportive symbolic algebra for strategy counting formulas"},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not needed; game logic constraints only"},
    "geomstats": {"tried": False, "used": False, "reason": "geomstats not needed; no differential geometry in this sim"},
    "e3nn": {"tried": False, "used": False, "reason": "e3nn not needed; no SO(3) equivariance required"},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx not needed; no graph structure in this sim"},
    "xgi": {"tried": False, "used": False, "reason": "xgi not needed; pairwise interactions only"},
    "toponetx": {"tried": False, "used": False, "reason": "toponetx not needed; standard algebraic ops sufficient"},
    "gudhi": {"tried": False, "used": False, "reason": "gudhi not needed; no persistent homology in this sim"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": "load_bearing",
    "sympy": "supportive",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# Try importing each tool
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


# =====================================================================
# POSITIVE TESTS: Alternation constraint satisfaction
# =====================================================================

def run_positive_tests():
    """
    Positive tests: plays that satisfy alternation constraint.
    If move k is by O, move k+1 must be by P.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        results["cvc5_unavailable"] = {"status": "skipped", "reason": "cvc5 not installed"}
        return results

    from cvc5 import Solver, Kind

    # Test 1: Simple alternating play (O, P) satisfies constraint
    try:
        solver = Solver()
        # Represent a 2-move play
        # move_0_owner: 0 = O, 1 = P
        # move_1_owner: 0 = O, 1 = P
        move_0_owner = solver.mkConst(solver.getIntegerSort(), "move_0_owner")
        move_1_owner = solver.mkConst(solver.getIntegerSort(), "move_1_owner")

        # move_0_owner = 0 (Opponent)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, move_0_owner, solver.mkInteger(0)))

        # If move_0_owner = 0 (O), then move_1_owner must = 1 (P)
        # Constraint: move_0_owner = 0 => move_1_owner = 1
        constraint = solver.mkTerm(
            Kind.IMPLIES,
            solver.mkTerm(Kind.EQUAL, move_0_owner, solver.mkInteger(0)),
            solver.mkTerm(Kind.EQUAL, move_1_owner, solver.mkInteger(1))
        )
        solver.assertFormula(constraint)

        is_sat = solver.checkSat().isSat()
        results["test_simple_alternation_O_P"] = {
            "status": "pass" if is_sat else "fail",
            "satisfiable": is_sat,
            "interpretation": "O move followed by P move satisfies alternation"
        }
    except Exception as e:
        results["test_simple_alternation_O_P"] = {"status": "error", "error": str(e)}

    # Test 2: 4-move sequence (O, P, O, P) satisfies alternation
    try:
        solver = Solver()
        moves = [solver.mkConst(solver.getIntegerSort(), f"move_{i}") for i in range(4)]

        # Sequence: O, P, O, P
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, moves[0], solver.mkInteger(0)))  # O
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, moves[1], solver.mkInteger(1)))  # P
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, moves[2], solver.mkInteger(0)))  # O
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, moves[3], solver.mkInteger(1)))  # P

        # Alternation constraint: for all i < 3, if moves[i] = 0, then moves[i+1] = 1
        for i in range(3):
            constraint = solver.mkTerm(
                Kind.IMPLIES,
                solver.mkTerm(Kind.EQUAL, moves[i], solver.mkInteger(0)),
                solver.mkTerm(Kind.EQUAL, moves[i+1], solver.mkInteger(1))
            )
            solver.assertFormula(constraint)

        is_sat = solver.checkSat().isSat()
        results["test_4move_alternation"] = {
            "status": "pass" if is_sat else "fail",
            "satisfiable": is_sat,
            "interpretation": "4-move alternating play (O,P,O,P) satisfies constraint"
        }
    except Exception as e:
        results["test_4move_alternation"] = {"status": "error", "error": str(e)}

    # Test 3: Strategy counting formula (sympy)
    try:
        if TOOL_MANIFEST["sympy"]["tried"]:
            # |Strat(A → B)| = |Strat(A)|^|Strat(B)|
            # Example: |Strat(Bool → Bool)| = 2^2 = 4
            strat_a = sp.Symbol("strat_a", integer=True, positive=True)
            strat_b = sp.Symbol("strat_b", integer=True, positive=True)
            formula = strat_a ** strat_b

            # Substitute: A = Bool (2 strategies), B = Bool (2 strategies)
            result = formula.subs([(strat_a, 2), (strat_b, 2)])
            expected = 4

            results["test_strategy_formula"] = {
                "status": "pass" if result == expected else "fail",
                "formula": "|Strat(A → B)| = |Strat(A)|^|Strat(B)|",
                "strat_A": 2,
                "strat_B": 2,
                "computed": int(result),
                "expected": expected,
                "match": result == expected
            }
        else:
            results["test_strategy_formula"] = {"status": "skipped", "reason": "sympy not installed"}
    except Exception as e:
        results["test_strategy_formula"] = {"status": "error", "error": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS: Constraint violations (UNSAT)
# =====================================================================

def run_negative_tests():
    """
    Negative tests: plays that violate alternation constraint.
    Two consecutive O-moves should be UNSAT.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        results["cvc5_unavailable"] = {"status": "skipped", "reason": "cvc5 not installed"}
        return results

    from cvc5 import Solver, Kind

    # Negative Test 1: Two consecutive O-moves (UNSAT)
    try:
        solver = Solver()
        move_0 = solver.mkConst(solver.getIntegerSort(), "move_0")
        move_1 = solver.mkConst(solver.getIntegerSort(), "move_1")

        # Both moves by O
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, move_0, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, move_1, solver.mkInteger(0)))

        # Alternation constraint
        constraint = solver.mkTerm(
            Kind.IMPLIES,
            solver.mkTerm(Kind.EQUAL, move_0, solver.mkInteger(0)),
            solver.mkTerm(Kind.EQUAL, move_1, solver.mkInteger(1))
        )
        solver.assertFormula(constraint)

        is_sat = solver.checkSat().isSat()
        results["test_consecutive_O_moves"] = {
            "status": "pass" if not is_sat else "fail",
            "satisfiable": is_sat,
            "interpretation": "Two consecutive O-moves violates alternation (should be UNSAT)"
        }
    except Exception as e:
        results["test_consecutive_O_moves"] = {"status": "error", "error": str(e)}

    # Negative Test 2: Violated alternation in longer sequence
    try:
        solver = Solver()
        moves = [solver.mkConst(solver.getIntegerSort(), f"m_{i}") for i in range(5)]

        # Invalid sequence: O, O, P, P, O
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, moves[0], solver.mkInteger(0)))  # O
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, moves[1], solver.mkInteger(0)))  # O (violation!)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, moves[2], solver.mkInteger(1)))  # P
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, moves[3], solver.mkInteger(1)))  # P
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, moves[4], solver.mkInteger(0)))  # O

        # Alternation constraints
        for i in range(4):
            constraint = solver.mkTerm(
                Kind.IMPLIES,
                solver.mkTerm(Kind.EQUAL, moves[i], solver.mkInteger(0)),
                solver.mkTerm(Kind.EQUAL, moves[i+1], solver.mkInteger(1))
            )
            solver.assertFormula(constraint)

        is_sat = solver.checkSat().isSat()
        results["test_invalid_sequence"] = {
            "status": "pass" if not is_sat else "fail",
            "satisfiable": is_sat,
            "sequence": "O, O, P, P, O",
            "interpretation": "Sequence with two consecutive O-moves violates alternation"
        }
    except Exception as e:
        results["test_invalid_sequence"] = {"status": "error", "error": str(e)}

    # Negative Test 3: Strategy formula contradiction (sympy)
    try:
        if TOOL_MANIFEST["sympy"]["tried"]:
            # If |Strat(A)| = 0, then |Strat(A → B)| = 0 for all B
            strat_a = sp.Symbol("strat_a", integer=True, nonnegative=True)
            strat_b = sp.Symbol("strat_b", integer=True, positive=True)
            formula = strat_a ** strat_b

            # When strat_a = 0, result should be 0 (for strat_b > 0)
            result = formula.subs([(strat_a, 0), (strat_b, 2)])
            expected = 0

            results["test_strategy_zero_strat"] = {
                "status": "pass" if result == expected else "fail",
                "interpretation": "|Strat(A → B)| = 0 when |Strat(A)| = 0",
                "computed": int(result),
                "expected": expected,
                "match": result == expected
            }
        else:
            results["test_strategy_zero_strat"] = {"status": "skipped", "reason": "sympy not installed"}
    except Exception as e:
        results["test_strategy_zero_strat"] = {"status": "error", "error": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS: Edge cases and limits
# =====================================================================

def run_boundary_tests():
    """
    Boundary tests: maximal plays, edge cases in strategy counting.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        results["cvc5_unavailable"] = {"status": "skipped", "reason": "cvc5 not installed"}
        return results

    from cvc5 import Solver, Kind

    # Boundary Test 1: Single move by P (no alternation required)
    try:
        solver = Solver()
        move_0 = solver.mkConst(solver.getIntegerSort(), "move_0")

        # Single move by P
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, move_0, solver.mkInteger(1)))

        # No alternation constraint needed for single move
        is_sat = solver.checkSat().isSat()
        results["test_single_P_move"] = {
            "status": "pass" if is_sat else "fail",
            "satisfiable": is_sat,
            "interpretation": "Single P-move is valid"
        }
    except Exception as e:
        results["test_single_P_move"] = {"status": "error", "error": str(e)}

    # Boundary Test 2: Maximal alternating play (10 moves)
    try:
        solver = Solver()
        moves = [solver.mkConst(solver.getIntegerSort(), f"move_{i}") for i in range(10)]

        # Alternating: O, P, O, P, O, P, O, P, O, P
        for i in range(10):
            expected_player = 0 if i % 2 == 0 else 1
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, moves[i], solver.mkInteger(expected_player)))

        # Alternation constraint
        for i in range(9):
            constraint = solver.mkTerm(
                Kind.IMPLIES,
                solver.mkTerm(Kind.EQUAL, moves[i], solver.mkInteger(0)),
                solver.mkTerm(Kind.EQUAL, moves[i+1], solver.mkInteger(1))
            )
            solver.assertFormula(constraint)

        is_sat = solver.checkSat().isSat()
        results["test_maximal_10move_alternation"] = {
            "status": "pass" if is_sat else "fail",
            "satisfiable": is_sat,
            "moves": 10,
            "interpretation": "10-move alternating play satisfies constraint"
        }
    except Exception as e:
        results["test_maximal_10move_alternation"] = {"status": "error", "error": str(e)}

    # Boundary Test 3: Strategy formula with large exponent (sympy)
    try:
        if TOOL_MANIFEST["sympy"]["tried"]:
            # |Strat(A → B)| where |Strat(A)| = 3, |Strat(B)| = 4
            # Result: 3^4 = 81
            strat_a = sp.Symbol("strat_a", integer=True, positive=True)
            strat_b = sp.Symbol("strat_b", integer=True, positive=True)
            formula = strat_a ** strat_b

            result = formula.subs([(strat_a, 3), (strat_b, 4)])
            expected = 81

            results["test_strategy_large_exponent"] = {
                "status": "pass" if result == expected else "fail",
                "formula": "|Strat(A → B)| = 3^4",
                "computed": int(result),
                "expected": expected,
                "match": result == expected
            }
        else:
            results["test_strategy_large_exponent"] = {"status": "skipped", "reason": "sympy not installed"}
    except Exception as e:
        results["test_strategy_large_exponent"] = {"status": "error", "error": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Mark tools as used
    if TOOL_MANIFEST["cvc5"]["tried"]:
        TOOL_MANIFEST["cvc5"]["used"] = True
    if TOOL_MANIFEST["sympy"]["tried"]:
        TOOL_MANIFEST["sympy"]["used"] = True

    results = {
        "name": "sim_cvc5_game_semantics_hyland_ong",
        "description": "Hyland-Ong game semantics: alternation constraint via cvc5 SMT, strategy counting via sympy",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_game_semantics_hyland_ong_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
