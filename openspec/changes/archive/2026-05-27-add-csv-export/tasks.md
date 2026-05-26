# Tasks: Add CSV Export

## Implementation

- [x] Add `GET /reports/export` endpoint to `app/main.py`
  - Accept `status`, `date_from`, `date_to`, `sort`, `descending` query params (same as `list_reports`, no `offset`/`limit`)
  - Call `reports.query()` with those params
  - Map results through `ReportPublic.from_internal()` to strip internal fields
  - Serialize to CSV using `csv.DictWriter` on an `io.StringIO` buffer
  - Return `StreamingResponse` with `media_type="text/csv"` and `Content-Disposition: attachment; filename="reports.csv"` header
  - Raise `HTTPException(400)` on `ValueError` from `query()` (invalid sort field)

## Tests

- [x] Add tests for the export endpoint in `tests/`
  - `test_export_returns_csv_content_type` — response header is `text/csv`
  - `test_export_has_content_disposition` — filename header is present
  - `test_export_header_row` — first row matches expected columns: `id,title,status,owner,amount,created_at`
  - `test_export_no_internal_fields` — `internal_id` and `owner_email` are absent from all rows
  - `test_export_filter_by_status` — `?status=approved` returns only approved rows
  - `test_export_rfc4180_edge_case` — row with commas, quotes, and newline in title is correctly quoted
  - `test_export_invalid_sort_returns_400` — `?sort=nonexistent` returns 400
  - `test_export_all_rows_no_pagination` — unfiltered export returns all 120 seed rows
