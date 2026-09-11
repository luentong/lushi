"""Immutable identity for data, checkpoints, and advisory reports."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .dragon_mirror import DRAGON_DECKSTRING, RULESET


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_FILES = (
    Path("src/hsa/dragon_mirror.py"),
    Path("src/hsa/rules.py"),
    Path("src/hsa/encoding.py"),
    Path("config/decks.json"),
)


def _digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ruleset_manifest(root: Path | None = None) -> dict[str, Any]:
    """Return deterministic provenance for the current simulator semantics."""
    root = REPOSITORY_ROOT if root is None else root
    files: dict[str, str] = {}
    aggregate = hashlib.sha256()
    for relative in SEMANTIC_FILES:
        digest = _digest_file(root / relative)
        key = relative.as_posix()
        files[key] = digest
        aggregate.update(key.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(digest.encode("ascii"))
        aggregate.update(b"\0")
    aggregate.update(RULESET.encode("utf-8"))
    aggregate.update(b"\0")
    aggregate.update(DRAGON_DECKSTRING.encode("utf-8"))
    return {
        "schema_version": 1,
        "ruleset": RULESET,
        "fingerprint_sha256": aggregate.hexdigest(),
        "dragon_deckstring": DRAGON_DECKSTRING,
        "semantic_files": files,
    }
