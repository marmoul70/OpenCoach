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



def test_metrics_snapshot_calculates_percentiles_and_error_rate():
    from opencoach.ai.observability import (
        _clear_ai_metrics_for_tests,
        get_ai_metrics_snapshot,
    )

    _clear_ai_metrics_for_tests()
    for index, duration in enumerate((10, 20, 30, 40, 50, 60, 70, 80, 90, 100)):
        log_ai_event(
            "ollama_generation",
            trace_id=f"trace-{index}",
            status="error" if index == 9 else "ok",
            model="qwen3:8b",
            duration_ms=duration,
        )

    snapshot = get_ai_metrics_snapshot(24)
    assert snapshot["sample_count"] == 10
    assert snapshot["summary"]["count"] == 10
    assert snapshot["summary"]["errors"] == 1
    assert snapshot["summary"]["error_rate_percent"] == 10.0
    assert snapshot["summary"]["latency_ms"]["p50"] == 50.0
    assert snapshot["summary"]["latency_ms"]["p95"] == 100.0
    assert snapshot["breakdown"][0]["dimension"] == "qwen3:8b"
    _clear_ai_metrics_for_tests()


def test_metrics_snapshot_ignores_events_without_valid_duration():
    from opencoach.ai.observability import (
        _clear_ai_metrics_for_tests,
        get_ai_metrics_snapshot,
    )

    _clear_ai_metrics_for_tests()
    log_ai_event("coach_router", status="ok", duration_ms=float("nan"))
    log_ai_event("coach_router", status="ok", duration_ms=-1)
    log_ai_event("coach_router", status="ok")
    assert get_ai_metrics_snapshot()["sample_count"] == 0
    _clear_ai_metrics_for_tests()


def test_metrics_window_validation():
    import pytest
    from opencoach.ai.observability import get_ai_metrics_snapshot

    with pytest.raises(ValueError):
        get_ai_metrics_snapshot(0)
    with pytest.raises(ValueError):
        get_ai_metrics_snapshot(169)
