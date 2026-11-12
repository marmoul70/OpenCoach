import json
import logging

from opencoach.ai.observability import log_ai_event, new_ai_trace_id, ollama_metrics


def test_trace_id_is_random_and_not_user_derived():
    first = new_ai_trace_id()
    second = new_ai_trace_id()

    assert len(first) == 32
    assert first != second


def test_log_ai_event_uses_strict_field_allowlist(caplog):
    caplog.set_level(logging.INFO, logger="opencoach.ai.observability")

    log_ai_event(
        "coach_request",
        trace_id="trace-safe",
        status="ok",
        model="qwen3:8b",
        prompt="private question",
        arguments={"secret": "private value"},
        athlete_profile_id="private-profile-id",
        base_url="http://127.0.0.1:11434",
    )

    records = [
        line.split("opencoach_ai_observability ", 1)[1]
        for line in caplog.text.splitlines()
        if "opencoach_ai_observability " in line
    ]
    assert len(records) == 1
    event = json.loads(records[0])
    assert event == {
        "event": "coach_request",
        "model": "qwen3:8b",
        "status": "ok",
        "trace_id": "trace-safe",
    }
    assert "private question" not in caplog.text
    assert "private value" not in caplog.text
    assert "private-profile-id" not in caplog.text
    assert "127.0.0.1" not in caplog.text


def test_ollama_metrics_convert_nanoseconds_to_milliseconds():
    class Result:
        total_duration = 1_250_000_000
        load_duration = 250_000_000
        prompt_eval_count = 120
        prompt_eval_duration = 500_000_000
        eval_count = 40
        eval_duration = 400_000_000

    assert ollama_metrics(Result()) == {
        "ollama_total_duration_ms": 1250.0,
        "ollama_load_duration_ms": 250.0,
        "prompt_eval_count": 120,
        "prompt_eval_duration_ms": 500.0,
        "eval_count": 40,
        "eval_duration_ms": 400.0,
    }
