from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hsa import DragonMirrorGame
from hsa.dragon_mirror import Action, Location
from hsa.observer_view import observer_view, observation_digest


class ObserverViewTests(unittest.TestCase):
    def setUp(self):
        self.game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 20260929)
        self.game.current = 0

    def view(self, game=None):
        game = game or self.game
        return observer_view(game, 0, actions=game.legal_actions())

    def test_audited_missing_mechanisms_now_change_observation(self):
        baseline = observation_digest(self.view())
        for field, value in (
            ("herald_count", 4), ("hero_power_imbues", 5),
            ("leyline_upgrade", 3), ("hero_power_id", "EDR_445p"),
            ("active_quests", {"TLC_817": {"progress": 5, "turns": 1, "flags": set()}}),
        ):
            with self.subTest(field=field):
                other = self.game.clone(include_history=True)
                setattr(other.players[0], field, value)
                self.assertNotEqual(baseline, observation_digest(self.view(other)))

    def test_enemy_hidden_hand_deck_and_rng_do_not_leak(self):
        other = self.game.clone(include_history=True)
        other.players[1].hand[0] = other._entity("CORE_CS2_065")
        other.players[1].deck[0] = other._entity("CORE_CS2_065")
        other.rng.seed(123456)
        self.assertEqual(self.view(), self.view(other))

    def test_own_unknown_deck_order_and_identities_do_not_leak(self):
        other = self.game.clone(include_history=True)
        other.players[0].deck[0] = other._entity("CORE_CS2_065")
        other.players[0].deck.reverse()
        self.assertEqual(self.view(), self.view(other))

    def test_private_draw_and_discover_events_are_not_history(self):
        other = self.game.clone(include_history=True)
        other.events.extend([{"kind": "draw", "player": 1, "card": "SECRET_DRAW_ID"},
                             {"kind": "discover", "player": 1, "card": "SECRET_PICK_ID"}])
        self.assertEqual(self.view()["history"], self.view(other)["history"])
        self.assertNotIn("SECRET_DRAW_ID", json.dumps(self.view(other)))

    def test_card_identity_is_bound_to_instance_stats(self):
        p = self.game.players[0]
        p.hand = [self.game._entity("EDR_456"), self.game._entity("CATA_556")]
        other = self.game.clone(include_history=True)
        other.players[0].hand[0].attack_delta += 1
        card = self.view(other)["entities"]
        own_hand = [e for e in card if e["zone"] == "hand"]
        self.assertEqual("EDR_456", own_hand[0]["card_id"])
        self.assertEqual(1, own_hand[0]["numeric"]["attack_delta"])
        self.assertEqual(0, own_hand[1]["numeric"]["attack_delta"])

    def test_damage_membership_not_just_cardinality(self):
        p = self.game.players[0]
        p.board = [self.game._entity("EDR_456"), self.game._entity("CATA_556")]
        p.damaged_characters_this_turn = {f"minion:{p.board[0].entity_id}"}
        other = self.game.clone(include_history=True)
        other.players[0].damaged_characters_this_turn = {f"minion:{p.board[1].entity_id}"}
        self.assertNotEqual(self.view(), self.view(other))

    def test_location_identity_and_hero_power_binding(self):
        self.game.players[0].locations = [Location(99999, "CORE_REV_990", 3, 0)]
        view = observer_view(self.game, 0, actions=[Action("HERO_POWER")])
        source = view["actions"][0]["source"]
        self.assertEqual("hero_power", view["entities"][source]["zone"])
        self.assertIn("CORE_REV_990", [e["card_id"] for e in view["entities"]])

    def test_opponent_choice_options_hidden(self):
        self.game.current = 1
        self.game.pending_choice = {"kind": "DISCOVER", "options": [self.game._entity("EDR_456")]}
        first = observer_view(self.game, 0)
        self.game.pending_choice["options"] = [self.game._entity("CATA_556")]
        self.assertEqual(first, observer_view(self.game, 0))

    def test_index_choice_binds_option_not_colliding_entity_id(self):
        self.game.pending_choice = {"kind": "RULE_CHOICE", "player": 0,
                                    "card": self.game._entity("EDR_456"),
                                    "options": [("damage", None), ("summon", None)]}
        view = observer_view(self.game, 0, actions=[Action("RULE_CHOICE_PICK", 1)])
        option = view["entities"][view["actions"][0]["source"]]
        self.assertEqual("summon", option["tags"]["option"])

    def test_unknown_option_type_fails_closed(self):
        self.game.pending_choice = {"kind": "UNKNOWN", "options": [object()]}
        with self.assertRaises(ValueError):
            observer_view(self.game, 0)

    def test_known_deck_is_explicit_context_not_engine_deck(self):
        view = observer_view(self.game, 0, known_deck={"EDR_456": 2})
        items = [e for e in view["entities"] if e["zone"] == "known_starting_deck"]
        self.assertEqual(1, len(items))
        self.assertEqual(2, items[0]["numeric"]["count"])

    def test_effective_hand_cost_is_visible(self):
        self.game.players[0].hand = [self.game._entity("CORE_CS2_029")]
        self.game.players[0].next_spell_cost_reduction = 2
        view = self.view()
        card = next(e for e in view["entities"] if e["zone"] == "hand")
        self.assertEqual(card["numeric"]["cost"] - 2, card["numeric"]["effective_cost"])

    def test_opponent_embedded_spell_is_not_visible(self):
        self.game.players[1].board = [self.game._entity("EDR_456")]
        other = self.game.clone(include_history=True)
        other.players[1].board[0].embedded_spell_id = "CORE_CS2_029"
        self.assertEqual(self.view(), self.view(other))

    def test_played_enemy_secret_does_not_leak_through_belief_or_last_card(self):
        secrets = [card_id for card_id, definition in self.game.card_defs.items()
                   if "SECRET" in definition.mechanics
                   and card_id in self.game.executable_card_ids][:2]
        self.assertEqual(2, len(secrets))
        self.game.search_deck_hypotheses[0] = tuple((1.0, {card_id: 2}) for card_id in secrets)
        views = []
        for card_id in secrets:
            game = self.game.clone(include_history=True)
            game.players[1].last_played_card_id = card_id
            game.players[1].previous_played_card_id = card_id
            game.players[1].secrets = [game._entity(card_id)]
            game._event("play", player=1, card=card_id, started_in_deck=True)
            views.append(self.view(game))
        self.assertEqual(views[0], views[1])

    def test_detached_json_snapshot(self):
        view = self.view()
        json.dumps(view, allow_nan=False)
        before = copy.deepcopy(view)
        self.game.players[0].armor += 5
        self.assertEqual(before, view)

    def test_nested_game_tags_are_detached(self):
        self.game.players[0].hand = [self.game._entity("EDR_456")]
        card = self.game.players[0].hand[0]
        card.gifts = ["first"]
        view = self.view()
        frozen = copy.deepcopy(view)
        card.gifts.append("second")
        self.assertEqual(frozen, view)

    def test_nonacting_player_cannot_receive_legal_action_list(self):
        with self.assertRaises(ValueError):
            observer_view(self.game, 1, actions=self.game.legal_actions())


@unittest.skipUnless(importlib.util.find_spec("torch"), "torch not installed")
class EntityNetworkTests(unittest.TestCase):
    def setUp(self):
        import torch
        torch.set_num_threads(1)
        from hsa.entity_model import EntityPolicyValueNet
        self.game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 20260929)
        self.view = observer_view(self.game, actions=self.game.legal_actions())
        self.model = EntityPolicyValueNet(sorted(self.game.card_defs), d_model=32, layers=2, heads=4)

    def test_forward_backward_masks_and_checkpoint(self):
        import torch
        from hsa.entity_model import collate_views, EntityPolicyValueNet
        second = copy.deepcopy(self.view)
        second["actions"] = second["actions"][:1]
        batch = collate_views([self.view, second], self.model.card_ids)
        logits, values = self.model(batch)
        self.assertTrue(torch.isfinite(values).all())
        self.assertTrue((logits[1, 1:] < -1e8).all())
        loss = -logits.log_softmax(-1)[:, 0].mean() + values.square().mean()
        loss.backward()
        self.assertTrue(all(p.grad is None or torch.isfinite(p.grad).all() for p in self.model.parameters()))
        clone = EntityPolicyValueNet.from_payload({"entity_model": self.model.metadata(),
                                                 "model_state_dict": self.model.state_dict()})
        torch.testing.assert_close(logits, clone(batch)[0])

    def test_mechanism_input_changes_tensor(self):
        from hsa.entity_model import collate_views
        original = collate_views([self.view], self.model.card_ids)
        self.game.players[self.game.current].herald_count += 3
        changed = collate_views([observer_view(self.game, actions=self.game.legal_actions())], self.model.card_ids)
        self.assertFalse(original["numeric"].equal(changed["numeric"]))

    def test_contract_mismatch_rejected(self):
        from hsa.entity_model import EntityPolicyValueNet
        meta = self.model.metadata()
        meta["input_contract"]["numeric_fields"].append("future_field")
        with self.assertRaises(ValueError):
            EntityPolicyValueNet.from_payload({"entity_model": meta, "model_state_dict": self.model.state_dict()})

    def test_unknown_card_keeps_semantics_without_resizing_model(self):
        from hsa.entity_model import collate_views
        view = copy.deepcopy(self.view)
        hand_index = next(i for i, e in enumerate(view["entities"]) if e["zone"] == "hand")
        view["entities"][hand_index]["card_id"] = "UNSEEN_RUNTIME_TOKEN"
        batch = collate_views([view], self.model.card_ids)
        self.assertEqual(0, int(batch["cards"][0, hand_index + 1]))
        self.assertTrue(batch["semantic"][0, hand_index + 1].abs().sum() > 0)
        self.assertEqual(len(view["actions"]), self.model(batch)[0].shape[1])

    def test_batch_padding_does_not_change_action_likelihoods(self):
        import torch
        from hsa.entity_model import collate_views
        longer = copy.deepcopy(self.view)
        longer["entities"] += [copy.deepcopy(longer["entities"][0]) for _ in range(10)]
        alone = self.model(collate_views([self.view], self.model.card_ids))[0][0]
        together = self.model(collate_views([self.view, longer], self.model.card_ids))[0][0]
        torch.testing.assert_close(alone.log_softmax(-1), together.log_softmax(-1), atol=2e-6, rtol=2e-6)


if __name__ == "__main__":
    unittest.main()
