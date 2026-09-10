"""Framework-neutral helpers shared by policy training tools."""

from __future__ import annotations


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
