from __future__ import annotations


def test_static_integrity_checker_does_not_require_unused_libcst():
    import constraintbox.gate_integrity_ast as module

    assert module.GateIntegrityChecker.__name__ == "GateIntegrityChecker"
