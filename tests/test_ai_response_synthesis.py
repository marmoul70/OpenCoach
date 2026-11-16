"""Tests ciblés des contrôles de présentation de la synthèse IA."""

from opencoach.ai.response_synthesis import _coach_response_needs_rewrite


def test_actionable_guidance_after_context_sentence_is_not_rejected():
    answer = (
        "Les données montrent une charge élevée cette semaine. "
        "Je te conseille de réduire la séance intense prévue demain."
    )

    assert _coach_response_needs_rewrite(
        "Que me conseilles-tu pour demain ?",
        answer,
    ) is False


def test_descriptive_answer_without_coaching_judgment_is_rejected():
    answer = (
        "Les données montrent une charge élevée cette semaine. "
        "La récupération est également limitée."
    )

    assert _coach_response_needs_rewrite(
        "Que me conseilles-tu pour demain ?",
        answer,
    ) is True


def test_explicit_request_for_metrics_keeps_structured_numeric_answer():
    answer = "Sur la période, tu as réalisé 48 km en 5 heures."

    assert _coach_response_needs_rewrite(
        "Donne-moi les chiffres de ma semaine.",
        answer,
    ) is False
