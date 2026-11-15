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
