"""Composable card rules for the deterministic simulator.

The module deliberately depends on the game through a small duck-typed API.
That keeps card declarations separate from ``dragon_mirror.py`` and avoids a
circular import between the state model and the rule catalogue.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Protocol


class Hook(StrEnum):
    BATTLECRY = "battlecry"
    DEATHRATTLE = "deathrattle"
    SPELL = "spell"
    AFTER_DRAW = "after_draw"
    AFTER_PLAY = "after_play"
    AFTER_ATTACK = "after_attack"
    AFTER_HERO_ATTACK = "after_hero_attack"
    LOCATION = "location"
    HERO_POWER = "hero_power"
    START_TURN = "start_turn"
    END_TURN = "end_turn"


class TargetKind(StrEnum):
    ANY_MINION = "any_minion"
    FRIENDLY_MINION = "friendly_minion"
    ENEMY_MINION = "enemy_minion"
    ANY_CHARACTER = "any_character"
    FRIENDLY_CHARACTER = "friendly_character"
    ENEMY_CHARACTER = "enemy_character"


@dataclass(frozen=True)
class TargetSpec:
    kind: TargetKind
    optional: bool = False


# Base metadata for these generated entities comes from the pinned
# HearthstoneJSON snapshot. Declaring the dependency here lets ordinary rules
# refer only to card IDs instead of rebuilding CardDef objects in the engine.
DECLARATIVE_METADATA_IDS = {
    "CORE_CS2_065",  # Voidwalker
    "EDR_492t",  # Duckling
    "EDR_260t",  # Illusion
    "EDR_810t",  # Bloated Leech
    "GAME_005",  # The Coin
    "JAIL_399t1",  # Grandmother Imp
    "TIME_713t",  # Timeless Chest
    "TLC_813",  # Purifying Vines
}

# Some Core printings retain the historical behavior ID while the pinned JSON
# snapshot only contains the original printing. Load its metadata under the
# runtime ID, but keep the alias explicit and auditable.
DECLARATIVE_METADATA_ALIASES = {
    "CORE_EX1_277": "EX1_277",  # Arcane Missiles
}

# New full-Standard rules are kept separate from the historical Dragon slice
# so adding cards does not mutate the vocabulary of existing neural models.
STANDARD_DECLARATIVE_IDS = {
    "CATA_131",
    "CATA_138",
    "CATA_190p",
    "CATA_492",
    "CATA_496",
    "CATA_725",
    "CORE_CS2_004",
    "CORE_CS2_062",
    "CORE_EX1_169",
    "CORE_EX1_197",
    "CORE_ICC_055",
    "CORE_OG_047",
    "CORE_SW_072",
    "DINO_432",
    "EDR_846t2",
    "EDR_846t4",
    "EDR_476",
    "END_007",
    "END_011",
    "JAIL_872",
    "JAIL_510",
    "JAIL_513",
    "JAIL_514",
    "JAIL_941",
    "JAIL_941t",
    "TIME_702",
    "TIME_701",
    "TLC_451",
    "TLC_COIN1",
}


@dataclass(frozen=True)
class RuleSource:
    kind: str
    reference: str
    upstream_card_id: str | None = None
    license: str | None = None
    verification: tuple[str, ...] = ()


@dataclass
class RuleContext:
    player: Any
    card: Any
    action: Any | None = None
    payload: dict[str, Any] = field(default_factory=dict)


class Effect(Protocol):
    def execute(self, game: Any, context: RuleContext) -> None: ...


class CostModifier(Protocol):
    def adjustment(self, game: Any, player: Any, card: Any) -> int: ...


def _recipient(game: Any, context: RuleContext, side: str) -> Any:
    if side == "controller":
        return context.player
    if side == "opponent":
        return game.players[1 - context.player.index]
    raise ValueError(f"unknown recipient side: {side}")


@dataclass(frozen=True)
class Draw:
    count: int = 1
    side: str = "controller"

    def execute(self, game: Any, context: RuleContext) -> None:
        player = _recipient(game, context, self.side)
        for _ in range(self.count):
            game._draw(player)


@dataclass(frozen=True)
class DrawMatching:
    count: int = 1
    card_type: str | None = None
    min_cost: int | None = None
    race: str | None = None
    cost_delta: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        def matches(card: Any) -> bool:
            return (
                (self.card_type is None or card.definition.card_type == self.card_type)
                and (self.min_cost is None or card.cost >= self.min_cost)
                and (self.race is None or card.has_race(self.race))
            )

        for _ in range(self.count):
            if game._draw_matching(
                context.player, matches, cost_delta=self.cost_delta
            ) is None:
                break


@dataclass(frozen=True)
class OfferDeckCardDiscover:
    temporary: bool = False
    bottom_unchosen: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        game._offer_deck_card_discover(
            context.player, temporary=self.temporary,
            bottom_unchosen=self.bottom_unchosen,
            source_card_id=context.card.card_id,
        )


@dataclass(frozen=True)
class CostMinusPerHandCard:
    def adjustment(self, game: Any, player: Any, card: Any) -> int:
        return -len(player.hand)


@dataclass(frozen=True)
class DamageHero:
    amount: int
    side: str = "controller"

    def execute(self, game: Any, context: RuleContext) -> None:
        amount = self.amount
        if context.card.definition.card_type == "SPELL":
            amount += game._spell_damage(context.player)
        game._damage_hero(
            _recipient(game, context, self.side), amount, context.card
        )


@dataclass(frozen=True)
class DamageBoard:
    amount: int
    side: str = "opponent"
    exclude_source: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        player = _recipient(game, context, self.side)
        amount = self.amount
        if context.card.definition.card_type == "SPELL":
            amount += game._spell_damage(context.player)
        for target in list(player.board):
            if self.exclude_source and target.entity_id == context.card.entity_id:
                continue
            game._damage_minion(player.index, target, amount, context.card)


@dataclass(frozen=True)
class ResolveDeaths:
    def execute(self, game: Any, context: RuleContext) -> None:
        game._resolve_deaths()


@dataclass(frozen=True)
class DamageActionTarget:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        amount = self.amount
        if context.card.definition.card_type == "SPELL":
            amount += game._spell_damage(context.player)
        game._deal_to_target(
            context.player.index,
            (context.action.target_player, context.action.target_entity),
            amount,
            source=context.card,
        )


@dataclass(frozen=True)
class DamageAllCharacters:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        amount = self.amount
        if context.card.definition.card_type == "SPELL":
            amount += game._spell_damage(context.player)
        for player in game.players:
            game._damage_hero(player, amount, context.card)
            for minion in list(player.board):
                game._damage_minion(
                    player.index, minion, amount, context.card
                )


@dataclass(frozen=True)
class DestroyMinionsByAttack:
    minimum: int

    def execute(self, game: Any, context: RuleContext) -> None:
        for player in game.players:
            for minion in list(player.board):
                if minion.attack >= self.minimum:
                    minion.damage = minion.max_health


@dataclass(frozen=True)
class DestroyEnemyWeapon:
    def execute(self, game: Any, context: RuleContext) -> None:
        enemy = game.players[1 - context.player.index]
        if enemy.weapon is not None:
            game._destroy_weapon(enemy)


@dataclass(frozen=True)
class DestroyAllMinions:
    def execute(self, game: Any, context: RuleContext) -> None:
        for player in game.players:
            for minion in player.board:
                minion.damage = minion.max_health


@dataclass(frozen=True)
class SummonMatchingFromBottomDeck:
    count: int
    race: str | None = None

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        # The simulator stores the bottom at index 0 and draws from the end.
        candidates = list(player.deck[:self.count])
        for card in candidates:
            if self.race is not None and not card.has_race(self.race):
                continue
            if len(player.board) + len(player.locations) >= 7:
                break
            player.deck.remove(card)
            card.summoned_turn = game.turn
            game._summon(player, card)
            game._event(
                "summon_from_bottom_deck", player=player.index,
                card=card.card_id, entity=card.entity_id,
                source=context.card.card_id,
            )


@dataclass(frozen=True)
class HeraldRagnaros:
    def execute(self, game: Any, context: RuleContext) -> None:
        game._herald_ragnaros(context.player, source=context.card.card_id)


@dataclass(frozen=True)
class BuffSourceHealthPerHandCard:
    def execute(self, game: Any, context: RuleContext) -> None:
        context.card.health_delta += len(context.player.hand)


@dataclass(frozen=True)
class GainArmor:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        game._gain_armor(context.player, self.amount)


@dataclass(frozen=True)
class GainManaCrystals:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        gained = min(self.amount, 10 - context.player.max_mana)
        context.player.max_mana += gained
        context.player.mana += gained


@dataclass(frozen=True)
class GainMana:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.mana += self.amount


@dataclass(frozen=True)
class GrantStartTurnTemporaryMana:
    turns: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.start_turn_temporary_mana_charges += self.turns


@dataclass(frozen=True)
class GainHeroAttack:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        context.player.hero_attack_bonus += self.amount


@dataclass(frozen=True)
class BuffActionTargetPerFriendlyMinion:
    attack: int = 0
    health: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        count = len(context.player.board)
        target.attack_delta += self.attack * count
        target.health_delta += self.health * count


@dataclass(frozen=True)
class SetActionTargetStats:
    attack: int
    health: int
    stealth: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        target.attack_delta += self.attack - target.attack
        target.health_delta += self.health - target.max_health
        if self.stealth:
            target.stealth = True


@dataclass(frozen=True)
class DestroyActionTarget:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        target.damage = target.max_health


@dataclass(frozen=True)
class ShuffleActionTargetIntoOwnerDeck:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        owner = game.players[context.action.target_player]
        target = game._find_minion(owner.index, context.action.target_entity)
        owner.board.remove(target)
        returned = game._entity(target.card_id, created_by=context.card.card_id)
        owner.deck.insert(game.rng.randrange(len(owner.deck) + 1), returned)
        game._refresh_continuous(owner)
        game._event(
            "shuffle_minion", player=owner.index, card=target.card_id,
            entity=target.entity_id, source=context.card.card_id,
        )


@dataclass(frozen=True)
class TakeControlActionTargetUntilEndOfOwnerTurn:
    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        owner = game.players[context.action.target_player]
        target = game._find_minion(owner.index, context.action.target_entity)
        owner.board.remove(target)
        context.player.board.append(target)
        target.return_control_to = owner.index
        target.return_control_at_end_of_turn = owner.index
        target.cant_attack_turn = game.turn
        game._refresh_continuous(owner)
        game._refresh_continuous(context.player)
        game._event(
            "temporary_control", player=context.player.index,
            target_player=owner.index, entity=target.entity_id,
            card=target.card_id, source=context.card.card_id,
        )


@dataclass(frozen=True)
class OfferEffectChoice:
    """Pause resolution until the controller selects one effect bundle."""

    options: tuple[tuple[str, tuple[Effect, ...]], ...]

    def execute(self, game: Any, context: RuleContext) -> None:
        game.pending_choice = {
            "kind": "RULE_CHOICE",
            "player": context.player.index,
            "card": context.card,
            "options": self.options,
        }
        game._event(
            "rule_choice", player=context.player.index,
            card=context.card.card_id,
            options=[label for label, _ in self.options],
        )


@dataclass(frozen=True)
class IfSourceAttribute:
    attribute: str
    effects: tuple[Effect, ...]

    def execute(self, game: Any, context: RuleContext) -> None:
        if getattr(context.card, self.attribute):
            for effect in self.effects:
                effect.execute(game, context)


@dataclass(frozen=True)
class ManaCrystalByHeldSpend:
    threshold: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.card.mana_spent_while_held >= self.threshold:
            GainManaCrystals(1).execute(game, context)
        else:
            GainMana(1).execute(game, context)


@dataclass(frozen=True)
class BuffActionTarget:
    attack: int = 0
    health: int = 0
    event: str | None = None

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        target = game._find_minion(
            context.action.target_player, context.action.target_entity
        )
        target.attack_delta += self.attack
        target.health_delta += self.health
        if self.event:
            game._event(
                self.event, player=context.player.index,
                target_player=context.action.target_player,
                target=target.entity_id,
            )


@dataclass(frozen=True)
class BuffZone:
    zone: str
    attack: int = 0
    health: int = 0
    card_types: tuple[str, ...] = ()
    require_attribute: str | None = None
    exclude_source: bool = False

    def execute(self, game: Any, context: RuleContext) -> None:
        cards = getattr(context.player, self.zone)
        affected = []
        for card in cards:
            if self.exclude_source and card.entity_id == context.card.entity_id:
                continue
            if self.card_types and card.definition.card_type not in self.card_types:
                continue
            if self.require_attribute and not getattr(card, self.require_attribute):
                continue
            card.attack_delta += self.attack
            card.health_delta += self.health
            affected.append(card.entity_id)
        game._event(
            "zone_buff", player=context.player.index,
            source=context.card.card_id, zone=self.zone,
            attack=self.attack, health=self.health,
            card_types=list(self.card_types),
            require_attribute=self.require_attribute,
            affected_count=len(affected), affected=affected,
        )


@dataclass(frozen=True)
class AddCurrentSourceStats:
    attack_multiplier: int = 0
    health_multiplier: int = 0

    def execute(self, game: Any, context: RuleContext) -> None:
        attack = context.card.attack
        health = context.card.max_health
        context.card.attack_delta += attack * self.attack_multiplier
        context.card.health_delta += health * self.health_multiplier


@dataclass(frozen=True)
class SetSourceAttributes:
    values: tuple[tuple[str, Any], ...]

    def execute(self, game: Any, context: RuleContext) -> None:
        for name, value in self.values:
            setattr(context.card, name, value)


@dataclass(frozen=True)
class Summon:
    card_id: str
    count: int = 1
    side: str = "controller"

    def execute(self, game: Any, context: RuleContext) -> None:
        player = _recipient(game, context, self.side)
        for _ in range(self.count):
            if len(player.board) + len(player.locations) >= 7:
                break
            minion = game._entity(self.card_id, created_by=context.card.card_id)
            minion.summoned_turn = game.turn
            game._summon(player, minion)


@dataclass(frozen=True)
class AddToHand:
    card_id: str
    count: int = 1
    side: str = "controller"

    def execute(self, game: Any, context: RuleContext) -> None:
        player = _recipient(game, context, self.side)
        for _ in range(self.count):
            card = game._entity(self.card_id, created_by=context.card.card_id)
            if len(player.hand) < 10:
                player.hand.append(card)
                game._event(
                    "generated_to_hand", player=player.index,
                    card=card.card_id, entity=card.entity_id,
                    source=context.card.card_id,
                )
            else:
                game._event(
                    "generated_burned", player=player.index,
                    card=card.card_id, source=context.card.card_id,
                )


@dataclass(frozen=True)
class AddToDeck:
    card_id: str
    count: int = 1
    position: str = "top"
    shuffle: bool = False
    attributes: tuple[tuple[str, Any], ...] = ()

    def execute(self, game: Any, context: RuleContext) -> None:
        for _ in range(self.count):
            card = game._entity(self.card_id, created_by=context.card.card_id)
            for name, value in self.attributes:
                setattr(card, name, value)
            if self.position == "top":
                context.player.deck.append(card)
            elif self.position == "bottom":
                context.player.deck.insert(0, card)
            else:
                raise ValueError(f"unknown deck position: {self.position}")
        if self.shuffle:
            game.rng.shuffle(context.player.deck)


@dataclass(frozen=True)
class HealHero:
    amount: int
    side: str = "controller"

    def execute(self, game: Any, context: RuleContext) -> None:
        player = _recipient(game, context, self.side)
        player.health = min(player.max_health, player.health + self.amount)


@dataclass(frozen=True)
class HealActionTarget:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        if context.action is None or context.action.target_player is None:
            raise ValueError("action target is required")
        if context.action.target_entity is None:
            target = game.players[context.action.target_player]
            target.health = min(target.max_health, target.health + self.amount)
        else:
            target = game._find_minion(
                context.action.target_player, context.action.target_entity
            )
            target.damage = max(0, target.damage - self.amount)


@dataclass(frozen=True)
class HealFriendlyCharacters:
    amount: int

    def execute(self, game: Any, context: RuleContext) -> None:
        player = context.player
        player.health = min(player.max_health, player.health + self.amount)
        for minion in player.board:
            minion.damage = max(0, minion.damage - self.amount)


@dataclass(frozen=True)
class SetPlayerAttributes:
    values: tuple[tuple[str, Any], ...]
    event: str | None = None

    def execute(self, game: Any, context: RuleContext) -> None:
        for name, value in self.values:
            setattr(context.player, name, value)
        if self.event:
            game._event(
                self.event, player=context.player.index,
                source=context.card.card_id,
                values=dict(self.values),
            )


@dataclass(frozen=True)
class CardRule:
    card_id: str
    hooks: dict[Hook, tuple[Effect, ...]]
    source: RuleSource
    targeting: TargetSpec | None = None
    cost_modifier: CostModifier | None = None


class RuleRegistry:
    def __init__(self, rules: tuple[CardRule, ...] = ()):
        self._rules: dict[str, CardRule] = {}
        for rule in rules:
            self.register(rule)

    def register(self, rule: CardRule) -> None:
        if rule.card_id in self._rules:
            raise ValueError(f"duplicate card rule: {rule.card_id}")
        self._rules[rule.card_id] = rule

    def dispatch(
        self, hook: Hook, card_id: str, game: Any, context: RuleContext
    ) -> bool:
        rule = self._rules.get(card_id)
        if rule is None or hook not in rule.hooks:
            return False
        for effect in rule.hooks[hook]:
            effect.execute(game, context)
        return True

    def targeting(self, card_id: str) -> TargetSpec | None:
        rule = self._rules.get(card_id)
        return None if rule is None else rule.targeting

    def has_hook(self, hook: Hook, card_id: str) -> bool:
        rule = self._rules.get(card_id)
        return rule is not None and hook in rule.hooks

    def cost_adjustment(self, game: Any, player: Any, card: Any) -> int:
        rule = self._rules.get(card.card_id)
        if rule is None or rule.cost_modifier is None:
            return 0
        return rule.cost_modifier.adjustment(game, player, card)

    def manifest(self) -> list[dict[str, Any]]:
        rows = []
        for card_id in sorted(self._rules):
            rule = self._rules[card_id]
            rows.append({
                "card_id": card_id,
                "hooks": sorted(hook.value for hook in rule.hooks),
                "source": asdict(rule.source),
                "targeting": (
                    None if rule.targeting is None else asdict(rule.targeting)
                ),
                "effects": {
                    hook.value: [type(effect).__name__ for effect in effects]
                    for hook, effects in rule.hooks.items()
                },
                "cost_modifier": (
                    None if rule.cost_modifier is None
                    else type(rule.cost_modifier).__name__
                ),
            })
        return rows


def build_rule_registry() -> RuleRegistry:
    rosetta = "vendor/RosettaStone@e10749b5f0c08d3a6135bce317cb11d1738846ad"
    local = "HearthstoneJSON build 251332 + local rule tests"
    return RuleRegistry((
        CardRule(
            "GAME_005", {Hook.SPELL: (GainMana(1),)},
            RuleSource(
                "upstream_adapted", rosetta, "GAME_005", "AGPL-3.0",
                ("test_windpeak_wyrm_battlecry_and_coin_spell_rules",),
            ),
        ),
        CardRule(
            "CORE_EX1_169", {Hook.SPELL: (GainMana(1),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_169", "AGPL-3.0",
                ("test_temporary_mana_spells",),
            ),
        ),
        CardRule(
            "CORE_OG_047",
            {Hook.SPELL: (OfferEffectChoice((
                ("hero_attack_4", (GainHeroAttack(4),)),
                ("armor_8", (GainArmor(8),)),
            )),)},
            RuleSource(
                "upstream_adapted", rosetta, "OG_047", "AGPL-3.0",
                ("test_feral_rage_choose_one",),
            ),
        ),
        CardRule(
            "TLC_COIN1", {Hook.SPELL: (GainMana(1),)},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_temporary_mana_spells",),
            ),
        ),
        CardRule(
            "CATA_138",
            {Hook.SPELL: (BuffActionTargetPerFriendlyMinion(1, 1),)},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_forest_gift_scales_with_friendly_board",),
            ),
            TargetSpec(TargetKind.FRIENDLY_MINION),
        ),
        CardRule(
            "CATA_131", {Hook.BATTLECRY: (ManaCrystalByHeldSpend(4),)},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_felwood_treant_tracks_mana_spent_while_held",),
            ),
        ),
        CardRule(
            "CATA_492", {Hook.LOCATION: (HeraldRagnaros(), Draw())},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_shrine_of_twilight_location_heralds_and_draws",),
            ),
        ),
        CardRule(
            "CATA_190p", {Hook.HERO_POWER: (GainHeroAttack(5),)},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_ruthless_custom_hero_power",),
            ),
        ),
        CardRule(
            "CATA_496",
            {Hook.SPELL: (TakeControlActionTargetUntilEndOfOwnerTurn(),)},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_cursed_chains_temporarily_controls_and_returns_minion",),
            ),
            TargetSpec(TargetKind.ENEMY_MINION),
        ),
        CardRule(
            "CATA_725",
            {Hook.BATTLECRY: (HeraldRagnaros(),), Hook.DEATHRATTLE: (HealHero(3),)},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_shadowsworn_disciple_heralds_and_heals_on_death",),
            ),
        ),
        CardRule(
            "DINO_432",
            {Hook.SPELL: (SetActionTargetStats(5, 4, stealth=True), Draw(2))},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_panther_mask_sets_stats_stealth_and_draws",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "EDR_846t2",
            {Hook.SPELL: (ShuffleActionTargetIntoOwnerDeck(),)},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_corrupted_dream_shuffles_without_death",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "EDR_846t4",
            {Hook.SPELL: (
                DamageHero(5, "opponent"), DamageBoard(5, "opponent"),
                ResolveDeaths(),
            )},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_corrupted_awakening_damages_only_enemies",),
            ),
        ),
        CardRule(
            "EDR_476",
            {Hook.SPELL: (
                DamageHero(4, "opponent"), DamageBoard(4, "opponent"),
                HealFriendlyCharacters(4), ResolveDeaths(),
            )},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea/61e3baf3 + HearthstoneJSON 251332",
                verification=("test_moonwell_damages_enemies_and_heals_friends",),
            ),
        ),
        CardRule(
            "END_007",
            {Hook.SPELL: (
                DamageActionTarget(1), GainHeroAttack(1), Draw(), GainArmor(1),
                ResolveDeaths(),
            )},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_press_the_advantage_all_effects",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "END_011", {Hook.SPELL: (GrantStartTurnTemporaryMana(3),)},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_acceleration_aura_grants_three_future_temporary_crystals",),
            ),
        ),
        CardRule(
            "JAIL_872", {Hook.AFTER_HERO_ATTACK: (Draw(),)},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_spider_rider_draws_after_hero_attack",),
            ),
        ),
        CardRule(
            "JAIL_510",
            {Hook.SPELL: (
                DestroyAllMinions(), ResolveDeaths(),
                SummonMatchingFromBottomDeck(3, race="DEMON"),
            )},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_annihilation_destroys_all_and_summons_bottom_demons",),
            ),
        ),
        CardRule(
            "JAIL_513", {Hook.BATTLECRY: (BuffSourceHealthPerHandCard(),)},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_caged_cranium_counts_hand_after_play",),
            ),
        ),
        CardRule(
            "JAIL_941",
            {Hook.SPELL: (HealActionTarget(4), AddToHand("JAIL_941t"))},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_holy_embrace_heals_and_generates_dark_embrace",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "JAIL_941t", {Hook.SPELL: (DamageActionTarget(4), ResolveDeaths())},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_dark_embrace_deals_damage",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "TIME_702",
            {Hook.SPELL: (
                DamageActionTarget(3),
                IfSourceAttribute("minion_played_while_held", (GainArmor(5),)),
                ResolveDeaths(),
            )},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_ebb_and_flow_tracks_minion_played_while_held",),
            ),
            TargetSpec(TargetKind.ANY_CHARACTER),
        ),
        CardRule(
            "TIME_701", {Hook.SPELL: (OfferDeckCardDiscover(bottom_unchosen=True),)},
            RuleSource(
                "powerlog_verified", "Power.log 61e3baf3 + HearthstoneJSON 251332",
                verification=("test_waveshaping_discovers_from_deck_and_bottoms_others",),
            ),
        ),
        CardRule(
            "JAIL_514", {Hook.SPELL: (Draw(3),)},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_unseen_atlas_costs_less_per_hand_card_and_draws",),
            ),
            cost_modifier=CostMinusPerHandCard(),
        ),
        CardRule(
            "TLC_451", {Hook.SPELL: (OfferDeckCardDiscover(temporary=True),)},
            RuleSource(
                "powerlog_verified", "Power.log 23282dea + HearthstoneJSON 251332",
                verification=("test_cursed_catacombs_discovers_temporary_deck_card",),
            ),
        ),
        CardRule(
            "CORE_CS2_004",
            {Hook.SPELL: (BuffActionTarget(health=2), Draw())},
            RuleSource(
                "upstream_adapted", rosetta, "CS2_004", "AGPL-3.0",
                ("test_power_word_shield",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "CORE_CS2_062",
            {Hook.SPELL: (DamageAllCharacters(3), ResolveDeaths())},
            RuleSource(
                "upstream_adapted", rosetta, "CS2_062", "AGPL-3.0",
                ("test_hellfire_damages_all_characters",),
            ),
        ),
        CardRule(
            "CORE_EX1_197",
            {Hook.SPELL: (DestroyMinionsByAttack(5), ResolveDeaths())},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_197", "AGPL-3.0",
                ("test_shadow_word_ruin_uses_current_attack",),
            ),
        ),
        CardRule(
            "CORE_ICC_055",
            {Hook.SPELL: (DamageActionTarget(3), ResolveDeaths())},
            RuleSource(
                "upstream_adapted", rosetta, "ICC_055", "AGPL-3.0",
                ("test_drain_soul_has_lifesteal_and_requires_a_minion",),
            ),
            TargetSpec(TargetKind.ANY_MINION),
        ),
        CardRule(
            "CORE_SW_072",
            {Hook.BATTLECRY: (DestroyEnemyWeapon(),)},
            RuleSource(
                "upstream_adapted", rosetta, "SW_072", "AGPL-3.0",
                ("test_rustrot_viper_destroys_opposing_weapon",),
            ),
        ),
        CardRule(
            "EX1_014t",
            {Hook.SPELL: (BuffActionTarget(1, 1, event="banana"),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_014t", "AGPL-3.0",
                ("test_thalnos_spell_damage_draw_and_mukla_bananas",),
            ),
        ),
        CardRule(
            "JAIL_882", {Hook.DEATHRATTLE: (Draw(),)},
            RuleSource(
                "local_spec", local,
                verification=(
                    "test_steamcleaner_pickpocket_and_ratcatcher_deck_rules",
                ),
            ),
        ),
        CardRule(
            "CORE_SW_068", {Hook.DEATHRATTLE: (GainArmor(8),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_SW_068", "AGPL-3.0",
                ("test_eight_cost_demon_rules",),
            ),
        ),
        CardRule(
            "EDR_571",
            {Hook.DEATHRATTLE: (DrawMatching(card_type="SPELL", min_cost=5),)},
            RuleSource(
                "local_spec", local,
                verification=("test_deathrattle_filtered_draws",),
            ),
        ),
        CardRule(
            "EDR_572",
            {Hook.DEATHRATTLE: (DrawMatching(
                count=2, race="DRAGON", cost_delta=-1,
            ),)},
            RuleSource(
                "local_spec", local,
                verification=("test_deathrattle_filtered_draws",),
            ),
        ),
        CardRule(
            "JAIL_007",
            {Hook.DEATHRATTLE: (
                DamageHero(2, "opponent"), DamageBoard(2, "opponent"),
            )},
            RuleSource(
                "local_spec", local,
                verification=("test_six_cost_demon_deathrattles_damage_correct_sides",),
            ),
        ),
        CardRule(
            "JAIL_398",
            {Hook.DEATHRATTLE: (
                DamageHero(3), DamageBoard(3, "controller"),
                DamageHero(3, "opponent"), DamageBoard(3, "opponent"),
            )},
            RuleSource(
                "local_spec", local,
                verification=("test_six_cost_demon_deathrattles_damage_correct_sides",),
            ),
        ),
        CardRule(
            "EDR_459",
            {
                Hook.BATTLECRY: (
                    DamageBoard(3, "controller", exclude_source=True),
                    ResolveDeaths(),
                ),
                Hook.DEATHRATTLE: (DamageBoard(3, "opponent"),),
            },
            RuleSource(
                "local_spec", local,
                verification=("test_death_batch_chillmaw_and_afflicted_devastator",),
            ),
        ),
        CardRule(
            "CORE_LOOT_368",
            {Hook.DEATHRATTLE: (Summon("CORE_CS2_065", 3),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_LOOT_368", "AGPL-3.0",
                ("test_voidlord_omen_and_moragg_deathrattles",),
            ),
        ),
        CardRule(
            "TLC_820", {Hook.DEATHRATTLE: (AddToHand("TLC_813"),)},
            RuleSource(
                "local_spec", local,
                verification=(
                    "test_glade_ecologist_generates_and_casts_purifying_vines",
                ),
            ),
        ),
        CardRule(
            "EDR_810", {Hook.BATTLECRY: (Summon("EDR_810t", 2),)},
            RuleSource(
                "local_spec", local,
                verification=(
                    "test_hideous_husk_summons_leeches_that_steal_health",
                ),
            ),
        ),
        CardRule(
            "EDR_260",
            {Hook.DEATHRATTLE: (AddToDeck(
                "EDR_260t", 2, shuffle=True,
                attributes=(("summoned_when_drawn", True),),
            ),)},
            RuleSource(
                "local_spec", local,
                verification=(
                    "test_illusory_greenwing_tokens_summon_when_drawn_and_replace_draw",
                ),
            ),
        ),
        CardRule(
            "JAIL_399",
            {Hook.DEATHRATTLE: (
                AddToDeck("JAIL_399t1", 2, position="bottom"),
            )},
            RuleSource(
                "local_spec", local,
                verification=(
                    "test_imp_gang_stooge_puts_two_grandmother_imps_on_deck_bottom",
                ),
            ),
        ),
        CardRule(
            "EDR_492", {Hook.BATTLECRY: (Summon("EDR_492t", 3),)},
            RuleSource(
                "local_spec", local,
                verification=("test_brood_keeper_and_mother_duck",),
            ),
        ),
        CardRule(
            "TIME_713",
            {Hook.BATTLECRY: (Summon("TIME_713t", side="opponent"),)},
            RuleSource(
                "local_spec", local,
                verification=("test_hooktail_chest_fills_original_players_hand_with_coins",),
            ),
        ),
        CardRule(
            "CORE_DRG_107",
            {Hook.DEATHRATTLE: (AddToHand("CORE_EX1_277"),)},
            RuleSource(
                "upstream_adapted", rosetta, "DRG_107", "AGPL-3.0",
                ("test_violet_spellwing_adds_playable_arcane_missiles",),
            ),
        ),
        CardRule(
            "TLC_600",
            {Hook.BATTLECRY: (DamageActionTarget(5), GainArmor(5))},
            RuleSource(
                "local_spec", local,
                verification=("test_windpeak_wyrm_battlecry_and_coin_spell_rules",),
            ),
        ),
        CardRule(
            "CORE_UNG_084", {Hook.BATTLECRY: (DamageActionTarget(3),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_UNG_084", "AGPL-3.0",
                ("test_fire_plume_phoenix_has_explicit_battlecry_target",),
            ),
        ),
        CardRule(
            "CATA_556", {},
            RuleSource(
                "local_spec", local,
                verification=("test_hook_carrier_and_cannonmaster_generation",),
            ),
        ),
        CardRule(
            "CAP_107", {Hook.BATTLECRY: (AddToHand("CAP_107t"),)},
            RuleSource(
                "local_spec", local,
                verification=("test_generated_weapon_passives_and_deathrattle",),
            ),
        ),
        CardRule(
            "CATA_591",
            {Hook.BATTLECRY: (SetPlayerAttributes((("geddon_draw", True),)),)},
            RuleSource(
                "local_spec", local,
                verification=("test_commander_geddon_replaces_turn_draw_with_deck_choice",),
            ),
        ),
        CardRule(
            "CAP_106", {Hook.BATTLECRY: (Summon("CAP_107t", 2),)},
            RuleSource(
                "local_spec", local,
                verification=("test_captain_crowley_summons_cannoneers_and_adds_shots",),
            ),
        ),
        CardRule(
            "CORE_WW_329",
            {Hook.BATTLECRY: (BuffZone(
                "hand", 2, 2, require_attribute="taunt",
            ),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_WW_329", "AGPL-3.0",
                ("test_detonation_juggernaut_buffs_taunts_in_hand",),
            ),
        ),
        CardRule(
            "END_004", {Hook.BATTLECRY: (Draw(2),)},
            RuleSource(
                "local_spec", local,
                verification=("test_remnant_costs_less_per_death_this_turn_and_draws_two",),
            ),
        ),
        CardRule(
            "JAIL_457",
            {Hook.BATTLECRY: (BuffZone(
                "board", 1, 1, card_types=("MINION",), exclude_source=True,
            ),)},
            RuleSource(
                "local_spec", local,
                verification=("test_hijacked_securitybot_buffs_other_friendly_minions",),
            ),
        ),
        CardRule(
            "EDR_000", {Hook.BATTLECRY: (GainManaCrystals(3),)},
            RuleSource(
                "local_spec", local,
                verification=("test_ysera_weaponsmith_and_cloud_serpent",),
            ),
        ),
        CardRule(
            "END_021",
            {Hook.BATTLECRY: (BuffZone(
                "hand", attack=2, card_types=("MINION", "WEAPON"),
            ),)},
            RuleSource(
                "local_spec", local,
                verification=("test_ysera_weaponsmith_and_cloud_serpent",),
            ),
        ),
        CardRule(
            "TIME_051",
            {Hook.BATTLECRY: (AddCurrentSourceStats(attack_multiplier=1),)},
            RuleSource(
                "local_spec", local,
                verification=("test_generated_dragon_stat_battlecries",),
            ),
        ),
        CardRule(
            "TIME_720",
            {Hook.BATTLECRY: (AddCurrentSourceStats(health_multiplier=1),)},
            RuleSource(
                "local_spec", local,
                verification=("test_generated_dragon_stat_battlecries",),
            ),
        ),
        CardRule(
            "TIME_024",
            {Hook.BATTLECRY: (SetSourceAttributes((
                ("infinite_attack_next_turn", True),
            )),)},
            RuleSource(
                "local_spec", local,
                verification=("test_murozond_becomes_infinite_at_next_owner_turn",),
            ),
        ),
        CardRule(
            "CORE_EX1_319", {Hook.BATTLECRY: (DamageHero(3),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_EX1_319", "AGPL-3.0",
                ("test_basic_demon_battlecries_self_damage_freeze_and_discard",),
            ),
        ),
        CardRule(
            "CORE_LOOT_013", {Hook.BATTLECRY: (DamageHero(2),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_LOOT_013", "AGPL-3.0",
                ("test_basic_demon_battlecries_self_damage_freeze_and_discard",),
            ),
        ),
        CardRule(
            "CAP_004", {Hook.DEATHRATTLE: (Draw(2, "opponent"),)},
            RuleSource(
                "local_spec", local,
                verification=("test_one_cost_simple_deathrattles",),
            ),
        ),
        CardRule(
            "EDR_485", {Hook.DEATHRATTLE: (DrawMatching(min_cost=7),)},
            RuleSource(
                "local_spec", local,
                verification=("test_one_cost_simple_deathrattles",),
            ),
        ),
        CardRule(
            "CORE_EX1_014",
            {Hook.BATTLECRY: (AddToHand("EX1_014t", 2, "opponent"),)},
            RuleSource(
                "upstream_adapted", rosetta, "EX1_014", "AGPL-3.0",
                ("test_thalnos_spell_damage_draw_and_mukla_bananas",),
            ),
        ),
        CardRule(
            "CORE_EX1_012", {Hook.DEATHRATTLE: (Draw(),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_EX1_012", "AGPL-3.0",
                ("test_thalnos_spell_damage_draw_and_mukla_bananas",),
            ),
        ),
        CardRule(
            "CORE_EX1_110", {Hook.DEATHRATTLE: (Summon("EX1_110t"),)},
            RuleSource(
                "upstream_adapted", rosetta, "CORE_EX1_110", "AGPL-3.0",
                ("test_cairne_taelan_and_tindral_deathrattles",),
            ),
        ),
        CardRule(
            "RLK_708", {Hook.BATTLECRY: (Draw(),), Hook.DEATHRATTLE: (Draw(),)},
            RuleSource(
                "local_spec", local,
                verification=("test_chillfallen_baron_draws_on_battlecry_and_deathrattle",),
            ),
        ),
        CardRule(
            "TLC_225", {Hook.DEATHRATTLE: (Summon("TLC_249"),)},
            RuleSource(
                "local_spec", local,
                verification=("test_cinderfin_deathrattle_and_firegill_kindred",),
            ),
        ),
        CardRule(
            "TIME_015",
            {Hook.BATTLECRY: (
                HealHero(3),
                SetPlayerAttributes((("hero_divine_shield", True),)),
            )},
            RuleSource(
                "local_spec", local,
                verification=("test_hardlight_pmm_clockwork_and_quantum_states",),
            ),
        ),
        CardRule(
            "CATA_615t",
            {Hook.BATTLECRY: (SetPlayerAttributes((
                ("hero_power_cost_override", 1), ("hero_power_armor", 4),
            ), event="genn_hero_power_upgrade"),)},
            RuleSource(
                "local_spec", local,
                verification=(
                    "test_genn_transforms_reversibly_and_upgrades_warrior_hero_power",
                ),
            ),
        ),
    ))
