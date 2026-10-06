"""Exact supported-domain regressions; no model, live retrieval or source fetching."""
from fractions import Fraction
from itertools import permutations

import pytest

from backend.rules.case_features import build_case_features
from backend.rules.case_readiness import assess_case
from backend.rules.distribution import allocate


def case(*relatives):
    return {"mentioned_relatives": [{"relation": r, "count": n} for r, n in relatives]}


def solve(parsed):
    from backend.rules.residuaries import select_solver_rules
    return allocate(parsed, select_solver_rules(parsed))


def shares(result):
    return {row["heir"]: Fraction(row["per_head_shares"])
            for row in result["post_tasil"]["distribution"]}


@pytest.mark.parametrize("relatives,expected", [
    ([("ابن", 1)], {"ابن": "1"}),
    ([("ابن", 2)], {"ابن": "1/2"}),
    ([("ابن", 3)], {"ابن": "1/3"}),
    ([("ابن", 1), ("بنت", 1)], {"ابن": "2/3", "بنت": "1/3"}),
    ([("ابن", 2), ("بنت", 2)], {"ابن": "1/3", "بنت": "1/6"}),
    ([("زوجة", 1), ("ابن", 2)], {"زوجة": "1/8", "ابن": "7/16"}),
    ([("زوجة", 1), ("ابن", 1), ("بنت", 1)], {"زوجة": "1/8", "ابن": "7/12", "بنت": "7/24"}),
    ([("زوج", 1), ("ابن", 1), ("بنت", 1)], {"زوج": "1/4", "ابن": "1/2", "بنت": "1/4"}),
    ([("أم", 1), ("ابن", 2)], {"أم": "1/6", "ابن": "5/12"}),
    ([("أب", 1), ("أم", 1), ("ابن", 2)], {"أب": "1/6", "أم": "1/6", "ابن": "1/3"}),
])
def test_children_families(relatives, expected):
    result = solve(case(*relatives))
    assert shares(result) == {r: Fraction(f) for r, f in expected.items()}
    assert result["verification"] == {"total_fraction": "1", "is_consistent": True}
    assert all(f >= 0 for f in shares(result).values())


@pytest.mark.parametrize("relation", ["ابن بنت", "بنت بنت", "ابن ابن بنت", "son_of_daughter", "daughter_of_daughter", "daughter's son"])
def test_matrilineal_descendants_do_not_activate_spouse_reduction(relation):
    parsed = case(("زوجة", 1), (relation, 1))
    features = build_case_features(parsed)
    assert features["has_descendant"] is False
    assert features["has_heir_descendant"] is False
    assert features["has_biological_descendant"] is True
    assert assess_case("مسألة ميراث", parsed, [])["reason"] == "unsupported_matrilineal_descendant"
    with pytest.raises(ValueError, match="unsupported_matrilineal_descendant"):
        solve(parsed)


@pytest.mark.parametrize("relation", ["ابن", "بنت", "ابن ابن", "بنت ابن", "ابن ابن ابن", "son_of_son", "daughter_of_son"])
def test_inheriting_descendant_direction(relation):
    features = build_case_features(case((relation, 1)))
    assert features["has_descendant"] is True
    assert features["has_heir_descendant"] is True


@pytest.mark.parametrize("spouse", ["زوج", "زوجة"])
def test_umariyyat_never_uses_whole_estate_third(spouse):
    from backend.rules.residuaries import select_solver_rules
    parsed = case((spouse, 1), ("أم", 1), ("أب", 1))
    rules = select_solver_rules(parsed)
    decision = assess_case("مسألة ميراث", parsed, rules)
    assert decision["decision_state"] == "specialist_referral"
    assert decision["reason"] == "unsupported_umariyyat"
    with pytest.raises(ValueError, match="unsupported_umariyyat"):
        allocate(parsed, rules)


def test_father_sibling_presence_affects_features_but_unknown_exclusion_refers():
    from backend.rules.residuaries import select_solver_rules
    parsed = case(("أب", 1), ("أم", 1), ("أخ شقيق", 2))
    features = build_case_features(parsed)
    assert features["sibling_count"] == 2
    assert features["present_in_case"]["أخ شقيق"] == 2
    rules = select_solver_rules(parsed)
    assert "mother_with_siblings" in {r["rule_id"] for r in rules}
    assert assess_case("مسألة ميراث", parsed, rules)["reason"] == "unsupported_sibling_exclusion_policy"
    with pytest.raises(ValueError, match="unsupported_sibling_exclusion_policy"):
        allocate(parsed, rules)


def test_source_backed_son_exclusion_retains_presence_and_zero_share():
    from backend.rules.population import prepare_case
    parsed = case(("ابن", 2), ("ابن ابن", 3))
    population = prepare_case(parsed)
    assert population.present_in_case == {"ابن": 2, "ابن ابن": 3}
    assert population.eligible_to_inherit == {"ابن": 2}
    assert set(population.excluded_by_another_heir) == {"ابن ابن"}
    assert build_case_features(parsed)["present_in_case"] == population.present_in_case
    result = solve(parsed)
    assert shares(result) == {"ابن": Fraction(1, 2), "ابن ابن": Fraction(0)}
    assert {row["heir"] for row in result["blocked"]} == {"ابن ابن"}
    assert any(t["category"] == "exclusion" and t["source_ids"] for t in result["rule_trace"])


def test_trace_is_exact_and_separates_sources_from_arithmetic():
    result = solve(case(("زوجة", 1), ("ابن", 2)))
    trace = result["rule_trace"]
    fixed = next(t for t in trace if t["category"] == "fixed_share")
    children = next(t for t in trace if t["category"] == "residuary")
    assert fixed["source_ids"] == ["quran:4:12"]
    assert children["rule_id"] == "children_residuary_equal_males"
    assert children["input_residue"] == "7/8"
    assert children["per_head_fractions"] == {"ابن": "7/16"}
    assert children["source_ids"] and all(s.startswith("fiqh:") for s in children["source_ids"])


@pytest.mark.parametrize("daughters", [1, 2, 7])
def test_daughters_without_sons_do_not_use_residuary_family(daughters):
    from backend.rules.residuaries import select_solver_rules
    rules = select_solver_rules(case(("بنت", daughters)))
    assert len(rules) == 1 and "fraction" in rules[0]["result"]
    with pytest.raises(ValueError):
        allocate(case(("بنت", daughters)), rules)  # No invented radd to complete the estate.


def test_pipeline_and_public_case_details_use_new_family(monkeypatch):
    from backend.pipeline import qwen_pipeline as pipeline
    from backend.pipeline.educational_pipeline import _run_request
    from backend.schemas.case import PipelineOutput
    parsed = case(("ابن", 2))
    monkeypatch.setattr(pipeline, "parse_relations", lambda _: parsed)
    monkeypatch.setattr(pipeline, "retrieve_fiqh", lambda _: [])
    monkeypatch.setattr(pipeline, "enrich_sources", lambda rules: rules)
    output = pipeline.run_pipeline("مات وترك ابنان")
    assert output["decision_state"] == "ready"
    assert output["result"]["verification"]["is_consistent"]
    assert PipelineOutput.model_validate(output).model_dump()["result"]["rule_trace"]
    response = _run_request("مات وترك ابنان", "case", case_result=output)
    assert response["case_details"]["result"]["rule_trace"]
    assert response["decision_state"] == "ready"


def test_supported_domain_properties():
    """Exhaustive bounded property checks without introducing a new dependency convention."""
    from backend.rules.residuaries import ResiduaryFamily
    family = ResiduaryFamily("direct_children", 10, {"ابن": 2, "بنت": 1})
    for sons in range(1, 31):
        for daughters in range(0, 21):
            counts = {"ابن": sons, **({"بنت": daughters} if daughters else {})}
            for residue in [Fraction(0), Fraction(1), Fraction(7, 8), Fraction(17, 24)]:
                individual = family.distribute(counts, residue)
                assert sum((individual[r] * n for r, n in counts.items()), Fraction()) == residue
                assert all(f >= 0 for f in individual.values())
                if daughters:
                    assert individual["ابن"] == 2 * individual["بنت"]
                else:
                    assert individual["ابن"] == residue / sons


def test_input_order_and_duplicate_aggregation_properties():
    for sons in range(1, 8):
        for daughters in range(1, 5):
            relatives = [("زوجة", 1), ("أم", 1), ("ابن", sons), ("بنت", daughters)]
            expected = shares(solve(case(*relatives)))
            for order in permutations(relatives):
                result = solve(case(*order))
                assert shares(result) == expected
                assert Fraction(result["verification"]["total_fraction"]) == 1
            duplicate = case(("ابن", sons), ("ابن", 1))
            assert shares(solve(duplicate))["ابن"] == Fraction(1, sons + 1)


def test_uncovered_competing_heirs_never_receive_a_guessed_share():
    for other in ["أخ شقيق", "عم", "جد", "ابن بنت"]:
        with pytest.raises(ValueError):
            solve(case(("ابن", 2), (other, 1)))


def test_external_impediment_cannot_silently_change_presence_policy():
    parsed = case(("ابن", 1), ("أم", 1))
    parsed["mentioned_relatives"][0]["barred_by_external_impediment"] = True
    assert build_case_features(parsed)["son_count"] == 1
    assert assess_case("مسألة ميراث", parsed, [])["reason"] == "unsupported_external_impediment_policy"
    with pytest.raises(ValueError, match="unsupported_external_impediment_policy"):
        solve(parsed)


def test_selected_rule_conditions_and_exact_types_are_rechecked():
    from copy import deepcopy
    from backend.rules.residuaries import select_solver_rules, ResiduaryFamily
    parsed = case(("زوجة", 1), ("ابن", 2))
    rules = select_solver_rules(parsed)
    wrong = deepcopy(rules)
    wrong[0]["conditions"]["has_descendant"] = False
    with pytest.raises(ValueError, match="inapplicable_selected_rule"):
        allocate(parsed, wrong)
    wrong = deepcopy(rules)
    wrong[0]["result"]["fraction"] = 0.125
    with pytest.raises(ValueError):
        allocate(parsed, wrong)
    with pytest.raises(ValueError):
        ResiduaryFamily("direct_children", 10, {"ابن": 1}).distribute({"ابن": 2}, 0.5)
    wrong = deepcopy(rules)
    wrong[-1]["result"]["male_weight"] = 3
    with pytest.raises(ValueError, match="unsupported_children_strategy"):
        allocate(parsed, wrong)
    with pytest.raises(ValueError, match="unsupported_competing_residuaries"):
        allocate(parsed, [*rules, rules[-1]])


def test_new_source_snapshots_preserve_integrity_and_provenance():
    import hashlib
    import json
    from pathlib import Path
    data = json.loads(Path("backend/rules/solver_sources.json").read_text(encoding="utf-8"))
    for source_id, passage in data["passages"].items():
        assert source_id.startswith("fiqh:" + passage["chunk_id"])
        assert hashlib.sha256(passage["exact_text"].encode()).hexdigest() == passage["text_sha256"]
        assert passage["excerpt_char_end"] - passage["excerpt_char_start"] == len(passage["exact_text"])
        assert passage["provenance"]["verified_source"]
        assert passage["provenance"]["volume"] == 3
        assert passage["provenance"]["section"]
        assert passage["provenance"]["document_sha256"]


@pytest.mark.parametrize("relatives,reason", [
    ([("زوج", 1), ("أم", 1), ("أب", 1)], "unsupported_umariyyat"),
    ([("زوجة", 1), ("ابن بنت", 1)], "unsupported_matrilineal_descendant"),
    ([("ابن", 1), ("عم", 1)], "unsupported_heir_or_residuary"),
])
def test_pipeline_preserves_named_referrals(relatives, reason, monkeypatch):
    from backend.pipeline import qwen_pipeline as pipeline
    monkeypatch.setattr(pipeline, "enrich_sources", lambda rules: rules)
    monkeypatch.setattr(pipeline, "retrieve_fiqh", lambda _: [])
    output = pipeline.run_pipeline("مسألة ميراث", parsed_relations=case(*relatives))
    assert output["decision_state"] == "specialist_referral"
    assert output["case_readiness"]["reason"] == reason
    assert output["result"] is None
