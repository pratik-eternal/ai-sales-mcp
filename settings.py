"""
STEP 1 — Read settings from .env

Copy .env.example → .env and fill in MCP_ACTING_USER_ID.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Express API (Node backend). Override via BACKEND_URL env (Horizon / .env).
    # Do not hardcode ngrok URLs here — trailing spaces break DNS.
    backend_url: str = "http://localhost:4000"
    internal_api_key: str = "dev-internal-key-change-me"

    # Which ERP user the MCP server pretends to be (controls permissions)
    mcp_acting_user_id: str = "cmrxavwxt008quumiiag90vui"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    # Trailing whitespace in env/defaults breaks DNS ("Name or service not known").
    s.backend_url = s.backend_url.strip().rstrip("/")
    s.internal_api_key = s.internal_api_key.strip()
    s.mcp_acting_user_id = s.mcp_acting_user_id.strip()
    return s
