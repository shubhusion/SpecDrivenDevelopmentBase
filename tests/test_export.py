import csv
import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _parse_csv(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


def test_export_status_200():
    response = client.get("/reports/export")
    assert response.status_code == 200


def test_export_content_type():
    response = client.get("/reports/export")
    assert response.headers["content-type"].startswith("text/csv")


def test_export_content_disposition():
    response = client.get("/reports/export")
    assert response.headers["content-disposition"] == 'attachment; filename="reports.csv"'


def test_export_columns():
    response = client.get("/reports/export")
    rows = _parse_csv(response.text)
    assert len(rows) > 0, "Expected at least one data row in CSV"
    assert list(rows[0].keys()) == ["id", "title", "status", "owner", "amount", "created_at"]


def test_export_no_internal_fields():
    response = client.get("/reports/export")
    rows = _parse_csv(response.text)
    assert len(rows) > 0, "Expected at least one data row in CSV"
    for row in rows:
        assert "internal_id" not in row
        assert "owner_email" not in row


def test_export_returns_all_rows_unfiltered():
    response = client.get("/reports/export")
    rows = _parse_csv(response.text)
    assert len(rows) == 120


def test_export_filter_by_status():
    all_rows = _parse_csv(client.get("/reports/export").text)
    expected_count = sum(1 for r in all_rows if r["status"] == "approved")

    filtered = _parse_csv(client.get("/reports/export?status=approved").text)
    assert len(filtered) == expected_count
    assert all(r["status"] == "approved" for r in filtered)


def test_export_invalid_sort_returns_400():
    response = client.get("/reports/export?sort=not_a_field")
    assert response.status_code == 400


def test_export_date_range_filter():
    from app.data import all_reports as _all_reports
    all_internal = _all_reports()
    dates = [r.created_at for r in all_internal]
    mid = sorted(dates)[len(dates) // 2]
    date_str = mid.isoformat()

    rows = _parse_csv(client.get("/reports/export", params={"date_to": date_str}).text)
    assert all(r["created_at"] <= date_str for r in rows)
    assert len(rows) > 0


def test_export_sort_ascending_by_amount():
    rows = _parse_csv(client.get("/reports/export?sort=amount&descending=false").text)
    amounts = [float(r["amount"]) for r in rows]
    assert amounts == sorted(amounts)
