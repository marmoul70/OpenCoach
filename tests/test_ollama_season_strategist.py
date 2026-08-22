import json

import pytest

from opencoach.planning import (
    OllamaSeasonStrategistConfig,
    SeasonStrategistInvalidResponseError,
    SeasonStrategistRequest,
)

from opencoach.planning.ollama_season_strategist import (
    _build_ollama_payload,
    _parse_ollama_response,
)

from urllib.error import (
    HTTPError,
    URLError,
)

def create_request():
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


def create_config():
    return OllamaSeasonStrategistConfig(
        base_url="http://127.0.0.1:11434",
        model="test-model",
        timeout_seconds=60.0,
        temperature=0.2,
    )


def test_config_requires_model() -> None:
    with pytest.raises(
        ValueError,
        match="modèle",
    ):
        OllamaSeasonStrategistConfig(
            model="",
        )


def test_payload_targets_local_model() -> None:
    payload = _build_ollama_payload(
        request=create_request(),
        config=create_config(),
    )

    assert (
        payload["model"]
        == "test-model"
    )

    assert payload["stream"] is False

def test_payload_uses_strategy_json_schema() -> None:
    payload = _build_ollama_payload(
        request=create_request(),
        config=create_config(),
    )

    schema = payload[
        "format"
    ]

    assert isinstance(
        schema,
        dict,
    )

    assert schema["type"] == "object"

    assert (
        schema["additionalProperties"]
        is False
    )

    assert "summary" in (
        schema["required"]
    )

    assert "weeks" in (
        schema["required"]
    )

def test_payload_contains_strategist_request() -> None:
    payload = _build_ollama_payload(
        request=create_request(),
        config=create_config(),
    )

    messages = payload[
        "messages"
    ]

    user_message = messages[1]

    decoded = json.loads(
        user_message["content"]
    )

    assert (
        decoded["schema_version"]
        == "1.0"
    )

    assert (
        decoded["planning"]["planning_date"]
        == "2027-03-01"
    )


def test_valid_ollama_response_is_parsed() -> None:
    response = _parse_ollama_response(
        {
            "model": "test-model",
            "message": {
                "role": "assistant",
                "content": json.dumps(
                    {
                        "summary": "Test",
                    }
                ),
            },
            "done": True,
        }
    )

    assert response.model == "test-model"

    assert response.content == {
        "summary": "Test",
    }


def test_invalid_message_is_rejected() -> None:
    with pytest.raises(
        SeasonStrategistInvalidResponseError,
        match="message",
    ):
        _parse_ollama_response(
            {
                "model": "test-model",
            }
        )


def test_invalid_content_json_is_rejected() -> None:
    with pytest.raises(
        SeasonStrategistInvalidResponseError,
        match="JSON valide",
    ):
        _parse_ollama_response(
            {
                "message": {
                    "content": "not-json",
                },
            }
        )

def test_http_error_is_also_url_error() -> None:
    error = HTTPError(
        url="http://127.0.0.1:11434/api/chat",
        code=500,
        msg="Internal Server Error",
        hdrs=None,
        fp=None,
    )

    assert isinstance(
        error,
        URLError,
    )