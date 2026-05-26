# CSV Export Endpoint — Design Spec

**Date:** 2026-05-27  
**Status:** Approved

---

## Overview

Add a `GET /reports/export` endpoint to the existing FastAPI reports API. The endpoint returns all reports matching the current filter parameters as a downloadable CSV file. No pagination — the export contains every matching row.

---

## Endpoint

```
GET /reports/export
```

### Query Parameters

Same filter and sort parameters as `GET /reports`, minus pagination:

| Parameter    | Type     | Default        | Notes                                              |
|--------------|----------|----------------|----------------------------------------------------|
| `status`     | enum     | —              | Filter by: pending, approved, rejected, archived   |
| `date_from`  | datetime | —              | Lower bound on `created_at` (inclusive, ISO 8601)  |
| `date_to`    | datetime | —              | Upper bound on `created_at` (inclusive, ISO 8601)  |
| `sort`       | string   | `"created_at"` | Sort by: id, title, status, owner, amount, created_at |
| `descending` | bool     | `true`         | Sort direction                                     |

No `offset` or `limit` — all matching rows are exported.

### Response

- **Content-Type:** `text/csv; charset=utf-8`
- **Content-Disposition:** `attachment; filename="reports.csv"`
- **Body:** RFC 4180-compliant CSV with header row

### CSV Columns

```
id,title,status,owner,amount,created_at
```

Public fields only. `internal_id` and `owner_email` are **never** included in the export.

---

## Architecture

### Implementation location

All changes in `app/main.py`. The new endpoint reuses `filter_reports()` from `app/reports.py` (which was explicitly designed for this purpose) without modification.

### Data flow

```
Client: GET /reports/export?status=approved
    → main.py: parse query params (same logic as /reports)
    → reports.py: filter_reports(data, params) — no limit applied
    → main.py: serialize to CSV via stdlib csv module
    → StreamingResponse(text/csv) with Content-Disposition header
```

### CSV encoding

Use Python's stdlib `csv.writer` with `quoting=csv.QUOTE_ALL` for RFC 4180 compliance. The existing dataset intentionally includes titles with commas, double-quotes, and newlines as edge-case test data — `QUOTE_ALL` handles all of these correctly.

Use `io.StringIO` as the in-memory buffer; wrap in FastAPI's `StreamingResponse`.

---

## Security

- Only `ReportPublic` fields are written to CSV — the same fields exposed by `GET /reports`.
- `internal_id` and `owner_email` must not appear in the output under any circumstances.
- No authentication changes — the new endpoint inherits whatever auth the existing endpoints use (currently none in this project).

---

## Error Handling

- Invalid query params (e.g. unknown `status` value, malformed date) return the same HTTP 422 Unprocessable Entity that FastAPI generates for `GET /reports`.
- No special CSV-level error handling needed — data is in-memory and cannot fail mid-stream.

---

## Testing

The existing dataset covers the relevant edge cases:

- Titles containing commas → must be quoted in CSV output
- Titles containing double-quotes → must be escaped per RFC 4180
- Titles containing newlines → must be quoted
- Filter params: same behaviour as `/reports` (covered by existing tests if any)

Manual smoke test: `curl "http://localhost:8000/reports/export?status=approved" -o approved.csv` and verify row count matches `total` from `GET /reports?status=approved`.

---

## Out of Scope

- Frontend UI (this is a backend-only project)
- Async/background export jobs
- Excel (`.xlsx`) format
- Column selection by the caller
