from datetime import date

from opencoach.integrations.coros.sync import (
    CorosImportService,
    _build_tool_arguments,
    _upsert_activity_snapshot,
    six_months_ago,
)


class FakeClient:
    def __init__(self):
        self.calls = []

    def list_tools(self):
        return [{"name": "querySleepOverview"}]

    def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return {
            "content": [{
                "type": "text",
                "text": '[{"date":"20260601","sleepScore":85},{"date":"20260602","sleepScore":90}]',
            }]
        }


class FakeDb:
    def __init__(self):
        self.added = []

    def scalar(self, statement):
        return None

    def add(self, row):
        self.added.append(row)

    def flush(self):
        pass

    def refresh(self, row):
        pass

    def commit(self):
        pass


def test_six_month_window_handles_month_end():
    assert six_months_ago(date(2026, 8, 31)) == date(2026, 2, 28)


def test_importer_stores_each_sleep_day_idempotently_by_upsert_key():
    client = FakeClient()
    db = FakeDb()
    service = CorosImportService(
        client,
        db,
        profile_id="00000000-0000-0000-0000-000000000001",
    )

    result = service.import_history(
        {"activities": False, "sleep": True},
        today=date(2026, 6, 2),
    )

    assert result["start_date"] == "2025-12-02"
    assert result["end_date"] == "2026-06-02"
    assert result["imported_snapshots"]["sleep"] == 54
    from opencoach.database.models import CorosDailyData
    snapshots = [row for row in db.added if isinstance(row, CorosDailyData)]
    assert len(snapshots) == 54
    assert {row.metric_date for row in snapshots} == {
        date(2026, 6, 1),
        date(2026, 6, 2),
    }
    assert all(row.category == "sleep" for row in snapshots)
    assert all(name == "querySleepOverview" for name, _ in client.calls)


def test_importer_resumes_from_saved_weekly_checkpoint():
    client = FakeClient()
    db = FakeDb()
    checkpoints = []
    service = CorosImportService(
        client,
        db,
        profile_id="00000000-0000-0000-0000-000000000001",
        progress_callback=lambda category, next_date: checkpoints.append((category, next_date)),
    )

    result = service.import_history(
        {"activities": False, "sleep": True},
        today=date(2026, 6, 2),
        checkpoint={"sleep": "2026-05-27"},
    )

    assert len(client.calls) == 1
    assert client.calls[0][1] == {"startDate": "20260527", "endDate": "20260602"}
    assert result["imported_snapshots"]["sleep"] == 2
    assert checkpoints == [("sleep", None)]


def test_importer_honors_requested_months():
    client = FakeClient()
    db = FakeDb()
    service = CorosImportService(client, db, profile_id="00000000-0000-0000-0000-000000000001")

    result = service.import_history(
        {"activities": False, "sleep": True},
        months=2,
        today=date(2026, 6, 2),
    )

    assert result["start_date"] == "2026-04-02"


def test_importer_uses_explicit_incremental_start_date():
    client = FakeClient()
    db = FakeDb()
    service = CorosImportService(client, db, profile_id="00000000-0000-0000-0000-000000000001")

    result = service.import_history(
        {"activities": False, "sleep": True},
        months=6,
        start_date=date(2026, 5, 27),
        today=date(2026, 6, 2),
    )

    assert result["start_date"] == "2026-05-27"
    assert len(client.calls) == 1
    assert client.calls[0][1] == {"startDate": "20260527", "endDate": "20260602"}


def test_activity_detail_arguments_follow_the_discovered_mcp_schema():
    tool = {
        "inputSchema": {
            "type": "object",
            "properties": {
                "labelId": {"type": "string"},
                "sportType": {"type": "integer"},
                "includeLaps": {"type": "boolean"},
            },
            "required": ["labelId", "sportType"],
        }
    }
    assert _build_tool_arguments(tool, {
        "labelId": 123,
        "sportType": "102",
        "unused": "ignored",
    }) == {"labelId": "123", "sportType": 102}


def test_activity_detail_arguments_skip_when_required_schema_value_missing():
    tool = {
        "inputSchema": {
            "type": "object",
            "properties": {"labelId": {"type": "string"}, "sportType": {"type": "integer"}},
            "required": ["labelId", "sportType"],
        }
    }
    assert _build_tool_arguments(tool, {"labelId": "abc"}) is None


class SnapshotAwareFakeDb(FakeDb):
    """Fake DB qui simule l'upsert par profil, date et catégorie."""

    def scalar(self, statement):
        from opencoach.database.models import CorosDailyData

        entity = statement.column_descriptions[0].get("entity")
        if entity is not CorosDailyData:
            return None
        params = statement.compile().params
        profile_id = params.get("athlete_profile_id_1")
        metric_date = params.get("metric_date_1")
        category = params.get("category_1")
        return next(
            (
                row for row in self.added
                if isinstance(row, CorosDailyData)
                and row.athlete_profile_id == profile_id
                and row.metric_date == metric_date
                and row.category == category
            ),
            None,
        )


class FakeActivityClient:
    def __init__(self):
        self.calls = []

    def list_tools(self):
        return [
            {
                "name": "querySportRecords",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "startDate": {"type": "string"},
                        "endDate": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": [],
                },
            },
            {
                "name": "getActivityDetail",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "labelId": {"type": "string"},
                        "sportType": {"type": "integer"},
                    },
                    "required": ["labelId", "sportType"],
                },
            },
        ]

    def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        if name == "querySportRecords":
            return {"content": [{
                "type": "text",
                "text": '[{"labelId":"activity-1","sportType":102,"startTimestamp":1790000000}]',
            }]}
        return {"content": [{"type": "text", "text": '{"laps":[{"lap":1}]}'}]}


def test_activity_details_use_discovered_tool_schema_during_import():
    client = FakeActivityClient()
    db = FakeDb()
    service = CorosImportService(
        client,
        db,
        profile_id="00000000-0000-0000-0000-000000000001",
    )

    result = service.import_history(
        {"activities": True, "activity_details": True},
        start_date=date(2026, 9, 21),
        today=date(2026, 9, 21),
    )

    assert result["imported_snapshots"]["activities"] == 1
    detail_calls = [call for call in client.calls if call[0] == "getActivityDetail"]
    assert detail_calls == [("getActivityDetail", {"labelId": "activity-1", "sportType": 102})]
    from opencoach.database.models import CorosDailyData
    activity_snapshot = next(
        row for row in db.added
        if isinstance(row, CorosDailyData) and row.category == "activities"
    )
    assert activity_snapshot.payload["activities"][0]["activity_detail"] == {"laps": [{"lap": 1}]}


def test_activity_import_groups_multiple_records_from_the_same_day():
    import json
    from opencoach.database.models import Activity, CorosDailyData

    class MultiActivityClient(FakeActivityClient):
        def call_tool(self, name, arguments):
            self.calls.append((name, arguments))
            if name == "querySportRecords":
                return {"content": [{
                    "type": "text",
                    "text": json.dumps([
                        {
                            "labelId": "trail-2026-05-10",
                            "name": "Trail Run",
                            "sportType": 102,
                            "startTimestamp": 1778431644,
                        },
                        {
                            "labelId": "strength-2026-05-10",
                            "name": "Strength",
                            "sportType": 402,
                            "startTimestamp": 1778389138,
                        },
                    ]),
                }]}
            return {"content": [{"type": "text", "text": "{}"}]}

    db = SnapshotAwareFakeDb()
    service = CorosImportService(
        MultiActivityClient(),
        db,
        profile_id="00000000-0000-0000-0000-000000000001",
    )

    result = service.import_history(
        {"activities": True, "activity_details": False},
        start_date=date(2026, 5, 10),
        today=date(2026, 5, 10),
    )

    activity_rows = [row for row in db.added if isinstance(row, Activity)]
    snapshots = [
        row for row in db.added
        if isinstance(row, CorosDailyData) and row.category == "activities"
    ]
    assert result["imported_snapshots"]["activities"] == 2
    assert len(activity_rows) == 2
    assert len(snapshots) == 1
    assert {item["labelId"] for item in snapshots[0].payload["activities"]} == {
        "trail-2026-05-10",
        "strength-2026-05-10",
    }


def test_empty_metric_response_does_not_create_a_fake_snapshot():
    class EmptyMetricClient(FakeClient):
        def call_tool(self, name, arguments):
            self.calls.append((name, arguments))
            return {"content": [{"type": "text", "text": "[]"}]}

    db = FakeDb()
    service = CorosImportService(
        EmptyMetricClient(),
        db,
        profile_id="00000000-0000-0000-0000-000000000001",
    )

    result = service.import_history(
        {"activities": False, "sleep": True},
        start_date=date(2026, 6, 2),
        today=date(2026, 6, 2),
    )

    assert result["imported_snapshots"]["sleep"] == 0
    assert db.added == []


def test_activity_detail_arguments_match_snake_case_schema_names():
    tool = {
        "inputSchema": {
            "type": "object",
            "properties": {
                "label_id": {"type": "string"},
                "sport_type": {"type": "integer"},
            },
            "required": ["label_id", "sport_type"],
        }
    }
    assert _build_tool_arguments(tool, {
        "labelId": "activity-2",
        "sportType": 102,
    }) == {"label_id": "activity-2", "sport_type": 102}


def test_activity_detail_boolean_string_false_is_not_coerced_to_true():
    tool = {
        "inputSchema": {
            "type": "object",
            "properties": {"includeLaps": {"type": "boolean"}},
            "required": ["includeLaps"],
        }
    }
    assert _build_tool_arguments(tool, {"include_laps": "false"}) == {
        "includeLaps": False
    }


def test_activity_detail_invalid_boolean_and_lossy_integer_are_rejected():
    boolean_tool = {
        "inputSchema": {
            "type": "object",
            "properties": {"includeLaps": {"type": "boolean"}},
            "required": ["includeLaps"],
        }
    }
    integer_tool = {
        "inputSchema": {
            "type": "object",
            "properties": {"sportType": {"type": "integer"}},
            "required": ["sportType"],
        }
    }
    assert _build_tool_arguments(boolean_tool, {"includeLaps": "perhaps"}) is None
    assert _build_tool_arguments(integer_tool, {"sportType": 102.5}) is None



def test_activity_import_builds_query_arguments_from_discovered_schema():
    client = FakeActivityClient()
    db = FakeDb()
    service = CorosImportService(
        client,
        db,
        profile_id="00000000-0000-0000-0000-000000000001",
    )

    service.import_history(
        {"activities": True, "activity_details": False},
        start_date=date(2026, 9, 21),
        today=date(2026, 9, 21),
    )

    assert client.calls[0] == (
        "querySportRecords",
        {"startDate": "20260921", "endDate": "20260921", "limit": 100},
    )


def test_mcp_text_with_json_prefix_is_decoded_into_activity_records():
    from opencoach.integrations.coros.sync import _decode_tool_result, _find_rows

    response = {
        "content": [{
            "type": "text",
            "text": 'COROS workout records:\\n[{"labelId":"run-1","sportType":102,"startTimestamp":1790000000}]',
        }]
    }

    rows = _find_rows(_decode_tool_result(response))

    assert rows == [{
        "labelId": "run-1",
        "sportType": 102,
        "startTimestamp": 1790000000,
    }]


def test_non_json_mcp_activity_text_does_not_create_fake_activity_rows():
    from opencoach.integrations.coros.sync import _decode_tool_result, _find_rows

    response = {"content": [{"type": "text", "text": "No workout records found."}]}

    assert _find_rows(_decode_tool_result(response)) == []


def test_human_readable_coros_sport_records_are_parsed_into_activity_rows():
    from opencoach.integrations.coros.sync import _decode_tool_result, _find_rows

    response = {
        "content": [{
            "type": "text",
            "text": """Sport Records — 2026-10-27 to 2026-11-02 (3 records)
========================

1. Trail Run — 2026-11-01
   Location: Lyoffans Trail
   Start Coordinates: 47.647999, 6.585000
   Time Window: startTimestamp=1793520440 | endTimestamp=1793527991
   Duration: 1:58:10 | Distance: 18.75 km
   Average Pace: 6:18 /km | Avg HR: 140 bpm | Calories: 1311 kcal
   LabelId: 481446507948572982 | SportType: 102

2. Soccer — 2026-10-30
   Location: Lure Football
   Time Window: startTimestamp=1793347403 | endTimestamp=1793349257
   Duration: 30:55 | Distance: 468 m
   Average Speed: 0.9 km/h | Avg HR: 91 bpm | Calories: 162 kcal
   LabelId: 481398528334135296 | SportType: 1003

3. Outdoor Run — 2026-10-28
   Location: Lure Course
   Time Window: startTimestamp=1793173915 | endTimestamp=1793176863
   Duration: 49:08 | Distance: 7.64 km
   Average Pace: 6:26 /km | Avg HR: 119 bpm | Calories: 529 kcal
   LabelId: 481352252475343251 | SportType: 100"""
        }]
    }

    rows = _find_rows(_decode_tool_result(response))

    assert len(rows) == 3
    assert rows[0]["name"] == "Trail Run"
    assert rows[0]["labelId"] == 481446507948572982
    assert rows[0]["sportType"] == 102
    assert rows[0]["startTimestamp"] == 1793520440
    assert rows[0]["workoutTime"] == 7090
    assert rows[0]["distanceMeters"] == 18750
    assert rows[0]["averagePaceSecondsPerKm"] == 378
    assert rows[0]["avgHr"] == 140
    assert rows[0]["calories"] == 1311
    assert rows[0]["location"] == "Lyoffans Trail"
    assert rows[0]["startLatitude"] == 47.647999
    assert rows[0]["startLongitude"] == 6.585

    assert rows[1]["workoutTime"] == 1855
    assert rows[1]["distanceMeters"] == 468
    assert rows[1]["average_speed_mps"] == 0.25

    assert rows[2]["workoutTime"] == 2948
    assert rows[2]["distanceMeters"] == 7640


def test_empty_activity_history_keeps_initial_checkpoint_for_full_retry():
    class EmptyActivityClient(FakeActivityClient):
        def call_tool(self, name, arguments):
            self.calls.append((name, arguments))
            return {"content": [{"type": "text", "text": "No workout records found."}]}

    checkpoints = []
    service = CorosImportService(
        EmptyActivityClient(),
        FakeDb(),
        profile_id="00000000-0000-0000-0000-000000000001",
        progress_callback=lambda category, next_date: checkpoints.append((category, next_date)),
    )

    result = service.import_history(
        {"activities": True, "activity_details": False},
        start_date=date(2026, 5, 1),
        today=date(2026, 11, 2),
    )

    assert result["imported_snapshots"]["activities"] == 0
    assert checkpoints[-1] == ("activities", "2026-05-01")


def test_activity_snapshots_keep_multiple_activities_on_the_same_day():
    from opencoach.database.models import CorosDailyData

    db = SnapshotAwareFakeDb()
    profile_id = "00000000-0000-0000-0000-000000000001"
    metric_date = date(2026, 5, 10)

    _upsert_activity_snapshot(db, profile_id, metric_date, {
        "labelId": "trail-1",
        "name": "Trail Run",
    })
    _upsert_activity_snapshot(db, profile_id, metric_date, {
        "labelId": "strength-1",
        "name": "Strength",
    })

    snapshots = [
        row for row in db.added
        if isinstance(row, CorosDailyData) and row.category == "activities"
    ]
    assert len(snapshots) == 1
    assert [item["labelId"] for item in snapshots[0].payload["activities"]] == [
        "trail-1",
        "strength-1",
    ]

    # Un nouvel import de la même activité met à jour son détail sans la dupliquer.
    _upsert_activity_snapshot(db, profile_id, metric_date, {
        "labelId": "trail-1",
        "name": "Trail Run",
        "activity_detail": {"laps": [{"lap": 1}]},
    })
    assert len(snapshots[0].payload["activities"]) == 2
    assert snapshots[0].payload["activities"][0]["activity_detail"] == {
        "laps": [{"lap": 1}]
    }


class AutoflushDisabledFakeDb:
    """Simule SessionLocal : les SELECT ne voient que les lignes flushées."""

    def __init__(self):
        self.persisted = []
        self.pending = []

    def scalar(self, statement):
        from opencoach.database.models import CorosDailyData

        params = statement.compile().params
        profile_id = params.get("athlete_profile_id_1")
        metric_date = params.get("metric_date_1")
        category = params.get("category_1")
        return next((
            row for row in self.persisted
            if isinstance(row, CorosDailyData)
            and row.athlete_profile_id == profile_id
            and row.metric_date == metric_date
            and row.category == category
        ), None)

    def add(self, row):
        self.pending.append(row)

    def flush(self):
        self.persisted.extend(self.pending)
        self.pending.clear()


def test_activity_snapshot_flushes_before_next_same_day_upsert_with_autoflush_disabled():
    db = AutoflushDisabledFakeDb()
    profile_id = "00000000-0000-0000-0000-000000000001"
    metric_date = date(2026, 5, 10)

    _upsert_activity_snapshot(db, profile_id, metric_date, {
        "labelId": "trail-1", "name": "Trail Run",
    })
    _upsert_activity_snapshot(db, profile_id, metric_date, {
        "labelId": "strength-1", "name": "Strength",
    })

    assert db.pending == []
    assert len(db.persisted) == 1
    assert {item["labelId"] for item in db.persisted[0].payload["activities"]} == {
        "trail-1", "strength-1",
    }


def test_activity_snapshot_migrates_legacy_single_activity_payload():
    from opencoach.database.models import CorosDailyData

    db = SnapshotAwareFakeDb()
    profile_id = "00000000-0000-0000-0000-000000000001"
    legacy = CorosDailyData(
        athlete_profile_id=profile_id,
        metric_date=date(2026, 5, 10),
        category="activities",
        payload={"labelId": "legacy-1", "name": "Trail Run"},
    )
    db.added.append(legacy)

    _upsert_activity_snapshot(db, profile_id, date(2026, 5, 10), {
        "labelId": "new-1",
        "name": "Strength",
    })

    assert legacy.payload == {
        "activities": [
            {"labelId": "legacy-1", "name": "Trail Run"},
            {"labelId": "new-1", "name": "Strength"},
        ]
    }



def test_importer_normalizes_each_date_from_a_multiday_coros_sleep_report():
    from opencoach.database.models import CorosDailyData, WellnessDaily

    class MultiDaySleepClient(FakeClient):
        def call_tool(self, name, arguments):
            self.calls.append((name, arguments))
            return {"content": [{
                "type": "text",
                "text": """Sleep Overview
2026-06-01
Sleep Score: 82
Main Sleep (asleep): 7h 30min
2026-06-02
Sleep Score: 90
Main Sleep (asleep): 8h 10min
""",
            }]}

    db = FakeDb()
    service = CorosImportService(
        MultiDaySleepClient(),
        db,
        profile_id="00000000-0000-0000-0000-000000000001",
    )
    result = service.import_history(
        {"activities": False, "sleep": True},
        start_date=date(2026, 6, 2),
        today=date(2026, 6, 2),
    )

    snapshots = [row for row in db.added if isinstance(row, CorosDailyData)]
    wellness = [row for row in db.added if isinstance(row, WellnessDaily)]
    assert result["imported_snapshots"]["sleep"] == 1
    assert len(snapshots) == 1
    assert {(row.date, row.sleep_seconds, row.sleep_score) for row in wellness} == {
        (date(2026, 6, 1), 27_000, 82),
        (date(2026, 6, 2), 29_400, 90),
    }


def test_hrv_import_persists_normalized_time_series_alongside_raw_report() -> None:
    from opencoach.database.models import CorosDailyData

    class HrvClient(FakeClient):
        def list_tools(self):
            return [{"name": "querySleepHrv"}]

        def call_tool(self, name, arguments):
            self.calls.append((name, arguments))
            return {
                "content": [{
                    "type": "text",
                    "text": """Sleep HRV — Last 1 day
2026-11-03:
  HRV Avg: 46 ms — Normal
  Normal Range: 35 - 49 ms
  Baseline: 42 ms

Sleep HRV Time Series — Last 1 day
2026-11-03:
  timestamp=1792969790, timezone=4, hrv=99 ms, status=4, confidence=95833
  timestamp=1792970390, timezone=4, hrv=36 ms, status=4, confidence=100000
""",
                }]
            }

    db = FakeDb()
    service = CorosImportService(
        HrvClient(),
        db,
        profile_id="00000000-0000-0000-0000-000000000001",
    )

    result = service.import_history(
        {"activities": False, "hrv": True},
        start_date=date(2026, 11, 3),
        today=date(2026, 11, 3),
    )

    snapshots = [row for row in db.added if isinstance(row, CorosDailyData)]
    raw_snapshot = next(row for row in snapshots if row.category == "hrv")
    series_snapshot = next(
        row for row in snapshots if row.category == "hrv_timeseries"
    )

    assert result["imported_snapshots"]["hrv"] == 1
    assert raw_snapshot.payload["data"].startswith("Sleep HRV")
    assert series_snapshot.payload["source_category"] == "hrv"
    assert series_snapshot.payload["samples"] == [
        {
            "metric": "sleep_hrv",
            "measured_at": "2026-10-25T23:09:50+00:00",
            "value": 99.0,
            "unit": "ms",
            "source_timezone": 4,
            "status": 4,
            "confidence": 95833,
        },
        {
            "metric": "sleep_hrv",
            "measured_at": "2026-10-25T23:19:50+00:00",
            "value": 36.0,
            "unit": "ms",
            "source_timezone": 4,
            "status": 4,
            "confidence": 100000,
        },
    ]
