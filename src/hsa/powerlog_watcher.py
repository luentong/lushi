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

    _CREATE_GAME_MARKER = b"GameState.DebugPrintPower() - CREATE_GAME"

    def __init__(
        self, path: str | Path, *, from_end: bool = True,
        from_last_create_game: bool = False,
    ) -> None:
        self.path = Path(path)
        self.offset = 0
        self._carry = b""
        self._identity: tuple[int, int] | None = None
        self._from_last_create_game = from_last_create_game
        if self.path.exists():
            if from_last_create_game:
                self.offset = self._last_create_game_offset()
            elif from_end:
                self.offset = self.path.stat().st_size

    def _last_create_game_offset(self) -> int:
        """Find the newest game once; later reads stay strictly incremental."""
        raw = self.path.read_bytes()
        marker = raw.rfind(self._CREATE_GAME_MARKER)
        return raw.rfind(b"\n", 0, marker) + 1 if marker >= 0 else 0

    def poll(self) -> list[LogLine]:
        if not self.path.exists():
            return []
        stat = self.path.stat()
        identity = (stat.st_dev, stat.st_ino)
        if self._identity != identity or stat.st_size < self.offset:
            self.offset = (self._last_create_game_offset()
                           if self._from_last_create_game else 0)
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

