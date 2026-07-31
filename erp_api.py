"""
STEP 2 — Call the Express ERP backend

Every tool uses get_erp_data() to fetch JSON from the backend.
We never talk to the database directly.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from settings import get_settings


async def get_erp_data(path: str, params: dict | None = None) -> Any:
    """
    GET {BACKEND_URL}{path} with auth headers.

    Example:
        data = await get_erp_data("/employees", {"search": "Rahul"})
    """
    settings = get_settings()

    if not settings.mcp_acting_user_id:
        raise RuntimeError("Set MCP_ACTING_USER_ID in mcp_server/.env")

    url = f"{settings.backend_url.rstrip('/')}{path}"
    headers = {
        "X-Internal-Key": settings.internal_api_key,
        "X-Acting-User-Id": settings.mcp_acting_user_id,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url, headers=headers, params=params)
        if response.status_code >= 400:
            raise RuntimeError(f"Backend error {response.status_code}: {response.text}")
        return response.json()


def to_json(data: Any) -> str:
    """MCP tools return text — convert dict/list to JSON string."""
    return json.dumps(data, default=str)
