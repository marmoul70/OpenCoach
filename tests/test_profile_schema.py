from opencoach.schemas.profile import AthleteTrainingSchema


def test_available_days_are_normalized_in_ascending_order() -> None:
    training = AthleteTrainingSchema(
        available_days=[5, 1, 3, 0],
    )

    assert training.available_days == [0, 1, 3, 5]


def test_available_days_reject_duplicates() -> None:
    try:
        AthleteTrainingSchema(available_days=[1, 3, 3, 5])
    except ValueError as exc:
        assert "ne peuvent pas être dupliqués" in str(exc)
    else:
        raise AssertionError(
            "Les jours disponibles dupliqués doivent être refusés"
        )