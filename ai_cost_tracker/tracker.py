"""Main tracking decorator and manual logging helpers."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, Union

from .models import CostLog
from .pricing import calculate_cost
from .storage import SQLiteStorage

logger = logging.getLogger(__name__)

FieldValue = Union[str, Callable[[], str]]
MetadataValue = Union[Dict[str, Any], Callable[[], Dict[str, Any]], None]

_storage: Optional[SQLiteStorage] = None
_org_id: str = "default"


def init_tracker(storage_path: str, org_id: str = "default") -> SQLiteStorage:
    """Initialize global tracker storage and default organization id."""
    global _storage, _org_id
    _storage = SQLiteStorage(storage_path)
    _org_id = org_id
    return _storage


def get_storage() -> SQLiteStorage:
    """Return the active storage instance, initializing a local default if needed."""
    global _storage
    if _storage is None:
        _storage = SQLiteStorage("ai_cost_tracker.db")
    return _storage


def track_costs(
    user_id: FieldValue,
    feature: FieldValue,
    metadata: MetadataValue = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to auto-track token usage and cost for provider API calls.

    The decorated function should return a response object (or dict) that includes
    a model identifier and token usage information.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if _is_coroutine_function(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.perf_counter()
                result = await func(*args, **kwargs)
                latency_ms = int((time.perf_counter() - start) * 1000)
                _safe_log_response(result, user_id, feature, metadata, latency_ms)
                return result

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            result = func(*args, **kwargs)
            latency_ms = int((time.perf_counter() - start) * 1000)
            _safe_log_response(result, user_id, feature, metadata, latency_ms)
            return result

        return sync_wrapper

    return decorator


def track_manual(
    user_id: str,
    feature: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    latency_ms: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
    org_id: Optional[str] = None,
) -> CostLog:
    """Manually log a usage record when a provider response is unavailable."""
    if tokens_in < 0 or tokens_out < 0:
        raise ValueError("tokens_in and tokens_out must be non-negative")
    if latency_ms < 0:
        raise ValueError("latency_ms must be non-negative")

    cost = calculate_cost(model, tokens_in, tokens_out)
    entry = CostLog(
        user_id=user_id,
        feature=feature,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost,
        latency_ms=latency_ms,
        timestamp=datetime.now(timezone.utc),
        org_id=org_id or _org_id,
        metadata=metadata or {},
    )
    get_storage().log(entry)
    return entry


def _safe_log_response(
    response: Any,
    user_id: FieldValue,
    feature: FieldValue,
    metadata: MetadataValue,
    latency_ms: int,
) -> None:
    try:
        model, tokens_in, tokens_out = _extract_usage(response)
        track_manual(
            user_id=_resolve_field(user_id, "unknown_user"),
            feature=_resolve_field(feature, "unknown_feature"),
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            metadata=_resolve_metadata(metadata),
        )
    except Exception as exc:  # pragma: no cover - defensive path
        logger.exception("Failed to record cost log: %s", exc)


def _extract_usage(response: Any) -> Tuple[str, int, int]:
    if response is None:
        raise ValueError("Response cannot be None")

    if isinstance(response, dict):
        model = str(response.get("model", "unknown"))
        usage = response.get("usage") or {}
        tokens_in = _int_value(usage.get("prompt_tokens", usage.get("input_tokens", 0)))
        tokens_out = _int_value(
            usage.get("completion_tokens", usage.get("output_tokens", 0))
        )
        return model, tokens_in, tokens_out

    model = str(getattr(response, "model", "unknown"))
    usage = getattr(response, "usage", None)
    if usage is None:
        raise ValueError("Response does not contain usage information")

    if isinstance(usage, dict):
        tokens_in = _int_value(usage.get("prompt_tokens", usage.get("input_tokens", 0)))
        tokens_out = _int_value(
            usage.get("completion_tokens", usage.get("output_tokens", 0))
        )
        return model, tokens_in, tokens_out

    tokens_in = _int_value(
        getattr(usage, "prompt_tokens", getattr(usage, "input_tokens", 0))
    )
    tokens_out = _int_value(
        getattr(usage, "completion_tokens", getattr(usage, "output_tokens", 0))
    )
    return model, tokens_in, tokens_out


def _resolve_field(value: FieldValue, fallback: str) -> str:
    try:
        resolved = value() if callable(value) else value
    except Exception:
        return fallback
    return str(resolved) if resolved else fallback


def _resolve_metadata(metadata: MetadataValue) -> Dict[str, Any]:
    if metadata is None:
        return {}
    try:
        resolved = metadata() if callable(metadata) else metadata
    except Exception:
        return {}
    return dict(resolved or {})


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _is_coroutine_function(func: Callable[..., Any]) -> bool:
    try:
        import inspect

        return inspect.iscoroutinefunction(func)
    except Exception:
        return False
