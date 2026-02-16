"""OpenAI usage example for ai-cost-tracker."""

from __future__ import annotations

import os

from openai import OpenAI

from ai_cost_tracker import init_tracker, track_costs

storage = init_tracker("openai_costs.db", org_id="example-org")


def _require_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY before running this example")
    return api_key


@track_costs(user_id="user_123", feature="chat")
def chat(client: OpenAI, prompt: str):
    """Send a basic chat request and track cost automatically."""
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=120,
    )


@track_costs(user_id="user_123", feature="summarize")
def summarize(client: OpenAI, text: str):
    """Summarize text with automatic cost tracking."""
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarize in 3 bullets."},
            {"role": "user", "content": text},
        ],
        max_tokens=160,
    )


def main() -> None:
    """Run two tracked calls and print cost stats."""
    client = OpenAI(api_key=_require_api_key())

    chat_response = chat(client, "Give me one tip to reduce LLM spend.")
    print("Chat response:", chat_response.choices[0].message.content)

    summarize_response = summarize(
        client,
        "Large prompts and verbose outputs drive cost growth. "
        "Caching and prompt tuning can reduce token usage.",
    )
    print("Summary response:", summarize_response.choices[0].message.content)

    print("\n--- Cost Stats ---")
    print("Total cost USD:", round(storage.get_total_cost(), 6))
    print("Top users:", storage.get_top_users(limit=5))
    print("Top features:", storage.get_top_features(limit=5))


if __name__ == "__main__":
    main()
