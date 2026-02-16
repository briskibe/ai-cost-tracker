"""FastAPI integration example with automatic per-request cost tracking."""

from __future__ import annotations

import asyncio
import contextvars
from typing import Any, Dict

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from ai_cost_tracker import get_storage, init_tracker, track_costs

app = FastAPI(title="ai-cost-tracker FastAPI Example")
init_tracker("fastapi_costs.db", org_id="fastapi-example")

current_user: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_user", default="anonymous"
)
current_feature: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_feature", default="unknown"
)


class PromptRequest(BaseModel):
    prompt: str


@app.middleware("http")
async def user_context_middleware(request, call_next):
    """Load user id from header into request context."""
    user_id = request.headers.get("x-user-id", "anonymous")
    token = current_user.set(user_id)
    try:
        return await call_next(request)
    finally:
        current_user.reset(token)


@track_costs(user_id=lambda: current_user.get(), feature=lambda: current_feature.get())
async def tracked_chat_call(prompt: str) -> Dict[str, Any]:
    """Simulate a tracked provider response for a chat endpoint."""
    await asyncio.sleep(0.05)
    return {
        "model": "gpt-4o-mini",
        "usage": {"prompt_tokens": max(12, len(prompt) // 4), "completion_tokens": 80},
        "content": f"Echo: {prompt}",
    }


@track_costs(user_id=lambda: current_user.get(), feature=lambda: current_feature.get())
async def tracked_summary_call(prompt: str) -> Dict[str, Any]:
    """Simulate a tracked provider response for a summary endpoint."""
    await asyncio.sleep(0.03)
    return {
        "model": "claude-sonnet-3.5",
        "usage": {"input_tokens": max(20, len(prompt) // 3), "output_tokens": 120},
        "content": "Summary complete.",
    }


@app.post("/chat")
async def chat(payload: PromptRequest, x_user_id: str | None = Header(default=None)):
    """Chat endpoint with automatic usage tracking."""
    if x_user_id is not None and not x_user_id.strip():
        raise HTTPException(status_code=400, detail="x-user-id header cannot be empty")

    token = current_feature.set("chat")
    try:
        result = await tracked_chat_call(payload.prompt)
        return {"message": result["content"], "model": result["model"]}
    finally:
        current_feature.reset(token)


@app.post("/summarize")
async def summarize(payload: PromptRequest, x_user_id: str | None = Header(default=None)):
    """Summarization endpoint with automatic usage tracking."""
    if x_user_id is not None and not x_user_id.strip():
        raise HTTPException(status_code=400, detail="x-user-id header cannot be empty")

    token = current_feature.set("summarize")
    try:
        result = await tracked_summary_call(payload.prompt)
        return {"message": result["content"], "model": result["model"]}
    finally:
        current_feature.reset(token)


@app.get("/costs/summary")
async def cost_summary():
    """Return aggregate cost stats from SQLite storage."""
    storage = get_storage()
    return {
        "total_cost_usd": storage.get_total_cost(),
        "top_users": storage.get_top_users(limit=10),
        "top_features": storage.get_top_features(limit=10),
    }


# Run with: uvicorn examples.example_fastapi:app --reload
