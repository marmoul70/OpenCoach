from opencoach.planning import (
    ASSESSMENT_PROTOCOLS,
    get_assessment_protocol,
    get_assessment_protocols,
)


def test_catalog_contains_unique_protocol_ids() -> None:
    protocol_ids = [
        protocol.protocol_id
        for protocol in ASSESSMENT_PROTOCOLS
    ]

    assert len(protocol_ids) == len(
        set(protocol_ids)
    )


def test_vma_need_returns_vameval_and_half_cooper() -> None:
    protocols = get_assessment_protocols(
        "vma_calibration"
    )

    protocol_ids = {
        protocol.protocol_id
        for protocol in protocols
    }

    assert "vameval" in protocol_ids
    assert "half_cooper" in protocol_ids


def test_threshold_need_returns_threshold_protocols() -> None:
    protocols = get_assessment_protocols(
        "threshold_calibration"
    )

    protocol_ids = {
        protocol.protocol_id
        for protocol in protocols
    }

    assert "twenty_minute_threshold" in (
        protocol_ids
    )

    assert "laboratory_threshold" in (
        protocol_ids
    )


def test_max_heart_rate_can_be_observed_by_multiple_protocols() -> None:
    protocols = get_assessment_protocols(
        "max_heart_rate_calibration"
    )

    protocol_ids = {
        protocol.protocol_id
        for protocol in protocols
    }

    assert "vameval" in protocol_ids
    assert "half_cooper" in protocol_ids
    assert "laboratory_threshold" in protocol_ids


def test_get_protocol_by_id() -> None:
    protocol = get_assessment_protocol(
        "VAMEVAL"
    )

    assert protocol is not None
    assert protocol.protocol_id == "vameval"
    assert protocol.environment == "track"
    assert protocol.intensity == "maximal"


def test_unknown_protocol_returns_none() -> None:
    assert get_assessment_protocol(
        "unknown"
    ) is None


def test_vameval_describes_measured_metrics() -> None:
    protocol = get_assessment_protocol(
        "vameval"
    )

    assert protocol is not None

    assert "vma" in protocol.metrics
    assert "max_heart_rate" in protocol.metrics


def test_twenty_minute_test_does_not_claim_sv1_measurement() -> None:
    protocol = get_assessment_protocol(
        "twenty_minute_threshold"
    )

    assert protocol is not None

    assert (
        "threshold_heart_rate_2"
        in protocol.metrics
    )

    assert (
        "threshold_heart_rate_1"
        not in protocol.metrics
    )
