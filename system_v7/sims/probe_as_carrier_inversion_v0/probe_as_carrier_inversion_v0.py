#!/usr/bin/env python3
"""Finite probe-word rewrite check for the primary-probe inversion branch."""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import z3

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "nonclassical"

TOOL_MANIFEST = {
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite word enumeration, parallel rewrite normalization, quotient grouping, and multiset update",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite structural check that zero/nonzero distinction count is bound to commuting flags",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive independent SMT check over the same commuting-flag/distinction-count relation",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "python_stdlib": "load_bearing",
    "z3": "supportive",
    "cvc5": "supportive",
}

SIM_ID = Path(__file__).resolve().parent.name
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
PAIR_ORDER = (("a", "b"), ("a", "c"), ("b", "c"))


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_spec() -> dict[str, Any]:
    return json.loads((HERE / "spec.json").read_text(encoding="utf-8"))


def pair_key(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def word_text(word: tuple[str, ...]) -> str:
    return "".join(word)


def seed_words(template: list[str]) -> list[tuple[str, ...]]:
    return list(dict.fromkeys(itertools.permutations(template, len(template))))


def single_words(count: int, width: int) -> list[tuple[str, ...]]:
    return [tuple("a" for _ in range(width)) for _ in range(count)]


def parallel_rewrite_once(
    word: tuple[str, ...],
    order: dict[str, int],
    commuting_pairs: set[tuple[str, str]],
) -> tuple[tuple[str, ...], list[dict[str, Any]]]:
    out: list[str] = []
    rewrites: list[dict[str, Any]] = []
    i = 0
    while i < len(word):
        if i + 1 >= len(word):
            out.append(word[i])
            i += 1
            continue
        left, right = word[i], word[i + 1]
        if left == right:
            out.append(left)
            rewrites.append({"at": i, "from": left + right, "to": left, "rule": "idempotent_letter"})
            i += 2
            continue
        if pair_key(left, right) in commuting_pairs and order[left] > order[right]:
            out.extend([right, left])
            rewrites.append({"at": i, "from": left + right, "to": right + left, "rule": "commuting_swap"})
            i += 2
            continue
        out.append(left)
        i += 1
    return tuple(out), rewrites


def normal_form(
    word: tuple[str, ...],
    alphabet: list[str],
    commuting_pairs: set[tuple[str, str]],
) -> tuple[tuple[str, ...], list[dict[str, Any]]]:
    order = {letter: idx for idx, letter in enumerate(alphabet)}
    current = word
    history: list[dict[str, Any]] = []
    for step in range(32):
        next_word, rewrites = parallel_rewrite_once(current, order, commuting_pairs)
        history.append(
            {
                "step": step,
                "before": word_text(current),
                "after": word_text(next_word),
                "rewrites": rewrites,
            }
        )
        if next_word == current:
            return current, history
        current = next_word
    raise RuntimeError(f"rewrite did not converge for {word_text(word)}")


def quotient_classes(normal_forms: dict[str, str]) -> list[list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for word, form in normal_forms.items():
        groups[form].append(word)
    return [sorted(words) for _, words in sorted(groups.items())]


def evolve_bag(words: list[tuple[str, ...]], normal_forms: dict[str, str]) -> dict[str, Any]:
    bag: Counter[str] = Counter()
    seen: set[str] = set()
    log: list[dict[str, Any]] = []
    for word in words:
        raw = word_text(word)
        form = normal_forms[raw]
        if form in seen:
            log.append(
                {
                    "word": raw,
                    "normal_form": form,
                    "action": "delete_no_new_distinction",
                    "multiplicity_delta": 0,
                }
            )
            continue
        seen.add(form)
        bag[raw] += 2
        log.append(
            {
                "word": raw,
                "normal_form": form,
                "action": "duplicate_new_distinction",
                "multiplicity_delta": 2,
            }
        )
    kept_forms = sorted({normal_forms[word] for word, n in bag.items() if n > 0})
    return {
        "word_bag": dict(sorted(bag.items())),
        "surviving_class_count": len(kept_forms),
        "surviving_normal_forms": kept_forms,
        "update_log": log,
    }


def run_mode(
    name: str,
    alphabet: list[str],
    words: list[tuple[str, ...]],
    commuting_pairs: set[tuple[str, str]],
) -> dict[str, Any]:
    forms: dict[str, str] = {}
    histories: dict[str, list[dict[str, Any]]] = {}
    for word in words:
        form, history = normal_form(word, alphabet, commuting_pairs)
        forms[word_text(word)] = word_text(form)
        histories[word_text(word)] = history
    classes = quotient_classes(forms)
    class_count = len(classes)
    distinction_count = max(0, class_count - 1)
    return {
        "mode": name,
        "alphabet": alphabet,
        "input_words": [word_text(word) for word in words],
        "commuting_pairs": [list(pair) for pair in sorted(commuting_pairs)],
        "normal_forms": forms,
        "rewrite_history": histories,
        "quotient_classes": classes,
        "quotient_class_count": class_count,
        "distinction_count": distinction_count,
        "evolution": evolve_bag(words, forms),
    }


def adjacent_swap_neighbors(
    word: tuple[str, ...],
    commuting_pairs: set[tuple[str, str]],
) -> list[tuple[str, ...]]:
    out: list[tuple[str, ...]] = []
    for i in range(len(word) - 1):
        left, right = word[i], word[i + 1]
        if left != right and pair_key(left, right) in commuting_pairs:
            swapped = list(word)
            swapped[i], swapped[i + 1] = swapped[i + 1], swapped[i]
            out.append(tuple(swapped))
    return out


def relation_class_count(
    words: list[tuple[str, ...]],
    commuting_pairs: set[tuple[str, str]],
) -> int:
    parent = {word: word for word in words}

    def find(word: tuple[str, ...]) -> tuple[str, ...]:
        while parent[word] != word:
            parent[word] = parent[parent[word]]
            word = parent[word]
        return word

    def union(left: tuple[str, ...], right: tuple[str, ...]) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    for word in words:
        for neighbor in adjacent_swap_neighbors(word, commuting_pairs):
            union(word, neighbor)
    return len({find(word) for word in words})


def relation_table(words: list[tuple[str, ...]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for flags in itertools.product([False, True], repeat=len(PAIR_ORDER)):
        pairs = {pair for pair, enabled in zip(PAIR_ORDER, flags, strict=True) if enabled}
        count = relation_class_count(words, pairs)
        rows.append(
            {
                "commuting_flags": {f"{left}{right}": enabled for (left, right), enabled in zip(PAIR_ORDER, flags, strict=True)},
                "class_count": count,
                "distinction_count": max(0, count - 1),
            }
        )
    return rows


def z3_relation_check(table: list[dict[str, Any]], single_distinction_count: int) -> dict[str, Any]:
    flag_vars = {f"{left}{right}": z3.Bool(f"z3_commutes_{left}{right}") for left, right in PAIR_ORDER}
    distinction_count = z3.Int("z3_distinction_count")
    cases = []
    for row in table:
        conds = [
            flag_vars[name] if enabled else z3.Not(flag_vars[name])
            for name, enabled in row["commuting_flags"].items()
        ]
        cases.append(z3.And(*(conds + [distinction_count == int(row["distinction_count"])])))
    relation = z3.Or(*cases)
    all_commuting = z3.And(*flag_vars.values())
    none_commuting = z3.And(*[z3.Not(var) for var in flag_vars.values()])

    def verdict(extra: Any) -> str:
        solver = z3.Solver()
        solver.add(relation)
        solver.add(extra)
        return str(solver.check()).lower()

    single_solver = z3.Solver()
    single_count = z3.Int("z3_single_distinction_count")
    single_solver.add(single_count == int(single_distinction_count))
    single_solver.add(single_count != 0)
    return {
        "all_commuting_counterexample": verdict(z3.And(all_commuting, distinction_count != 0)),
        "none_commuting_counterexample": verdict(z3.And(none_commuting, distinction_count <= 0)),
        "single_generator_counterexample": str(single_solver.check()).lower(),
    }


def cvc5_relation_check(table: list[dict[str, Any]], single_distinction_count: int) -> dict[str, Any]:
    def terms_for_solver() -> tuple[cvc5.TermManager, cvc5.Solver, dict[str, Any], Any]:
        tm = cvc5.TermManager()
        solver = cvc5.Solver(tm)
        solver.setLogic("QF_LIA")
        bool_sort = tm.getBooleanSort()
        int_sort = tm.getIntegerSort()
        flag_vars = {f"{left}{right}": tm.mkConst(bool_sort, f"cvc5_commutes_{left}{right}") for left, right in PAIR_ORDER}
        distinction_count = tm.mkConst(int_sort, "cvc5_distinction_count")
        cases = []
        for row in table:
            conds = [
                flag_vars[name] if enabled else tm.mkTerm(Kind.NOT, flag_vars[name])
                for name, enabled in row["commuting_flags"].items()
            ]
            conds.append(tm.mkTerm(Kind.EQUAL, distinction_count, tm.mkInteger(int(row["distinction_count"]))))
            cases.append(tm.mkTerm(Kind.AND, *conds))
        solver.assertFormula(tm.mkTerm(Kind.OR, *cases))
        return tm, solver, flag_vars, distinction_count

    def verdict(extra_builder: Any) -> str:
        tm, solver, flag_vars, distinction_count = terms_for_solver()
        solver.assertFormula(extra_builder(tm, flag_vars, distinction_count))
        return str(solver.checkSat()).lower()

    def all_commuting_bad(tm: cvc5.TermManager, flag_vars: dict[str, Any], distinction_count: Any) -> Any:
        all_flags = tm.mkTerm(Kind.AND, *flag_vars.values())
        nonzero = tm.mkTerm(Kind.NOT, tm.mkTerm(Kind.EQUAL, distinction_count, tm.mkInteger(0)))
        return tm.mkTerm(Kind.AND, all_flags, nonzero)

    def none_commuting_bad(tm: cvc5.TermManager, flag_vars: dict[str, Any], distinction_count: Any) -> Any:
        no_flags = tm.mkTerm(Kind.AND, *[tm.mkTerm(Kind.NOT, var) for var in flag_vars.values()])
        not_positive = tm.mkTerm(Kind.LEQ, distinction_count, tm.mkInteger(0))
        return tm.mkTerm(Kind.AND, no_flags, not_positive)

    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_LIA")
    single_count = tm.mkConst(tm.getIntegerSort(), "cvc5_single_distinction_count")
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, single_count, tm.mkInteger(int(single_distinction_count))))
    solver.assertFormula(tm.mkTerm(Kind.NOT, tm.mkTerm(Kind.EQUAL, single_count, tm.mkInteger(0))))
    return {
        "all_commuting_counterexample": verdict(all_commuting_bad),
        "none_commuting_counterexample": verdict(none_commuting_bad),
        "single_generator_counterexample": str(solver.checkSat()).lower(),
    }


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    spec = load_spec()
    template = list(spec["word_template"])
    base_words = seed_words(template)
    all_commuting_pairs = {pair_key(*pair) for pair in spec["modes"]["all_commuting"]["commuting_pairs"]}
    empty_pairs: set[tuple[str, str]] = set()
    runs = {
        "single_generator": run_mode(
            "single_generator",
            ["a"],
            single_words(len(base_words), len(template)),
            empty_pairs,
        ),
        "all_commuting": run_mode(
            "all_commuting",
            list(spec["alphabet"]),
            base_words,
            all_commuting_pairs,
        ),
        "noncommuting": run_mode(
            "noncommuting",
            list(spec["alphabet"]),
            base_words,
            empty_pairs,
        ),
    }
    table = relation_table(base_words)
    z3_check = z3_relation_check(table, runs["single_generator"]["distinction_count"])
    cvc5_check = cvc5_relation_check(table, runs["single_generator"]["distinction_count"])
    decisive_flip_control = {
        "single_generator_distinctions_vanish": runs["single_generator"]["distinction_count"] == 0,
        "all_commuting_distinctions_vanish": runs["all_commuting"]["distinction_count"] == 0,
        "noncommuting_distinctions_survive": runs["noncommuting"]["distinction_count"] > 0,
        "single_generator_class_count": runs["single_generator"]["quotient_class_count"],
        "all_commuting_class_count": runs["all_commuting"]["quotient_class_count"],
        "noncommuting_class_count": runs["noncommuting"]["quotient_class_count"],
    }
    smt_ok = all(value == "unsat" for value in z3_check.values()) and all(value == "unsat" for value in cvc5_check.values())
    expected = spec["modes"]
    expected_ok = (
        runs["single_generator"]["quotient_class_count"] == int(expected["single_generator"]["expected_class_count"])
        and runs["single_generator"]["distinction_count"] == int(expected["single_generator"]["expected_distinction_count"])
        and runs["all_commuting"]["quotient_class_count"] == int(expected["all_commuting"]["expected_class_count"])
        and runs["all_commuting"]["distinction_count"] == int(expected["all_commuting"]["expected_distinction_count"])
        and runs["noncommuting"]["quotient_class_count"] >= int(expected["noncommuting"]["expected_min_class_count"])
        and runs["noncommuting"]["distinction_count"] >= int(expected["noncommuting"]["expected_min_distinction_count"])
    )
    all_pass = all(decisive_flip_control.values()) and smt_ok and expected_ok
    failures: list[str] = []
    if not decisive_flip_control["single_generator_distinctions_vanish"]:
        failures.append("single_generator_distinctions_survived")
    if not decisive_flip_control["all_commuting_distinctions_vanish"]:
        failures.append("all_commuting_distinctions_survived")
    if not decisive_flip_control["noncommuting_distinctions_survive"]:
        failures.append("noncommuting_distinctions_did_not_survive")
    if not smt_ok:
        failures.append("smt_relation_check_failed")
    if not expected_ok:
        failures.append("expected_fixture_counts_failed")
    result = {
        "schema": "codex_ratchet.word_probe_inversion_result.v1",
        "sim_id": SIM_ID,
        "engine": "python_word_rewrite_plus_smt",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "does_not_self_upgrade": True,
        "all_pass": all_pass,
        "build_status": "PASS" if all_pass else "BUILD FAILED",
        "failures": failures,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_path": str(Path(__file__).resolve()),
        "source_sha256": sha256_of(Path(__file__).resolve()),
        "spec_sha256": sha256_of(HERE / "spec.json"),
        "claim_ceiling": spec["claim_ceiling"],
        "claim": "Finite probe words over a common letter multiset keep order distinctions exactly when the alphabet is not forced to commute.",
        "decisive_flip_control": decisive_flip_control,
        "rewrite_modes": runs,
        "smt_relation": {
            "relation_table": table,
            "z3": z3_check,
            "cvc5": cvc5_check,
            "all_smt_counterexamples_unsat": smt_ok,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "packages_used": ["python_stdlib", "z3", "cvc5"],
    }
    out = RESULTS / f"{SIM_ID}_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": all_pass,
                "build_status": result["build_status"],
                "result_path": str(out),
                "flip_control": decisive_flip_control,
                "smt_ok": smt_ok,
                "failures": failures,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
