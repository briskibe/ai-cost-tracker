"""Anthropic usage example for ai-cost-tracker."""

from __future__ import annotations

import os

from anthropic import Anthropic

from ai_cost_tracker import init_tracker, track_costs

storage = init_tracker("anthropic_costs.db", org_id="example-org")


def _require_api_key() -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Set ANTHROPIC_API_KEY before running this example")
    return api_key


@track_costs(user_id="user_456", feature="analysis")
def analyze(client: Anthropic, text: str):
    """Analyze input text using a Claude model."""
    return client.messages.create(
        model="claude-sonnet-3.5",
        max_tokens=220,
        messages=[{"role": "user", "content": f"Analyze this text: {text}"}],
    )


@track_costs(user_id="user_456", feature="rewrite")
def rewrite(client: Anthropic, text: str):
    """Rewrite text in a more concise style."""
    return client.messages.create(
        model="claude-haiku-3.5",
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": f"Rewrite this more clearly and concisely: {text}",
            }
        ],
    )


def _extract_text(response) -> str:
    if not response.content:
        return ""
    first = response.content[0]
    return getattr(first, "text", "")


def main() -> None:
    """Run two tracked Anthropic requests and print storage stats."""
    client = Anthropic(api_key=_require_api_key())

    analysis = analyze(client, "AI cost governance should be per feature and per user.")
    print("Analysis:\n", _extract_text(analysis))

    rewritten = rewrite(
        client,
        "Our monthly bill increased unexpectedly due to no visibility by customer.",
    )
    print("\nRewrite:\n", _extract_text(rewritten))

    print("\n--- Cost Stats ---")
    print("Total cost USD:", round(storage.get_total_cost(), 6))
    print("Top users:", storage.get_top_users(limit=5))
    print("Top features:", storage.get_top_features(limit=5))


if __name__ == "__main__":
    main()
