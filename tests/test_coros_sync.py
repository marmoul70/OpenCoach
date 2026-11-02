from datetime import date

from opencoach.integrations.coros.sync import CorosImportService, six_months_ago


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
