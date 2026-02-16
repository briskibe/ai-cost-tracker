from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_cost_tracker import (
    CostLog,
    calculate_cost,
    get_model_pricing,
    init_tracker,
    track_costs,
)
from ai_cost_tracker.storage import SQLiteStorage


def test_pricing_exact_and_partial_model_matches() -> None:
    in_price, out_price = get_model_pricing("gpt-4o-mini")
    assert in_price == 0.15
    assert out_price == 0.6

    # Partial model variant should match base pricing key.
    partial_cost = calculate_cost("gpt-4-0125-preview", tokens_in=1000, tokens_out=500)
    expected = (1000 / 1_000_000.0) * 30.0 + (500 / 1_000_000.0) * 60.0
    assert partial_cost == expected


def test_storage_log_query_and_rankings() -> None:
    with TemporaryDirectory() as tmp_dir:
        db_path = str(Path(tmp_dir) / "costs.db")
        storage = SQLiteStorage(db_path)

        storage.log(
            CostLog(
                user_id="alice",
                feature="chat",
                model="gpt-4o-mini",
                tokens_in=100,
                tokens_out=200,
                cost_usd=0.0002,
                latency_ms=120,
                timestamp=datetime.now(timezone.utc),
                org_id="org-1",
                metadata={"env": "test"},
            )
        )
        storage.log(
            CostLog(
                user_id="bob",
                feature="summary",
                model="claude-sonnet-3.5",
                tokens_in=300,
                tokens_out=500,
                cost_usd=0.0014,
                latency_ms=90,
                timestamp=datetime.now(timezone.utc),
                org_id="org-1",
                metadata={"env": "test"},
            )
        )
        storage.log(
            CostLog(
                user_id="alice",
                feature="summary",
                model="gpt-4o-mini",
                tokens_in=200,
                tokens_out=100,
                cost_usd=0.00009,
                latency_ms=70,
                timestamp=datetime.now(timezone.utc),
                org_id="org-1",
                metadata={"env": "test"},
            )
        )

        total = storage.get_total_cost(filters={"org_id": "org-1"})
        assert round(total, 8) == round(0.0002 + 0.0014 + 0.00009, 8)

        top_users = storage.get_top_users(limit=2)
        assert top_users[0][0] == "bob"
        assert top_users[1][0] == "alice"

        top_features = storage.get_top_features(limit=2)
        assert top_features[0][0] == "summary"
        assert top_features[1][0] == "chat"


def test_decorator_with_mock_openai_response() -> None:
    with TemporaryDirectory() as tmp_dir:
        db_path = str(Path(tmp_dir) / "decorator.db")
        storage = init_tracker(db_path, org_id="org-decorator")

        class MockUsage:
            prompt_tokens = 250
            completion_tokens = 125

        class MockResponse:
            model = "gpt-4o-mini"
            usage = MockUsage()

        @track_costs(user_id="user-1", feature="chat")
        def make_call() -> MockResponse:
            return MockResponse()

        _ = make_call()

        total = storage.get_total_cost(filters={"user_id": "user-1", "feature": "chat"})
        assert total > 0.0


def test_decorator_with_mock_anthropic_response_shape() -> None:
    with TemporaryDirectory() as tmp_dir:
        db_path = str(Path(tmp_dir) / "decorator_anthropic.db")
        storage = init_tracker(db_path, org_id="org-decorator")

        class MockUsage:
            input_tokens = 400
            output_tokens = 90

        class MockResponse:
            model = "claude-sonnet-3.5"
            usage = MockUsage()

        @track_costs(user_id="user-2", feature="analysis")
        def make_call() -> MockResponse:
            return MockResponse()

        _ = make_call()

        total = storage.get_total_cost(filters={"user_id": "user-2", "feature": "analysis"})
        assert total > 0.0
