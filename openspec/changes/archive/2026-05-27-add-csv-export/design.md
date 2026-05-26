# Design: Add CSV Export

## Endpoint

```
GET /reports/export
```

Accepts the same query parameters as `GET /reports`, minus `offset` and `limit` (export is always unbounded):

| Parameter   | Type                              | Description                          |
|-------------|-----------------------------------|--------------------------------------|
| `status`    | `pending\|approved\|rejected\|archived` | Filter by status              |
| `date_from` | ISO 8601 datetime                 | Lower bound on `created_at`          |
| `date_to`   | ISO 8601 datetime                 | Upper bound on `created_at`          |
| `sort`      | string (default `created_at`)    | Sort field                           |
| `descending`| bool (default `true`)            | Sort direction                       |

## Response

- **Content-Type**: `text/csv; charset=utf-8`
- **Content-Disposition**: `attachment; filename="reports.csv"`
- **Body**: RFC 4180 CSV with a header row

## CSV Columns

Derived from `ReportPublic` — the same public-only fields exposed by the JSON endpoint:

```
id, title, status, owner, amount, created_at
```

`internal_id` and `owner_email` are excluded by construction (never present on `ReportPublic`).

## Request Flow

```
Client
  │
  ▼
GET /reports/export?status=approved&...
  │
  ▼
main.py — export_reports()
  │  same filter params as list_reports()
  ▼
reports.query()           ← reuses existing query layer, no pagination
  │  returns list[Report]
  ▼
[ReportPublic.from_internal(r) for r in rows]
  │  strips internal_id, owner_email
  ▼
csv.DictWriter → StringIO
  │  RFC 4180 compliant, handles commas/quotes/newlines
  ▼
StreamingResponse(iter([buf.getvalue()]), media_type="text/csv")
  │
  ▼
Client receives reports.csv
```

## Implementation Notes

- Use `io.StringIO` + `csv.DictWriter` — stdlib only, no new dependencies
- `extrasaction="ignore"` is not needed; build the dict explicitly from `ReportPublic` fields to keep it explicit
- `datetime` values serialized via `.isoformat()` for unambiguous round-trip
- Use `StreamingResponse` from `fastapi.responses` — appropriate even for the in-memory case and forward-compatible with a future database-backed implementation
- The endpoint is placed in `main.py` alongside `list_reports()` for consistency

## Error Handling

- Invalid `sort` field → `400 Bad Request` (same `ValueError` path as `list_reports`)
- All other validation handled by FastAPI's query parameter parsing
