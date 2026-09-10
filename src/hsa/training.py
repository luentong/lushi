"""Framework-neutral helpers shared by policy training tools."""

from __future__ import annotations

import math


def temperature_scale_probabilities(
    probabilities: list[float], temperature: float
) -> list[float]:
    """Return a normalized temperature transform of a probability vector."""
    if temperature <= 0:
        raise ValueError("policy target temperature must be positive")
    if temperature == 1.0:
        return list(probabilities)
    scaled = [max(0.0, value) ** (1.0 / temperature) for value in probabilities]
    total = sum(scaled)
    if total <= 0:
        raise ValueError("policy target must contain positive probability mass")
    return [value / total for value in scaled]


def value_weighted_policy_target(
    probabilities: list[float], action_values: list[float], value_temperature: float
) -> list[float]:
    """Reweight root visits toward actions with stronger search mean values."""
    if value_temperature <= 0:
        raise ValueError("policy value temperature must be positive")
    if len(probabilities) != len(action_values):
        raise ValueError("policy probabilities and action values must align")
    if not probabilities:
        return []
    maximum = max(action_values)
    weights = [
        max(0.0, probability)
        * math.exp((value - maximum) / value_temperature)
        for probability, value in zip(probabilities, action_values, strict=True)
    ]
    total = sum(weights)
    if total <= 0:
        raise ValueError("value-weighted policy target has no probability mass")
    return [weight / total for weight in weights]
