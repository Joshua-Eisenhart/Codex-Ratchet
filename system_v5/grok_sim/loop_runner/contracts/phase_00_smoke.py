"""phase_00_smoke.py — importability + required-function existence + return-type checks.

This phase is hidden from Grok. Grok only sees the public API contract in
loop_runner/prompts/public_api_contract.md.

Goal-stability: once green, this phase's pass criteria are frozen.
"""

REQUIRED_FUNCTIONS = [
    # (function_name, expected_return_type_hint)
    ("run_engine",                dict),
    ("compute_axis_metrics",      dict),
    ("mequivalence_demo",         dict),
    ("finite_witness",            int),
    ("noncomm_pair",              dict),
    ("gstack_layers",             dict),
    ("flux_holonomy",             float),
    ("weyl_chirality_probe",      dict),
    ("tool_manifest",             dict),
    ("sidequest_claim_boundary",  dict),
]


def _check_callable(candidate, name):
    fn = getattr(candidate, name, None)
    if fn is None:
        return False, f"function `{name}` not exported"
    if not callable(fn):
        return False, f"`{name}` exists but is not callable"
    return True, None


def _check_return_type(candidate, name, expected_type):
    fn = getattr(candidate, name)
    try:
        if name == "finite_witness":
            result = fn(8)   # takes truncation arg
        else:
            result = fn()
    except Exception as e:
        return False, f"`{name}()` raised {type(e).__name__}: {str(e)[:200]}", None
    if not isinstance(result, expected_type):
        return False, f"`{name}()` returned {type(result).__name__}, expected {expected_type.__name__}", result
    return True, None, result


def run(candidate):
    failures = []
    successes = []

    # 1. Function existence
    for fn_name, _expected_type in REQUIRED_FUNCTIONS:
        ok, msg = _check_callable(candidate, fn_name)
        if not ok:
            failures.append({"check": f"function_exists_{fn_name}", "msg": msg})
        else:
            successes.append(f"{fn_name}: exported and callable")

    # If function existence failed, return early
    if failures:
        return {
            "pass": False,
            "failures": failures,
            "successes": successes,
            "metrics": {"functions_present": len(successes), "functions_required": len(REQUIRED_FUNCTIONS)},
            "graveyard_companions": ["function name typos must die", "extra/missing args must die"],
        }

    # 2. Each function returns the expected type
    return_results = {}
    for fn_name, expected_type in REQUIRED_FUNCTIONS:
        ok, msg, result = _check_return_type(candidate, fn_name, expected_type)
        if not ok:
            failures.append({"check": f"return_type_{fn_name}", "msg": msg})
        else:
            successes.append(f"{fn_name}: returns {expected_type.__name__}")
            return_results[fn_name] = type(result).__name__

    # 3. Deterministic return shape — call twice, check shape stability
    for fn_name, _expected_type in REQUIRED_FUNCTIONS:
        try:
            if fn_name == "finite_witness":
                r1 = candidate.finite_witness(8)
                r2 = candidate.finite_witness(8)
            else:
                r1 = getattr(candidate, fn_name)()
                r2 = getattr(candidate, fn_name)()
            # Shape stability — for dicts, check keys match
            if isinstance(r1, dict):
                if set(r1.keys()) != set(r2.keys()):
                    failures.append({
                        "check": f"deterministic_keys_{fn_name}",
                        "msg": f"keys differ between calls: {set(r1.keys()) ^ set(r2.keys())}",
                    })
                else:
                    successes.append(f"{fn_name}: stable key set across calls")
            else:
                successes.append(f"{fn_name}: returned value type stable")
        except Exception as e:
            failures.append({
                "check": f"deterministic_call_{fn_name}",
                "msg": f"second call raised {type(e).__name__}: {str(e)[:200]}",
            })

    metrics = {
        "functions_present": sum(1 for f, _ in REQUIRED_FUNCTIONS if getattr(candidate, f, None) is not None),
        "functions_required": len(REQUIRED_FUNCTIONS),
        "return_types": return_results,
    }

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "successes": successes,
        "metrics": metrics,
        "graveyard_companions": [
            "function-typo candidates die",
            "candidates that print but don't return die",
            "candidates with non-deterministic return shapes die",
        ],
        "baseline_variants": ["bare-script candidate (no functions exported) baseline"],
    }
