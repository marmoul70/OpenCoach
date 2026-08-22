from opencoach.planning import (
    FakeSeasonStrategist,
    SeasonStrategistPort,
    SeasonStrategistRequest,
    SeasonStrategistResponse,
)


def create_request() -> SeasonStrategistRequest:
    return SeasonStrategistRequest(
        schema_version="1.0",
        planning={
            "planning_date": "2027-03-01",
        },
        knowledge={
            "knowledge_version": "2027.03",
        },
        instructions={
            "output_contract": (
                "SeasonStrategyProposal"
            ),
        },
    )


def create_response() -> SeasonStrategistResponse:
    return SeasonStrategistResponse(
        content={
            "summary": "Stratégie fake.",
        },
        model="fake",
        raw_response={
            "provider": "fake",
        },
    )


def test_fake_implements_strategist_port() -> None:
    strategist = FakeSeasonStrategist(
        response=create_response(),
    )

    assert isinstance(
        strategist,
        SeasonStrategistPort,
    )


def test_fake_returns_configured_response() -> None:
    response = create_response()

    strategist = FakeSeasonStrategist(
        response=response,
    )

    result = strategist.generate(
        request=create_request(),
    )

    assert result is response


def test_fake_records_last_request() -> None:
    strategist = FakeSeasonStrategist(
        response=create_response(),
    )

    request = create_request()

    strategist.generate(
        request=request,
    )

    assert (
        strategist.last_request
        is request
    )


def test_fake_counts_calls() -> None:
    strategist = FakeSeasonStrategist(
        response=create_response(),
    )

    request = create_request()

    strategist.generate(
        request=request,
    )

    strategist.generate(
        request=request,
    )

    assert strategist.calls == 2


def test_fake_response_preserves_content() -> None:
    strategist = FakeSeasonStrategist(
        response=create_response(),
    )

    result = strategist.generate(
        request=create_request(),
    )

    assert result.content == {
        "summary": "Stratégie fake.",
    }

    assert result.model == "fake"


def test_fake_initial_state_is_empty() -> None:
    strategist = FakeSeasonStrategist(
        response=create_response(),
    )

    assert strategist.calls == 0
    assert strategist.last_request is None