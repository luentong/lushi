"""Deck order knowledge, separate from the simulator's private card order.

Unknown mutations conservatively invalidate knowledge. Ordinary top draws
preserve the remaining known positions. Rules explicitly reveal fixed cards.
The rightmost element is the next draw, matching DragonMirrorGame._draw.
"""
from __future__ import annotations

import copy
import random


class SearchDeck(list):
    def __init__(self, cards=()):
        super().__init__(cards)
        self.known: dict[int, dict[int, int]] = {}

    def __deepcopy__(self, memo):
        result = type(self)()
        memo[id(self)] = result
        # The deck itself is branch-local, but avoid generator/deepcopy
        # dispatch overhead for the overwhelmingly common empty knowledge map.
        list.extend(result, [copy.deepcopy(card, memo) for card in self])
        result.known = copy.deepcopy(self.known, memo) if self.known else {}
        return result

    def reveal(self, index: int, observers):
        index %= len(self)
        for observer in observers:
            self.known.setdefault(observer, {})[index] = self[index].entity_id

    def sample_unknown_order(self, observer: int, rng: random.Random):
        fixed = self.known.get(observer, {})
        positions = [i for i in range(len(self)) if i not in fixed]
        # Canonicalize before shuffling: identical visible information must
        # give identical samples even if the real deck's hidden order differs.
        cards = sorted((self[i] for i in positions), key=lambda c: c.entity_id)
        rng.shuffle(cards)
        for index, card in zip(positions, cards):
            list.__setitem__(self, index, card)
        self.known = {observer: dict(fixed)}

    def pop(self, index=-1):
        index = index if index >= 0 else len(self) + index
        card = super().pop(index)
        if index == len(self):
            self.known = {viewer: {i: eid for i, eid in slots.items() if i != index}
                          for viewer, slots in self.known.items()}
        else:
            self.known.clear()
        return card

    def take(self, index=-1):
        """Remove and return one card through the canonical deck API.

        Keeping deck extraction behind one method is the prerequisite for a
        future copy-on-write search deck. It currently has exactly pop's
        semantics, so existing rules and entity identity remain unchanged.
        """
        return self.pop(index)

    def extract(self, card):
        """Remove and return an already selected card instance."""
        self.remove(card)
        return card

    def append(self, value):
        super().append(value)
        # Inserting a card on top does not reorder the existing deck.

    def extend(self, values):
        super().extend(values)

    def insert(self, index, value):
        self.known.clear()
        super().insert(index, value)

    def remove(self, value):
        self.known.clear()
        super().remove(value)

    def clear(self):
        self.known.clear()
        super().clear()

    def __setitem__(self, key, value):
        self.known.clear()
        super().__setitem__(key, value)

    def __delitem__(self, key):
        self.known.clear()
        super().__delitem__(key)

    def reverse(self):
        self.known.clear()
        super().reverse()

    def sort(self, *args, **kwargs):
        self.known.clear()
        super().sort(*args, **kwargs)

    def __iadd__(self, values):
        self.extend(values)
        return self

    def __imul__(self, count):
        self.known.clear()
        return super().__imul__(count)
