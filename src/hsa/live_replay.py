"""Deterministic event extraction from normalized Power.log games.

This is the first half of the log-to-engine bridge: it preserves ordering and
all explicit choices/targets without pretending that hidden deck order is
known.  The resulting diagnostics tell the simulator adapter exactly why a
replay can or cannot be opened for model decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True)
class ReplayEvent:
    packet_id: int | None
    timestamp: str | None
    kind: str
    source_entity: int | None = None
    source_card: str | None = None
    target_entity: int | None = None
    target_card: str | None = None
    controller: int | None = None
    choice_id: int | None = None
    choice_type: str | None = None
    task_list: int | None = None
    choices: tuple[int, ...] = ()
    chosen: tuple[int, ...] = ()
    effects: tuple[dict[str, Any], ...] = ()
    observed_entities: tuple[int, ...] = ()


@dataclass
class ReplayDiagnostics:
    events: list[ReplayEvent] = field(default_factory=list)
    hidden_randomness: int = 0
    unresolved_choices: int = 0
    unsupported_blocks: list[str] = field(default_factory=list)
    hidden_state_required: bool = True
    deck_counts: dict[str, dict[str, int]] = field(default_factory=dict)
    unknown_deck_slots: dict[str, int] = field(default_factory=dict)
    hand_entities: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    generated_entities: list[dict[str, Any]] = field(default_factory=list)
    transition_errors: list[dict[str, Any]] = field(default_factory=list)
    reset_count: int = 0
    retained_pre_reset_entities: set[int] = field(default_factory=set)

    @property
    def replayable(self) -> bool:
        return (not self.hidden_randomness and not self.unresolved_choices
                and not self.unsupported_blocks and not self.hidden_state_required)

    @property
    def event_stream_closed(self) -> bool:
        """All explicit events/choices are understood, ignoring hidden state."""
        return not self.hidden_randomness and not self.unresolved_choices and not self.unsupported_blocks

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_count": len(self.events),
            "hidden_randomness": self.hidden_randomness,
            "unresolved_choices": self.unresolved_choices,
            "unsupported_blocks": list(dict.fromkeys(self.unsupported_blocks)),
            "replayable": self.replayable,
            "event_stream_closed": self.event_stream_closed,
            "hidden_state_required": self.hidden_state_required,
            "deck_counts": self.deck_counts,
            "unknown_deck_slots": self.unknown_deck_slots,
            "hand_entities": self.hand_entities,
            "generated_entities": self.generated_entities,
            "transition_errors": self.transition_errors[:50],
            "reset_count": self.reset_count,
            "retained_pre_reset_entity_count": len(self.retained_pre_reset_entities),
        }


@dataclass
class ReplayCursor:
    """Ordered cursor over a closed explicit event stream."""

    events: tuple[ReplayEvent, ...]
    index: int = 0
    entities: dict[int, dict[str, Any]] = field(default_factory=dict)
    choices: dict[int, tuple[int, ...]] = field(default_factory=dict)
    failure: str | None = None

    @property
    def done(self) -> bool:
        return self.index >= len(self.events)

    def step(self) -> ReplayEvent | None:
        if self.failure or self.done:
            return None
        event = self.events[self.index]
        for entity in event.observed_entities:
            self.entities.setdefault(entity, {})["observed_at"] = event.packet_id
        if event.choices:
            if not event.chosen:
                self.failure = f"unresolved choice at packet {event.packet_id}"
                return None
            self.choices[event.packet_id or self.index] = event.chosen
        if event.source_entity is not None and event.source_card:
            self.entities.setdefault(event.source_entity, {})["card_id"] = event.source_card
        if event.target_entity is not None and event.target_card:
            self.entities.setdefault(event.target_entity, {})["card_id"] = event.target_card
        self.index += 1
        return event

    def run_until(self, packet_id: int | None = None) -> int:
        consumed = 0
        while not self.done and not self.failure:
            if packet_id is not None and self.events[self.index].packet_id == packet_id:
                break
            if self.step() is not None:
                consumed += 1
        return consumed


def make_replay_cursor(game: dict[str, Any]) -> tuple[ReplayDiagnostics, ReplayCursor]:
    diagnostics = extract_replay_events(game)
    return diagnostics, ReplayCursor(tuple(diagnostics.events))


@dataclass(frozen=True)
class SimulatorActionPlan:
    index: int
    kind: str
    source_card: str | None
    target_card: str | None
    source_entity: int | None
    target_entity: int | None
    choices: tuple[int, ...]
    mappable: bool
    reason: str | None = None


def action_from_plan(plan: SimulatorActionPlan, mapper: EntityIdMapper):
    """Convert a mapped plan to the engine Action type when unambiguous."""
    from .dragon_mirror import Action
    if not plan.mappable:
        return None, plan.reason or "plan is not mappable"
    source = mapper.resolve(plan.source_entity)
    target = mapper.resolve(plan.target_entity)
    if plan.kind in {"PLAY", "ATTACK", "HERO_POWER", "TRADE", "LOCATION"}:
        if plan.source_entity is not None and source is None:
            return None, "source entity has no simulator mapping"
        if plan.target_entity is not None and target is None:
            return None, "target entity has no simulator mapping"
        kind = "HERO_ATTACK" if plan.kind == "ATTACK" and plan.source_card and plan.source_card.startswith("HERO_") else plan.kind
        return Action(kind, source, None, target), None
    if plan.kind == "END_TURN":
        return Action("END_TURN"), None
    return None, "event kind requires pending-choice adapter"


@dataclass
class EntityIdMapper:
    """Conservative live-entity to simulator-entity correspondence."""

    live_to_sim: dict[int, int] = field(default_factory=dict)
    sim_to_live: dict[int, int] = field(default_factory=dict)
    ambiguous: list[dict[str, Any]] = field(default_factory=list)

    def bind(self, live_id: int, sim_id: int) -> bool:
        old_sim = self.live_to_sim.get(live_id)
        old_live = self.sim_to_live.get(sim_id)
        if old_sim not in (None, sim_id) or old_live not in (None, live_id):
            self.ambiguous.append({"live_id": live_id, "sim_id": sim_id,
                                   "old_sim": old_sim, "old_live": old_live})
            return False
        self.live_to_sim[live_id] = sim_id
        self.sim_to_live[sim_id] = live_id
        return True

    def resolve(self, live_id: int | None) -> int | None:
        return self.live_to_sim.get(live_id) if live_id is not None else None


def match_entity_candidates(
    live_entities: Iterable[dict[str, Any]],
    simulator_entities: Iterable[dict[str, Any]],
) -> tuple[EntityIdMapper, list[dict[str, Any]]]:
    """Match only unique (controller, card_id, zone) candidates."""
    mapper = EntityIdMapper()
    unresolved: list[dict[str, Any]] = []
    sims = list(simulator_entities)
    for live in live_entities:
        key = (live.get("controller"), live.get("card_id"), live.get("zone"))
        candidates = [s for s in sims if (s.get("controller"), s.get("card_id"), s.get("zone")) == key]
        if len(candidates) == 1:
            mapper.bind(int(live["entity"]), int(candidates[0]["entity"]))
        else:
            unresolved.append({"live_entity": live.get("entity"), "key": key,
                               "candidate_count": len(candidates)})
    return mapper, unresolved


def build_simulator_action_plan(diagnostics: ReplayDiagnostics) -> list[SimulatorActionPlan]:
    """Translate explicit log events into engine-facing action descriptors."""
    plans: list[SimulatorActionPlan] = []
    for index, event in enumerate(diagnostics.events):
        mappable = True
        reason = None
        if event.kind in {"PLAY", "ATTACK", "POWER", "TRADE", "LOCATION"}:
            if event.source_entity is None:
                mappable = False
                reason = "missing source entity"
            elif not event.source_card and event.kind != "ATTACK":
                mappable = False
                reason = "source card hidden"
        elif event.kind in {"DISCOVER", "CHOOSE_ONE"} and not event.chosen:
            mappable = False
            reason = "choice unresolved"
        elif event.kind not in {"TURN_START", "TURN_END"}:
            mappable = False
            reason = "event kind requires rule adapter"
        plans.append(SimulatorActionPlan(
            index=index, kind=event.kind, source_card=event.source_card,
            target_card=event.target_card, source_entity=event.source_entity,
            target_entity=event.target_entity, choices=event.chosen,
            mappable=mappable, reason=reason,
        ))
    return plans


def _effects(block: dict[str, Any]) -> Iterable[dict[str, Any]]:
    return block.get("effects", ()) or ()


def _is_game_reset(block: dict[str, Any]) -> bool:
    if str(block.get("block_type") or block.get("type") or "").upper() == "GAME_RESET":
        return True
    return any(str(effect.get("kind") or "").upper() == "RESETGAME"
               for effect in _effects(block))


def _current_reset_segment(
    game: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, set[int]]:
    """Return the authoritative public-state segment after the last reset.

    ``GAME_RESET`` carries a replacement FullEntity snapshot. Earlier actions
    are historical context only and must not be replayed into the reset state.
    """
    blocks = list(game.get("blocks", ()))
    reset_indices = [index for index, block in enumerate(blocks) if _is_game_reset(block)]
    if not reset_indices:
        return list(game.get("preamble", ())), blocks, 0, set()
    reset_index = reset_indices[-1]
    reset = blocks[reset_index]
    snapshot = [effect for effect in _effects(reset)
                if str(effect.get("kind") or "") in {"FullEntity", "ShowEntity", "TagChange"}]
    retained: set[int] = set()
    for block in blocks[:reset_index]:
        for effect in _effects(block):
            if str(effect.get("kind") or "") not in {"FullEntity", "ShowEntity"}:
                continue
            try:
                retained.add(int(effect.get("entity")))
            except (TypeError, ValueError):
                pass
    return snapshot, blocks[reset_index + 1:], len(reset_indices), retained


def extract_replay_events(game: dict[str, Any]) -> ReplayDiagnostics:
    result = ReplayDiagnostics()
    entity_zone: dict[str, str] = {}
    entity_controller: dict[str, str] = {}
    entity_creator: dict[str, Any] = {}
    preamble_rows, blocks, result.reset_count, result.retained_pre_reset_entities = _current_reset_segment(game)
    rows = list(preamble_rows)
    for block in blocks:
        rows.extend(e for e in _effects(block) if e.get("kind") in {"FullEntity", "ShowEntity", "TagChange"})
    for row in rows:
        entity = row.get("entity")
        if entity is None:
            continue
        key = str(entity)
        kind = str(row.get("kind") or "")
        if kind in {"FullEntity", "ShowEntity"}:
            card = row.get("card_id") or ""
            tags = {str(t.get("tag")): t.get("value") for t in row.get("tags", ())}
            zone = tags.get("ZONE")
            controller = tags.get("CONTROLLER")
            if zone is not None:
                entity_zone[key] = str(zone)
            if controller is not None:
                entity_controller[key] = str(controller)
            if tags.get("CREATOR") is not None or tags.get("COPIED_FROM_ENTITY_ID") is not None:
                entity_creator[key] = tags.get("CREATOR") or tags.get("COPIED_FROM_ENTITY_ID")
            # Only the pre-game snapshot is a deck-list observation.  Cards
            # entering DECK later are generated/rewound cards, not original
            # deck counts, and must be tracked separately.
            if zone == "DECK" and card and row in preamble_rows:
                owner = str(controller or "unknown")
                counts = result.deck_counts.setdefault(owner, {})
                counts[card] = counts.get(card, 0) + 1
            if zone == "HAND" and card:
                owner = str(controller or "unknown")
                result.hand_entities.setdefault(owner, []).append({"entity": entity, "card_id": card})
            if tags.get("CREATOR") is not None or tags.get("COPIED_FROM_ENTITY_ID") is not None:
                result.generated_entities.append({"entity": entity, "card_id": card,
                                                   "creator": entity_creator[key]})
        elif kind == "TagChange":
            tag = str(row.get("tag"))
            if tag == "ZONE":
                entity_zone[key] = str(row.get("value"))
    # A hidden deck slot is represented by an entity without a card ID.
    for row in preamble_rows:
        if row.get("kind") in {"FullEntity", "ShowEntity"} and row.get("card_id"):
            continue
        entity = str(row.get("entity")) if row.get("entity") is not None else None
        if entity and entity_zone.get(entity) == "DECK":
            owner = entity_controller.get(entity, "unknown")
            result.unknown_deck_slots[owner] = result.unknown_deck_slots.get(owner, 0) + 1
    # Mulligan choices are special: current Power.log clients mark their
    # completion through MULLIGAN_STATE=DONE, rather than ChosenEntities.
    # Collect that public acknowledgement before evaluating the choice blocks.
    completed_mulligans: set[int] = set()
    for block in blocks:
        for effect in _effects(block):
            if (str(effect.get("kind") or "").upper() == "TAGCHANGE"
                    and str(effect.get("tag") or "").upper() == "MULLIGAN_STATE"
                    and str(effect.get("value") or "").upper() == "DONE"
                    and effect.get("entity") is not None):
                try:
                    completed_mulligans.add(int(effect["entity"]))
                except (TypeError, ValueError):
                    pass

    # Choices and their confirmations may be emitted in different Power.log
    # blocks. Resolve them by protocol id before building replay events, as a
    # zone alone cannot distinguish a live Discover from stale SETASIDE data.
    choice_records: dict[int, dict[str, Any]] = {}
    for block in blocks:
        for effect in _effects(block):
            kind = str(effect.get("kind") or "").upper()
            raw_id = effect.get("id")
            try:
                choice_id = int(raw_id)
            except (TypeError, ValueError):
                choice_id = None
            if choice_id is None:
                continue
            if kind == "CHOICES":
                record = choice_records.setdefault(choice_id, {
                    "choices": [], "chosen": [], "type": None, "task_list": None,
                })
                record["choices"].extend(
                    int(value) for value in effect.get("choices", ())
                    if str(value).lstrip("-").isdigit())
                record["type"] = str(effect.get("type") or "").upper() or record["type"]
                try:
                    record["task_list"] = int(effect.get("tasklist"))
                except (TypeError, ValueError):
                    pass
            elif kind in {"CHOSENENTITIES", "SENDCHOICES"} and choice_id in choice_records:
                record = choice_records[choice_id]
                record["chosen"].extend(
                    int(value) for value in effect.get("choices", ())
                    if str(value).lstrip("-").isdigit())
                record["chosen"].extend(
                    int(value) for value in effect.get("entities", ())
                    if str(value).lstrip("-").isdigit())

    for block in blocks:
        kind = str(block.get("block_type") or block.get("type") or "").upper()
        choices: list[int] = []
        chosen: list[int] = []
        unresolved_choice_entities: list[int] = []
        choice_id: int | None = None
        choice_type: str | None = None
        task_list: int | None = None
        effects: list[dict[str, Any]] = []
        observed_entities: list[int] = []
        inline_chosen: list[int] = []
        for effect in _effects(block):
            if effect.get("entity") is not None:
                try:
                    observed_entities.append(int(effect["entity"]))
                except (TypeError, ValueError):
                    pass
            ek = str(effect.get("kind") or "").upper()
            if ek == "CHOICES":
                try:
                    effect_choice_id = int(effect.get("id"))
                except (TypeError, ValueError):
                    effect_choice_id = None
                record = choice_records.get(effect_choice_id, {}) if effect_choice_id is not None else {}
                choices.extend(record.get("choices", ()) or (
                    int(x) for x in effect.get("choices", ()) if str(x).lstrip("-").isdigit()))
                chosen.extend(record.get("chosen", ()))
                choice_id = effect_choice_id
                choice_type = record.get("type") or str(effect.get("type") or "").upper() or None
                task_list = record.get("task_list")
                if (str(effect.get("type") or "").upper() == "MULLIGAN"
                        and effect.get("entity") is not None):
                    try:
                        unresolved_choice_entities.append(int(effect["entity"]))
                    except (TypeError, ValueError):
                        pass
            elif ek in {"CHOSENENTITIES", "SENDCHOICES"}:
                # Resolved above by choice id. Keep the raw effect for audit,
                # but do not turn its own block into a second choice event.
                # Some old/client-specific records omit the protocol id but
                # put Choices and ChosenEntities in the same block. Preserve
                # that narrow legacy form without guessing across blocks.
                inline_chosen.extend(
                    int(value) for value in effect.get("choices", ())
                    if str(value).lstrip("-").isdigit())
                inline_chosen.extend(
                    int(value) for value in effect.get("entities", ())
                    if str(value).lstrip("-").isdigit())
            elif ek in {"RANDOM", "RANDOMCHOICE", "RANDOMTARGET"}:
                result.hidden_randomness += 1
            if ek not in {"TAGCHANGE", "SHOWENTITY", "FULLENTITY", "HIDEENTITY"}:
                effects.append(effect)
        mulligan_completed = bool(unresolved_choice_entities) and all(
            entity in completed_mulligans for entity in unresolved_choice_entities)
        if kind in {"PLAY", "ATTACK", "POWER", "TRADE", "LOCATION", "CHOOSE_ONE", "DISCOVER", "TURN_START", "TURN_END"}:
                result.events.append(ReplayEvent(
                packet_id=block.get("packet_id"), timestamp=block.get("timestamp"),
                kind=kind, source_entity=block.get("source_entity"),
                source_card=block.get("source_card"), target_entity=block.get("target_entity"),
                target_card=block.get("target_card"), controller=block.get("controller"),
                choice_id=choice_id, choice_type=choice_type, task_list=task_list, choices=tuple(choices),
                chosen=tuple(chosen), effects=tuple(effects),
                observed_entities=tuple(dict.fromkeys(observed_entities)),
            ))
        # DECK_ACTION is a client bookkeeping block (draw/shuffle/deck zone
        # maintenance). Its resulting public entities and zones are already
        # present in the snapshot. It is not an unresolved player choice and
        # must not freeze live advice for the rest of a turn.
        elif kind and kind not in {"TRIGGER", "META", "DEATHS", "DECK_ACTION"}:
            result.unsupported_blocks.append(kind)
        if choices and not chosen and inline_chosen:
            # No id means the association is only safe within this block.
            event = result.events[-1] if result.events else None
            if event is not None and event.choices == tuple(choices):
                result.events[-1] = ReplayEvent(
                    packet_id=event.packet_id, timestamp=event.timestamp,
                    kind=event.kind, source_entity=event.source_entity,
                    source_card=event.source_card, target_entity=event.target_entity,
                    target_card=event.target_card, controller=event.controller,
                    choice_id=event.choice_id, choice_type=event.choice_type,
                    task_list=event.task_list, choices=event.choices,
                    chosen=tuple(inline_chosen), effects=event.effects,
                    observed_entities=event.observed_entities,
                )
                chosen = inline_chosen
        if choices and not chosen and not mulligan_completed:
            result.unresolved_choices += 1
    _validate_event_stream(result)
    return result


def _validate_event_stream(result: ReplayDiagnostics) -> None:
    """Validate only facts observable in the log; never infer hidden state."""
    known: set[int] = set(result.retained_pre_reset_entities)
    for event in result.events:
        # Entities exposed by this packet are available before its action is
        # validated (e.g. a generated minion created by a Battlecry).
        known.update(event.observed_entities)
        if event.source_entity is not None and event.source_card:
            known.add(event.source_entity)
        if event.target_entity is not None and event.target_card:
            known.add(event.target_entity)
        for entity in (event.source_entity, event.target_entity):
            if entity in (None, 0):
                continue
            if entity not in known:
                # A source may be introduced by an effect in the same packet;
                # this is common for generated cards, so record instead of
                # rejecting it. The engine adapter can resolve it later.
                result.transition_errors.append({
                    "packet_id": event.packet_id,
                    "kind": event.kind,
                    "reason": "entity_not_seen_before_action",
                    "entity": entity,
                })
            known.add(entity)
        if event.kind == "ATTACK" and event.source_entity is None:
            result.transition_errors.append({
                "packet_id": event.packet_id,
                "kind": event.kind,
                "reason": "attack_without_source",
            })
        if event.choices and not event.chosen:
            result.transition_errors.append({
                "packet_id": event.packet_id,
                "kind": event.kind,
                "reason": "choice_not_resolved",
                "choices": list(event.choices),
            })
