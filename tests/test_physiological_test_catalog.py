from opencoach.physiology.testing import (
    EvidenceLevel,
    PhysiologicalMetric,
    PhysiologicalTestType,
    SportDiscipline,
    get_test_protocol,
    list_test_protocols_for_disciplines,
    list_test_protocols_for_metric,
)


def test_catalog_ids_are_unique() -> None:
    from opencoach.physiology.testing import (
        PHYSIOLOGICAL_TEST_CATALOG,
    )

    ids = tuple(
        protocol.id
        for protocol
        in PHYSIOLOGICAL_TEST_CATALOG
    )

    assert len(ids) == len(
        set(ids)
    )


def test_half_cooper_is_available_to_all_runners() -> None:
    protocol = get_test_protocol(
        PhysiologicalTestType.HALF_COOPER
    )

    assert (
        SportDiscipline.ROAD_RUNNING
        in protocol.disciplines
    )

    assert (
        SportDiscipline.TRAIL_RUNNING
        in protocol.disciplines
    )

    assert (
        SportDiscipline.TRACK_RUNNING
        in protocol.disciplines
    )


def test_half_cooper_targets_vma() -> None:
    protocol = get_test_protocol(
        PhysiologicalTestType.HALF_COOPER
    )

    assert (
        PhysiologicalMetric.VMA
        in protocol.target_metrics
    )


def test_trail_runner_gets_general_and_trail_tests() -> None:
    protocols = (
        list_test_protocols_for_disciplines(
            (
                SportDiscipline.TRAIL_RUNNING,
            )
        )
    )

    ids = {
        protocol.id
        for protocol
        in protocols
    }

    assert (
        PhysiologicalTestType.HALF_COOPER
        in ids
    )

    assert (
        PhysiologicalTestType.UPHILL_6_MIN
        in ids
    )

    assert (
        PhysiologicalTestType.INCREMENTRAIL
        in ids
    )


def test_road_only_runner_does_not_get_trail_tests() -> None:
    protocols = (
        list_test_protocols_for_disciplines(
            (
                SportDiscipline.ROAD_RUNNING,
            )
        )
    )

    ids = {
        protocol.id
        for protocol
        in protocols
    }

    assert (
        PhysiologicalTestType.HALF_COOPER
        in ids
    )

    assert (
        PhysiologicalTestType.UPHILL_6_MIN
        not in ids
    )

    assert (
        PhysiologicalTestType.INCREMENTRAIL
        not in ids
    )


def test_road_and_trail_combines_both_catalogs() -> None:
    protocols = (
        list_test_protocols_for_disciplines(
            (
                SportDiscipline.ROAD_RUNNING,
                SportDiscipline.TRAIL_RUNNING,
            )
        )
    )

    ids = {
        protocol.id
        for protocol
        in protocols
    }

    assert (
        PhysiologicalTestType.VAMEVAL
        in ids
    )

    assert (
        PhysiologicalTestType.UPHILL_20_MIN
        in ids
    )


def test_vma_metric_has_multiple_protocols() -> None:
    protocols = (
        list_test_protocols_for_metric(
            PhysiologicalMetric.VMA
        )
    )

    ids = {
        protocol.id
        for protocol
        in protocols
    }

    assert (
        PhysiologicalTestType.HALF_COOPER
        in ids
    )

    assert (
        PhysiologicalTestType.VAMEVAL
        in ids
    )


def test_uphill_6_min_is_marked_as_opencoach_monitoring() -> None:
    protocol = get_test_protocol(
        PhysiologicalTestType.UPHILL_6_MIN
    )

    assert (
        protocol.evidence_level
        is EvidenceLevel.OPENCOACH_MONITORING
    )


def test_incrementrail_is_research_protocol() -> None:
    protocol = get_test_protocol(
        PhysiologicalTestType.INCREMENTRAIL
    )

    assert (
        protocol.evidence_level
        is EvidenceLevel.RESEARCH_PROTOCOL
    )
