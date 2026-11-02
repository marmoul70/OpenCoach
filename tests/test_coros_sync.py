from datetime import date

from opencoach.integrations.coros.sync import CorosImportService, _build_tool_arguments, six_months_ago


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
    assert len(db.added) == 54
    assert {row.metric_date for row in db.added} == {
        date(2026, 6, 1),
        date(2026, 6, 2),
    }
    assert all(row.category == "sleep" for row in db.added)
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
    assert activity_snapshot.payload["activity_detail"] == {"laps": [{"lap": 1}]}


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
