"""Reports query layer.

Pure functions that filter, sort, and paginate the in-memory dataset. Kept separate
from the HTTP layer (`main.py`) so it can be reused by any future export feature.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from app.data import all_reports
from app.models import Report, ReportStatus


_SORTABLE_FIELDS = {"id", "title", "status", "owner", "amount", "created_at"}


def query(
    *,
    status: ReportStatus | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort: str = "created_at",
    descending: bool = True,
) -> list[Report]:
    """Filter and sort reports. Pagination is applied by the caller."""

    if sort not in _SORTABLE_FIELDS:
        raise ValueError(f"Unsupported sort field: {sort!r}")

    rows: Iterable[Report] = all_reports()

    if status is not None:
        rows = (r for r in rows if r.status == status)
    if date_from is not None:
        # Ensure timezone-aware comparison by adding UTC if naive
        date_from_aware = date_from if date_from.tzinfo is not None else date_from.replace(tzinfo=timezone.utc)
        rows = (r for r in rows if r.created_at >= date_from_aware)
    if date_to is not None:
        # Ensure timezone-aware comparison by adding UTC if naive
        date_to_aware = date_to if date_to.tzinfo is not None else date_to.replace(tzinfo=timezone.utc)
        rows = (r for r in rows if r.created_at <= date_to_aware)

    return sorted(rows, key=lambda r: getattr(r, sort), reverse=descending)
