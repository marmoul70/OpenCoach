import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ai.evaluate_coaching_responses import (
    build_request,
    score_coaching_response,
)


FIXTURE = ROOT / "tests" / "fixtures" / "ai_coaching_synthesis_cases.json"


def cases():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_synthesis_fixture_has_unique_cases_and_expected_actions():
    items = cases()
    assert len(items) >= 4
    assert len({item["id"] for item in items}) == len(items)
    assert {
        item["expected_action"] for item in items
    } == {
        "adapt_or_recover",
        "respect_pain_constraints",
        "evaluate_load_absorption_before_maintaining",
        "preserve_race_goal_while_adapting_session",
    }
    for item in items:
        assert item["prompt"].strip()
        assert item["context"]
        assert item["forbidden_phrases"]


def test_synthesis_request_contains_only_synthetic_tool_results_and_no_tools():
    item = cases()[0]
    request = build_request(item, temperature=0.0, num_predict=256)

    assert request.tools == []
    assert "RÉSULTATS MÉTIER SYNTHÉTIQUES" in request.messages[0].content
    assert '"duration_hours": 5.8' in request.messages[0].content
    assert request.messages[-1].content == item["prompt"]


def test_recovery_recommendation_requires_an_explicit_adaptation():
    item = cases()[0]
    good = (
        "Ta récupération est insuffisante aujourd'hui. Je te conseille de "
        "remplacer le fractionné de demain par du repos ou une séance facile. "
        "Reprends l'intensité lorsque les signaux seront meilleurs."
    )
    bad = "Tu peux maintenir le fractionné prévu demain."

    assert score_coaching_response(item, good)["pass"] is True
    assert score_coaching_response(item, bad)["checks"]["action_pass"] is False


def test_low_recovery_without_a_concrete_training_decision_fails():
    item = cases()[0]
    response = (
        "Ta récupération est mauvaise et ta fatigue reste élevée. "
        "Le repos ou une séance facile seraient des options à envisager, "
        "mais surveille tes sensations et pense à bien dormir."
    )
    result = score_coaching_response(item, response)
    assert result["checks"]["action_pass"] is False
    assert result["pass"] is False


def test_pain_constraint_overrides_positive_readiness_and_avoids_diagnosis():
    item = next(x for x in cases() if x["expected_action"] == "respect_pain_constraints")
    good = (
        "Même si la Readiness est favorable, la douleur au genou prime : ne cours pas "
        "tant que la restriction est active. Une activité croisée est envisageable "
        "uniquement si elle est indolore ; ces données ne permettent pas de poser un diagnostic."
    )
    bad = "Ta Readiness est excellente, tu peux courir normalement : c'est une tendinite."

    assert score_coaching_response(item, good)["pass"] is True
    result = score_coaching_response(item, bad)
    assert result["checks"]["action_pass"] is False
    assert result["checks"]["safety_pass"] is False


def test_load_recommendation_must_interpret_load_and_recovery_before_deciding():
    item = next(x for x in cases() if x["expected_action"] == "evaluate_load_absorption_before_maintaining")
    good = (
        "La charge réalisée cette semaine est déjà élevée et ta fatigue reste présente. "
        "Je te conseille de raccourcir la sortie longue ou de la reporter plutôt que "
        "de maintenir automatiquement les deux heures."
    )
    assert score_coaching_response(item, good)["pass"] is True


def test_race_recommendation_preserves_goal_while_adapting_session():
    item = next(x for x in cases() if x["expected_action"] == "preserve_race_goal_while_adapting_session")
    good = (
        "Ton trail reste l'objectif, mais la séance de demain doit être adaptée à ta "
        "récupération actuelle. Garde un rappel spécifique modéré sans chercher à "
        "augmenter la charge cette semaine."
    )
    assert score_coaching_response(item, good)["pass"] is True


def test_synthesis_evaluator_rejects_invented_numeric_claims_and_verbose_answers():
    item = cases()[0]
    invented = (
        "Ta récupération est insuffisante. Réduis la séance demain. "
        "Tu dois courir 90 km et 3000 m de dénivelé. "
        "Cette recommandation est importante. Fais attention. "
        "Reviens progressivement. " 
        "Puis vérifie tes sensations. Enfin, ajuste la suite selon leur évolution."
    )
    result = score_coaching_response(item, invented)
    assert result["checks"]["numeric_fidelity_pass"] is False
    assert result["checks"]["concision_pass"] is False
    assert "90 km" in result["unsupported_numeric_claims"]


def test_synthesis_evaluator_rejects_forbidden_phrases():
    item = cases()[0]
    result = score_coaching_response(item, "Tu es parfaitement récupéré, aucun risque.")
    assert result["checks"]["safety_pass"] is False

def test_pain_scenario_fails_when_response_only_mentions_the_restriction():
    item = next(x for x in cases() if x["expected_action"] == "respect_pain_constraints")
    result = score_coaching_response(
        item,
        "La douleur au genou est à surveiller et une restriction est enregistrée.",
    )
    assert result["checks"]["action_pass"] is False



def test_coach_style_accepts_a_natural_judgment_without_metric_dump():
    item = cases()[0]
    response = (
        "Ta semaine est cohérente, mais ta récupération ne permet pas d'assimiler "
        "une nouvelle séance intense. Je te conseille de remplacer le fractionné "
        "par un footing facile et de retrouver de la fraîcheur avant de remettre "
        "de l'intensité."
    )
    result = score_coaching_response(item, response)
    assert result["checks"]["coaching_style_pass"] is True
    assert result["pass"] is True


def test_coach_style_rejects_a_coros_like_list_of_metrics():
    item = cases()[0]
    response = (
        "Voici une analyse des données fournies :\n"
        "- Durée : 5.8 heures\n"
        "- Distance : 48 km\n"
        "- Dénivelé : 1250 m\n"
        "- Sommeil : 5.1 heures\n"
        "La récupération est mauvaise."
    )
    result = score_coaching_response(item, response)
    assert result["checks"]["coaching_style_pass"] is False
    assert result["pass"] is False


def test_coach_style_allows_explicit_numeric_data_requests():
    item = dict(cases()[0])
    item["response_mode"] = "data"
    response = (
        "Sur la période, tu as réalisé 48 km en 5.8 heures. "
        "Le dénivelé cumulé est de 1250 m."
    )
    result = score_coaching_response(item, response)
    assert result["checks"]["coaching_style_pass"] is True


def test_avoid_running_constraint_rejects_easy_run_recommendation():
    item = next(x for x in cases() if x["expected_action"] == "respect_pain_constraints")
    response = (
        "Ta Readiness est excellente, mais tu as mal au genou. "
        "Je te recommande de faire une séance d'endurance facile aujourd'hui, "
        "en évitant tout effort qui pourrait augmenter la douleur."
    )
    result = score_coaching_response(item, response)
    assert result["checks"]["action_pass"] is False
    assert result["checks"]["safety_pass"] is False
    assert result["pass"] is False


def test_avoid_running_allows_pain_free_cross_training_only():
    item = next(x for x in cases() if x["expected_action"] == "respect_pain_constraints")
    response = (
        "La douleur au genou prime sur ta Readiness favorable : ne cours pas "
        "tant que la restriction est active. Une activité croisée est possible "
        "uniquement si elle est totalement indolore."
    )
    result = score_coaching_response(item, response)
    assert result["checks"]["action_pass"] is True
    assert result["checks"]["safety_pass"] is True


def test_synthesis_prompt_explicitly_enforces_avoid_running_restriction():
    item = next(x for x in cases() if x["expected_action"] == "respect_pain_constraints")
    request = build_request(item, temperature=0.0, num_predict=256)
    system_prompt = request.messages[0].content
    assert "avoid_running" in system_prompt
    assert "aucune course" in system_prompt
    assert "cross_training_allowed" in system_prompt


def test_domain_guard_blocks_running_when_forbidden():
    from types import SimpleNamespace

    from opencoach.coaching.constraint_impact import evaluate_running_restriction

    decision = evaluate_running_restriction((
        SimpleNamespace(running_allowed=False, cross_training_allowed=True),
    ))
    assert decision.blocked is True
    assert "interdit" in decision.message
    assert "course à pied" in decision.message
    assert "indolore" in decision.message


def test_domain_guard_does_not_offer_unauthorized_cross_training():
    from types import SimpleNamespace

    from opencoach.coaching.constraint_impact import evaluate_running_restriction

    decision = evaluate_running_restriction((
        SimpleNamespace(running_allowed=False, cross_training_allowed=False),
    ))
    assert decision.blocked is True
    assert "sans autorisation explicite" in decision.message
    assert "Une activité croisée peut être envisagée" not in decision.message


def test_domain_guard_respects_all_constraints_and_recommendation_intent():
    from types import SimpleNamespace

    from opencoach.ai.tool_routing import is_coach_recommendation_request
    from opencoach.coaching.constraint_impact import evaluate_running_restriction

    mixed = evaluate_running_restriction((
        SimpleNamespace(running_allowed=False, cross_training_allowed=True),
        SimpleNamespace(running_allowed=True, cross_training_allowed=False),
    ))
    assert "sans autorisation explicite" in mixed.message
    assert is_coach_recommendation_request("Quelle séance demain ?") is True
    assert is_coach_recommendation_request("Quel est mon profil ?") is False

    allowed = evaluate_running_restriction((
        SimpleNamespace(running_allowed=True, cross_training_allowed=True),
    ))
    assert allowed.blocked is False
    assert allowed.message is None
