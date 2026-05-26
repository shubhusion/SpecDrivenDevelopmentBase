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
    assert list(rows[0].keys()) == ["id", "title", "status", "owner", "amount", "created_at"]


def test_export_no_internal_fields():
    response = client.get("/reports/export")
    rows = _parse_csv(response.text)
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
