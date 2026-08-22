from datetime import date

from opencoach.planning import (
    AssessmentSessionSpec,
    build_assessment_training_session,
)


def test_maximal_assessment_becomes_very_hard_training_session() -> None:
    spec = AssessmentSessionSpec(
        assessment_type="vma_calibration",
        protocol_id="vameval",
        title="Test VAMEVAL",
        description="Calibration VMA.",
        sport_type="run",
        intensity="maximal",
        duration_minutes=45,
        priority="high",
        requires_maximal_effort=True,
        covered_metrics=(
            "vma",
            "max_heart_rate",
        ),
    )

    session = build_assessment_training_session(
        spec=spec,
        session_date=date(
            2026,
            8,
            26,
        ),
    )

    assert session.id is None

    assert session.date == date(
        2026,
        8,
        26,
    )

    assert session.type == "assessment"
    assert session.sport_type == "run"

    assert session.intensity == "very_hard"

    assert session.duration_minutes == 45
    assert session.status == "planned"
