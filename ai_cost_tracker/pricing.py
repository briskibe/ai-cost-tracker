"""Pricing utilities for supported language models."""

from __future__ import annotations

from typing import Dict, Tuple

# USD per 1M tokens: (input, output)
PRICING: Dict[str, Tuple[float, float]] = {
    "gpt-4": (30.0, 60.0),
    "gpt-4-turbo": (10.0, 30.0),
    "gpt-4o": (5.0, 15.0),
    "gpt-4o-mini": (0.15, 0.6),
    "gpt-3.5-turbo": (0.5, 1.5),
    "claude-opus-4": (15.0, 75.0),
    "claude-sonnet-4": (3.0, 15.0),
    "claude-sonnet-3.5": (3.0, 15.0),
    "claude-haiku-3.5": (0.8, 4.0),
}

_ALIASES = {
    "claude-3-5-sonnet": "claude-sonnet-3.5",
    "claude-3-5-haiku": "claude-haiku-3.5",
    "claude-3-opus": "claude-opus-4",
}


def _normalize_model_name(model: str) -> str:
    return model.strip().lower().replace("_", "-")


def _resolve_model_key(model: str) -> str:
    normalized = _normalize_model_name(model)

    if normalized in PRICING:
        return normalized

    for alias_prefix, canonical in _ALIASES.items():
        if normalized.startswith(alias_prefix):
            return canonical

    # Prefer more specific keys first, then allow prefix/substring matches.
    keys_by_specificity = sorted(PRICING.keys(), key=len, reverse=True)
    for key in keys_by_specificity:
        if normalized.startswith(key) or key in normalized:
            return key

    raise ValueError(f"Unsupported model for pricing: {model}")


def get_model_pricing(model: str) -> Tuple[float, float]:
    """Return `(input_per_million, output_per_million)` pricing for a model."""
    key = _resolve_model_key(model)
    return PRICING[key]


def calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """Calculate USD cost from model name and token counts."""
    if tokens_in < 0 or tokens_out < 0:
        raise ValueError("Token counts must be non-negative")

    input_per_million, output_per_million = get_model_pricing(model)
    input_cost = (tokens_in / 1_000_000.0) * input_per_million
    output_cost = (tokens_out / 1_000_000.0) * output_per_million
    return float(input_cost + output_cost)
