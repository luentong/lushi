# Power.log rules evidence — 2026-09-11

Source SHA-256: `61e3baf3d34f15a9e997eff54c00139f2beb0b224a9a62ec285f0c86661733ab`.
The raw log is kept out of Git because it contains player/account identifiers.
The importer strips those identifiers before analysis.

## Coverage

- Parsed games: 1
- Revealed card/enchantment entities: 103
- Entities belonging to the pinned Standard sets: 88
- Standard cards observed in PLAY blocks: 39
- Played Standard cards still lacking executable rules: 25

## Real-play implementation priority

| Card ID | Name | Class | Type | Plays | Triggers |
|---|---|---|---|---:|---:|
| `CORE_CFM_670` | Mayor Noggenfogger | NEUTRAL | MINION | 1 | 9 |
| `EDR_270` | Horn of Plenty | DRUID | SPELL | 3 | 0 |
| `EDR_271` | Grove Shaper | DRUID | MINION | 2 | 0 |
| `EDR_449` | Lunarwing Messenger | PRIEST | MINION | 1 | 0 |
| `EDR_449p` | Blessing of the Moon | PRIEST | HERO_POWER | 1 | 0 |
| `EDR_476` | Moonwell | PRIEST | SPELL | 1 | 0 |
| `EDR_846` | Shaladrassil | NEUTRAL | SPELL | 1 | 1 |
| `EDR_846t3` | Corrupted Laughing Sister | DREAM | MINION | 1 | 0 |
| `EDR_970` | Kaldorei Priestess | PRIEST | MINION | 1 | 0 |
| `END_011` | Acceleration Aura |  | SPELL | 3 | 5 |
| `FIR_907` | Amirdrassil | DRUID | LOCATION | 4 | 0 |
| `JAIL_200` | Infest the Scullery | DRUID | SPELL | 3 | 0 |
| `JAIL_201` | Secret Ingredient | DRUID | SPELL | 3 | 0 |
| `JAIL_432` | Mind Sweeper | PRIEST | MINION | 2 | 7 |
| `JAIL_433` | Unshackle Soul | PRIEST | SPELL | 1 | 2 |
| `JAIL_872` | Spider Rider | DRUID | MINION | 4 | 7 |
| `JAIL_875` | Staff of Trickery | DRUID | WEAPON | 2 | 7 |
| `JAIL_912` | Soothsayer | PRIEST | MINION | 1 | 1 |
| `MEND_042` | Lifebloom | DRUID | SPELL | 1 | 0 |
| `MEND_046` | Bashana Runetotem | DRUID | MINION | 1 | 0 |
| `TIME_432` | Intertwined Fate | PRIEST | SPELL | 1 | 0 |
| `TIME_701` | Waveshaping | DRUID | SPELL | 4 | 0 |
| `TIME_890t` | Atiesh the Greatstaff | PRIEST | WEAPON | 1 | 0 |
| `TLC_100` | Elise the Navigator | NEUTRAL | MINION | 2 | 0 |
| `TLC_100t1` | Un'Goro Jungle | NEUTRAL | LOCATION | 3 | 0 |

This report proves observed packet ordering and state/tag changes only. It does not by itself prove hidden candidate pools or server-side random logic.
