"""PRAXIS Trace Telemetry Manager.

Manages in-memory trace frame streams for the SSE endpoints.
"""

import asyncio
from typing import Dict, AsyncGenerator
from api.schemas import TraceFrame

# Map from user_id -> List of asyncio.Queue to broadcast trace frames to listeners
_listeners: Dict[str, list[asyncio.Queue]] = {}


def register_listener(user_id: str) -> asyncio.Queue:
    """Register a new SSE stream queue for the user."""
    queue = asyncio.Queue()
    if user_id not in _listeners:
        _listeners[user_id] = []
    _listeners[user_id].append(queue)
    return queue


def unregister_listener(user_id: str, queue: asyncio.Queue) -> None:
    """Remove a queue from active listeners."""
    if user_id in _listeners:
        try:
            _listeners[user_id].remove(queue)
        except ValueError:
            pass
        if not _listeners[user_id]:
            del _listeners[user_id]


async def emit_trace(user_id: str, node: str, status: str, ms: int, summary: str) -> None:
    """Emit a trace frame to all active listeners for this user."""
    frame = TraceFrame(
        node=node,
        status=status,
        ms=ms,
        summary=summary
    )
    if user_id in _listeners:
        # Put frame into all active queues
        for queue in _listeners[user_id]:
            await queue.put(frame)


async def trace_stream(user_id: str) -> AsyncGenerator[str, None]:
    """Yield SSE formatted JSON frames for a specific user."""
    queue = register_listener(user_id)
    try:
        while True:
            frame = await queue.get()
            yield f"data: {frame.model_dump_json()}\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        unregister_listener(user_id, queue)
