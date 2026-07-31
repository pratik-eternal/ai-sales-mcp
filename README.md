# AI Sales MCP Server

Exposes ERP data to Cursor / Claude via MCP.

## How it works (3 files)

```
settings.py   →  reads .env (backend URL, API key, user id)
erp_api.py    →  get_erp_data("/sales") calls Express
server.py     →  @mcp.tool functions + mcp.run()
```

```
Cursor / Claude  →  server.py (tool)  →  erp_api.py  →  Express  →  Postgres
```

## Start the whole system

MCP talks to the Express backend. Start backend (and DB) first, then MCP.

### 1. Backend + database

```bash
# From repo root — ensure Postgres is running and DATABASE_URL is set
cd backend
cp ../.env.example ../.env   # or use backend/.env
npm install
npx prisma migrate deploy
npx tsx prisma/seed.ts
npm run dev
```

Backend: `http://localhost:4000`

### 2. MCP server deps + env

```bash
cd mcp_server
uv sync
cp .env.example .env
```

Edit `.env` (see [Environment variables](#environment-variables) below), then use one of the run modes in the sections that follow.

---

## Environment variables

Copy from `.env.example`:

```env
BACKEND_URL=http://localhost:4000
INTERNAL_API_KEY=dev-internal-key-change-me
MCP_ACTING_USER_ID=
MCP_TRANSPORT=stdio
```

| Variable | Required | Where to get the value |
|----------|----------|------------------------|
| `BACKEND_URL` | Yes | Express server URL. Local default: `http://localhost:4000` (see `backend/README.md`). Use your deployed API URL for remote backends. |
| `INTERNAL_API_KEY` | Yes | Must match the backend’s `INTERNAL_API_KEY`. Local default in `backend/.env` / root `.env.example`: `dev-internal-key-change-me`. Sent as `X-Internal-Key`. |
| `MCP_ACTING_USER_ID` | Yes | ERP **user id** (cuid) used for RBAC. Get it after seeding: login as `admin@acme.com` / `Password123!`, or query Postgres `User` table (`SELECT id, email FROM "User";`). Seed logins are in `backend/README.md`. Sent as `X-Acting-User-Id`. |
| `MCP_TRANSPORT` | No | Documented default is `stdio` (Cursor / Claude Desktop). For HTTP remote mode use the `fastmcp run --transport http` command below. |

Example after seeding (id will differ on your machine):

```env
MCP_ACTING_USER_ID=cmrxavwxt008quumiiag90vui   # e.g. admin@acme.com
```

---

## Inspect / develop with FastMCP

### Inspect tools (CLI summary)

```bash
cd mcp_server
uv run fastmcp inspect server.py
```

JSON report:

```bash
uv run fastmcp inspect server.py --format mcp
# or write to a file:
uv run fastmcp inspect server.py --format mcp -o inspect.json
```

### MCP Inspector (interactive UI)

Starts the server with the MCP Inspector for trying tools in the browser:

```bash
cd mcp_server
uv run fastmcp dev inspector server.py
```

Optional ports:

```bash
uv run fastmcp dev inspector server.py --ui-port 6274 --server-port 6277
```

Ensure `.env` is filled and the Express backend is running before calling tools.

### Run stdio locally (manual)

```bash
uv run python server.py
# or
uv run fastmcp run server.py --transport stdio
```

---

## Local setup — Claude Desktop

Install this server into Claude Desktop (writes Claude’s MCP config):

```bash
cd mcp_server
uv run fastmcp install claude-desktop server.py \
  --name ai-sales-erp \
  --env-file .env
```

Or pass env vars explicitly:

```bash
uv run fastmcp install claude-desktop server.py \
  --name ai-sales-erp \
  --env BACKEND_URL=http://localhost:4000 \
  --env INTERNAL_API_KEY=dev-internal-key-change-me \
  --env MCP_ACTING_USER_ID=YOUR_USER_ID
```

Then **restart Claude Desktop**. Claude launches the MCP process via stdio; keep the Express backend running on `BACKEND_URL`.

Config file (macOS): `~/Library/Application Support/Claude/claude_desktop_config.json`

---

## Local setup — Cursor

### Option A — FastMCP install

```bash
cd mcp_server
uv run fastmcp install cursor server.py \
  --name ai-sales-erp \
  --env-file .env
```

### Option B — Manual `mcp.json`

```json
{
  "mcpServers": {
    "ai-sales-erp": {
      "command": "/Users/pratik/Work/ai-sales/mcp_server/.venv/bin/python",
      "args": ["server.py"],
      "cwd": "/Users/pratik/Work/ai-sales/mcp_server",
      "env": {
        "BACKEND_URL": "http://localhost:4000",
        "INTERNAL_API_KEY": "dev-internal-key-change-me",
        "MCP_ACTING_USER_ID": "YOUR_USER_ID"
      }
    }
  }
}
```

Update paths for your machine. Restart Cursor / reload MCP after changes.

---

## Remote setup (HTTP)

Local Claude/Cursor installs use **stdio** (client spawns `server.py`). For a **remote** MCP, run the server as an HTTP process and point clients at its URL.

### 1. Start MCP over HTTP

```bash
cd mcp_server
# Backend must be reachable from this host (set BACKEND_URL in .env)
uv run fastmcp run server.py --transport http --host 0.0.0.0 --port 8000
```

Default path is `/mcp/`, so the endpoint is:

```text
http://<host>:8000/mcp/
```

Use your public hostname / reverse proxy URL in production.

### 2. Connect Claude Desktop to remote HTTP

Claude Desktop’s config file prefers **stdio**. Bridge HTTP with `mcp-remote`:

```json
{
  "mcpServers": {
    "ai-sales-erp": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://YOUR_HOST:8000/mcp/"]
    }
  }
}
```

Or add a **custom connector** in Claude: Settings → Connectors → Add custom connector → paste `https://YOUR_HOST/mcp/` (for internet-reachable servers; OAuth if required).

### 3. Connect Cursor to remote HTTP

In Cursor MCP settings / `mcp.json`, use a URL entry (Streamable HTTP):

```json
{
  "mcpServers": {
    "ai-sales-erp": {
      "url": "http://YOUR_HOST:8000/mcp/"
    }
  }
}
```

If your Cursor build only supports stdio, use the same `npx mcp-remote ...` bridge as Claude Desktop.

### 4. Quick check against a remote server

```bash
uv run fastmcp list http://YOUR_HOST:8000/mcp/
uv run fastmcp inspect http://YOUR_HOST:8000/mcp/
```

---

## Tools (all in `server.py`)

| Tool | What it does |
|------|----------------|
| `search_employees` | Find employees |
| `list_sales` | List sales with filters |
| `search_customers` | Find customers |
| `get_dashboard` | Dashboard metrics |
| `top_customers` | Top customers by revenue |
| `top_products` | Top products by revenue |

## Add a new tool

Open `server.py` and copy this pattern:

```python
@mcp.tool
async def my_new_tool(name: str) -> str:
    """Short description for the AI."""
    data = await get_erp_data("/some/path", {"search": name})
    return to_json(data)
```

Restart the MCP client (or reload MCP) so it picks up the new tool.
