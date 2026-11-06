def test_sql_training_session_repository_save_preserves_coros_metadata_when_planner_rebuilds_session() -> None:
    db = create_session()
    try:
        profile = create_profile(db)
        repository = SqlTrainingSessionRepository(db)
        original = create_training_session()
        original.coros_workout_id = "coros-remote-123"
        original.coros_scheduled_date = date(2026, 8, 10)
        original.coros_sync_status = "synced"
        original.coros_sync_started_at = datetime(2026, 8, 9, 7, 0)
        original.coros_last_synced_at = datetime(2026, 8, 9, 7, 1)
        original.coros_payload_hash = "a" * 64
        original.coros_sync_error = None
        saved = repository.save_session(profile.id, original)

        rebuilt = create_training_session()
        rebuilt.id = saved.id
        rebuilt.title = "Nouvelle prescription déterministe"
        # The planner's mapper creates a fresh domain model with no COROS metadata.
        updated = repository.save_session(profile.id, rebuilt)

        assert updated.coros_workout_id == "coros-remote-123"
        assert updated.coros_scheduled_date == date(2026, 8, 10)
        assert updated.coros_sync_status == "synced"
        assert updated.coros_sync_started_at == datetime(2026, 8, 9, 7, 0)
        assert updated.coros_last_synced_at == datetime(2026, 8, 9, 7, 1)
        assert updated.coros_payload_hash == "a" * 64
        assert updated.coros_sync_error is None
        assert updated.title == "Nouvelle prescription déterministe"
    finally:
        db.close()


def test_sql_training_session_repository_updates_status() -> None: