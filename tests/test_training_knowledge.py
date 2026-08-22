from datetime import date

import pytest

from opencoach.planning import (
    TrainingKnowledgeBase,
    TrainingKnowledgeItem,
    TrainingKnowledgeSource,
)


def create_source():
    return TrainingKnowledgeSource(
        source_id="review-2027",
        source_type="systematic_review",
        title="Endurance training review",
        authors="Test et al.",
        publication_year=2027,
        reference="doi:test",
    )


def create_item(
    *,
    knowledge_id="load-001",
    topic="load_progression",
    valid_from=date(
        2027,
        1,
        1,
    ),
    valid_until=None,
    applicability=(
        "general_endurance",
    ),
):
    return TrainingKnowledgeItem(
        knowledge_id=knowledge_id,
        topic=topic,
        statement=(
            "La progression de charge doit être "
            "individualisée selon la réponse de l'athlète."
        ),
        rationale=(
            "Une valeur universelle ne décrit pas "
            "la tolérance individuelle."
        ),
        evidence_level="moderate",
        applicability=tuple(
            applicability
        ),
        sources=(
            create_source(),
        ),
        valid_from=valid_from,
        valid_until=valid_until,
    )


def create_base(
    *items,
):
    if not items:
        items = (
            create_item(),
        )

    return TrainingKnowledgeBase(
        knowledge_base_id="training-knowledge",
        version="2027.01",
        effective_from=date(
            2027,
            1,
            1,
        ),
        items=tuple(
            items
        ),
    )


def test_knowledge_item_has_verifiable_sources() -> None:
    item = create_item()

    assert len(
        item.sources
    ) == 1

    assert (
        item.sources[0].source_type
        == "systematic_review"
    )


def test_knowledge_is_not_a_python_policy() -> None:
    item = create_item()

    assert not hasattr(
        item,
        "authority",
    )

    assert not hasattr(
        item,
        "hard_limit",
    )


def test_base_filters_active_items() -> None:
    active = create_item(
        knowledge_id="active",
    )

    expired = create_item(
        knowledge_id="expired",
        valid_from=date(
            2025,
            1,
            1,
        ),
        valid_until=date(
            2026,
            12,
            31,
        ),
    )

    base = create_base(
        active,
        expired,
    )

    items = base.active_items(
        on_date=date(
            2027,
            3,
            1,
        )
    )

    assert items == (
        active,
    )


def test_base_filters_by_topic() -> None:
    load = create_item(
        knowledge_id="load",
        topic="load_progression",
    )

    taper = create_item(
        knowledge_id="taper",
        topic="taper",
    )

    base = create_base(
        load,
        taper,
    )

    assert base.items_for_topic(
        "taper",
        on_date=date(
            2027,
            3,
            1,
        ),
    ) == (
        taper,
    )


def test_base_filters_by_applicability() -> None:
    general = create_item(
        knowledge_id="general",
        applicability=(
            "general_endurance",
        ),
    )

    trail = create_item(
        knowledge_id="trail",
        applicability=(
            "trail_running",
            "long_trail",
        ),
    )

    base = create_base(
        general,
        trail,
    )

    assert base.items_for_applicability(
        "long_trail",
        on_date=date(
            2027,
            3,
            1,
        ),
    ) == (
        trail,
    )


def test_item_can_supersede_old_knowledge() -> None:
    item = TrainingKnowledgeItem(
        knowledge_id="new-taper-review",
        topic="taper",
        statement="Nouvelle synthèse.",
        rationale="Données plus récentes.",
        evidence_level="high",
        applicability=(
            "general_endurance",
        ),
        sources=(
            create_source(),
        ),
        valid_from=date(
            2028,
            1,
            1,
        ),
        supersedes=(
            "old-taper-review",
        ),
    )

    assert item.supersedes == (
        "old-taper-review",
    )


def test_invalid_validity_range_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="validité",
    ):
        create_item(
            valid_from=date(
                2027,
                2,
                1,
            ),
            valid_until=date(
                2027,
                1,
                1,
            ),
        )


def test_duplicate_knowledge_ids_are_rejected() -> None:
    item = create_item()

    with pytest.raises(
        ValueError,
        match="uniques",
    ):
        create_base(
            item,
            item,
        )


def test_source_requires_title() -> None:
    with pytest.raises(
        ValueError,
        match="titre",
    ):
        TrainingKnowledgeSource(
            source_id="source",
            source_type="other",
            title="",
        )
