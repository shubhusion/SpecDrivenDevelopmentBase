"""Tests for GET /reports/export."""

from __future__ import annotations

import csv
import io

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _parse_csv(text: str) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    return list(reader.fieldnames or []), rows


def test_export_returns_csv_content_type():
    r = client.get("/reports/export")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]


def test_export_has_content_disposition():
    r = client.get("/reports/export")
    assert "attachment" in r.headers["content-disposition"]
    assert "reports.csv" in r.headers["content-disposition"]


def test_export_header_row():
    r = client.get("/reports/export")
    fieldnames, _ = _parse_csv(r.text)
    assert fieldnames == ["id", "title", "status", "owner", "amount", "created_at"]


def test_export_no_internal_fields():
    r = client.get("/reports/export")
    _, rows = _parse_csv(r.text)
    for row in rows:
        assert "internal_id" not in row
        assert "owner_email" not in row


def test_export_filter_by_status():
    r = client.get("/reports/export?status=approved")
    assert r.status_code == 200
    _, rows = _parse_csv(r.text)
    assert len(rows) > 0
    assert all(row["status"] == "approved" for row in rows)


def test_export_rfc4180_edge_case():
    # Seed data contains a title with commas, double-quotes, and an embedded newline.
    # csv.DictWriter must quote it correctly so it parses back to a single field.
    r = client.get("/reports/export")
    _, rows = _parse_csv(r.text)
    tricky = [row for row in rows if "\n" in row["title"] or '"' in row["title"]]
    assert len(tricky) > 0, "edge-case title not found in seed data"
    for row in tricky:
        assert row["title"]  # parsed back as a single non-empty string


def test_export_invalid_sort_returns_400():
    r = client.get("/reports/export?sort=nonexistent")
    assert r.status_code == 400


def test_export_all_rows_no_pagination():
    r = client.get("/reports/export")
    _, rows = _parse_csv(r.text)
    assert len(rows) == 120
