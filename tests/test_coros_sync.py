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
            {"name": "querySportRecords"},
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
