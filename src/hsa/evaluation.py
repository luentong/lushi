"""Small, dependency-free statistics for paired agent benchmarks."""

from __future__ import annotations

import math
from collections import Counter, defaultdict


def wilson_interval(wins: int, games: int, z: float = 1.96) -> list[float]:
    if games <= 0:
        return [0.0, 0.0]
    proportion = wins / games
    denominator = 1.0 + z * z / games
    center = (proportion + z * z / (2.0 * games)) / denominator
    radius = z * math.sqrt(
        proportion * (1.0 - proportion) / games
        + z * z / (4.0 * games * games)
    ) / denominator
    return [max(0.0, center - radius), min(1.0, center + radius)]


def exact_two_sided_sign_p(successes: int, failures: int) -> float:
    """Exact two-sided binomial sign test, ignoring tied seed pairs."""
    decisive = successes + failures
    if decisive == 0:
        return 1.0
    minority = min(successes, failures)
    tail = sum(math.comb(decisive, index) for index in range(minority + 1))
    return min(1.0, 2.0 * tail / (2 ** decisive))


def paired_seed_summary(games: list[dict]) -> dict[str, object]:
    """Summarize two seat-swapped games per random seed."""
    by_seed: dict[int, list[dict]] = defaultdict(list)
    for game in games:
        by_seed[int(game["seed"])].append(game)
    pair_scores = Counter()
    for seed, pair in by_seed.items():
        seats = {int(game["mcts_seat"]) for game in pair}
        if len(pair) != 2 or seats != {0, 1}:
            raise ValueError(f"seed {seed} is not a complete seat-swapped pair")
        pair_scores[sum(bool(game["mcts_win"]) for game in pair)] += 1
    swept = pair_scores[2]
    split = pair_scores[1]
    lost = pair_scores[0]
    return {
        "pairs": len(by_seed),
        "swept_pairs": swept,
        "split_pairs": split,
        "lost_pairs": lost,
        "decisive_pairs": swept + lost,
        "exact_two_sided_sign_p": exact_two_sided_sign_p(swept, lost),
    }
