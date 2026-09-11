# Power.log rules evidence — 2026-09-11

Source SHA-256: `23282dea458ed0dfb0cbd50cc051655e47650f780c9ab2e2f566f1d4d0e06743`.
The raw log is kept out of Git because it contains player/account identifiers.
The importer strips those identifiers before analysis.

## Coverage

- Parsed games: 1
- Revealed card/enchantment entities: 80
- Entities belonging to the pinned Standard sets: 71
- Standard cards observed in PLAY blocks: 35
- Played Standard cards still lacking executable rules: 19

## Real-play implementation priority

| Card ID | Name | Class | Type | Plays | Triggers |
|---|---|---|---|---:|---:|
| `CAP_404` | Harsh Sentence | WARLOCK | SPELL | 2 | 0 |
| `CATA_155` | Arisen Onyxia | DEATHKNIGHT | MINION | 1 | 3 |
| `CATA_190h` | Deathwing, Worldbreaker |  | HERO | 1 | 1 |
| `CATA_190p` | Ruthless | NEUTRAL | HERO_POWER | 5 | 0 |
| `CATA_492` | Shrine of Twilight | WARLOCK | LOCATION | 11 | 4 |
| `CATA_496` | Cursed Chains | WARLOCK | SPELL | 3 | 0 |
| `DINO_431` | Atlasaurus | PRIEST | MINION | 1 | 1 |
| `EDR_449` | Lunarwing Messenger | PRIEST | MINION | 1 | 3 |
| `EDR_449p` | Blessing of the Moon | PRIEST | HERO_POWER | 3 | 0 |
| `EDR_970` | Kaldorei Priestess | PRIEST | MINION | 1 | 0 |
| `JAIL_432` | Mind Sweeper | PRIEST | MINION | 1 | 13 |
| `JAIL_509` | Godfrey the Betrayer | WARLOCK | MINION | 1 | 1 |
| `JAIL_511` | Spire of Solitude | WARLOCK | LOCATION | 9 | 0 |
| `JAIL_514` | The Unseen Atlas | WARLOCK | SPELL | 3 | 0 |
| `JAIL_912` | Soothsayer | PRIEST | MINION | 1 | 1 |
| `TIME_432` | Intertwined Fate | PRIEST | SPELL | 2 | 0 |
| `TIME_890` | Medivh the Hallowed | PRIEST | MINION | 1 | 0 |
| `TIME_890t` | Atiesh the Greatstaff | PRIEST | WEAPON | 1 | 0 |
| `TLC_451` | Cursed Catacombs | WARLOCK | SPELL | 3 | 0 |

This report proves observed packet ordering and state/tag changes only. It does not by itself prove hidden candidate pools or server-side random logic.
