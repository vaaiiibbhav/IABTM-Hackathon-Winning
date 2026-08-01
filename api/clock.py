"""PRAXIS virtual clock (I1).

Every timestamp in the app flows through here — never `datetime.now()` /
`datetime.utcnow()` anywhere else. `advance()`/`reset()` let the demo
time-travel (§11) without touching real system time.

Offset is a process-local module variable in this phase (no DB yet). The
`clock` table in §8 is where this becomes persistent once Postgres is wired
up in Phase 2 — same shape (`virtual_offset_seconds`), just backed by a row
instead of a global.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

_virtual_offset_seconds: int = 0


def now() -> datetime:
    """Real UTC time plus the stored virtual offset."""
    return datetime.now(timezone.utc) + timedelta(seconds=_virtual_offset_seconds)


def advance(days: int) -> datetime:
    """Move the virtual offset forward by `days` (fractional allowed). Returns the new now()."""
    global _virtual_offset_seconds
    _virtual_offset_seconds += int(days * 86400)
    return now()


def reset() -> datetime:
    """Zero the offset, returning to real-time baseline."""
    global _virtual_offset_seconds
    _virtual_offset_seconds = 0
    return now()
