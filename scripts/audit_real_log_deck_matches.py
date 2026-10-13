#!/usr/bin/env python3
"""Rank dated decklists against causal evidence on opening deck entities.

This is a feasibility audit, not opponent-deck identification: many variants
share all observed cards, and Start of Game effects can change the deck.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts"), str(ROOT / ".deps")]

from hsa.deck_metadata import apply_deck_metadata_overrides
from hsa.live_replay import extract_replay_events
from hsa.real_log_deck_evidence import collect_deck_evidence
from audit_real_log_action_bridge import initial_public_classes


def rank_decks(observed, entries, by_dbf, eligible_ids, player_class=None):
    collectible = {card_id: int(count) for card_id, count in observed.items()
                   if card_id in eligible_ids}
    ignored = {card_id: int(count) for card_id, count in observed.items()
               if card_id not in eligible_ids}
    if not collectible:
        return {"observed_deck_card_count": 0,
                "ignored_non_deck_entries": ignored,
                "best_mismatch": None, "equally_best_candidates": 0,
                "top_candidates": [],
                "status": "opening_deck_identities_not_visible"}
    from export_live_deck_configs import decode_counts, get_deck_class
    ranked = []
    for entry in entries:
        deck_class = get_deck_class(entry["deckstring"], by_dbf)
        if player_class and deck_class != player_class.upper():
            continue
        counts = decode_counts(entry["deckstring"], by_dbf)
        missing = {card_id: count - counts.get(card_id, 0)
                   for card_id, count in collectible.items()
                   if count > counts.get(card_id, 0)}
        ranked.append({"id": entry["id"], "name": entry.get("name_zh"),
                       "class": deck_class,
                       "unexplained_collectible_cards": missing,
                       "unexplained_count": sum(missing.values()),
                       "matched_count": sum(min(count, counts.get(card_id, 0))
                                            for card_id, count in collectible.items())})
    ranked.sort(key=lambda item: (item["unexplained_count"],
                                  -item["matched_count"], item["id"]))
    best = ranked[0]["unexplained_count"] if ranked else None
    return {"observed_deck_card_count": sum(collectible.values()),
            "ignored_non_deck_entries": ignored,
            "best_mismatch": best,
            "equally_best_candidates": sum(item["unexplained_count"] == best
                                           for item in ranked),
            "compatible_candidates": sum(item["unexplained_count"] == 0
                                         for item in ranked),
            "status": ("compatible_partial_evidence" if any(
                item["unexplained_count"] == 0 for item in ranked)
                else "no_compatible_manifest_deck"),
            "top_candidates": ranked[:10]}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--revealed-opening-entities", action="store_true",
                   help="Use later reveals on original opening deck entity IDs")
    p.add_argument("--before-packet", type=int,
                   help="Exclude this packet and all later evidence")
    p.add_argument("--known-controller", type=int, choices=(1, 2))
    p.add_argument("--known-output", type=Path,
                   help="Export only a completely revealed opening deck for this controller")
    args = p.parse_args()
    payload = json.loads(args.log.read_text(encoding="utf-8"))
    game = payload["games"][-1] if payload.get("games") else payload
    if game.get("identity_timing") != "causal_reveal_only":
        p.error("legacy import can backfill future card identities; reimport causally")
    diagnostic = extract_replay_events(game)
    cards = json.loads(args.cards.read_text(encoding="utf-8"))
    by_dbf = {int(card["dbfId"]): card for card in cards if "dbfId" in card}
    apply_deck_metadata_overrides(by_dbf)
    collectible_ids = {str(card["id"]) for card in cards if card.get("collectible")}
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entries = manifest["decks"]
    # Fabled companion cards can be legitimate starting deck entries despite
    # collectible=false (e.g. Axe of Cenarius / First Portal to Argus).
    from export_live_deck_configs import decode_counts
    companion_ids = {card_id for entry in entries
                     for card_id in decode_counts(entry["deckstring"], by_dbf)
                     if card_id not in collectible_ids}
    eligible_ids = collectible_ids | companion_ids
    if args.before_packet is not None and not args.revealed_opening_entities:
        p.error("--before-packet requires --revealed-opening-entities")
    evidence = (collect_deck_evidence(game, eligible_ids,
                                     before_packet=args.before_packet)
                if args.revealed_opening_entities else None)
    observed_counts = ({side: value["observed_counts"] for side, value in
                        evidence["controllers"].items()} if evidence
                       else diagnostic.deck_counts)
    classes = initial_public_classes(game)
    recovered_counts = None
    if args.known_output or args.known_controller:
        if not (args.known_output and args.known_controller and evidence):
            p.error("known-deck export needs --known-controller, --known-output and --revealed-opening-entities")
        recovered = evidence["controllers"].get(str(args.known_controller), {})
        if not recovered.get("all_opening_slots_identified"):
            p.error("cannot export an incomplete opening deck")
        if args.known_output.exists():
            p.error("known-output exists; choose a new file")
        recovered_counts = {str(args.known_controller): recovered["observed_counts"]}
    report = {"schema": "real-log-deck-feasibility-v2",
              "source_sha256": payload.get("source_sha256"),
              "manifest": str(args.manifest),
              "event_count": len(diagnostic.events),
              "evidence_mode": ("revealed_opening_entities" if evidence else "opening_snapshot"),
              "evidence": evidence,
              "public_classes": classes,
              "known_noncollectible_deck_entries": sorted(companion_ids),
              "controllers": {controller: rank_decks(
                  observed_counts.get(controller, {}), entries, by_dbf,
                  eligible_ids, player_class=classes.get(int(controller)))
                  for controller in ("1", "2")},
              "training_authorized": False,
              "warning": "Partial observed evidence constrains candidate lists; it does not identify an exact deck or hidden order. An end-of-log ranking must not be used as the belief at earlier decisions. Generated cards and unlisted variants remain possible."}
    if args.output.exists():
        p.error("output exists; choose a new audit file")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    if recovered_counts is not None:
        args.known_output.parent.mkdir(parents=True, exist_ok=True)
        args.known_output.write_text(json.dumps(recovered_counts, ensure_ascii=False,
                                               indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"event_count": report["event_count"],
                      "controllers": {key: {"observed_deck_card_count": value["observed_deck_card_count"],
                                            "best_mismatch": value["best_mismatch"],
                                            "equally_best_candidates": value["equally_best_candidates"],
                                            "top": value["top_candidates"][:3]}
                                      for key, value in report["controllers"].items()}},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
