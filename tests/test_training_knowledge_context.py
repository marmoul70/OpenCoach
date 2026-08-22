from datetime import date

import pytest

from opencoach.planning import (
    KnowledgeRequirementReason,
    TrainingKnowledgeContext,
    TrainingKnowledgeItem,
    TrainingKnowledgeRequirements,
    TrainingKnowledgeSelection,
    TrainingKnowledgeSource,
    build_training_knowledge_context,
)


def create_source(
    source_id="source-1",
):
    return TrainingKnowledgeSource(
        source_id=source_id,
        source_type="systematic_review",
        title="Review",
    )


def create_item(
    *,
    knowledge_id="knowledge-1",
    topic="periodization",
    applicability=(
        "general_endurance",
    ),
    sources=None,
):
    if sources is None:
        sources = (
            create_source(),
        )

    return TrainingKnowledgeItem(
        knowledge_id=knowledge_id,
        topic=topic,
        statement="Connaissance test.",
        rationale="Justification test.",
        evidence_level="moderate",
        applicability=tuple(
            applicability
        ),
        sources=tuple(
            sources
        ),
        valid_from=date(
            2027,
            1,
            1,
        ),
    )


def create_requirements():
    return TrainingKnowledgeRequirements(
        topics=(
            "periodization",
            "load_progression",
        ),
        applicabilities=(
            "general_endurance",
            "trail_running",
        ),
        reasons=(
            KnowledgeRequirementReason(
                requirement="periodization",
                reason="Planification de saison.",
            ),
            KnowledgeRequirementReason(
                requirement="trail_running",
                reason="Course trail.",
            ),
        ),
    )


def create_selection(
    *,
    topics=None,
    applicabilities=None,
    items=None,
):
    if topics is None:
        topics = (
            "periodization",
            "load_progression",
        )

    if applicabilities is None:
        applicabilities = (
            "general_endurance",
            "trail_running",
        )

    if items is None:
        items = (
            create_item(),
        )

    return TrainingKnowledgeSelection(
        knowledge_base_id="training-knowledge",
        knowledge_version="2027.03",
        items=tuple(
            items
        ),
        requested_topics=tuple(
            topics
        ),
        requested_applicabilities=tuple(
            applicabilities
        ),
        minimum_evidence_level=None,
    )


def test_context_preserves_selected_knowledge() -> None:
    context = build_training_knowledge_context(
        requirements=create_requirements(),
        selection=create_selection(),
    )

    assert isinstance(
        context,
        TrainingKnowledgeContext,
    )

    assert context.knowledge_ids == (
        "knowledge-1",
    )

    assert (
        context.knowledge_version
        == "2027.03"
    )


def test_context_contains_selection_reasons() -> None:
    requirements = create_requirements()

    context = build_training_knowledge_context(
        requirements=requirements,
        selection=create_selection(),
    )

    assert (
        context.selection_reasons
        == requirements.reasons
    )


def test_context_contains_no_python_policy() -> None:
    context = build_training_knowledge_context(
        requirements=create_requirements(),
        selection=create_selection(),
    )

    assert not hasattr(
        context,
        "policy",
    )

    assert not hasattr(
        context,
        "hard_limits",
    )


def test_context_deduplicates_sources() -> None:
    shared_source = create_source(
        "shared"
    )

    items = (
        create_item(
            knowledge_id="one",
            sources=(
                shared_source,
            ),
        ),
        create_item(
            knowledge_id="two",
            topic="load_progression",
            sources=(
                shared_source,
            ),
        ),
    )

    context = build_training_knowledge_context(
        requirements=create_requirements(),
        selection=create_selection(
            items=items,
        ),
    )

    assert len(
        context.sources
    ) == 1

    assert (
        context.sources[0].source_id
        == "shared"
    )


def test_empty_selection_is_explicit() -> None:
    context = build_training_knowledge_context(
        requirements=create_requirements(),
        selection=create_selection(
            items=(),
        ),
    )

    assert context.empty is True


def test_mismatched_topics_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="topics",
    ):
        build_training_knowledge_context(
            requirements=create_requirements(),
            selection=create_selection(
                topics=(
                    "periodization",
                ),
            ),
        )


def test_mismatched_applicabilities_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="applicabilités",
    ):
        build_training_knowledge_context(
            requirements=create_requirements(),
            selection=create_selection(
                applicabilities=(
                    "general_endurance",
                ),
            ),
        )
