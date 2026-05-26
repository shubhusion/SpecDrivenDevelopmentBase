# CSV Export Endpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `GET /reports/export` to the FastAPI app, returning all filter-matching reports as a downloadable RFC 4180 CSV file.

**Architecture:** A new endpoint in `app/main.py` reuses the existing `query()` function from `app/reports.py` without modification, converts the results to CSV using Python's stdlib `csv` module, and returns a `StreamingResponse` with the correct `Content-Disposition` header. No new files needed beyond the test file.

**Tech Stack:** Python 3.10+, FastAPI, Starlette `StreamingResponse`, stdlib `csv`/`io`, pytest, httpx (for `TestClient`)

---

### Task 1: Add test dependencies and write failing tests

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/__init__.py`
- Create: `tests/test_export.py`

- [ ] **Step 1: Add pytest and httpx to pyproject.toml**

Open `pyproject.toml` and add an `[project.optional-dependencies]` section:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "httpx>=0.27",
]
```

- [ ] **Step 2: Install the new dev dependencies**

```bash
pip install -e ".[dev]"
```

Expected output: Successfully installed pytest and httpx (or "already satisfied").

- [ ] **Step 3: Create the tests package**

Create `tests/__init__.py` as an empty file.

- [ ] **Step 4: Write all failing tests in tests/test_export.py**

Create `tests/test_export.py` with this content:

```python
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
```

- [ ] **Step 5: Run the tests — verify they all fail**

```bash
pytest tests/test_export.py -v
```

Expected: all 8 tests FAIL with `404 Not Found` or import errors (endpoint does not exist yet).

- [ ] **Step 6: Commit the failing tests**

```bash
git add pyproject.toml tests/__init__.py tests/test_export.py
git commit -m "test: add failing tests for GET /reports/export"
```

---

### Task 2: Implement the export endpoint

**Files:**
- Modify: `app/main.py`

- [ ] **Step 1: Add the new imports to app/main.py**

At the top of `app/main.py`, add `csv`, `io`, and `StreamingResponse` to the existing imports:

```python
"""FastAPI HTTP layer for the Reports app."""

from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.models import ReportListResponse, ReportPublic, ReportStatus
from app.reports import query
```

- [ ] **Step 2: Add the export endpoint to app/main.py**

Append this endpoint after the existing `list_reports` function:

```python
@app.get("/reports/export")
def export_reports(
    status: ReportStatus | None = Query(None, description="Filter by status"),
    date_from: datetime | None = Query(None, description="Lower bound on created_at (inclusive)"),
    date_to: datetime | None = Query(None, description="Upper bound on created_at (inclusive)"),
    sort: str = Query("created_at", description="Sort field"),
    descending: bool = Query(True, description="Sort descending"),
) -> StreamingResponse:
    """Export all matching reports as a CSV file.

    No pagination — returns every row that matches the filter.
    Public fields only; internal_id and owner_email are never included.
    """
    try:
        rows = query(
            status=status,
            date_from=date_from,
            date_to=date_to,
            sort=sort,
            descending=descending,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL)
    writer.writerow(["id", "title", "status", "owner", "amount", "created_at"])
    for r in rows:
        pub = ReportPublic.from_internal(r)
        writer.writerow([pub.id, pub.title, pub.status, pub.owner, pub.amount, pub.created_at.isoformat()])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="reports.csv"'},
    )
```

- [ ] **Step 3: Run the tests — verify they all pass**

```bash
pytest tests/test_export.py -v
```

Expected output: all 8 tests PASS.

```
PASSED tests/test_export.py::test_export_status_200
PASSED tests/test_export.py::test_export_content_type
PASSED tests/test_export.py::test_export_content_disposition
PASSED tests/test_export.py::test_export_columns
PASSED tests/test_export.py::test_export_no_internal_fields
PASSED tests/test_export.py::test_export_returns_all_rows_unfiltered
PASSED tests/test_export.py::test_export_filter_by_status
PASSED tests/test_export.py::test_export_invalid_sort_returns_400
```

- [ ] **Step 4: Commit the implementation**

```bash
git add app/main.py
git commit -m "feat: add GET /reports/export CSV download endpoint"
```

---

### Task 3: Manual smoke test

- [ ] **Step 1: Start the dev server**

```bash
uvicorn app.main:app --reload
```

- [ ] **Step 2: Verify the full unfiltered export**

In a second terminal:

```bash
curl -s "http://localhost:8000/reports/export" -o /tmp/all.csv
wc -l /tmp/all.csv
head -2 /tmp/all.csv
```

Expected: 121 lines (1 header + 120 data rows). First two lines:

```
"id","title","status","owner","amount","created_at"
"1","...","...","...","...","..."
```

- [ ] **Step 3: Verify filtered export matches list endpoint count**

```bash
curl -s "http://localhost:8000/reports?status=pending&limit=1" | python -c "import sys,json; print(json.load(sys.stdin)['total'])"
curl -s "http://localhost:8000/reports/export?status=pending" | wc -l
```

Expected: the `wc -l` result equals `total + 1` (header row).

- [ ] **Step 4: Stop the server** (Ctrl+C)
