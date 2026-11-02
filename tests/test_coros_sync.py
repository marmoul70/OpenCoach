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
