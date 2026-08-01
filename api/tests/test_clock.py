"""Tests for the virtual clock module."""

from datetime import timedelta
from api import clock


def test_clock_now():
    """Test that clock.now() returns virtual time matching the offset."""
    clock.reset()
    t1 = clock.now()
    
    # Advance clock by 4 days
    clock.advance(4)
    t2 = clock.now()
    
    # Assert difference is roughly 4 days (handling a small millisecond latency)
    diff = t2 - t1
    assert diff >= timedelta(days=4)
    assert diff < timedelta(days=4, seconds=2)


def test_clock_reset():
    """Test resetting the virtual clock offset."""
    clock.advance(10)
    assert clock.get_offset() == 10 * 24 * 3600
    
    clock.reset()
    assert clock.get_offset() == 0
