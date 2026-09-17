"""Canonical public entry point for the Hearthstone game engine.

The implementation historically lived in :mod:`hsa.dragon_mirror` while the
project only simulated the Dragon Warrior mirror.  The engine now supports
multiple Standard cards and matchups, so new code should import from this
module.  The old module remains as a compatibility layer until all external
scripts have migrated.
"""

from .dragon_mirror import (  # noqa: F401
    DragonMirrorGame,
    RULESET,
    UnsupportedGeneratedCard,
)

__all__ = ["DragonMirrorGame", "RULESET", "UnsupportedGeneratedCard"]
