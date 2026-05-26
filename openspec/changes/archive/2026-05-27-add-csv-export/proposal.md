# Proposal: Add CSV Export

## What

Add a `GET /reports/export` endpoint that returns all reports matching the existing filter parameters as a downloadable RFC 4180-compliant CSV file.

## Why

The JSON pagination endpoint (`GET /reports`) caps at 200 rows and is designed for UI consumption. Analysts and downstream systems need a way to export the full filtered dataset in a format that works natively in spreadsheet tools. CSV is the lowest-friction format for that use case.

## Goals

- Export all rows matching `status`, `date_from`, `date_to`, `sort`, and `descending` — no pagination cap
- Produce a valid RFC 4180 CSV (handles commas, quotes, and embedded newlines in field values)
- Expose only public fields — `internal_id` and `owner_email` must never appear in the output
- Return a file download response with a descriptive filename

## Non-goals

- Authentication / authorization (not in scope for this project)
- Custom column selection
- Formats other than CSV
- Async or background job processing

## Risks

- **Field exposure**: If CSV serialization bypasses `ReportPublic`, internal fields leak silently. The design must route through the existing public model.
- **RFC 4180 edge case**: The seed data contains a title with commas, double-quotes, and embedded newlines. Python's `csv` stdlib handles this correctly; a naive string-join approach would not.
