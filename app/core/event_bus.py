from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class BusMessage:
    topic: str
    payload: dict[str, Any]
    priority: int
    created_at: datetime
    retries: int = 0


class InMemoryEventBus:
    """Simple in-memory event bus with retry/DLQ semantics for MVP+."""

    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries
        self._queue: deque[BusMessage] = deque()
        self._dlq: list[BusMessage] = []

    def publish(self, topic: str, payload: dict[str, Any], priority: int = 5) -> None:
        self._queue.append(BusMessage(topic=topic, payload=payload, priority=priority, created_at=datetime.now(timezone.utc)))

    def drain(self) -> list[BusMessage]:
        drained: list[BusMessage] = []
        while self._queue:
            drained.append(self._queue.popleft())
        return drained

    def fail_message(self, message: BusMessage) -> None:
        message.retries += 1
        if message.retries >= self.max_retries:
            self._dlq.append(message)
            return
        self._queue.append(message)

    def get_dlq(self) -> list[BusMessage]:
        return list(self._dlq)
