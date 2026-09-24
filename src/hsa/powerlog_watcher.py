"""Incremental, read-only watcher for a Windows Hearthstone Power.log.

The watcher deliberately does not interpret game rules or send input to the
client.  It only handles file rotation/truncation and yields complete lines so
the state adapter can consume them without rereading the entire log.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LogLine:
    text: str
    offset: int


class PowerLogTailer:
    """Tail a Power.log safely across append, truncation, and replacement."""

    def __init__(self, path: str | Path, *, from_end: bool = True) -> None:
        self.path = Path(path)
        self.offset = 0
        self._carry = b""
        self._identity: tuple[int, int] | None = None
        if from_end and self.path.exists():
            self.offset = self.path.stat().st_size

    def poll(self) -> list[LogLine]:
        if not self.path.exists():
            return []
        stat = self.path.stat()
        identity = (stat.st_dev, stat.st_ino)
        if self._identity != identity or stat.st_size < self.offset:
            self.offset = 0
            self._carry = b""
        self._identity = identity
        with self.path.open("rb") as handle:
            handle.seek(self.offset)
            chunk = handle.read()
            self.offset = handle.tell()
        if not chunk:
            return []
        data = self._carry + chunk
        parts = data.split(b"\n")
        self._carry = parts.pop()
        result: list[LogLine] = []
        cursor = self.offset - len(self._carry) - sum(len(part) + 1 for part in parts)
        for part in parts:
            result.append(LogLine(part.decode("utf-8", errors="replace").rstrip("\r"), cursor))
            cursor += len(part) + 1
        return result

