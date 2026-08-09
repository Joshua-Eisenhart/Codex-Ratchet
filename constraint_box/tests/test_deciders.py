import json
from pathlib import Path
from constraintbox.deciders import decide, load_registry, run_registry

def test_every_registered_case_reaches_decision():
    registry=load_registry()
    for kind,spec in registry["question_kinds"].items():
        for payload in spec["cases"].values():
            result=decide(kind,payload,registry)
            assert result["verdicts"]
            assert result["agreed"] is True, (kind, result)

def test_negative_cases_are_refusals():
    registry=load_registry()
    for kind,spec in registry["question_kinds"].items():
        result=decide(kind,spec["cases"]["negative"],registry)
        assert set(result["verdicts"].values()) == {False}, (kind,result)

def test_receipt_has_full_case_payloads():
    out=run_registry()
    assert out["disagreements"] == []
    assert all(set(v["cases"]) >= {"positive","negative"} for v in out["question_kinds"].values())
